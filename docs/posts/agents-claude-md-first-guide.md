# AGENTS.md·CLAUDE.md 작성법: 어떤 파일을 읽는지 직접 확인하는 법

같은 프로젝트에 AGENTS.md와 CLAUDE.md가 둘 다 있으면 AI 코딩 도구는 어느 파일을 읽을까요? 이름이 비슷해서 하나만 써도 두 도구에 모두 적용될 것 같지만, 도구마다 읽는 규칙이 다릅니다. 임시 폴더에서 두 도구로 직접 확인해 보고, 처음 쓰는 지침 파일의 최소 형태까지 정리했습니다.

확인일: 2026-11-15 · 범위: Codex CLI 0.167.2, Claude Code 2.1.325를 같은 Linux 환경에서 실행한 결과입니다. 요금제와 다른 운영체제는 확인하지 않았습니다.

## 지침 파일은 도구가 시작할 때 읽는 안내서

지침 파일은 프로젝트에서 지켜야 할 규칙을 적어 두는 일반 텍스트(Markdown) 파일입니다. 매번 "테스트는 이 명령으로 돌려줘"라고 말하는 대신 파일에 적어 두면, 도구가 작업을 시작할 때 읽고 따릅니다. Codex는 `AGENTS.md`, Claude Code는 `CLAUDE.md`를 기본 이름으로 사용합니다.

두 도구의 읽는 방식은 공식 문서에서 다음과 같이 설명합니다.

| 구분 | Codex | Claude Code |
| --- | --- | --- |
| 기본 파일 이름 | `AGENTS.md` | `CLAUDE.md` |
| 내 모든 프로젝트에 적용 | `~/.codex/AGENTS.md` | `~/.claude/CLAUDE.md` |
| 프로젝트에 적용 | 프로젝트 루트부터 현재 폴더까지 폴더마다 한 파일 | `./CLAUDE.md` 또는 `./.claude/CLAUDE.md` |
| 같은 위치에서 덮어쓰거나 내 것만 쓰는 파일 | `AGENTS.override.md` (있으면 같은 폴더의 `AGENTS.md` 대신 읽음) | `CLAUDE.local.md` (내 것만 쓰는 프로젝트 설정) |
| 다른 도구의 파일 | 대체 파일 이름을 설정으로 추가 | CLAUDE.md가 없을 때만 AGENTS.md를 읽음 |
| 크기 | 합친 크기 기본 32 KiB까지 | 파일당 200줄 이하를 권장 |

여기서 눈여겨볼 곳은 Claude Code의 기본 규칙입니다. 공식 문서에 따르면 작업 폴더나 그 위에 `CLAUDE.md`가 하나라도 있으면 `AGENTS.md`는 읽지 않습니다.

![지침 파일을 만들고 같은 질문으로 확인한 뒤 읽은 파일을 대조하는 순서](asset:flow)

## 임시 폴더에서 직접 확인했다

문서의 설명이 실제와 같은지 작은 폴더로 확인했습니다. 먼저 규칙이 한 줄씩 다른 두 파일을 만듭니다. 폴더 이름은 예시입니다.

```bash
mkdir instr-lab && cd instr-lab
printf '# AGENTS.md\n\n- 답변 첫 줄에 [지침확인]을 붙인다.\n- 테스트 명령은 python3 -m unittest 이다.\n' > AGENTS.md
```

Codex에는 파일을 바꾸지 못하게 읽기 전용으로 물어봤습니다. Git 저장소가 아닌 폴더라 `--skip-git-repo-check`를 붙였습니다.

```bash
codex exec -s read-only --skip-git-repo-check "이 폴더에서 읽은 지침 파일 이름과 지침 내용을 짧게 알려줘. 파일은 수정하지 마."
```

Codex는 첫 줄에 `[지침확인]`을 붙이고, `AGENTS.md`를 읽었으며 테스트 명령이 `python3 -m unittest`라고 답했습니다. 지침을 읽고 따른 것입니다.

Claude Code는 같은 폴더에 `CLAUDE.md`를 추가하는 경우와 없는 경우를 나눠 물어봤습니다. 내 전역 설정이 섞이지 않도록 `--setting-sources project,local`로 프로젝트와 로컬 설정만 사용했습니다.

```bash
printf '# CLAUDE.md\n\n- 답변 첫 줄에 [CLAUDE확인]을 붙인다.\n' > CLAUDE.md
claude -p "이 폴더의 지침 파일 중 네가 따르는 것의 이름과 첫 줄 규칙만 한 줄로 말해줘. 도구는 쓰지 마." --setting-sources project,local
```

| 폴더 안의 파일 | Claude Code의 답 |
| --- | --- |
| `AGENTS.md`와 `CLAUDE.md` 둘 다 | 첫 줄 `[CLAUDE확인]`, 따르는 파일은 `CLAUDE.md` |
| `AGENTS.md`만 | 첫 줄 `[지침확인]`, 따르는 파일은 `AGENTS.md` |

문서의 설명과 같은 결과였습니다. 다만 각 조건을 한 번씩만 실행했고, 모델의 답은 매번 조금씩 달라질 수 있습니다. 그래서 답변만 믿기보다 도구가 직접 보여 주는 확인 방법을 함께 쓰는 편이 좋습니다. Claude Code는 세션 안에서 `/context all`을 입력하면 읽은 파일이 Memory files 아래에 나열됩니다. Codex는 공식 문서가 안내하는 `codex --ask-for-approval never "Summarize the current instructions."`로 읽은 지침을 요약하게 할 수 있습니다.

## 처음 쓰는 지침은 짧고 확인할 수 있게

처음부터 길게 쓰지 않아도 됩니다. 공식 문서도 확인할 수 있을 만큼 구체적으로 쓰라고 안내합니다.

| 모호한 표현 | 확인할 수 있는 표현 |
| --- | --- |
| 코드를 깔끔하게 정리해줘 | 들여쓰기는 공백 4칸을 쓴다 |
| 변경하면 테스트해줘 | 변경한 뒤 `python3 -m unittest`를 실행한다 |
| 파일을 잘 정리해줘 | 새 모듈은 `automation/` 아래에 둔다 |

처음에는 이 정도 다섯 줄이면 충분합니다.

```markdown
# 프로젝트 지침

- 이 프로젝트는 하루 한 편 블로그 글을 발행하는 Python 도구입니다.
- 변경한 뒤에는 `python3 -m unittest discover -s tests`를 실행합니다.
- 비밀 값이 들어 있는 `.env` 파일은 읽거나 수정하지 않습니다.
- 확인하지 못한 내용은 추측하지 말고 확인하지 못했다고 답합니다.
```

위 예시는 이 글을 위해 만든 설명용 예시이며, 실제 프로젝트에 넣을 때는 명령과 경로를 본인 프로젝트에 맞게 바꿉니다. 지침 파일은 도구에게 주는 참고 내용이지 실행을 강제하는 설정이 아닙니다. 지키지 말아야 할 일은 도구의 권한 설정으로도 함께 막아야 합니다.

## 두 도구를 함께 쓸 때는 한 파일을 기준으로 삼는다

Codex와 Claude Code를 번갈아 쓰면 같은 규칙을 두 파일에 적게 되어 서로 어긋나기 쉽습니다. Claude Code 공식 문서는 `AGENTS.md`를 기준 파일로 두고 `CLAUDE.md`에서 가져오는 방법을 안내합니다.

```markdown
@AGENTS.md

## Claude Code

- 답변 둘째 줄에 [Claude추가]를 붙인다.
```

이 방식도 직접 확인했습니다. `AGENTS.md`에 `[지침확인]` 규칙이, `CLAUDE.md`에는 위 내용이 있는 폴더에서 Claude Code는 첫 줄에 `[지침확인]`, 둘째 줄에 `[Claude추가]`를 붙여 답했습니다. 두 파일의 규칙이 모두 적용된 것입니다.

공식 문서에는 `ln -s AGENTS.md CLAUDE.md`처럼 심볼릭 링크를 쓰는 방법도 있습니다. 다만 Windows에서는 링크 생성에 관리자 권한이나 개발자 모드가 필요하고, 저장소를 내려받으면 링크가 한 줄짜리 텍스트 파일로 바뀔 수 있다고 안내합니다. Windows 환경이 섞인다면 위의 `@AGENTS.md` 방식이 안전합니다.

## 막힐 때 확인할 것

| 증상 | 확인할 것 |
| --- | --- |
| 지침을 따르지 않는다 | 파일이 비어 있지 않은지, 작업하는 폴더가 맞는지 확인합니다 |
| Claude Code가 AGENTS.md를 읽지 않는다 | 작업 폴더 또는 위쪽 폴더에 `CLAUDE.md`나 `CLAUDE.local.md`가 있는지 확인합니다 |
| Codex가 예전 규칙을 따른다 | 위쪽 폴더나 `~/.codex`에 `AGENTS.override.md`가 있는지 확인합니다 |
| 뒷부분 규칙이 무시된다 | 파일이 너무 길지 않은지 확인하고, 한 폴더에 맞는 규칙만 남깁니다 |

## 내 프로젝트에 적용할 때

이 글의 실행은 임시 폴더에서 한 실험이며, 실제 프로젝트에 적용한 뒤의 효과(규칙 준수율이나 작업 시간)는 측정하지 않았습니다. 본인 프로젝트에 적용한다면 위의 다섯 줄 예시에서 시작해, 도구가 실수한 일이 생길 때마다 한 줄씩 추가하는 방식을 권합니다. 다음 글에서는 도구가 임의로 실행하는 명령을 어디까지 허용할지 정하는 권한 설정을 다룰 예정입니다.

## 참고 문서와 확인 범위

- [OpenAI: AGENTS.md로 지침 주기](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Anthropic: Claude Code의 CLAUDE.md와 메모리](https://code.claude.com/docs/en/memory)

이 글의 실행 결과는 Linux 한 환경에서 한 번씩 실행한 결과입니다. 요금제별 한도, Windows·macOS의 동작, 이후 버전의 변경은 확인하지 않았습니다.
