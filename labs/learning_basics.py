"""작은 자동화 예제: 각 함수가 정상·실패 조건을 직접 확인한다."""


def lesson_timezone():
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    utc = datetime(2026, 11, 12, 15, 1, tzinfo=timezone.utc)
    korean = utc.astimezone(ZoneInfo('Asia/Seoul'))
    assert utc.date().isoformat() == '2026-11-12'
    assert korean.date().isoformat() == '2026-11-13'
    assert korean.tzinfo is not None
    return [f'UTC 날짜: {utc.date()}', f'한국 날짜: {korean.date()}',
            '검증: 같은 순간에도 날짜가 다를 수 있습니다.']


def lesson_paths():
    from pathlib import Path
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        base = Path(directory)
        data = base / 'data'
        data.mkdir()
        (data / 'example.txt').write_text('학습 기록', encoding='utf-8')
        nested = base / 'other'
        nested.mkdir()
        assert (base / 'data/example.txt').read_text(encoding='utf-8') == '학습 기록'
        assert not (nested / 'data/example.txt').exists()
        assert not (base / '../outside').resolve().is_relative_to(base.resolve())
    return ['기준 경로에서 읽기: 성공', '다른 작업 경로에서 같은 상대경로: 파일 없음',
            '검증: 기준 디렉터리 밖 경로를 구분했습니다.']


def lesson_input():
    def read_title(payload):
        if not isinstance(payload, dict):
            raise ValueError('객체가 필요합니다')
        title = payload.get('title')
        if not isinstance(title, str) or not title.strip():
            raise ValueError('비어 있지 않은 제목이 필요합니다')
        return title.strip()

    assert read_title({'title': '  첫 실습  '}) == '첫 실습'
    failures = 0
    for value in [None, [], {}, {'title': None}, {'title': '  '}, {'title': 12}]:
        try:
            read_title(value)
        except ValueError:
            failures += 1
    assert failures == 6
    return ['정상 제목: 첫 실습', '거부한 잘못된 입력: 6개',
            '검증: 필드의 존재뿐 아니라 타입과 빈 문자열을 확인했습니다.']


def lesson_atomic():
    import json
    import os
    from pathlib import Path
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        target = Path(directory) / 'state.json'
        temp = target.with_suffix('.tmp')
        target.write_text('{"status":"before"}', encoding='utf-8')
        temp.write_text('{"status":', encoding='utf-8')
        assert json.loads(target.read_text())['status'] == 'before'
        temp.write_text('{"status":"after"}', encoding='utf-8')
        os.replace(temp, target)
        assert json.loads(target.read_text())['status'] == 'after'
        assert not temp.exists()
    return ['교체 전 기존 상태: before', '교체 후 새 상태: after',
            '검증: 임시 파일을 쓰는 중에는 기존 JSON이 보존됐습니다.']


def lesson_duplicate():
    import sqlite3

    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE TABLE jobs (request_id TEXT PRIMARY KEY, result TEXT NOT NULL)')
        first = db.execute('INSERT OR IGNORE INTO jobs VALUES (?, ?)', ('request-1', 'done')).rowcount
        second = db.execute('INSERT OR IGNORE INTO jobs VALUES (?, ?)', ('request-1', 'done')).rowcount
        count = db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
        assert (first, second, count) == (1, 0, 1)
    return ['첫 요청 저장: 1개', '같은 요청 다시 저장: 0개', '남은 행: 1개',
            '검증: 같은 식별자를 중복 저장하지 않았습니다.']


def lesson_timeout():
    import subprocess
    import sys

    normal = subprocess.run([sys.executable, '-c', 'print("ok")'], capture_output=True,
                            text=True, timeout=3, check=True)
    assert normal.stdout.strip() == 'ok'
    stopped = False
    try:
        subprocess.run([sys.executable, '-c', 'import time; time.sleep(2)'], timeout=0.1, check=True)
    except subprocess.TimeoutExpired:
        stopped = True
    assert stopped
    return ['정상 작업 출력: ok', '지연 작업: TimeoutExpired',
            '검증: 제한 시간을 넘긴 작업을 성공으로 처리하지 않았습니다.']


def lesson_url():
    from urllib.parse import urlsplit

    expected = 'jacks-aiblog.tistory.com'

    def allowed(value):
        parsed = urlsplit(value)
        return parsed.scheme == 'https' and parsed.netloc == expected

    assert allowed('https://jacks-aiblog.tistory.com/2')
    assert not allowed('https://jacks-aiblog.tistory.com.evil.test/2')
    assert not allowed('https://jacks-aiblog.tistory.com@evil.test/2')
    assert not allowed('http://jacks-aiblog.tistory.com/2')
    assert not allowed('https://jack-0314.tistory.com/2')
    return ['정확한 HTTPS 호스트: 허용', '비슷한 이름·사용자 정보·다른 블로그: 거부',
            '검증: 문자열 포함 여부로 발행 대상을 판단하지 않았습니다.']


LABS = {
    'timezone': lesson_timezone, 'paths': lesson_paths, 'input': lesson_input,
    'atomic': lesson_atomic, 'duplicate': lesson_duplicate,
    'timeout': lesson_timeout, 'url': lesson_url,
}


def run_lab(name):
    if name not in LABS:
        raise ValueError('등록된 실습만 실행할 수 있습니다')
    return LABS[name]()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('name', choices=LABS)
    for line in run_lab(parser.parse_args().name):
        print(line)
