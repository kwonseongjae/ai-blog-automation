# 어떤 상황에 어떤 스킬을 설치할까: 문서 작업·화면 디자인·개발 절차·코드 줄이기·한글 윤문 다섯 가지

스킬이 너무 많아서 무엇부터 깔지 막막했습니다. 이름을 읽는 것만으로는 내 작업에 어디서 쓸지 감이 잡히지 않아 자주 하는 일 다섯 가지에 하나씩 짝지었습니다. 내 상황에 맞는 항목에서 설치 명령을 복사해 갈 수 있도록 적었습니다.

확인일: 2026-11-16 · 범위: Linux 한 환경, Claude Code 2.1.325, 설치된 플러그인 폴더를 열어 센 값과 각 저장소 README

## 스킬은 설치한 뒤 필요할 때 불러 쓰는 지침 묶음이다

`anthropics/skills` README는 스킬을 지침·스크립트·자료가 든 폴더로 설명하며 Claude가 특정 작업을 반복할 때 필요에 따라 불러온다고 적습니다. 만드는 데 필요한 파일은 `SKILL.md` 하나입니다. 머리글(frontmatter)의 필수 필드는 소문자와 하이픈으로 쓰는 `name`, 무엇을 하고 언제 쓰는지 적는 `description`입니다.

Claude Code에서는 마켓플레이스를 추가한 뒤 플러그인을 설치하고 설치된 스킬 이름을 요청에 넣어 사용합니다. README에는 PDF 스킬 이름과 파일 경로를 함께 지정하는 예가 있습니다. 기본 명령은 다음 두 줄입니다.

```text
/plugin marketplace add <저장소>
/plugin install <플러그인>@<마켓플레이스>
```

![내 작업을 고르고 마켓플레이스를 추가한 뒤 플러그인을 설치하고 새 세션에서 확인하는 순서](asset:flow)

## 이런 작업이 많다면 이 스킬

| 상황 | 추천 | GitHub 주소 |
|---|---|---|
| 문서를 자주 만듭니다 | anthropics/skills의 문서 스킬 | [anthropics/skills](https://github.com/anthropics/skills) |
| 화면 디자인을 자주 만듭니다 | frontend-design | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) |
| 개발 절차를 갖추고 싶습니다 | superpowers | [obra/superpowers](https://github.com/obra/superpowers) |
| 에이전트가 코드를 너무 길게 씁니다 | ponytail | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) |
| 한글 글의 기계적인 표현을 고치고 싶습니다 | humanize-korean | [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai) |

아래 별 수는 2026-11-16에 GitHub API로 확인한 값이며 저장소의 인기를 보여 줄 뿐 효과를 보증하지 않습니다. 선택 기준은 자주 하는 작업에 두었습니다.

## 문서를 자주 만든다면 문서 스킬부터 고른다

문서 작업이 잦다면 `anthropics/skills`의 문서 스킬을 먼저 고를 수 있으며 README는 문서용과 예제용 설치 명령을 구분해 안내합니다. 여기서는 문서용 명령을 적습니다.

저장소는 [anthropics/skills](https://github.com/anthropics/skills)입니다. 2026-11-16 확인 기준 별은 195,473개이며 마지막 푸시는 2026-11-14입니다.

저장소의 `skills` 폴더에는 스킬 이름이 19개 있으며 문서 외에 디자인과 개발 관련 항목도 들어 있습니다. 대표 항목은 다음과 같습니다.

- 문서: `doc-coauthoring`, `docx`, `pdf`, `pptx`, `xlsx`
- 디자인: `brand-guidelines`, `canvas-design`, `frontend-design`
- 개발: `mcp-builder`, `webapp-testing`

```text
/plugin marketplace add anthropics/skills
/plugin install document-skills@anthropic-agent-skills
```

README에서 읽은 내용은 `docx`·`pdf`·`pptx`·`xlsx`가 Claude의 문서 기능을 뒷받침하며 참고용으로 공개된 스킬이라는 설명입니다. 시연과 교육 목적으로 제공한다는 고지도 있습니다. 중요한 작업에 쓰기 전에는 직접 시험하라고 적혀 있습니다.

직접 확인한 범위에서는 문서 품질이나 작업 시간의 변화를 제시할 수 없으며 같은 작업에 스킬을 켜고 끄는 비교도 하지 않았습니다. 문서 결과가 얼마나 달라지는지는 이 글에서 판단하지 않습니다.

## 화면 디자인을 자주 만든다면 frontend-design을 고른다

화면의 UI/UX를 구현하는 작업이 잦다면 `frontend-design`을 고를 수 있으며 설치된 플러그인 설명도 이 용도를 명시합니다. 들어 있는 스킬은 하나입니다.

저장소는 [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official)입니다. 2026-11-16 확인 기준 별은 47,409개이며 마지막 푸시는 2026-11-14입니다. 라이선스는 Apache-2.0입니다.

- `frontend-design`: UI/UX 구현을 위한 프런트엔드 디자인 스킬

```text
/plugin install frontend-design@claude-plugins-official
```

직접 폴더를 열어 센 값은 설치 버전 1.1.1에서 스킬 1개, 명령 0개, 에이전트 0개이며 화면 결과물의 차이는 확인하지 않았습니다. 설치된 구성만 확인한 셈입니다. 디자인 품질이 좋아졌다는 효과는 이 글에 붙이지 않습니다.

## 개발 절차를 갖추고 싶다면 superpowers를 고른다

만들 것이 정해지면 곧바로 코드를 쓰는 흐름을 바꾸고 싶다면 `superpowers`가 맞는 후보이며 README는 이를 코딩 에이전트용 개발 방법론으로 설명합니다. 설계와 구현 계획을 거치는 절차가 중심입니다.

저장소는 [obra/superpowers](https://github.com/obra/superpowers)입니다. 2026-11-16 확인 기준 별은 318,143개이며 마지막 푸시는 2026-11-03입니다. 라이선스는 MIT입니다.

README가 설명하는 기능과 절차는 다음과 같습니다.

- 무엇을 만들려는지 먼저 묻고 설계를 읽을 만한 크기로 나눠 제시합니다.
- 승인 뒤 구현 계획을 만듭니다.
- 빨강-초록 TDD와 YAGNI를 강조합니다.
- 서브에이전트가 작업을 나눠 처리하고 검토합니다.
- 상황에 맞는 스킬이 자동으로 발동한다고 설명합니다.

설치된 스킬에는 `brainstorming`, `writing-plans`, `systematic-debugging`, `test-driven-development`가 있습니다. 검토와 완료 확인을 위한 `requesting-code-review`, `verification-before-completion`도 포함됩니다.

Claude Code의 공식 마켓플레이스 설치 명령은 다음과 같습니다.

```text
/plugin install superpowers@claude-plugins-official
```

README에는 효과 수치가 없으며 직접 확인한 값도 설치 버전 7.0.0의 스킬 15개, 명령 0개, 에이전트 0개입니다. 작업 시간이나 오류가 얼마나 줄었는지는 확인하지 않았습니다. README는 Codex 등 다른 도구용 설치 방법도 따로 안내합니다.

## 에이전트가 코드를 너무 길게 쓴다면 ponytail을 고른다

요청한 범위보다 추상화가 늘어나거나 코드가 길어지는 일이 고민이라면 `ponytail`이 맞는 후보이며 가장 단순하고 짧은 해법을 고르는 데 초점을 둡니다. README는 이를 “lazy senior dev” 모드라고 부릅니다.

저장소는 [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail)입니다. 2026-11-16 확인 기준 별은 191,555개이며 마지막 푸시는 2026-10-29입니다. 라이선스는 MIT입니다.

- 불필요한 추상화를 만들지 않고 표준 라이브러리를 먼저 쓰는 원칙을 둡니다.
- 설치된 스킬은 `ponytail`, `ponytail-audit`, `ponytail-debt`, `ponytail-gain`, `ponytail-help`, `ponytail-review`입니다.

```text
/plugin marketplace add DietrichGebert/ponytail
/plugin install ponytail@ponytail
```

README는 Claude Code에서 스킬 없이 실행한 같은 에이전트와 비교했다고 설명하며 실제 FastAPI+React 저장소를 포함한 작업 39개를 사용했습니다. 모델은 Opus 5.5입니다. 각 작업은 5회씩 실행했다고 적혀 있습니다.

다음은 모두 Ponytail 5의 **README가 밝힌 값**이며 제가 직접 재현하지 않았습니다.

- 코드 줄 수: 53% 감소
- 시간: 41% 감소
- 비용: 26% 감소
- 토큰: 45% 감소
- 위험한 로직에 테스트가 딸려 나온 비율: 98%, 스킬 없이 실행했을 때는 68%

직접 확인한 설치 버전은 4.8.4이며 폴더에서 센 값은 스킬 6개, 명령 6개, 에이전트 0개입니다. README의 수치와 설치 버전이 다릅니다. 제 환경에서도 같은 감소 폭이 나온다고 말할 근거는 없습니다.

## 한글 글에서 AI 티를 줄이고 싶다면 humanize-korean을 고른다

사실과 수치는 유지하면서 한글 문장의 기계적인 표현을 고치고 싶다면 `humanize-korean`이 맞는 후보이며 README도 문체·리듬·표현을 수정 범위로 설명합니다. 글의 사실과 주장은 바꾸지 않는다고 적혀 있습니다.

저장소는 [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai)입니다. 2026-11-16 확인 기준 별은 6,580개이며 마지막 푸시는 2026-11-15입니다. 라이선스는 MIT입니다.

- README는 번역투, 과한 영어 인용, 기계적 병렬, 피동태 남용, 이모지·불릿 남용 등 10개 분류 85개 패턴을 다룬다고 설명합니다.
- `/humanize-korean` 또는 `/humanize`로 호출합니다.
- 자연어로 “이 글 AI 티 없애줘”라고 요청할 수도 있습니다.
- `humanize-scan`은 손볼 부분이 많은지 먼저 보는 가벼운 점검용입니다. 이 용도는 스킬 설명에서 읽었습니다.
- 설치된 스킬은 `humanize`, `humanize-korean`, `humanize-redo`, `humanize-scan`입니다.

```text
/plugin marketplace add epoko77-ai/im-not-ai
/plugin install humanize-korean@im-not-ai
```

직접 확인한 값은 설치 버전 2.3.2에서 스킬 4개, 명령 4개, 에이전트 9개이며 윤문 효과를 정량으로 확인한 것은 없습니다. 설치 뒤 글이 얼마나 자연스러워졌는지도 비교하지 않았습니다. 위 기능 설명과 실제 효과 판단은 구분해서 읽어야 합니다.

## 여러 개를 함께 깔아도 되는가

여러 스킬을 함께 써 본 결과는 확인하지 않았으며 동시에 설치했을 때 충돌하는지도 이 글에서는 판단할 수 없습니다. 점검 순서는 아래 정도로 잡습니다.

1. 지금 자주 하는 작업에 맞는 플러그인 하나를 고릅니다.
2. 해당 절의 설치 명령을 실행합니다.
3. 새 세션을 엽니다.
4. 스킬 목록에 설치한 항목이 뜨는지 확인합니다.
5. 다른 플러그인도 필요하면 하나씩 같은 순서로 확인합니다.

## 이 글로 알 수 없는 것

이번 확인은 Linux 한 환경의 설치 폴더와 각 저장소 README를 기준으로 했으며 설치된 폴더의 구성은 최신 저장소와 다를 수 있습니다. 다음 항목은 확인하지 않았습니다.

- 같은 작업에 스킬을 켜고 끄며 비교한 결과
- README에 적힌 효과 수치의 재현 여부
- 여러 스킬을 동시에 설치했을 때의 충돌 여부
- Codex에서 설치하는 방법
- Windows·macOS에서의 설치와 동작
- 설치 뒤 응답 품질의 주관적인 차이

따라서 이 글에서 가져갈 수 있는 것은 상황별 후보와 Claude Code 설치 명령이며 내 작업에서의 효과까지 확인된 것은 아닙니다. 별 수만으로 우열을 정하지도 않았습니다.

## 참고 문서

- [anthropics/skills](https://github.com/anthropics/skills)
- [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official)
- [obra/superpowers](https://github.com/obra/superpowers)
- [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail)
- [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai)
- [공식 스킬 문서: anthropics/skills README](https://github.com/anthropics/skills#readme)
- [이번에 센 값과 확인 기록](https://github.com/kwonseongjae/ai-blog-automation/blob/main/docs/posts/evidence/skill-picks.json)
