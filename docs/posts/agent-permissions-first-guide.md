# AI 코딩 도구 권한 처음 설정하기: 파일을 만들기 전에 물어보게 하는 법

AI 코딩 도구가 파일을 마음대로 바꾸거나 명령을 실행하면 불안합니다. 두 도구 모두 어디까지 허용할지 정하는 권한 설정이 있고, 처음에는 좁게 시작하는 편이 안전합니다.

임시 폴더에서 같은 요청을 권한만 바꿔 보내 보고, 어떤 일이 막히고 어떤 일이 허용되는지 직접 확인했습니다.

확인일: 2026-11-15 · 범위: Codex CLI 0.167.2, Claude Code 2.1.325를 같은 Linux 환경에서 실행한 결과입니다. 조건별 1회 실행이며 Windows·macOS와 요금제별 차이는 확인하지 않았습니다.

## 권한은 두 겹으로 나눠 생각한다

공식 문서는 두 도구의 권한을 조금 다르게 설명합니다. 먼저 용어부터 비교합니다.

| 구분 | Codex | Claude Code |
| --- | --- | --- |
| 기술적으로 할 수 있는 일 | 샌드박스 `read-only`, `workspace-write` | 권한 모드 `default`, `acceptEdits`, `plan` 등 |
| 언제 사람에게 물을지 | 승인 정책 `on-request`, `never` | 규칙 `allow`(허용), `ask`(확인), `deny`(차단) |
| 처음 보이는 이름 | `--sandbox`, `--ask-for-approval` | `/permissions`, `--permission-mode` |

Codex의 샌드박스는 명령을 실행할 때 파일을 어디에 쓰고 네트워크에 접근할 수 있는지를 정합니다. 승인 정책은 그 범위를 벗어나는 일을 사람에게 물을지를 정합니다.

공식 문서의 `Auto` 설정(`--sandbox workspace-write --ask-for-approval on-request`)에서는 작업 폴더 안의 파일 읽기·수정·명령 실행은 자동으로 하고, 작업 폴더 밖 수정이나 네트워크 접근은 승인을 요구합니다.

Claude Code의 기본 모드는 각 도구를 처음 사용할 때 확인을 받습니다. 공식 문서 기준으로 작업 폴더 안의 파일 읽기는 승인 없이 되고, 파일 수정과 대부분의 셸 명령은 승인을 요구합니다.

![권한 단계를 고르고 같은 요청으로 시험한 뒤 결과로 설정을 확정하는 순서](asset:flow)

## 같은 요청을 권한만 바꿔 보냈다

임시 폴더 하나에서 "hello.txt 파일을 만들고 안에 hi 라고 써줘"라는 같은 요청을 권한 설정만 바꿔 보냈습니다. 실행 사이에는 만들어진 파일을 지웠습니다. 파일 이름과 내용은 예시입니다.

```bash
codex exec -s read-only --skip-git-repo-check "hello.txt 파일을 만들고 안에 hi 라고 써줘."
codex exec -s workspace-write --skip-git-repo-check "hello.txt 파일을 만들고 안에 hi 라고 써줘."
claude -p "hello.txt 파일을 만들고 안에 hi 라고 써줘." --setting-sources project,local
claude -p "hello.txt 파일을 만들고 안에 hi 라고 써줘." --permission-mode acceptEdits --setting-sources project,local
```

각 실행 뒤에는 폴더에 파일이 실제로 생겼는지 `ls`로 확인했습니다.

| 도구와 설정 | 도구의 답 | 폴더에 파일이 생겼나 |
| --- | --- | --- |
| Codex `read-only` | 읽기 전용이라 쓸 수 없다고 답함 | 생기지 않음 |
| Codex `workspace-write` | 파일을 만들고 `hi`를 썼다고 답함 | 생김 (내용 `hi`) |
| Claude Code 기본 모드 | 쓰기 권한이 승인되지 않아 만들지 못했다고 답함 | 생기지 않음 |
| Claude Code `acceptEdits` | 파일을 만들고 `hi`를 적었다고 답함 | 생김 |

Claude Code의 기본 모드는 파일 수정 전에 사람에게 승인을 묻습니다. `-p`로 한 번만 실행하면 그 자리에서 답할 수 없어 승인되지 않은 채로 끝났습니다. 화면에서 대화하는 평소 사용에서는 승인 창이 뜨는 자리입니다.

이 실행만으로 승인 창의 모양까지 확인한 것은 아닙니다.

## 규칙으로 정할 때 만난 두 가지 함정

Claude Code는 `.claude/settings.json`에 허용·차단 규칙을 적을 수 있습니다. 공식 문서에 따르면 규칙은 deny, ask, allow 순서로 검사하고 처음 일치한 규칙이 결과를 정합니다.

즉 차단 규칙이 있으면 더 좁은 허용 규칙으로도 풀 수 없습니다. 이 순서는 문서의 설명이며 제가 직접 시험하지는 않았습니다.

직접 시험하다가 만난 것은 다음 두 가지입니다. 임시 폴더에서 아래 설정을 넣고 실행했습니다.

```json
{"permissions":{"allow":["Write"],"deny":["Write(./blocked.txt)"]}}
```

- 프로젝트의 허용 규칙은 폴더를 신뢰하기 전에는 적용되지 않았습니다.
- 실행 결과에 "Ignoring 1 permissions.allow entry from .claude/settings.json: this workspace has not been trusted" 안내가 나왔습니다.
- 설정 파일에 허용을 적어도 처음 열 때 신뢰 확인을 거쳐야 합니다.
- 파일을 막는 규칙은 `Write(...)`가 아니라 `Edit(...)`로 적어야 했습니다.
- 실행 결과에 "Write(./blocked.txt) is not matched by file permission checks — only Edit(path) rules are. Use Edit(./blocked.txt) instead"라는 안내가 나왔습니다.
- 규칙을 적었는데 효과가 없다면 도구 이름부터 확인합니다.

또 하나 기억할 점은 공식 문서의 설명입니다. 권한 규칙은 모델이 아니라 Claude Code가 강제합니다. 프롬프트나 `CLAUDE.md`에 "파일을 지우지 마"라고 적어도 허용 여부 자체가 바뀌지는 않습니다.

지침 파일은 도구가 시도하는 일에 영향을 주고, 권한 설정은 도구가 할 수 있는 일을 정합니다. 둘을 함께 쓰는 이유입니다.

## 처음에는 이렇게 시작한다

공식 문서가 안내하는 기본값과 위 확인 결과를 바탕으로 한 권장입니다.

| 상황 | Codex | Claude Code |
| --- | --- | --- |
| 처음 써보거나 설명만 받을 때 | `--sandbox read-only` | 기본 모드, 또는 읽기만 하는 `plan` 모드 |
| 작업 폴더 안에서 수정을 맡길 때 | `--sandbox workspace-write --ask-for-approval on-request` | 기본 모드로 승인하거나 `acceptEdits` |
| 피할 설정 | `danger-full-access` | `bypassPermissions` |

Codex 공식 문서는 Git으로 관리하지 않는 폴더에서는 `read-only`를 권장한다고 안내합니다.

Claude Code 문서는 `bypassPermissions`가 `.git` 같은 보호 경로에 쓰는 것까지 승인 없이 넘기므로, 컨테이너나 가상 머신처럼 격리된 환경에서만 쓰라고 안내합니다.

## 막힐 때 확인할 것

| 증상 | 확인할 것 |
| --- | --- |
| 파일을 못 만든다고 답한다 | Codex는 `--sandbox` 값, Claude Code는 권한 모드를 확인합니다 |
| 한 번만 실행했더니 계속 승인이 안 된다 | `-p` 같은 한 번 실행에서는 승인 창에 답할 수 없습니다. 화면에서 대화하거나 허용 범위를 미리 정합니다 |
| 허용 규칙을 적었는데 계속 묻는다 | 폴더 신뢰 확인을 마쳤는지, 규칙의 도구 이름이 맞는지 확인합니다 |
| 현재 규칙을 한눈에 보고 싶다 | Claude Code는 `/permissions`, Codex는 화면에서 `/permissions`로 확인합니다 |

## 내 프로젝트에 적용할 때

이 글의 실행은 임시 폴더에서 한 실험이며, 실제 프로젝트에 적용한 뒤의 작업 시간이나 사고 감소 효과는 측정하지 않았습니다.

처음에는 읽기 전용으로 시작해 도구가 어떤 파일을 읽고 무엇을 하려는지 보고, 신뢰가 쌓이면 작업 폴더 안의 수정만 허용하는 순서를 권합니다. 비밀 값이 든 파일은 권한 설정과 별개로 저장소에 두지 않는 것이 기본입니다.

## 참고 문서와 확인 범위

- [OpenAI: 에이전트 승인과 보안](https://learn.chatgpt.com/docs/agent-approvals-security)
- [Anthropic: Claude Code 권한 설정](https://code.claude.com/docs/en/permissions)

이 글의 실행 결과는 Linux 한 환경에서 조건별로 한 번씩 실행한 결과입니다. 요금제별 한도, Windows·macOS의 동작, 이후 버전의 변경은 확인하지 않았습니다.
