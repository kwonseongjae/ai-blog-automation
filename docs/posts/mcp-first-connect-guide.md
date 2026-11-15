# MCP 서버 처음 연결하기: Codex와 Claude Code에 연습용 서버를 붙여 도구 호출까지 확인한 기록

연습용 MCP 서버를 연결한 뒤 Claude Code는 도구 허용을 지정했을 때, Codex는 승인 설정을 `approve`로 덮어썼을 때 덧셈 결과 42를 반환했고 그 외 조건에서는 호출이 막혔습니다. 서버 연결과 도구 호출 허용은 서로 다른 단계입니다.

확인일: 2026-11-16 · 범위: Linux 한 환경, Codex CLI 0.167.2, Claude Code 2.1.325, 조건별 1회 실행, stdio 서버만 확인

## MCP는 외부 도구를 붙이는 공개 규격이다

Claude Code 문서는 MCP를 AI 도구 연동을 위한 공개 표준으로 설명하며 서버를 붙이면 도구나 데이터베이스, API를 사용할 수 있다고 안내합니다. 이 글에서 연결한 것은 직접 만든 덧셈 도구입니다.

문서에 나오는 Claude Code의 전송 방식은 http, sse, stdio이고 이번에 실행한 서버는 stdio 방식입니다. 표준 입력과 표준 출력으로 메시지를 주고받으며 HTTP 서버 연결은 확인하지 않았습니다.

Codex 문서도 stdio 서버 등록을 안내하며 스트리머블 HTTP 서버는 `--url`로 등록한다고 설명합니다. OAuth 로그인 명령은 `codex mcp login <이름>`입니다. 여기서는 두 기능을 실행하지 않았습니다.

## 연습용 서버는 파일 하나로 만든다

서버 파일은 `samples/mcp_demo_server.py`이고 파이썬 표준 라이브러리만 사용합니다. 표준 입출력으로 줄 단위 JSON-RPC를 주고받는 구조입니다.

도구는 두 개이며 `add`는 두 정수의 합을 구하고 `word_count`는 공백으로 나눈 단어 수를 셉니다. 환경변수 `MCP_DEMO_LOG`를 지정하면 해당 파일에 서버 시작과 도구 호출 내용을 남깁니다.

두 도구에 연결하기 전에 프로토콜 메시지를 파이프로 넣어 서버 자체가 요청에 응답하는지 먼저 확인했습니다. 메시지를 넣은 순서는 다음과 같습니다.

1. `initialize`
2. `notifications/initialized`
3. `tools/list`
4. `tools/call`: `add`에 17과 25 전달
5. `tools/call`: `word_count`에 `"hello mcp world"` 전달

`add`의 결과는 42였고 `word_count`의 결과는 3이었습니다. 서버 로그에는 `start`와 두 번의 호출 기록이 남았으며 끝에는 `stop`도 확인했습니다. 서버 자체의 응답을 확인한 뒤 연결 설정으로 넘어갔습니다.

![연습용 서버를 두 도구에 연결하고 도구 호출과 서버 로그를 확인하는 순서](asset:flow)

## Claude Code에 연결한다

작업은 임시 프로젝트 폴더에서 진행했고 사용자 설정 파일을 건드리지 않으려고 프로젝트 범위로 등록했습니다. `<로그 파일>`은 실제 기록을 남길 파일 경로입니다.

실제 실행에서는 임시 폴더에 둔 같은 내용의 파일을 절대 경로로 지정했습니다.

```bash
claude mcp add --scope project demo -e MCP_DEMO_LOG=<로그 파일> -- python3 <서버 파일 경로>
```

Claude Code 문서에서 `--`는 Claude 쪽 옵션과 서버 실행 명령을 나누며 뒤에 오는 내용은 서버로 그대로 전달됩니다. 위 명령은 `python3`로 서버 파일 `samples/mcp_demo_server.py`를 실행합니다.

저장 범위는 문서에 세 가지로 나뉘어 있고 기본값은 `local`입니다. 이번에는 `.mcp.json`을 확인할 수 있는 `project`를 선택했습니다.

| 범위 | 적용 대상 | 저장 위치 | 버전 관리로 공유 |
|---|---|---|---|
| `local` | 현재 프로젝트 | `~/.claude.json` | 안 됨 |
| `project` | 현재 프로젝트 | 프로젝트 루트의 `.mcp.json` | 팀과 공유 |
| `user` | 모든 프로젝트 | `~/.claude.json` | 안 됨 |

생성된 `.mcp.json`에는 `mcpServers.demo` 아래에 실행 명령과 인자, 환경변수가 저장됐습니다. 서버와 로그 파일 경로를 자리 표시자로 적으면 다음 구조입니다.

```json
{
  "mcpServers": {
    "demo": {
      "type": "stdio",
      "command": "python3",
      "args": ["<서버 파일 경로>"],
      "env": {
        "MCP_DEMO_LOG": "<로그 파일>"
      }
    }
  }
}
```

등록 후 `claude mcp list`를 실행하자 demo는 다음 상태로 표시됐습니다. `claude mcp get demo`에서도 같은 상태가 나왔습니다.

```text
⏸ Pending approval (run `claude` to approve)
```

상세 출력에는 Type `stdio`와 실행 명령, 인자, 환경변수가 함께 보였습니다. 승인 전에 연결 확인을 하지 않는다는 추측은 이 목록 출력에만 근거합니다.

문서는 프로젝트 범위의 `.mcp.json` 서버를 쓰기 전에 대화형 세션에서 승인을 묻는다고 설명하며 세션 안의 `/mcp`도 안내합니다. 이번에는 대화형 화면을 열지 않았고 아래 결과는 모두 `claude -p` 실행 결과입니다.

요청 문장은 조건마다 같았고 모델 별칭은 `haiku`를 사용했습니다. 설정을 읽는 범위로 지정한 값은 `--setting-sources project,local`입니다.

> demo MCP 서버의 add 도구로 17과 25를 더하고 결과 숫자만 알려 주세요. 그 도구를 쓸 수 없으면 쓸 수 없다고만 답하세요.

| 조건 | 실행 결과 | 서버 로그 |
|---|---|---|
| A. 설정 파일의 서버 사용, `--allowedTools mcp__demo__add` 지정 | 42, 3턴 | `start`, `call add {"a": 17, "b": 25}` |
| B. A에 `--mcp-config .mcp.json --strict-mcp-config` 추가 | 42, 3턴 | A와 같음 |
| C. B에서 `--allowedTools` 제거 | “이 도구는 사용할 수 없습니다.”, 3턴. 권한 거부 기록에 `mcp__demo__add` 표시 | `start`만 |
| D. 서버 경로가 틀린 설정 | “쓸 수 없습니다.”, 2턴 | 없음 |

A에서는 목록에 승인 대기로 표시됐는데도 `-p` 실행에서 서버 연결과 호출이 이뤄졌습니다. 문서가 승인 절차를 설명하는 대상은 대화형 세션입니다.

실행 중 도구 이름은 `mcp__<서버 이름>__<도구 이름>` 형태였습니다. 덧셈 도구는 `mcp__demo__add`, 다른 도구는 `mcp__demo__word_count`로 표시됐습니다.

시작 정보를 보려고 `--output-format stream-json --verbose`도 사용했습니다. 정상 설정에서는 다음 상태와 도구 두 개를 확인했고 경로가 틀린 설정은 `status: failed`였으며 MCP 도구가 없었습니다.

```json
{"name": "demo", "status": "connected"}
```

## Codex에 연결한다

Codex에서는 개인 전역 설정에 서버가 남지 않도록 `CODEX_HOME`을 임시 폴더로 바꾸고 인증 파일만 링크해 실행했습니다. 등록에 사용한 명령은 다음과 같습니다.

```bash
CODEX_HOME=<임시 폴더> codex mcp add demo --env MCP_DEMO_LOG=<로그 파일> -- python3 <서버 파일 경로>
```

Codex 문서에서 MCP 설정의 기본 위치는 `~/.codex/config.toml`이며 신뢰한 프로젝트에서는 `.codex/config.toml`도 사용합니다. 서버별 설정은 `[mcp_servers.<이름>]` 표에 들어갑니다.

이번에는 임시 폴더의 `config.toml`을 사용했고 기록된 설정은 다음과 같습니다. 아래 경로는 해당 실행 기록의 자리 표시자입니다.

```toml
[mcp_servers.demo]
command = "python3"
args = ["<작업폴더>/demo_server.py"]

[mcp_servers.demo.env]
MCP_DEMO_LOG = "<작업폴더>/codex.log"
```

`codex mcp list`에는 Name, Command, Args, Env, Cwd, Status, Auth 열이 나왔으며 demo의 Status는 `enabled`였습니다. Auth는 `Unsupported`로 표시됐고 환경변수 값은 `*****`로 가려졌습니다.

`codex mcp get demo`에서는 `enabled true`와 `transport stdio`, 실행 명령과 인자를 확인했습니다. 삭제 명령으로 표시된 것은 `codex mcp remove demo`입니다.

호출 확인에는 Claude Code에서 쓴 요청 문장을 그대로 사용했고 다음 명령에 조건별 옵션을 붙였습니다. 실행 출력 첫머리에 표시된 승인 정책은 `approval: never`입니다.

```bash
codex exec -m gpt-6.1-sol -c model_reasoning_effort=low --skip-git-repo-check
```

승인 설정은 파일을 수정하지 않고 실행 옵션으로 덮어썼습니다. `approve` 조건에 사용한 옵션은 다음과 같으며 다른 조건에서는 값만 바꿨습니다.

```bash
-c 'mcp_servers.demo.default_tools_approval_mode="approve"'
```

| 조건 | 실행 결과 | 서버 로그 |
|---|---|---|
| 기본 설정, `-s read-only` | “쓸 수 없습니다.”, `mcp: demo/add (failed)`, 승인 필요 오류 | `start`만 |
| 기본 설정, `-s workspace-write` | 기본 `read-only`와 같음 | `start`만 |
| `default_tools_approval_mode="approve"` | 42, `mcp: demo/add (completed)` | `start`, `call add {"a": 17, "b": 25}` |
| `default_tools_approval_mode="auto"` | “쓸 수 없습니다.”, 같은 승인 필요 오류 | `start`만 |
| `default_tools_approval_mode="writes"` | “쓸 수 없습니다.”, 같은 승인 필요 오류 | `start`만 |
| `approve`에서 서버 경로를 틀리게 지정 | “쓸 수 없습니다.”, 출력에 서버 시작 실패를 알리는 줄은 없었음 | 없음 |

기본 설정에서 나온 오류는 다음과 같았고 작업 공간 쓰기를 허용한 조건에서도 같은 메시지를 확인했습니다. 이번 실행에서는 샌드박스 범위를 바꾸는 것만으로 호출이 허용되지 않았습니다.

```text
MCP tool call requires approval, but approval policy is never
```

설정 참조에는 `default_tools_approval_mode`의 값으로 `auto | prompt | writes | approve`가 나옵니다. 설명은 서버 MCP 도구의 기본 승인 동작이라는 수준이며 각 값의 구체적인 동작은 적혀 있지 않습니다.

이번 조건에서 호출이 완료된 값은 `approve`입니다. `prompt`는 실행하지 않았고 대화형 승인 창도 확인하지 않았습니다.

서버 경로를 틀리게 지정한 뒤에도 `codex mcp list`는 `enabled`를 표시했습니다.

## 연결이 실패했을 때와 호출이 막혔을 때

같은 “쓸 수 없습니다”라는 답변이 나와도 중간 상태는 달랐습니다. 최종 답변만으로는 연결 실패와 호출 거부를 구분할 수 없어 연결 정보와 서버 로그를 함께 확인했습니다.

| 구분 | Claude Code에서 확인한 증상 | Codex에서 확인한 증상 | 서버 로그 |
|---|---|---|---|
| 연결 성공 후 호출 거부 | C에서 연결 성공, `mcp__demo__add` 권한 거부 | 승인 필요 오류와 `demo/add (failed)` | `start`만 |
| 잘못된 경로로 연결 실패 | 시작 정보에 `status: failed`, MCP 도구 없음 | 최종 답변은 사용 불가. 목록에는 여전히 `enabled` | 없음 |
| 연결과 호출 완료 | A·B에서 42 반환 | `approve` 조건에서 42와 `demo/add (completed)` | `start`와 `call add` |

이 서버에서는 `start`가 남으면 서버가 시작된 것이고 `call add`까지 남으면 덧셈 호출이 서버에 도달한 것입니다. 서버 시작 여부와 호출 도달 여부는 이 두 기록으로 구분했습니다.

다만 로그가 없다는 사실 하나만으로 모든 서버의 연결 실패를 판정할 수는 없습니다. 이번에는 로그 환경변수를 지정한 연습용 서버에서 경로를 틀리게 넣었고 그 조건에서 로그가 남지 않았습니다.

Claude Code의 승인 대기와 Codex의 `enabled`도 의미가 달랐습니다. 목록 상태만 보고 호출 가능 여부를 판단하지 않고 실제 실행 정보와 호출 기록을 대조했습니다.

## 처음 연결한다면

1. 연습용 서버에 프로토콜 메시지를 직접 넣어 `add`가 42를 반환하는지 확인합니다.
2. `MCP_DEMO_LOG`를 지정해 서버 시작과 호출 기록을 남깁니다.
3. Claude Code에서는 저장 범위를 정해 등록하고 `.mcp.json`의 명령과 경로를 확인합니다.
4. Codex에서는 실제로 사용할 `config.toml`에 서버 설정이 들어갔는지 확인합니다.
5. 두 도구에서 같은 덧셈 요청을 실행하고 최종 답변과 서버 로그를 대조합니다.
6. 호출이 막히면 연결 상태와 권한 오류를 나눠 확인합니다.

Claude Code 문서는 서버를 연결하기 전에 신뢰할 수 있는지 확인하라고 경고합니다. 외부 내용을 가져오는 서버의 프롬프트 주입 위험도 안내합니다.

등록 내용은 Claude Code의 `claude mcp list`와 `claude mcp get demo`, Codex의 `list`와 `get`으로 확인합니다. Claude Code의 시작 정보를 자세히 볼 때는 앞서 사용한 출력 옵션을 붙일 수 있습니다.

## 이 실험으로 알 수 없는 것

확인 범위는 Linux 한 환경의 stdio 서버이고 각 조건은 한 번씩 실행했습니다. 승인 설정에 따른 결과를 다른 모델이나 환경, 반복 실행에 일반화할 수는 없습니다. Windows와 macOS에서도 확인하지 않았습니다.

스트리머블 HTTP 서버와 OAuth 로그인은 실행하지 않았으며 서버 여러 개를 동시에 연결한 경우도 다루지 않았습니다. 대화형 화면의 `/mcp`와 승인 창 역시 확인 범위 밖입니다.

Codex 사용량 표시는 `approve` 6,845토큰, `auto` 6,841토큰, 기본 `read-only` 7,597토큰이었습니다. 조건별 한 번의 기록이므로 비용이나 성능 비교에는 사용하지 않습니다.

## 참고 문서

- [OpenAI: Codex MCP 문서](https://learn.chatgpt.com/docs/extend/mcp)
- [OpenAI: 설정 참조](https://learn.chatgpt.com/docs/config-file/config-reference)
- [Anthropic: Claude Code MCP 문서](https://code.claude.com/docs/en/mcp)
- [연습용 서버](https://github.com/kwonseongjae/ai-blog-automation/blob/main/samples/mcp_demo_server.py)
- [이번 실행 기록](https://github.com/kwonseongjae/ai-blog-automation/blob/main/docs/posts/evidence/mcp-first-connect.json)