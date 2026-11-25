# Codex exec MCP enabled인데 approval required가 뜰 때 · 도구별 승인 설정

Linux에서 Codex CLI(코덱스) 0.167.2로 MCP 서버를 연결해도 호출은 approval required로 실패했습니다. demo의 default_tools_approval_mode를 approve로 바꾸니 덧셈만 실행됐습니다.

## 읽기 도구와 쓰기 도구가 섞인 서버 두 개를 준비했다

이전 글 [MCP 서버 연결과 호출 확인](https://jacks-aiblog.tistory.com/14)에서 쓴 `demo` 서버를 그대로 재사용하고 `notes` 서버를 직접 만들었습니다. 두 서버 모두 stdio 방식입니다.

| 서버 | 파일 | 도구와 동작 |
|---|---|---|
| `demo` | `samples/mcp_demo_server.py` | 두 정수의 합을 구하는 `add`, `word_count` |
| `notes` | `samples/mcp_notes_server.py` | `notes.txt`에 메모 한 줄을 덧붙이는 `write_note`, 합에 1000을 더하는 `add` |

`notes`의 `add`는 `demo`의 도구와 이름이 겹치고 계산 결과는 다릅니다. 요청에서는 서버 이름까지 지정합니다.

두 도구에 넣은 요청 문장은 같습니다.

> demo 서버의 add 도구로 17과 25를 더한 다음 notes 서버의 write_note 도구로 "합계=42"를 기록해 주세요. 쓸 수 없는 도구가 있으면 어떤 도구인지만 말해 주세요.

답변만으로 성공을 판정하지 않고 서버 로그와 결과 파일을 함께 확인합니다. 조건마다 로그와 파일을 비운 뒤 실행했습니다.

`demo` 로그에는 `call add {"a": 17, "b": 25}`가 있어야 합니다. `notes` 로그의 `write_note` 호출도 확인하고 `notes.txt`에 `합계=42`가 생겼는지 봅니다.

쓰기 차단 여부는 반대로 확인합니다. `notes.txt`가 비어 있고 `notes` 서버 로그에도 `write_note` 호출이 없어야 합니다.

![서버 두 개를 붙이고 허용 범위를 바꿔 가며 도구 호출과 서버 로그를 비교하는 순서](asset:flow)

## Claude Code는 허용 목록으로 도구를 고른다

다음 명령을 기본으로 사용하고 조건마다 허용·차단 옵션을 붙였습니다. `<요청>`에는 앞의 요청 문장이 들어갑니다.

```bash
claude -p "<요청>" \
  --model haiku \
  --setting-sources project,local \
  --mcp-config mcp.json \
  --strict-mcp-config \
  --output-format stream-json \
  --verbose
```

출력의 시작 정보인 `init`에서 도구 목록을 읽고 `permission_denials`에서 권한 거부를 확인합니다. 서버 로그와 `notes.txt`도 대조했습니다.

| 조건 | 추가 옵션 | 시작 정보의 notes 도구 | 권한 거부 | demo의 add | write_note | notes.txt |
|---|---|---|---|---|---|---|
| A 도구 하나만 허용 | `--allowedTools mcp__demo__add` | `write_note`, `add` | `mcp__notes__write_note` | 호출됨, 42 | 시도했으나 거부 | 비어 있음 |
| B 도구 둘 허용 | `--allowedTools mcp__demo__add mcp__notes__write_note` | 둘 다 보임 | 없음 | 호출됨 | 호출됨 | `합계=42` |
| C 서버 이름으로 허용 | `--allowedTools mcp__demo mcp__notes` | 둘 다 보임 | 없음 | 호출됨 | 호출됨 | `합계=42` |
| D 서버 와일드카드 | `--allowedTools 'mcp__demo__*' 'mcp__notes__*'` | 둘 다 보임 | 없음 | 호출됨 | 호출됨 | `합계=42` |
| E 서버 허용 + 도구 차단 | `--allowedTools mcp__demo mcp__notes --disallowedTools mcp__notes__write_note` | `add`만 보임 | 기록 없음 | 호출됨 | 시도 없음 | 비어 있음 |
| F 허용 없음 | 허용 옵션 없음 | 둘 다 보임 | `mcp__demo__add`, `mcp__notes__write_note` | 시도했으나 거부 | 시도했으나 거부 | 비어 있음 |

A에서는 `demo`의 `add`만 실행됐고 `notes`의 `write_note`는 권한 거부로 남았습니다. 덧셈은 허용하면서 파일 쓰기는 막은 결과입니다.

B에서는 필요한 도구 둘을 지정했고 C와 D에서는 서버 범위로 허용했습니다. 세 조건 모두 파일에 `합계=42`가 남습니다. 서버 이름 전체와 와일드카드는 이번 조건에서 같은 결과를 보였습니다.

모든 조건에서 두 서버는 `connected`였고 A와 F에서는 도구 호출이 거부됐습니다. 서버 연결과 호출 허용은 별개입니다.

## 차단한 도구는 거부로 나타나기도 하고 목록에서 사라지기도 한다

A와 E는 모두 파일이 비어 있었고 `write_note`가 실행되지 않았습니다. 다만 막힌 흔적이 다릅니다.

A의 시작 정보에는 `write_note`가 보이고 호출을 시도한 뒤 거부 기록이 남습니다. `notes` 서버 로그에는 `start`만 있었습니다. 답변도 권한이 없어 기록하지 못했으며 허용해 주면 다시 하겠다고 설명합니다.

E에서는 `write_note`가 시작 도구 목록에서 빠졌고 호출 시도도 없었습니다. 권한 거부 기록 역시 없습니다. 답변에는 도구 검색에서 `write_note`가 나오지 않았고 `notes`에서 찾은 도구는 `add`뿐이라고 나옵니다.

따라서 거부 기록이 없다는 사실만 보고 호출이 허용됐다고 판단할 수는 없습니다. A는 거부 기록을 확인하고 E는 도구 목록에서 빠졌는지 확인해야 구분됩니다.

## Codex는 서버와 도구마다 승인 설정을 덮어쓴다

이 실험은 2026-11-16 Linux에서 Codex CLI 0.167.2와 Claude Code(클로드 코드) 2.1.325로 조건별 1회 실행했습니다.

Codex에서는 다음 명령에 조건별 `-c` 덮어쓰기를 붙였고 설정 파일은 수정하지 않았습니다. 요청 문장은 앞과 같습니다.

```bash
codex exec --json \
  -m gpt-6.1-sol \
  -c model_reasoning_effort=low \
  -s read-only \
  --skip-git-repo-check \
  -C <작업폴더>
```

실행에 표시된 승인 정책은 `never`였고 출력 JSON의 MCP 호출 항목을 확인했습니다. 서버와 도구 이름, 상태와 오류를 읽습니다. 서버 로그와 `notes.txt`도 함께 봤습니다.

표의 설정은 각각 `-c`로 덮어쓴 값입니다. C를 기준으로 한 조건은 C의 서버 승인 설정도 포함합니다.

| 조건 | 덮어쓴 설정 | demo의 add | write_note | notes.txt |
|---|---|---|---|---|
| A 승인 설정 없음 | 없음 | `failed` | `failed` | 비어 있음 |
| B demo만 승인 | `mcp_servers.demo.default_tools_approval_mode="approve"` | `completed` | `failed` | 비어 있음 |
| C 두 서버 승인 | `mcp_servers.demo.default_tools_approval_mode="approve"`, `mcp_servers.notes.default_tools_approval_mode="approve"` | `completed` | `completed` | `합계=42` |
| D notes는 승인이고 write_note만 auto | C에 `mcp_servers.notes.tools.write_note.approval_mode="auto"` 추가 | `completed` | `failed` | 비어 있음 |
| E write_note 차단 | C에 `mcp_servers.notes.disabled_tools=["write_note"]` 추가 | `completed` | 호출 항목 없음 | 비어 있음 |
| F notes 허용 목록을 add로 제한 | C에 `mcp_servers.notes.enabled_tools=["add"]` 추가 | 호출 항목 없음 | 호출 항목 없음 | 비어 있음 |

A, B, D에서 실패한 호출에는 같은 오류가 남았고 문구는 다음과 같습니다.

```text
MCP tool call requires approval, but approval policy is never
```

B에서는 `demo`의 `add`가 완료됐고 `notes`의 `write_note`는 실패했습니다. 이 조건에서는 서버마다 승인을 따로 줘야 했습니다. 두 서버를 승인한 C에서는 파일 쓰기까지 완료됩니다.

E는 오류로 실패한 경우와 다르고 `write_note` 호출 항목 자체가 없습니다. 답변은 해당 도구를 쓸 수 없다고 알립니다. 파일도 비어 있었습니다.

답변은 대부분 쓸 수 없는 도구 이름을 짧게 알려 줬고 실제 호출 결과까지 드러내지는 않았습니다. A는 둘 다 실패했지만 B는 덧셈에 성공합니다. 답변이 비슷해도 호출 항목과 로그를 확인해야 차이가 보입니다.

## 서버 기본값과 도구별 설정이 부딪히는 경우

D는 두 서버의 기본값을 `approve`로 두고 `write_note`만 `auto`로 덮어쓴 조건입니다. `add`는 완료됐습니다. `write_note`는 승인 정책이 `never`라는 오류로 실패합니다.

이번 D 조건에서는 도구별 설정이 서버 기본값보다 우선했고 `auto`가 호출을 통과시키지 못했습니다. 이전 글에서 서버 기본값을 `auto`로 시험했을 때와 같은 결과입니다. 여기서 `auto`라는 이름만 보고 호출 허용을 예상하면 결과가 어긋납니다.

F는 `notes`의 허용 목록을 `add`로 제한했고 요청은 여전히 `demo`의 `add`를 지정했습니다. 그런데 두 도구 모두 호출 항목이 없습니다. 서버 로그에도 `start`만 남았습니다.

왜 `demo`의 `add`까지 호출되지 않았는지는 확인하지 못했고 같은 이름의 도구 때문인지도 알 수 없습니다. F에서 확인한 것은 호출이 없었다는 결과까지입니다. 이름이 겹칠 때의 선택 우선순위를 이 기록으로 설명할 수는 없습니다.

## 도구 하나만 허용할 때 확인하는 순서

1. 증상: 서버는 연결됐는데 도구가 실행되지 않습니다. 원인 후보: 연결은 됐지만 호출 권한이 없습니다. 확인: 연결 상태와 별도로 권한 거부 또는 MCP 호출 오류를 읽습니다.
2. 증상: Claude Code에서 파일 쓰기가 막힙니다. 원인 후보: 허용 목록에서 빠졌거나 명시적으로 차단됐습니다. 확인: `init`의 도구 목록과 `permission_denials`를 비교합니다.
3. 증상: Codex에서 덧셈은 완료되고 쓰기는 실패합니다. 원인 후보: 서버별 승인 설정이 다르거나 도구별 설정이 기본값을 덮어썼습니다. 확인: 실패한 호출의 오류와 해당 서버·도구 설정을 대조합니다.
4. 증상: 쓸 수 없다는 답변은 있지만 호출 오류가 없습니다. 원인 후보: 차단이나 허용 목록 제한으로 호출 시도가 없었습니다. 확인: 도구 목록과 호출 항목을 보고 서버 로그에도 호출이 없는지 확인합니다.
5. 증상: 쓰기 차단 여부를 확정하기 어렵습니다. 원인 후보: 답변 문장만으로 판정하고 있습니다. 확인: 조건마다 로그와 파일을 비우고 실행한 뒤 `notes.txt`와 `write_note` 서버 로그를 함께 봅니다.

## 이 실험으로 알 수 없는 것

Linux 한 환경에서 각 조건을 한 번씩 실행했고 다른 모델이나 반복 실행은 확인하지 않았습니다. Windows와 macOS도 범위 밖입니다. 조건별 소요 시간은 비교에 사용하지 않습니다.

대화형 승인 창을 사용하지 않았고 `prompt` 값도 시험하지 않았습니다. HTTP 서버와 OAuth도 확인하지 않았습니다. Claude Code의 다른 `--allowedTools` 패턴 표기와 Codex의 다른 샌드박스 범위도 다루지 않습니다.

같은 이름의 도구가 있는 서버를 연결했지만 충돌 시 우선순위는 확인하지 못했습니다. 특히 F에서 덧셈까지 멈춘 이유는 남아 있습니다.

두 도구 모두 덧셈을 허용하면서 파일 쓰기를 막는 결과를 확인했고 막힌 흔적은 조건마다 달랐습니다. 거부된 호출과 호출 시도가 없는 경우를 구분하는 데까지가 이번 기록의 범위입니다.

## 참고 문서

아래 공식 문서는 설정을 확인할 때 참고할 링크이며 본문의 실행 결과는 직접 남긴 기록입니다. 예제 서버와 실행 기록도 함께 연결합니다.

- [Claude Code MCP 문서](https://code.claude.com/docs/en/mcp)
- [Codex MCP 문서](https://learn.chatgpt.com/docs/extend/mcp)
- [예제 서버 notes](https://github.com/kwonseongjae/ai-blog-automation/blob/main/samples/mcp_notes_server.py)
- [이번 실행 기록](https://github.com/kwonseongjae/ai-blog-automation/blob/main/docs/posts/evidence/mcp-tool-scope.json)