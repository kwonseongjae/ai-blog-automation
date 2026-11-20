# Claude Code headless(-p) 스크립트 실행: 출력 형식과 종료 코드, 조용히 실패하는 경우를 확인한 기록

Claude Code를 스크립트에서 한 번 실행하는 방식으로 열한 가지 조건을 확인했고 종료 코드만으로는 놓치는 실패가 있었습니다. 파일을 만들지 못했는데도 종료 코드는 0이었습니다. 이 기록은 json 출력에서 성공 여부를 판정하는 데 초점을 맞춥니다.

확인일: 2026-11-16 · 범위: Linux 한 환경, Claude Code 2.1.325, 모델 별칭 haiku, 조건별 1회 실행

## 한 번 실행하는 방식은 -p 옵션 하나로 시작한다

프로그램 실행 문서에서 읽은 시작 방법은 `claude`에 `-p` 또는 `--print`를 붙이는 것이고 대화 없이 한 번 실행합니다. 기본 출력 형식은 일반 글인 `text`입니다. 결과와 세션 ID를 담는 `json`, 줄마다 JSON을 내보내는 실시간 출력용 `stream-json`도 있습니다.

문서에는 성공 시 종료 코드가 0이고 실패 시에는 0이 아닌 값이라고 나옵니다. `claude -p`를 SIGTERM으로 멈췄을 때의 코드는 143입니다. 다만 이 설명만으로 요청한 작업까지 끝났다고 판단할 수 있는지는 직접 확인할 필요가 있었습니다.

## 출력 형식과 입력 방법을 확인했다

실행에는 공통으로 `--model haiku --setting-sources project,local`을 붙였고 먼저 짧은 계산을 요청했습니다. 기본 텍스트 출력부터 확인합니다.

```bash
claude -p "2 더하기 3은? 숫자만 답하세요." \
  --model haiku \
  --setting-sources project,local
```

표준 출력에는 `5`만 나왔고 종료 코드는 0이었습니다. 같은 요청에 `--output-format json`을 붙이면 한 줄 JSON이 나옵니다. 그중 판정에 관련된 값은 다음과 같았습니다.

```json
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "num_turns": 1,
  "result": "5",
  "permission_denials": []
}
```

문서에서 소개한 필드는 아래와 같고 정상 실행에서 확인한 출력에는 그 밖에 시간과 사용량 필드도 있었습니다. 모든 필드를 읽을 필요는 없었습니다.

| 필드 | 이 글에서 확인할 내용 |
|---|---|
| `result` | 응답 내용. 제한으로 중단된 실행에서는 없었음 |
| `session_id` | 이어서 실행할 때 사용하는 세션 ID |
| `total_cost_usd` | 비용 정보 |
| `num_turns` | 턴 수 |
| `is_error` | 오류 여부 |
| `subtype` | `success` 또는 확인된 제한 오류 종류 |
| `permission_denials` | 거부된 도구 호출 기록 |
| `structured_output` | JSON 스키마에 맞춘 결과 |

표준 입력도 확인했고 `printf`로 두 줄 내용을 전달한 뒤 “부산 날씨만 알려 주세요”라고 요청했습니다. 출력은 “부산의 날씨는 흐림입니다.”였으며 종료 코드는 0입니다. 이는 전달한 내용에 대한 응답을 확인한 결과입니다.

문서에는 아래처럼 파일 내용을 파이프로 넣는 예가 있고 출력을 파일로 저장할 수도 있다고 나옵니다. 파이프 입력의 상한은 10MB로 안내되어 있습니다.

```bash
cat build-error.txt | claude -p '...' > output.txt
```

`--json-schema`에는 정수 `answer` 하나를 요구하는 스키마를 전달했고 종료 코드 0을 확인했습니다. `structured_output`은 `{"answer": 5}`였습니다. 같은 실행의 `result`에는 `{"answer":5}`가 문자열로 들어 있었습니다.

세션을 이어서 실행할 때는 앞선 응답의 `session_id`를 사용했고 `--resume <세션 ID>`로 이름을 다시 물었습니다. 앞에서 “제 이름은 하늘입니다”라고 알려 준 세션은 “하늘”이라고 답했습니다. 새로 실행한 요청의 답은 “모릅니다. 이 대화에서 이름을 말씀하신 적이 없습니다.”였습니다.

문서에는 이어서 실행하는 옵션으로 `--continue`도 소개되어 있습니다. 이번에 직접 확인한 방식은 세션 ID를 지정하는 `--resume`입니다.

![조건을 하나씩 바꿔 스크립트에서 한 번 실행하고 종료 코드와 json 필드로 성공 여부를 판정하는 순서](asset:flow)

## 제한을 넘으면 종료 코드 1로 끝난다

파일을 읽어야 하는 요청에 `--max-turns 1`을 붙였고 종료 코드는 1이었습니다. 같은 요청을 `--max-turns 3`으로 실행했을 때는 둘째 줄 내용을 답했습니다. 두 결과의 차이는 json에도 남았습니다.

| 조건 | 종료 코드 | 관찰한 결과 |
|---|---:|---|
| `--max-turns 1` | 1 | `subtype: "error_max_turns"`, `is_error: true`, `result` 없음 |
| `--max-turns 3` | 0 | `subtype: "success"`, 둘째 줄 내용을 답함 |
| `--max-budget-usd 0.0001` | 1 | `subtype: "error_max_budget_usd"`, `is_error: true`, `result` 없음 |

턴 제한과 예산 상한으로 멈춘 출력에는 `result` 자체가 없었고 이 필드만 읽는 스크립트는 답을 얻지 못합니다. 오류를 구분할 때는 `subtype`을 확인할 수 있었습니다.

없는 모델 이름인 `--model nonexistent-model`도 실행했고 종료 코드 1과 다음 메시지를 확인했습니다.

```text
There's an issue with the selected model (nonexistent-model). It may not exist or you may not have access to it.
```

이 조건은 처음에 잘못 실행했고 뒤에 공통 옵션인 `--model haiku`까지 붙여 정상 응답을 받았습니다. 겹친 모델 옵션에서는 뒤의 값이 쓰인 것으로 보였습니다. 모델 옵션을 하나만 남겨 다시 실행한 결과가 위 메시지입니다.

## 권한이 거부돼도 종료 코드는 0이었다

가장 주의할 결과는 허용하지 않은 `touch made.txt` 요청에서 나왔고 파일은 만들어지지 않았습니다. 그런데 종료 코드는 0입니다. json의 `is_error`도 `false`였습니다.

```json
{
  "subtype": "success",
  "is_error": false
}
```

실패의 흔적은 `permission_denials`에 있었고 `Bash` 거부 기록이 한 건 들어 있었습니다. 답변에도 승인이 필요해 막혔다는 설명이 나왔습니다. 종료 코드와 `subtype`만 읽었다면 요청이 끝났다고 처리할 수 있는 상태였습니다.

문서에서 읽은 권한 설명은 이 결과를 이해하는 데 도움이 됐고 일반(Manual) 모드의 승인 처리 조건도 확인할 수 있었습니다. `PermissionRequest` 훅이나 `--permission-prompt-tool` 등이 승인하지 않으면 승인이 필요한 호출은 거부됩니다.

같은 요청에 `--allowedTools "Bash(touch *)"`를 붙였을 때는 파일이 만들어졌고 거부 목록은 비어 있었습니다. 종료 코드는 이때도 0입니다. 두 실행을 가른 값은 종료 코드가 아닌 거부 기록이었습니다.

처음에는 `echo hello`로 권한 거부를 확인하려 했고 이 명령은 승인 없이 실행됐습니다. 거부 기록도 없었습니다. 읽기만 하는 단순 명령은 별도 허용 없이 실행될 수 있어 `touch`로 바꿔 확인한 것입니다.

## 성공 여부를 판정하는 스크립트

`samples/claude_headless_check.py`에서는 json을 읽고 종료 코드와 오류 상태를 확인한 뒤 권한 거부도 검사합니다. 거부 기록이 있으면 실패로 판정합니다.

```python
import json
import subprocess
import sys


def ask(prompt, *options):
    p = subprocess.run(
        ['claude', '-p', prompt, '--output-format', 'json', *options],
        capture_output=True,
        text=True,
    )
    try:
        data = json.loads(p.stdout)
    except json.JSONDecodeError:
        return {
            'ok': False,
            'reason': (
                f'json이 아닌 출력(종료 코드 {p.returncode}): '
                f'{p.stdout.strip()[:120]}'
            ),
        }

    problems = []
    if p.returncode != 0:
        problems.append(f'종료 코드 {p.returncode}')
    if data.get('is_error') or data.get('subtype') != 'success':
        problems.append(f"subtype={data.get('subtype')}")
    if data.get('permission_denials'):
        problems.append(
            '권한 거부: '
            + ', '.join(d['tool_name'] for d in data['permission_denials'])
        )

    return {
        'ok': not problems,
        'reason': '; '.join(problems),
        'result': data.get('result'),
    }
```

이 함수로 세 가지 요청을 실행했고 계산 요청은 성공으로 판정됐습니다. `result`는 `"5"`입니다.

| 요청 | `ok` | `reason` | `result` |
|---|---|---|---|
| 계산 요청 | `true` | 빈 문자열 | `"5"` |
| 파일 읽기 요청에 `--max-turns 1` | `false` | `종료 코드 1; subtype=error_max_turns` | `null` |
| 허용하지 않은 `touch` 요청 | `false` | `권한 거부: Bash` | 실행되지 않았다는 설명 글 |

세 번째 요청은 종료 코드가 0이고 `subtype`도 `success`였지만 함수는 실패로 판정했습니다. 거부 기록이 있었기 때문입니다. `result`에는 `touch made2.txt`가 실행되지 않았다는 설명이 들어 있었습니다.

이 판정은 응답 문장이 성공처럼 보이더라도 거부 기록을 함께 확인하고 실패로 처리합니다. 여기서 `ok`는 종료 코드만 옮긴 값이 아닙니다. 작업을 시키는 스크립트에서는 이 차이를 구분할 필요가 있었습니다.

## 스크립트에서 쓸 때 확인하는 순서

1. 증상: 출력에서 답을 꺼내지 못한다. 원인 후보: 기본 `text` 출력을 json으로 읽고 있다. 확인: `--output-format json`을 지정했는지 보고 실제 표준 출력을 확인한다.

2. 증상: 종료 코드가 1이고 `result`가 없다. 원인 후보: 턴 제한이나 예산 상한에 걸렸다. 확인: `is_error`와 `subtype`을 읽고 지정한 제한 값을 대조한다.

3. 증상: 없는 모델을 지정했는데 정상 응답이 나온다. 원인 후보: 모델 옵션이 겹쳐 뒤에 다른 값이 붙었다. 확인: 실행 명령 전체에서 `--model`을 찾고 하나만 남겨 다시 확인한다.

4. 증상: 종료 코드는 0인데 요청한 파일이 없다. 원인 후보: 도구 호출이 거부됐다. 확인: `permission_denials`를 읽고 필요한 도구를 `--allowedTools`로 허용했는지 확인한다.

5. 증상: 앞서 알려 준 이름을 기억하지 못한다. 원인 후보: 이전 세션을 이어서 실행하지 않았다. 확인: 앞선 출력의 `session_id`와 `--resume`에 전달한 값을 대조한다.

6. 증상: 스키마로 요구한 값을 꺼내기 어렵다. 원인 후보: 문자열인 `result`만 읽고 있다. 확인: `--json-schema`를 지정한 실행의 `structured_output`을 확인한다.

## 이 실험으로 알 수 없는 것

이번 기록은 Linux 한 환경에서 조건별 한 번씩 실행한 결과이고 반복 실행에서도 같은 결과가 나오는지는 확인하지 않았습니다. 다른 모델과 Windows·macOS도 범위에 없습니다.

`stream-json`의 이벤트 구성은 직접 확인하지 않았고 `--bare`와 `--append-system-prompt`도 실행하지 않았습니다. 입력 10MB 상한은 문서에서 읽은 내용입니다. Codex의 비대화 실행도 비교하지 않았습니다.

확인한 권한 거부 사례에서는 종료 코드 0만으로 작업 완료를 판정할 수 없었고 json의 거부 기록까지 읽어야 차이가 드러났습니다. 다만 이 스크립트가 성공으로 판정하는 모든 요청의 실제 작업 결과까지 보장하는지는 확인하지 않았습니다.

## 참고 문서

- [Anthropic: Claude Code를 프로그램에서 실행하기](https://code.claude.com/docs/en/headless)
- [예제 스크립트](https://github.com/kwonseongjae/ai-blog-automation/blob/main/samples/claude_headless_check.py)
- [이번 실행 기록](https://github.com/kwonseongjae/ai-blog-automation/blob/main/docs/posts/evidence/claude-headless-scripting.json)