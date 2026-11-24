"""Append article stage events observed by the scheduled publisher."""
import json
import logging
import os
import re
import stat
from datetime import datetime, timezone


def emit(root, article, stage, state, summary, link=None):
    artifact, title = article.get("id"), article.get("title")
    if not isinstance(artifact, str) or not re.fullmatch(r"[a-z][a-z0-9-]{1,70}", artifact):
        return
    if not isinstance(title, str) or not title.strip():
        return
    event = {
        "artifact": artifact, "title": title.strip()[:240], "stage": stage, "state": state,
        "at": datetime.now(timezone.utc).isoformat(), "summary": summary, "actor": "개발노트 발행기",
        "evidence": ["automation/learning_blog.py"],
    }
    if link:  # The publisher validates the target and public post path before returning.
        event["link"] = link
    path = root / "storage/sjon-operations/tistory-ai-dev-note.jsonl"
    try:
        data = (json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8")
        if not path.parent.resolve().is_relative_to(root.resolve()):
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        try:
            if stat.S_ISREG(os.fstat(fd).st_mode) and os.write(fd, data) != len(data):
                logging.getLogger(__name__).warning("운영 이벤트를 끝까지 기록하지 못했습니다")
        finally:
            os.close(fd)
    except (OSError, ValueError, RuntimeError):
        logging.getLogger(__name__).warning("운영 이벤트를 기록하지 못했습니다")
