# services/publish_queue.py
"""내구성 발행 큐 — data/publish_queue.json. post_verify_tracker 패턴 미러링.

스케줄러가 발행 job을 적재(enqueue)하고, 단일 worker가 due_jobs를 drain한다.
실패 시 지수 백오프로 재시도, MAX_ATTEMPTS 초과 시 dead.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from filelock import FileLock

import config

logger = logging.getLogger(__name__)

BACKOFF_MINUTES = [10, 30, 120, 360, 360]
MAX_ATTEMPTS = 5


def _path() -> Path:
    # 호출 시점에 config.DATA_DIR 해석 → 테스트의 temp_data_dir 격리가 유효
    return config.DATA_DIR / "publish_queue.json"


def _lock() -> FileLock:
    return FileLock(str(_path()) + ".lock")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _ts(minutes: int) -> str:
    return (_now() + timedelta(minutes=minutes)).isoformat()


def _load() -> list[dict]:
    p = _path()
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(queue: list[dict]) -> None:
    _path().write_text(
        json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def enqueue(rank: int, draft_id: str, title: str = "") -> bool:
    with _lock():
        queue = _load()
        for j in queue:
            if j.get("draft_id") == draft_id and j.get("status") == "pending":
                return False
        queue.append({
            "job_id": draft_id,
            "rank": rank,
            "draft_id": draft_id,
            "title": title,
            "status": "pending",
            "attempts": 0,
            "next_run": _now_iso(),
            "last_error": "",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        })
        _save(queue)
        logger.info("[publish_queue] 적재 rank=%s draft=%s", rank, draft_id)
        return True


def due_jobs() -> list[dict]:
    now = _now_iso()
    due = [j for j in _load()
           if j.get("status") == "pending" and j.get("next_run", "") <= now]
    due.sort(key=lambda j: j.get("next_run", ""))
    return due


def mark_done(job_id: str) -> None:
    with _lock():
        queue = _load()
        matched = False
        for j in queue:
            if j.get("job_id") == job_id:
                j["status"] = "done"
                j["updated_at"] = _now_iso()
                matched = True
        if not matched:
            logger.warning("[publish_queue] mark_done: job_id 없음 %s", job_id)
        _save(queue)


def reschedule(job_id: str, error: str = "") -> str:
    with _lock():
        queue = _load()
        state = "pending"
        matched = False
        for j in queue:
            if j.get("job_id") != job_id:
                continue
            matched = True
            j["attempts"] = int(j.get("attempts", 0)) + 1
            j["last_error"] = (error or "")[:200]
            j["updated_at"] = _now_iso()
            if j["attempts"] >= MAX_ATTEMPTS:
                j["status"] = "dead"
                state = "dead"
            else:
                idx = min(j["attempts"] - 1, len(BACKOFF_MINUTES) - 1)
                j["next_run"] = _ts(BACKOFF_MINUTES[idx])
                state = "pending"
        if not matched:
            logger.warning("[publish_queue] reschedule: job_id 없음 %s", job_id)
        _save(queue)
        return state


def purge_done(keep_days: int = 3) -> None:
    cutoff = (_now() - timedelta(days=keep_days)).isoformat()
    with _lock():
        queue = _load()
        kept = [j for j in queue
                if j.get("status") == "pending" or j.get("updated_at", "") > cutoff]
        if len(kept) != len(queue):
            _save(kept)
