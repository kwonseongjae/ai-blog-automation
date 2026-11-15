# Codex와 Claude Code 비교: 같은 버그 수정을 맡겨 보고 설정 차이까지 정리

같은 버그 수정을 Codex와 Claude Code에 한 번씩 맡겨 실행 결과를 비교하고 처음 사용할 때 알아둘 설정 차이도 정리했습니다. 어느 쪽이 더 낫다는 결론을 내리기 위한 글은 아닙니다.

확인일: 2026-11-15 · 범위: Linux 한 환경, Codex CLI 0.167.2, Claude Code 2.1.325, 조건별 1회 실행

## 비교 기준을 먼저 정했다

같은 시작 폴더를 두 개 복사해 도구마다 복사본 하나를 사용했습니다. 요청 문장도 똑같이 보냈습니다.

성공 기준은 테스트 3개 통과이며 테스트를 바꿔서 통과시키지 않았는지도 확인했습니다. 확인 방법은 실행 전후 테스트 파일의 해시 비교입니다.

가격이나 모델 성능 전반은 비교하지 않았고 큰 프로젝트에서 어떻게 동작하는지도 이번 범위에서 제외했습니다.

## 같은 폴더에서 같은 요청을 보냈다

작은 Python 폴더를 준비했으며 `textutil.py`에는 `slugify(text)` 함수가 있습니다. `tests/test_textutil.py`에는 테스트 3개가 있습니다.

처음 함수는 `text.strip().lower().split(" ")`로 문자열을 나눈 뒤 `"-".join`으로 합쳤습니다.

기본 입력인 `"Hello World"`는 `"hello-world"`로 바뀌어 통과했으나 나머지 2개는 실패로 나왔습니다.

| 테스트 | 입력 | 기대 결과 |
|---|---|---|
| 기본 | `"Hello World"` | `"hello-world"` |
| 앞뒤·연속 공백 | `"  Hello   World  "` | `"hello-world"` |
| 문장부호 제거 | `"Hello, World!"` | `"hello-world"` |

두 도구에는 다음 문장을 그대로 보냈습니다.

> tests 폴더의 테스트가 실패합니다. 원인을 찾아 textutil.py만 고치고 python3 -m unittest discover -s tests 로 통과를 확인해 주세요. 테스트 파일은 수정하지 마세요. 마지막에 무엇을 고쳤는지 두 줄로 알려주세요.

Codex 실행 명령입니다.

```bash
codex exec -s workspace-write --skip-git-repo-check "<요청 문장>"
```

Claude Code 실행 명령입니다.

```bash
claude -p "<요청 문장>" --permission-mode acceptEdits \
  --allowedTools "Read" "Edit" "Write" "Bash(python3 -m unittest *)" \
  --setting-sources project,local
```

Claude Code의 한 번 실행 방식인 `-p`에서는 승인 창에 답할 수 없어 필요한 도구를 `--allowedTools`로 미리 허용했습니다. 시간과 토큰 집계를 위해 실제 실행에는 `--output-format json`도 추가했습니다.

![같은 폴더를 두 개 복사해 같은 요청을 보내고 결과를 비교하는 순서](asset:flow)

실행해 보니 두 도구 모두 성공 기준을 충족했습니다.

| 항목 | Codex | Claude Code |
|---|---|---|
| 테스트 | 3개 통과 | 3개 통과 |
| 테스트 파일 수정 | 안 함. 실행 전후 해시 동일 | 안 함. 실행 전후 해시 동일 |
| 걸린 시간: 명령 시작부터 끝까지 | 약 71초 | 약 6.9초. 응답에 보고된 시간은 5.9초, 4턴 |
| 표시된 사용량 | 총 18,882 토큰 | 출력 712 토큰. 입력 중 캐시 생성 10,375 토큰, 캐시 읽기 42,802 토큰. 보고된 비용 약 0.053달러 |
| 마지막 보고 | 문장부호 제거와 연속 공백 처리를 두 줄로 설명. “별도 검증은 하지 않았습니다”라고 덧붙임 | 실패 원인과 수정 방법, 테스트 통과를 두 줄로 설명 |

고친 방식에는 차이가 있었습니다.

Codex는 소문자로 바꾼 문자열에서 `isalnum()` 또는 `isspace()`를 만족하는 문자만 남긴 뒤 인자 없는 `split()`으로 나눴습니다.

```python
"".join(c for c in text.lower() if c.isalnum() or c.isspace()).split()
```

Claude Code는 `import re`를 추가해 정규식으로 문장부호를 제거한 뒤 `split()`으로 나눴습니다.

```python
re.sub(r"[^\w\s-]", "", text.lower()).split()
```

두 방식 모두 이번 테스트를 통과했지만 밑줄이나 기존 하이픈을 처리하는 조건은 코드상 다릅니다. 이번 테스트에는 해당 입력이 없습니다. 따라서 테스트 통과만으로 두 구현의 동작이 같다고 말하지는 않겠습니다.

Codex는 마지막 보고에서 별도 검증은 하지 않았다고 했지만 실행이 끝난 뒤 제가 같은 명령으로 직접 테스트를 돌려 3개 통과를 확인했습니다.

시간도 이번 실행의 기록으로만 봐야 합니다. Codex는 개인 전역 지침과 훅을 끄지 않았고 Claude Code는 `--setting-sources project,local`로 개인 설정을 제외했습니다. 두 도구가 사용한 모델과 추론 설정도 서로 다른 조건입니다.

사용량 숫자는 직접 비교하지 않았습니다. Codex는 총합을 한 숫자로 표시했고 Claude Code는 입력 캐시와 출력을 나눠 표시했습니다. 집계 방식이 다릅니다.

## 설정에서 달랐던 점

| 항목 | Codex | Claude Code |
|---|---|---|
| 기본 지침 파일 | `AGENTS.md` | `CLAUDE.md`. 직접 확인한 환경에서는 작업 폴더나 상위에 `CLAUDE.md`가 있으면 `AGENTS.md`를 읽지 않았음 |
| 전역 지침 위치 | `~/.codex/AGENTS.md` | `~/.claude/CLAUDE.md` |
| 권한 구조 | 공식 문서에 따르면 샌드박스와 승인 정책을 따로 설정. 예: `workspace-write`, `on-request` | 공식 문서에 따르면 권한 모드와 allow·ask·deny 규칙을 사용. 규칙 검사 순서는 deny → ask → allow |
| 한 번 실행 명령 | `codex exec` | `claude -p` |
| 한 번 실행에서 파일 수정 | 직접 실행해 보니 `workspace-write`에서 작업 폴더 안에 파일을 만들었음 | 직접 실행해 보니 기본 모드에서는 파일 수정이 승인되지 않아 실패했음. 필요한 도구를 미리 허용해야 했음 |
| 읽은 지침 확인 | 공식 문서 안내: `codex --ask-for-approval never "Summarize the current instructions."` | 공식 문서 안내: 세션에서 `/context all`의 Memory files 목록 확인 |
| 파일 수정 차단 규칙 | 이번 비교에서 별도 확인하지 않음 | 직접 확인할 때 `Write(...)`가 아니라 `Edit(...)`로 적어야 한다는 안내가 출력됨 |

지침 파일은 이름만 바꾸면 된다고 생각하기 쉬웠지만 직접 확인해 보니 Claude Code는 작업 폴더나 상위에 `CLAUDE.md`가 있으면 `AGENTS.md`를 읽지 않았습니다. `CLAUDE.md` 안에서 `@AGENTS.md`로 가져오자 두 규칙이 함께 적용됐습니다.

공식 문서에 따르면 Codex는 샌드박스로 작업 범위를 정하고 승인 정책을 따로 설정합니다. Claude Code는 권한 모드에 도구와 명령별 규칙을 더하는 구조입니다. Claude Code의 deny → ask → allow 검사 순서는 문서에서 읽은 내용입니다. 직접 시험하지는 않았습니다.

한 번 실행하는 명령에서는 권한을 미리 정하는 과정도 필요했습니다. 직접 실행해 보니 Claude Code는 기본 모드에서 파일 수정 승인을 받지 못했습니다. 이번 비교 명령에 허용할 도구를 적은 이유입니다.

## 처음 써 본다면 어느 쪽부터

아래는 제 환경에서 실행한 결과와 공식 문서를 기준으로 한 판단입니다. 먼저 확인할 것은 저장소의 지침 파일과 원하는 권한 범위입니다.

저장소에 이미 `AGENTS.md`가 있다면 Codex가 기존 파일을 그대로 읽으므로 Codex부터 시작하는 편이 맞을 수 있습니다. Claude Code를 쓴다면 `CLAUDE.md`의 존재 여부를 확인해야 합니다. 필요하면 `@AGENTS.md`로 기존 지침을 가져오는 설정이 들어갑니다.

공식 문서의 권한 구조를 기준으로 보면 “작업 폴더 안에서 쓰기를 허용한다”는 범위로 시작하려는 경우에는 Codex의 `workspace-write`가 맞을 수 있습니다. 허용하거나 확인받을 동작을 도구와 명령 단위로 정하려는 경우에는 Claude Code의 규칙 구조가 더 가깝습니다.

이번처럼 작은 버그 수정은 두 도구 모두 한 번에 통과시켰습니다. 처음 선택할 때는 이번 실행 시간만 보기보다 자기 저장소의 지침과 권한 설정에 어느 쪽이 맞는지부터 확인하는 편이 낫다고 판단합니다.

## 이 비교로 알 수 없는 것

- 각 조건에서 한 번만 실행했습니다. 다시 실행하면 시간과 사용량뿐 아니라 고치는 방식도 달라질 수 있습니다.
- 개인 설정의 적용 범위가 달랐고 모델과 추론 설정도 같지 않아 도구 자체의 속도 차이로 단정하기 어렵습니다.
- 시간은 계정과 서버 상태에도 영향을 받으므로 이번 기록만으로 평소 소요 시간을 예측하지 않았습니다.
- 사용량 집계 방식이 달라 토큰 숫자로 비용이나 성능의 우열을 판단하지 않았습니다.
- 테스트 3개 밖의 입력은 확인하지 않았으며 큰 프로젝트에서의 동작과 모델 성능 전반도 이번 비교로는 알 수 없습니다.

## 참고 문서

- [OpenAI: 에이전트 승인과 보안](https://learn.chatgpt.com/docs/agent-approvals-security)
- [Anthropic: Claude Code 권한 설정](https://code.claude.com/docs/en/permissions)
- [이번 실행 기록(시작 폴더, 요청 문장, 결과)](https://github.com/kwonseongjae/ai-blog-automation/blob/main/docs/posts/evidence/compare-slugify.json)