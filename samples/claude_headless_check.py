"""claude -p의 json 출력을 읽어 성공 여부를 판정한다. 종료 코드만 믿지 않고 세 가지를 함께 본다."""
import json
import subprocess
import sys


def ask(prompt, *options):
    p = subprocess.run(['claude', '-p', prompt, '--output-format', 'json', *options], capture_output=True, text=True)
    try:
        data = json.loads(p.stdout)
    except json.JSONDecodeError:
        return {'ok': False, 'reason': f'json이 아닌 출력(종료 코드 {p.returncode}): {p.stdout.strip()[:120]}'}
    problems = []
    if p.returncode != 0:
        problems.append(f'종료 코드 {p.returncode}')
    if data.get('is_error') or data.get('subtype') != 'success':
        problems.append(f"subtype={data.get('subtype')}")
    if data.get('permission_denials'):
        problems.append('권한 거부: ' + ', '.join(d['tool_name'] for d in data['permission_denials']))
    return {'ok': not problems, 'reason': '; '.join(problems), 'result': data.get('result')}


if __name__ == '__main__':
    print(json.dumps(ask(sys.argv[1], *sys.argv[2:]), ensure_ascii=False))
