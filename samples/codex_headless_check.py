import json
import subprocess
from pathlib import Path


def ask(prompt, *options, cwd='.'):
    p = subprocess.run(
        ['codex', 'exec', '--json', '--skip-git-repo-check', *options, prompt],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        cwd=cwd,
    )
    events = []
    for line in p.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)

    types = [e.get('type') for e in events]
    problems = []
    if p.returncode != 0:
        problems.append(f'종료 코드 {p.returncode}')
    if 'turn.failed' in types or 'error' in types:
        problems.append('오류 이벤트')
    if 'turn.completed' not in types:
        problems.append('turn.completed 없음')

    message = None
    for e in events:
        item = e.get('item') or {}
        if e.get('type') == 'item.completed' and item.get('type') == 'agent_message':
            message = item.get('text')
    return {'ok': not problems, 'reason': '; '.join(problems), 'result': message, 'types': types}


def made(directory, name):
    return (Path(directory) / name).is_file()
