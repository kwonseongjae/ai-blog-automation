# 입문자 중심 블로그 개편 구현 계획

작성자: 권성재
기준일: 2026-11-15

**목표:** 승인된 설계대로 분류·발행 순서·대문·프로젝트 소개 상자를 바꾸고, 빈 날을 프로젝트 적용 글로 채울 준비를 한다.

**구성:** 발행기(`automation/learning_blog.py`)의 분류와 검증을 바꾸고, 원고 목록과 보관 목록을 분리하며, 스킨 변환(`automation/technical_skin.py`)에서 대문과 표지 표시를 바꾼다. 실제 블로그 반영은 코드 변경과 분리한 확인 단계로 둔다.

**기술:** Python 3 표준 `unittest`, Node 점검 스크립트, 기존 Playwright 발행기.

**설계:** `docs/design/specs/2026-11-15-beginner-ai-blog-design.md`

## 전역 조건

- 하루 최대 1편, 한국 시각 20:30. 2026-11-15 글은 발행 완료라 추가 발행하지 않는다.
- 분류 이름은 정확히 `AI 시작하기`, `도구·모델 비교`, `프로젝트 적용기`, `Python·자동화`.
- 안내 글은 확인일·확인 범위·공식 출처 두 개 이상·표지가 필요하다.
- 발행기는 작업 폴더에 변경이 있거나 HEAD가 원격 main과 다르면 발행을 보류한다. 반영은 main 병합과 푸시까지 끝나야 한다.
- 로그인 정보·세션은 문서와 저장소에 넣지 않는다. 고객명·가격표·운영 데이터는 쓰지 않는다.
- 문서에는 작업 도구·모델 이름과 작업 경로를 쓰지 않는다. 문서를 쓴 뒤 저장소의 점검 절차(보고서 점검)가 `흔적 없음`이어야 한다.
- 기존 테스트 32개와 `node tests/check_skin_widgets.js`가 계속 통과한다.

## 점검 중점

각 항목은 아래 해당 작업의 테스트로 고정한다.

1. 보관 목록에 있는 식별자가 준비 스크립트를 다시 돌려도 원고 목록에 되살아나지 않는다. (작업 2)
2. 옛 분류 이름을 쓴 원고는 검증에서 거부된다. (작업 1)
3. `project`의 주소가 본인 저장소가 아니거나 이름에 HTML이 있어도 안전하게 거부·이스케이프된다. (작업 3)
4. 알 수 없는 분류도 태그가 빈 목록이 되지 않는다. (작업 1)
5. 목록 썸네일 이미지가 깨져도 직접 그린 표지가 보이고, 스크립트를 두 번 실행해도 결과가 같다. (작업 4)
6. "먼저 읽을 글" 링크는 이 블로그 주소만 허용한다. (작업 4)
7. `related`가 발행되지 않았거나 없는 식별자를 가리키면 링크를 만들지 않고 거부한다. (작업 5)
8. 안내 글의 태그가 3개 미만이거나 6개 초과이면 거부한다. (작업 5)

---

### 작업 1: 분류와 태그

**파일**
- 수정: `automation/learning_blog.py:19` (`CATEGORIES`)
- 수정: `automation/tistory_publisher.py:187` (태그 선택)
- 수정: `docs/posts/catalogue.json` (분류만)
- 수정: `tests/test_learning_blog.py:18`, `tests/test_rich_posts.py:27` (옛 분류 이름)
- 테스트: `tests/test_learning_blog.py`

**인터페이스**
- 제공: `CATEGORIES: tuple[str, ...]` 위 네 이름. `tistory_publisher.default_tags(category: str) -> list[str]`.

- [ ] **1단계: 실패하는 테스트.** `test_old_category_is_rejected`(옛 `'Python·자동화'` 원고가 `validate_article`에서 `ValueError`), `test_default_tags`(`'Python·자동화'` → `['Python', '자동화']`, 나머지 세 분류 → `['AI 활용']`).
- [ ] **2단계:** `python3 -m unittest tests.test_learning_blog -v` 실행, 두 테스트가 실패하는지 확인.
- [ ] **3단계:** `CATEGORIES`를 바꾸고 `default_tags`를 구현해 `article.get('tags', default_tags(article['category']))`로 호출한다. 기존 두 테스트 파일의 분류 이름을 `Python·자동화`과 `AI 시작하기`로 바꾼다.
- [ ] **4단계:** 카탈로그 분류를 정한다. `python-kst-date`, `python-path-base` → `Python·자동화`. `ai-agent-first-task`와 터미널 도구 첫 설정 글 두 편(식별자는 카탈로그 참조) → `AI 시작하기`. `daily-publish-state` → `프로젝트 적용기`.
- [ ] **5단계:** 전체 테스트 실행, 통과 확인.
- [ ] **6단계: 커밋** `feat: 입문자 중심 분류로 변경`

### 작업 2: 보관 목록과 발행 순서

**파일**
- 생성: `docs/posts/archive.json` (보관 항목 5개를 그대로 옮긴 목록)
- 수정: `docs/posts/catalogue.json`, `scripts/prepare_learning_posts.py:86-114`
- 테스트: 생성 `tests/test_catalogue.py`

**인터페이스**
- 제공: `prepare_learning_posts.merge_catalogue(existing: list[dict], generated: dict[str, dict], archived_ids: set[str]) -> list[dict]` — 보관 식별자는 결과에 넣지 않는다. 기존 항목의 순서를 보존하고 새 항목만 뒤에 붙인다.

- [ ] **1단계: 실패하는 테스트.**
  - `test_merge_skips_archived`: 보관 식별자를 생성 목록에 넣어도 결과에 없다.
  - `test_catalogue_order`: 현재 `catalogue.json`의 식별자 순서가 `python-kst-date, python-path-base, ai-agent-first-task`(발행 완료분) 다음에 터미널 도구 첫 설정 두 편, 마지막이 `daily-publish-state`이고, `validate_catalogue`를 통과한다.
  - `test_archive_not_in_catalogue`: `archive.json`의 식별자 5개(`python-json-boundary`, `python-atomic-state`, `python-request-id`, `python-subprocess-timeout`, `python-url-target`)가 카탈로그에 없다.
- [ ] **2단계:** 실행해 실패 확인. `python3 -m unittest tests.test_catalogue -v`
- [ ] **3단계:** `merge_catalogue`를 만들어 `main()`이 호출하고 `archive.json`의 식별자를 읽도록 한다. 보관 5개를 카탈로그에서 `archive.json`으로 옮긴다. 이미 발행한 두 `python-*` 글은 카탈로그에 남기고 순서는 발행 이력과 맞춘다(발행기는 이력으로 중복을 거른다).
- [ ] **4단계:** `TMPDIR=/dev/shm python3 -m unittest discover -s tests` 통과 확인. `python3 scripts/prepare_learning_posts.py` 재실행 뒤 `git diff docs/posts/catalogue.json`이 비어 있는지 확인(보관 항목이 되살아나지 않음).
- [ ] **5단계: 커밋** `feat: 보관 실습을 발행 목록에서 분리`

### 작업 3: 프로젝트 소개 상자

**파일**
- 수정: `automation/learning_blog.py` (`validate_article`, `publish_daily`의 본문 조립부)
- 수정: `docs/posts/catalogue.json` (`daily-publish-state`에 `project`)
- 테스트: `tests/test_learning_blog.py`

**인터페이스**
- 제공: `project_box(project: dict) -> str`. 입력 키 `name`, `url`, `role`, `result`(모두 문자열). 출력은 `<h2>이 글의 프로젝트</h2>` 아래 이름·저장소 링크·내가 한 일·확인한 결과. 모든 값은 HTML 이스케이프.
- `validate_article`: `project`가 있으면 네 키가 모두 필요하고, `url`은 `https://github.com/kwonseongjae/`로 시작해야 한다.

- [ ] **1단계: 실패하는 테스트.** `test_project_box_escapes`(이름에 `<b>`가 있으면 `&lt;b&gt;`), `test_project_url_must_be_own_repo`(다른 호스트·다른 계정 거부), `test_no_project_no_box`(항목이 없으면 본문에 `이 글의 프로젝트`가 없다).
- [ ] **2단계:** 실패 확인.
- [ ] **3단계:** 구현한다. 본문은 고정 버전 링크 앞에 상자를 붙인다. `daily-publish-state`의 `project` 값 문구는 권성재가 확인한 사실만 쓴다(이름: 기술블로그 발행기, 주소: 저장소 주소, 역할·결과는 본인 확인 후 기입).
- [ ] **4단계:** 전체 테스트 통과 확인.
- [ ] **5단계: 커밋** `feat: 글에 프로젝트 소개 상자 추가`

### 작업 4: 대문과 표지

**파일**
- 수정: `automation/technical_skin.py` (`home`, 새 `start_here`), `automation/technical_skin.css`, `automation/technical_skin.js`
- 테스트: `tests/test_technical_skin.py:36-48`(문구 단언 갱신), `tests/check_skin_widgets.js`

**인터페이스**
- 제공: `START_HERE: tuple[tuple[str, str], ...]` — (제목, 주소). 처음에는 `https://jacks-aiblog.tistory.com/3` 한 편. 글이 발행될 때마다 직접 추가한다. `start_here() -> str` — 주소가 `https://jacks-aiblog.tistory.com/`가 아니면 `ValueError`.
- JS: 깨진 썸네일을 숨기는 함수 `hideBrokenThumbnails()`(`img.complete && img.naturalWidth === 0`이거나 `error` 이벤트).

- [ ] **1단계: 실패하는 테스트.**
  - `test_technical_skin.py`: 소개 문구에 `AI를 처음 쓰는 개발자`, 주제 칩 세 개(`AI 시작하기`, `도구·모델 비교`, `프로젝트 적용기`), `먼저 읽을 글`이 있고 `Python·자동화` 칩은 없다. 두 번 변환해도 같다.
  - `test_start_here_only_own_blog`: 다른 주소를 넣으면 `ValueError`.
  - `check_skin_widgets.js`: `naturalWidth 0`인 썸네일이 숨고 정상 썸네일은 그대로이며, 스크립트 두 번 실행해도 같다.
- [ ] **2단계:** 실패 확인. `python3 -m unittest tests.test_technical_skin -v`, `node tests/check_skin_widgets.js`
- [ ] **3단계:** 구현한다. 소개 문구는 "AI를 처음 쓰는 개발자를 위한 설정·비교·적용 기록"을 기준으로 한다. CSS는 직접 그린 표지를 항상 아래에 깔고 이미지는 그 위에 얹으며(기존 `[has-thumbnail="1"] .learning-cover{display:none}` 규칙 제거), 목록을 카드형(넓은 화면 2열, 휴대폰 1열)으로 바꾼다. 목록 구조는 `/home/jack/blog-automation/data/technical_blog/backups/2026-11-15/readability-after.json`의 현재 스킨으로 확인한다.
- [ ] **4단계:** 전체 테스트와 위젯 점검 통과 확인.
- [ ] **5단계: 화면 확인.** 로컬 미리보기에서 폭 1440·375px로 대문을 캡처해 가로 넘침이 없고 표지가 비지 않는지 눈으로 확인한다.
- [ ] **6단계: 커밋** `style: 입문자용 대문과 카드형 목록`

### 작업 5: 관련 글, 사이드바 상자, 태그

**파일**
- 수정: `automation/learning_blog.py`(`validate_article`, `publish_daily` 본문 조립), `automation/technical_skin.py`, `automation/technical_skin.css`, `docs/posts/catalogue.json`
- 테스트: `tests/test_learning_blog.py`, `tests/test_technical_skin.py`

**인터페이스**
- 제공: `reading_minutes(source: str) -> int` — 한글 기준 분당 500자로 올림, 최소 1. 본문 첫머리에 `읽는 시간 약 N분`을 넣는다. 선택 항목 `correction`(문자열)이 있으면 본문 첫머리에 `정정 안내: ...`로 표시하고 HTML은 이스케이프한다.
- 제공: `related_box(related_ids: list[str], posted: list[dict]) -> str` — `posted`는 상태 파일의 발행 이력. 발행된 글만 제목·주소로 링크하고 해당 글이 없으면 `ValueError`. 빈 목록이면 빈 문자열.
- `validate_article`: `kind == 'guide'`이면 `tags`가 3~6개의 비어 있지 않은 문자열이어야 한다.
- `technical_skin.SIDE_PROMO: tuple[str, str]` — (문구, 주소). 주소는 이 블로그 또는 `REPOSITORY` 하위만 허용.

- [ ] **1단계: 실패하는 테스트.** `test_related_links_only_posted`, `test_related_unknown_id_rejected`, `test_guide_tags_3_to_6`, `test_side_promo_external_host_rejected`, `test_reading_minutes`(500자→1, 501자→2, 빈 문자열→1), `test_correction_escaped`, `test_popular_tab_hidden`(변환 결과에 인기글 탭을 숨기는 규칙이 있고 두 번 변환해도 같다).
- [ ] **2단계:** 실패 확인.
- [ ] **3단계:** 구현한다. 관련 글 상자는 `이 글의 프로젝트` 상자 앞에 붙이고, 사이드바 상자는 프로필 아래에 둔다. 카탈로그의 안내 글에 태그 3~6개를 채우고 관련 글 후보는 설계의 발행 순서 기준으로 정한다.
- [ ] **4단계:** 전체 테스트와 위젯 점검 통과 확인.
- [ ] **5단계: 커밋** `feat: 관련 글·사이드바 상자·태그 검증`

### 작업 6: GitHub 프로필 정리 (계정 변경은 항목마다 확인 후 진행)

**파일**: `/home/jack/github-profile/README.md`(로컬 사본), 필요 시 `tests/`의 기존 점검.

- [ ] **1단계:** 로컬 사본을 실제 프로필 저장소와 맞춘다(원격에서 가져와 차이를 확인). 덮어쓰지 않는다.
- [ ] **2단계:** README에 About 블록(이름·역할·지금 하는 일·블로그)과 대표 프로젝트 표(프로젝트·설명·바로가기)를 추가하고, 기술 학습 소개문을 입문자 방향으로 고친다. 수치와 기간은 현재 README에 이미 있는 값만 쓰고 공개 가능한 범위인지 확인받는다. 최근 글 자동 갱신 구간(`BLOG-POST-LIST`)은 건드리지 않는다.
- [ ] **3단계: 확인 후 실행.** README를 푸시하고, GitHub 설정에서 프로필의 블로그 주소를 `https://jacks-aiblog.tistory.com/`로 바꾸며, 고정 저장소를 `ai-blog-automation` 등으로 교체한다. 고정 저장소는 웹 화면에서 직접 바꾼다.
- [ ] **4단계:** 공개 프로필을 열어 주소·고정 저장소·README 표시와 최근 글 3편이 맞는지 확인한다.

### 작업 7: 실제 블로그 반영 (권성재 확인 후 진행)

코드가 아닌 실제 블로그 변경이다. 각 항목 전에 확인을 받는다.

- [ ] **1단계:** 관리 화면에서 카테고리 이름을 제자리에서 바꾼다(글이 따라 옮겨지므로 기존 글 수정 없음): `Python·자동화`는 그대로 두고, `AI·데이터`→`AI 시작하기`, `API·백엔드`→`도구·모델 비교`, `오류 해결`→`프로젝트 적용기`. `학습 회고`는 남기되 사용하지 않는다. **2026-11-16 20:30 발행 전에 끝내야 한다.** 발행기가 분류 이름으로 항목을 고르기 때문이다.
- [ ] **2단계:** 스킨을 수정하기 전에 현재 HTML·CSS·설정을 운영 디렉터리에 백업한 뒤 변경한 스킨을 적용한다.
- [ ] **3단계:** 변경을 main에 병합·푸시한다. 푸시 후 `git rev-parse HEAD`와 `git ls-remote origin refs/heads/main`이 같고 `git status --short`가 비어 있는지 확인한다.
- [ ] **4단계:** `... python3 -m automation.learning_blog --dry-run`으로 다음 글이 `status: ready`, 분류가 `AI 시작하기`인지 확인한다.
- [ ] **5단계:** 공개 대문을 열어 소개 문구·칩·카드·표지, 글 1·2·3의 분류 표시, 대문의 robots 태그가 `noindex`가 아닌 것을 확인한다.

### 작업 8: 새 입문 글과 빈 날 글 (글마다 반복)

글 한 편마다 아래를 거친다. 한 편의 원고가 한 번에 한 가지 질문에 답한다.

- [ ] 공식 문서 두 개 이상에서 사실을 확인하고, 직접 실행한 것과 설명용 예시를 구분해 쓴다.
- [ ] 비교 글은 표, 흐름은 그림을 쓴다. 표지 항목(`cover_text`, `diagram_*`)을 채우고 `scripts/build_post_assets.py`로 PNG를 만든다.
- [ ] 카탈로그에 추가하고 `checked_on`, `verification`, `assets`를 채운다. 순서는 설계서의 표를 따른다.
- [ ] 빈 날용 프로젝트 적용 글은 "어떤 AI로, 어떤 스킬과 기능을 써서, 무엇을 만들고, 어떻게 적용 중인가" 순서로 쓴다. `project` 항목을 채우고 고객명·가격표·운영 데이터는 제외한다.
- [ ] 발행되면 `START_HERE`에 입문 글을 추가한다(작업 4의 인터페이스).
- [ ] 전체 테스트와 `--dry-run` 통과 후 커밋·병합한다.

**일정 위험:** 새 글 5편이 필요한데 원고는 3편(시작하기 2, 적용 사례 1)뿐이다. 2026-11-18 이후 매일 발행하려면 11월 17일까지 새 글을 먼저 확보해야 한다. 없는 날은 발행기가 보류한다.
