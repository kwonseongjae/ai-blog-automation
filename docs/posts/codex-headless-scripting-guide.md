# Codex 스크립트 실행: 읽기 전용에서 파일 없이 종료 코드 0이 나왔다

`codex exec`를 읽기 전용 샌드박스로 실행하면 파일이 만들어지지 않아도 종료 코드가 0으로 끝났습니다. 열두 가지 조건으로 출력 위치와 `--json` 이벤트, 성공 판정 방법을 확인했습니다.

순서는 출력 위치, `--json` 이벤트, 샌드박스 설정, 판정 스크립트입니다.

확인일: 2026-11-17 · 범위: Linux 한 환경, Codex CLI 0.167.2, 모델 gpt-6.1-sol(추론 강도 low), 조건별 1회 실행

## 한 번 실행하는 명령은 codex exec이다

공식 비대화 실행 문서는 `codex exec`로 TUI를 열지 않고 스크립트나 CI에서 Codex를 실행한다고 설명합니다.

문서에서 읽은 기본 동작은 세 가지입니다. 진행 상황은 표준 오류로 나가고 마지막 답변만 표준 출력에 찍힙니다. 기본 샌드박스는 읽기 전용입니다. Git 저장소 밖에서는 `--skip-git-repo-check`가 필요합니다.

아래 표는 열두 가지 중 다섯 가지의 결과이고 나머지는 이어지는 절에서 다룹니다. 실행에는 공통으로 `--skip-git-repo-check --ignore-user-config`를 붙였습니다.

| 조건 | 종료 코드 | 표준 출력 | 확인한 점 |
|---|---:|---|---|
| 기본 출력 | 0 | `5` | 진행 문구는 표준 오류로 분리 |
| `--json` | 0 | 이벤트 줄들 | 이벤트 4종 확인 |
| `-o out.txt` | 0 | `5` | 파일에도 `5` 저장 |
| `--output-schema` | 0 | `{"answer":5}` | 스키마에 맞는 JSON만 출력 |
| 없는 모델 | 1 | 빈 출력 | 표준 오류에 오류 문구 |

## 출력은 표준 출력과 표준 오류로 나뉜다

가장 단순한 확인은 짧은 계산 요청이었고 표준 출력에는 `5`만 나왔습니다.

```bash
codex exec "2 더하기 3은? 숫자만 답하세요."
```

표준 오류에는 헤더와 진행 문구가 나왔습니다. 결과를 파일로 저장하는 스크립트에서는 표준 출력만 리디렉션하면 답만 남습니다.

`-o out.txt`를 붙이면 마지막 메시지가 파일에 저장되고 표준 출력에도 같은 내용이 나왔습니다. 문서의 설명과 같은 동작이었습니다.

## --json을 붙이면 이벤트가 한 줄씩 나온다

같은 요청에 `--json`을 붙이면 표준 출력이 JSON 줄의 연속으로 바뀝니다. 이번에 나온 이벤트 종류는 네 가지였습니다.

```json
{"type":"thread.started","thread_id":"…"}
{"type":"turn.started"}
{"type":"item.completed","item":{"type":"agent_message","text":"5"}}
{"type":"turn.completed","usage":{"input_tokens":15757,…}}
```

답변 본문은 `item.completed` 이벤트의 `agent_message` 항목에 들어 있었습니다. 마지막 줄 `turn.completed`에는 사용량이 있었습니다.

문서에는 `turn.failed`와 `error` 이벤트도 나옵니다. 정상 실행에서는 나오지 않았고 없는 모델을 지정했을 때 확인했습니다.

`--output-schema`에는 정수 `answer` 하나를 요구하는 스키마를 넘겼습니다. 출력은 `{"answer":5}` 한 줄이었고 종료 코드는 0이었습니다.

## 입력은 인자와 표준 입력으로 넣을 수 있다

내용은 표준 입력으로 넘기고 지시는 인자로 주는 방식을 확인했습니다. 두 줄짜리 날씨 메모를 `printf`로 넘기고 "부산 날씨만 알려 주세요"라고 요청했습니다.

출력은 "부산의 날씨는 흐림입니다."였고 종료 코드는 0이었습니다. 문서에서는 이 방식을 인자를 지시로, 표준 입력을 추가 맥락으로 쓴다고 설명합니다.

프롬프트 인자 없이 `codex exec -`로 실행하면 표준 입력 전체가 프롬프트가 됩니다. 계산 요청을 이 방식으로 넘기자 `5`가 나왔습니다.

## 읽기 전용에서는 파일을 못 만들어도 종료 코드가 0이었다

가장 주의할 결과는 샌드박스 조건에서 나왔습니다. 같은 요청을 두 가지 설정으로 실행했습니다.

```bash
codex exec -s read-only "이 폴더에 made.txt 파일을 만들고 \"테스트\" 한 줄을 쓰세요."
codex exec -s workspace-write "같은 요청"
```

| 샌드박스 | 종료 코드 | 답변 | made.txt |
|---|---:|---|---|
| `read-only` | 0 | 폴더가 읽기 전용이라 만들 수 없다는 설명 | 없음 |
| `workspace-write` | 0 | 파일에 한 줄을 썼다는 설명 | 있음(`테스트`) |

읽기 전용에서는 파일이 없는데도 종료 코드가 0입니다. 요청한 작업이 끝났는지는 종료 코드로 알 수 없었습니다.

답변 문장은 실행마다 달랐습니다. 읽기 전용 실행에서 한 번은 "현재 폴더가 읽기 전용이라 파일을 만들 수 없습니다."가, 다른 한 번은 "못 합니다."가 나왔습니다. 문장을 읽어서 판정하는 방식은 안정적이지 않았습니다.

## 성공 여부를 판정하는 스크립트

`samples/codex_headless_check.py`는 `--json` 출력을 읽고 종료 코드와 오류 이벤트, `turn.completed` 여부를 확인합니다. JSON이 아니거나 객체가 아닌 줄은 건너뜁니다.

```python
def ask(prompt, *options, cwd='.'):
    p = subprocess.run(
        ['codex', 'exec', '--json', '--skip-git-repo-check',
         *options, prompt],
        capture_output=True, text=True,
        stdin=subprocess.DEVNULL, cwd=cwd,
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
    return {'ok': not problems, 'reason': '; '.join(problems)}
```

네 가지 요청으로 이 함수를 돌렸습니다. 마지막 열은 요청한 파일이 실제로 있는지 따로 확인한 값입니다.

| 요청 | `ok` | `reason` | 파일 |
|---|---|---|---|
| 계산 | `true` | 빈 문자열 | 해당 없음 |
| 읽기 전용에서 파일 만들기 | `true` | 빈 문자열 | 없음 |
| 작업 폴더 쓰기에서 파일 만들기 | `true` | 빈 문자열 | 있음 |
| 없는 모델 | `false` | 종료 코드 1; 오류 이벤트; `turn.completed` 없음 | 해당 없음 |

둘째 줄이 문제입니다. 함수는 성공으로 판정했지만 파일은 없었습니다. 이 함수가 알려 주는 것은 Codex가 한 턴을 끝냈다는 사실뿐이었습니다.

그래서 파일을 만드는 작업은 파일이 있는지 스크립트가 직접 확인해야 했습니다. 샘플에는 이를 위한 `made(디렉터리, 이름)` 함수도 넣었습니다. 읽기 전용 실행의 이벤트는 계산 요청과 같은 네 종류였고 쓰기를 시도한 흔적은 나오지 않았습니다.

![조건을 하나씩 바꿔 codex exec를 한 번 실행하고 종료 코드와 이벤트, 결과 파일로 판정하는 순서](asset:flow)

## 이어서 실행하려면 resume을 쓴다

앞 실행에서 "제 이름은 하늘입니다"라고 알려 준 뒤 같은 폴더에서 이름을 다시 물었습니다. 이어서 실행하는 명령은 아래와 같습니다.

```bash
codex exec resume --last "제 이름이 뭐라고 했죠? 이름만 답하세요."
```

답은 "하늘"이었습니다. `resume` 없이 새로 실행했을 때는 "모릅니다."였습니다. 이번에는 `--last`만 확인했고 세션 ID를 지정하는 방식은 실행하지 않았습니다.

## 스크립트에서 쓸 때 확인하는 순서

1. 증상: 결과 파일에 답 말고 다른 글자가 섞인다. 원인 후보: 표준 오류를 같이 저장했다. 확인: 리디렉션에서 표준 오류를 분리했는지 본다.

2. 증상: 종료 코드가 1이고 출력이 비어 있다. 원인 후보: 모델 이름이나 계정 문제다. 확인: 표준 오류의 `ERROR:` 줄을 읽는다.

3. 증상: 종료 코드는 0인데 요청한 파일이 없다. 원인 후보: 읽기 전용 샌드박스다. 확인: `-s workspace-write`를 지정했는지 보고 파일 존재를 직접 확인한다.

4. 증상: 앞서 알려 준 내용을 기억하지 못한다. 원인 후보: `resume` 없이 새로 실행했다. 확인: 명령에 `resume --last`가 있는지 본다.

## 이 실험으로 알 수 없는 것

이번 기록은 Linux 한 환경에서 조건별 한 번씩 실행한 결과입니다. 반복 실행에서 같은 결과가 나오는지는 확인하지 않았습니다.

첫 실행 한 건은 142.7초가 걸렸고 나머지는 5~13초였습니다. 처음 실행하는 설정 폴더 때문인지는 확인하지 못했습니다.

API 키로 인증하는 방식과 `--ephemeral`, `--output-schema`와 `-o`를 함께 쓰는 방식은 실행하지 않았습니다. 승인 정책 옵션과 `danger-full-access`도 범위에 없습니다.

읽기 전용에서 모델이 쓰기를 시도하지 않은 것인지 막힌 것인지는 이벤트만으로 구분하지 못했습니다. 표준 입력을 열어 둔 채 실행하는 경우도 확인하지 않았습니다. Windows와 macOS, 다른 모델도 비교하지 않았습니다.

## 참고 문서

- [OpenAI: Codex 비대화 실행](https://learn.chatgpt.com/docs/non-interactive-mode)
- [OpenAI: Codex 개발자 명령 `codex exec`](https://learn.chatgpt.com/docs/developer-commands)
- [예제 스크립트](https://github.com/kwonseongjae/ai-blog-automation/blob/main/samples/codex_headless_check.py)
- [이번 실행 기록](https://github.com/kwonseongjae/ai-blog-automation/blob/main/docs/posts/evidence/codex-headless-scripting.json)
