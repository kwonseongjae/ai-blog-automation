# Claude Code hooks 사용법: 훅으로 명령 막기, 막히는 경우와 조용히 통과하는 경우 일곱 가지 확인

Claude Code hooks 사용법을 확인하려고 훅 하나로 명령을 막아 봤고 설정을 잘못했을 때 명령이 그대로 실행되는 경우도 함께 재현했습니다. 막힌 결과보다 눈에 남은 것은 훅을 설정해 놓고도 차단되지 않는 경우였습니다. 호출 기록과 결과 파일을 따로 보니 어디서 어긋났는지 구분할 수 있었습니다.

확인일: 2026-11-16 · 범위: Linux 한 환경, Claude Code 2.1.325, 모델 별칭 haiku, 조건별 1회 실행, 대화형 화면은 사용하지 않음

## 훅은 도구를 쓰기 직전에 끼어드는 셸 명령이다

가이드에서 읽은 훅은 사용자가 정의한 셸 명령이며 Claude Code가 정해진 시점에 실행합니다. 모델이 실행 여부를 고르는 방식과 구분되는 결정적 제어입니다. 이벤트는 서른 개가 넘고 `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop` 등이 있습니다. 이번에는 도구 사용 직전의 `PreToolUse`를 골랐습니다.

설정 위치에 따라 적용 범위와 공유 여부가 달라지며 프로젝트 설정은 저장소에 커밋할 수도 있습니다. `~/.claude/settings.json`은 내 모든 프로젝트에 적용하고 공유하지 않습니다. `.claude/settings.json`은 한 프로젝트에서 공유할 설정입니다. `.claude/settings.local.json`은 한 프로젝트에서 공유하지 않을 설정입니다. 조직 관리 설정과 플러그인의 `hooks/hooks.json`, 스킬이나 서브에이전트 머리글에도 둘 수 있습니다.

설정은 `hooks` 아래에 이벤트를 두고 그 안에 `matcher`와 실행할 `hooks` 배열을 넣는 구조입니다. `PreToolUse`는 표준 입력으로 JSON을 받습니다. 입력에는 `hook_event_name`, `tool_name`, `tool_input`이 있고 Bash 명령은 `tool_input.command`에 들어 있습니다. 문서가 안내한 차단 방법은 stderr에 이유를 쓰고 종료 코드 2로 끝내거나 거부 JSON을 출력하는 것입니다. 거부 JSON에는 `hookSpecificOutput` 안에 `permissionDecision: "deny"`와 `permissionDecisionReason`을 담습니다. 프롬프트의 `/hooks`로 목록을 볼 수 있다는 안내도 있습니다. 훅은 내 권한으로 셸 명령을 실행한다는 보안 경고가 붙어 있습니다.

## 훅을 만들어 명령 하나를 막는다

예제 스크립트는 `samples/claude_hook_guard.sh`이며 실험 프로젝트에서는 `hooks/guard.sh`로 두었습니다. 받은 입력에 `danger-test`가 있으면 이유를 남기고 종료 코드 2로 끝냅니다. 호출 여부를 구분하려고 입력을 받은 직후 `hook.log`에 기록을 남겼습니다.

```bash
#!/bin/bash
input=$(cat)
echo "fired" >> "$CLAUDE_PROJECT_DIR/hook.log"
if echo "$input" | grep -q 'danger-test'; then
  echo "danger-test가 들어간 명령은 이 프로젝트에서 막혀 있습니다" >&2
  exit 2
fi
exit 0
```

이 예제는 입력 JSON 전체에서 문자열을 찾으며 `tool_input.command`만 따로 해석하지는 않습니다. 이번 요청을 막는 데 사용한 단순한 검사입니다.

스크립트를 저장한 뒤에는 실행 권한을 주고 프로젝트의 `.claude/settings.json`에 다음 설정을 넣습니다. `matcher`는 `Bash`입니다. 문서 예제처럼 경로는 `"$CLAUDE_PROJECT_DIR"`를 기준으로 적었습니다.

```bash
chmod +x hooks/guard.sh
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/hooks/guard.sh" }
        ]
      }
    ]
  }
}
```

![훅을 설정하고 명령을 실행시켜 파일이 생겼는지와 훅이 호출됐는지를 확인하는 순서](asset:flow)

요청에는 결과 파일을 만드는 명령을 넣었고 뒤에 차단할 문자열을 붙였습니다. 사용한 요청 문장은 다음과 같습니다.

> Bash 도구로 `touch ran.flag && echo danger-test` 를 실행하고 출력을 알려 주세요. 실행이 막히면 막힌 이유만 알려 주세요.

실행 명령의 `<요청>`에는 위 문장을 넣으며 조건마다 새 임시 폴더를 사용했습니다. 프로젝트 설정과 로컬 설정을 읽도록 지정한 명령입니다.

```bash
claude -p "<요청>" --model haiku --setting-sources project,local --allowedTools Bash --output-format json
```

판정은 답변만 읽지 않고 파일도 확인하는 방식으로 잡았습니다. `ran.flag`가 생기면 명령이 실행된 것입니다. `hook.log`에 `fired`가 있으면 훅이 호출된 것입니다.

## 일곱 가지 조건으로 실행했다

훅을 둔 조건은 H1부터 H7까지 일곱 가지이며 비교 기준으로 훅이 없는 H0도 실행했습니다. 차단된 조건은 둘입니다. 나머지 다섯 조건에서는 명령이 실행됐습니다.

| 조건 | 바꾼 내용 | 명령 실행됨 | 훅 호출됨 |
|---|---|---|---|
| H0 훅 없음 | 설정 파일 없음 | 실행됨 | 해당 없음 |
| H1 exit 2 | 위 스크립트와 설정 그대로 | 막힘 | 1회 |
| H2 JSON deny | stderr 대신 `permissionDecision: "deny"` JSON을 출력하고 exit 0 | 막힘 | 1회 |
| H3 스크립트 exit 1 | 오류 메시지를 쓰고 exit 1로 끝남 | 실행됨 | 1회 |
| H4 경로가 틀림 | 존재하지 않는 `hooks/missing.sh`를 지정 | 실행됨 | 0회 |
| H5 실행 권한 없음 | 스크립트 권한을 644로 둠 | 실행됨 | 0회 |
| H6 matcher 소문자 | `matcher`를 `bash`로 씀 | 실행됨 | 0회 |
| H7 범위에서 제외 | `--setting-sources local`로 project 설정을 읽지 않음 | 실행됨 | 0회 |

H1과 H2는 결과 파일이 생기지 않았고 권한 거부 기록에는 모두 `Bash`가 남았습니다. 답변도 훅이 막은 이유를 전했습니다. H1은 `hooks/guard.sh`가 명령의 `danger-test` 때문에 막았다고 설명했습니다. H2는 “danger-test가 들어간 명령은 이 프로젝트에서 막혀 있습니다”라는 훅 메시지를 인용했습니다.

H3은 호출 기록이 남았지만 결과 파일도 생겼으며 오류 메시지가 차단으로 이어지지는 않았습니다. 이번 환경에서 exit 1은 명령 실행을 막지 못했습니다.

## 훅이 조용히 통과하는 경우

H4부터 H7까지는 호출 기록이 없었고 명령 실행에 오류나 경고도 보여 주지 않았습니다. 답변은 명령이 막히지 않고 실행됐다고 전했습니다. 명령을 실행하는 쪽에서 보면 훅이 없는 H0과 같은 모양입니다.

이때 호출 기록을 따로 남겨 둔 덕분에 H3과 나머지 실패를 구분할 수 있었습니다. H3은 훅이 실행됐지만 차단하지 못한 경우입니다. H4부터 H7까지는 훅 스크립트의 호출 기록 자체가 없었습니다.

문서에서 읽은 차단 방법은 exit 2와 거부 JSON이며 exit 1이나 경로 오류의 처리는 읽은 범위에 없었습니다. 이 글의 해당 결과는 실행에서 확인한 내용입니다. 오류로 끝나거나 호출되지 않은 훅은 이번 조건에서 명령을 통과시켰습니다.

훅 설정이 있다는 사실만으로 차단을 믿기는 어려웠고 실제로 막히는 결과를 확인할 필요가 있었습니다. 호출 기록과 결과 파일은 서로 다른 것을 알려 줍니다. 둘 중 하나만 봤다면 실패 원인을 좁히기 어려웠을 것입니다.

## 훅이 안 먹힐 때 확인하는 순서

호출 기록이 남는 경우부터 구분하고 기록이 없다면 실행 파일과 설정을 차례로 확인하는 순서로 잡았습니다. 이번 결과를 바탕으로 만든 점검 목록입니다.

1. 증상: 호출 기록과 결과 파일이 모두 있습니다. 원인 후보: 훅은 실행됐지만 차단 응답이 맞지 않습니다. 확인: 종료 코드가 2인지 확인하고 JSON 방식이면 `permissionDecision: "deny"`가 있는지 봅니다.
2. 증상: 호출 기록이 없고 명령은 실행됩니다. 원인 후보: 설정에 적은 스크립트 경로가 틀렸습니다. 확인: `"$CLAUDE_PROJECT_DIR"/hooks/guard.sh`가 실제 파일을 가리키는지 봅니다.
3. 증상: 파일 경로가 맞는데 호출 기록이 없습니다. 원인 후보: 스크립트에 실행 권한이 없습니다. 확인: H5처럼 권한이 644로 되어 있는지 보고 실행 권한을 확인합니다.
4. 증상: 경로와 실행 권한을 확인해도 기록이 없습니다. 원인 후보: `matcher`의 대소문자가 다릅니다. 확인: 이번 설정의 `Bash`와 비교하고 `bash`로 적지 않았는지 봅니다.
5. 증상: 설정 파일이 있는데도 호출 기록이 없습니다. 원인 후보: 실행할 때 프로젝트 설정을 읽지 않았습니다. 확인: `--setting-sources local`로 실행했는지 보고 프로젝트 설정이 범위에 포함됐는지 확인합니다.

## 이 실험으로 알 수 없는 것

각 조건은 한 번씩 실행했으며 Linux 한 환경의 Claude Code 2.1.325와 모델 별칭 haiku만 사용했습니다. 반복했을 때도 같은 결과가 나오는지는 확인하지 않았습니다.

대화형 화면을 사용하지 않았고 `/hooks` 목록과 훅 신뢰 확인 창도 직접 확인하지 않았습니다. `PostToolUse` 등 다른 이벤트도 범위 밖입니다. `Edit`·`Write` 차단과 개인 설정의 훅도 시험하지 않았습니다.

입력 JSON을 파이썬 등으로 해석하는 방식은 다루지 않았으며 다른 모델이나 Codex의 훅도 확인하지 않았습니다. Windows와 macOS에서의 동작 역시 이 기록으로 판단할 수 없습니다.

위험한 명령을 허용 목록에서 빼는 권한 설정과 함께 쓰는 방법도 있지만 이번에는 실행하지 않았습니다.

## 참고 문서

- [Anthropic: Claude Code 훅 가이드](https://code.claude.com/docs/en/hooks-guide)
- [예제 스크립트](https://github.com/kwonseongjae/ai-blog-automation/blob/main/samples/claude_hook_guard.sh)
- [예제 설정](https://github.com/kwonseongjae/ai-blog-automation/blob/main/samples/claude_hook_settings.example.json)
- [이번 실행 기록](https://github.com/kwonseongjae/ai-blog-automation/blob/main/docs/posts/evidence/claude-hooks-guard.json)
