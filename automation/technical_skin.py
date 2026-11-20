"""Odyssey의 글·카테고리·검색·댓글을 보존하는 학습 블로그 화면."""
import re
from pathlib import Path
from urllib.parse import quote

from automation.learning_blog import CATEGORIES, REPOSITORY, validate_url

BLOG_TITLE = 'Jack의 AI 개발노트'
# 처음이라면 읽는 순서: 실제로 이어서 읽는 순서라서 번호를 붙인다. 새 입문 글이 발행되면 한 줄 추가한다.
START_HERE = (('AI 에이전트란? 챗봇과 다른 점과 처음 맡길 일 3가지', 'https://jacks-aiblog.tistory.com/3'),
              ('Codex 설치 방법: 처음 쓸 때 로그인·작업 폴더까지 확인하는 법', 'https://jacks-aiblog.tistory.com/4'))
# 대문 주제 목록: 분류 이름(CATEGORIES 앞 세 개)과 한 줄 설명
TOPIC_NOTES = ('설치, 로그인, 지침 파일, 권한 같은 첫 설정', '같은 과제를 맡겨 보고 차이를 기록합니다', '직접 만든 프로젝트에 쓴 방법과 결과')
# 대문 실행 기록 예시: 실제로 실행한 명령과 결과만 적는다(Codex 첫 설정 글의 확인 값).
RECORD = (('명령', 'codex --version'), ('결과', 'codex-cli 0.167.2'))
RECORD_NOTE = '2026-11-15 · Linux · 1회 실행'
PRINCIPLES = ('하루 최대 한 편', '직접 실행해 확인한 내용', '확인일과 공식 출처 표기')
# 사이드바 안내 상자: (제목, 설명, 주소). 주소는 내 블로그 글이나 내 저장소만 허용한다.
SIDE_LINKS = (('AI 에이전트란?', '챗봇과 다른 점, 처음 맡길 일', 'https://jacks-aiblog.tistory.com/3'),
              ('Codex 처음 쓰기', '설치와 로그인, 첫 요청까지', 'https://jacks-aiblog.tistory.com/4'),
              ('실습 코드', '글에 쓴 코드와 실행 기록', REPOSITORY))
# 검색엔진 소유 확인 태그(공개 값). 서치콘솔·서치어드바이저 확인이 끝난 뒤에도 지우지 않는다.
VERIFY = ('<meta name="google-site-verification" content="kiT270Ci3IlqxFGJc5FkJyqgmk1WbyalXPzMM0uSE6E" />\n'
          '<meta name="naver-site-verification" content="8e426f4aff52279727befdfbbe719b39b53f3cd4" />')
CSS = '<style id="learning-style">\n' + Path(__file__).with_suffix('.css').read_text().strip() + '\n</style>'
EXTRAS = '<script id="learning-extras">\n' + Path(__file__).with_name('technical_skin_extras.js').read_text().strip() + '\n</script>'
SCRIPT = '<script id="learning-widgets">\n' + Path(__file__).with_suffix('.js').read_text().strip() + '\n</script>'


def navigation():
    topics = ''.join(f'<li><a href="/category/{quote(name)}">{name}</a></li>' for name in CATEGORIES)
    return f"""<!-- learning-navigation:start -->
<nav class="learning-navigation" aria-label="블로그 메뉴"><a href="/">전체 글</a><details class="learning-menu"><summary>주제별 보기</summary><ul>{topics}</ul></details><a href="/tag">태그</a><a href="{REPOSITORY}" target="_blank" rel="noopener">GitHub 코드</a><a href="/rss">RSS</a></nav>
<!-- learning-navigation:end -->"""


def side_promo():
    items = []
    for title, note, url in SIDE_LINKS:
        if not url.startswith(REPOSITORY):
            validate_url(url)
        items.append(f'<li><a href="{url}"><strong>{title}</strong><span>{note}</span></a></li>')
    return '<section class="learning-promo" aria-label="처음 쓰는 분께"><h3>처음 쓰는 분께</h3><ul>' + ''.join(items) + '</ul></section>'


def start_here():
    items = ''.join(f'<li><a href="{validate_url(url)}">{title}</a></li>' for title, url in START_HERE)
    return f'<div class="learning-start"><h3>처음이라면 이 순서로</h3><ol>{items}</ol></div>'


def home():
    topics = ''.join(f'<li><a href="/category/{quote(name)}"><strong>{name}</strong><span>{note}</span><em data-count-for="{quote(name)}"></em></a></li>'
                     for name, note in zip(CATEGORIES[:3], TOPIC_NOTES))
    record = ''.join(f'<dt>{k}</dt><dd><code>{v}</code></dd>' for k, v in RECORD)
    rules = ''.join(f'<li>{text}</li>' for text in PRINCIPLES)
    return f"""<!-- learning-home:start -->
<section id="learning-home" class="learning-home" aria-labelledby="learning-title">
  <div class="learning-lead-block">
    <h2 id="learning-title">AI 코딩 도구, 설정부터 같이 확인합니다</h2>
    <p class="learning-lead">Codex와 Claude Code를 직접 실행해 보고 되는 것과 막히는 것을 기록합니다. 처음 쓰는 분도 따라 할 수 있게 한 단계씩 씁니다.</p>
    {start_here()}
  </div>
  <figure class="learning-record" aria-label="실행 기록 예시">
    <figcaption>모든 글에 붙는 실행 기록</figcaption>
    <dl>{record}<dt>확인</dt><dd><mark>{RECORD_NOTE}</mark></dd></dl>
    <ul class="learning-principles">{rules}</ul>
    <a class="learning-repo" href="{REPOSITORY}" target="_blank" rel="noopener">글에 쓴 코드와 실행 기록은 GitHub에 있습니다</a>
  </figure>
</section>
<nav class="learning-topics" aria-label="주제">
  <h3>주제별로 읽기</h3>
  <ul>{topics}</ul>
</nav>
<!-- learning-home:end -->"""


PROFILE = """<section class="learning-profile" aria-label="블로그 소개"><h3 class="title-sidebar">Jack</h3><p>AI 도구를 처음 쓰는 개발자를 위해<br>설정과 비교, 직접 만든 프로젝트에<br>적용한 과정을 기록합니다.</p><p>실행한 내용과 예시를 구분하고,<br>코드와 참고 문서를 남깁니다.</p></section>"""

COVER = '<span class="learning-cover" aria-hidden="true"><span class="learning-cover-category">[##_list_rep_category_##]</span><strong>[##_list_rep_title_text_##]</strong></span>'


def _sidebar(match):
    body = match[1]
    if 'class="box-profile' in body or 'class="learning-profile"' in body:
        body = '<!-- 프로필 -->\n' + PROFILE + side_promo()
    if 'class="box-category' in body and 'learning-category-title' not in body:
        body = re.sub(r'(<div class="box-category[^\"]*">)', r'\1<h3 class="title-sidebar learning-category-title">주제별 기록</h3>', body, count=1)
    body = body.replace('>학습 주제</h3>', '>주제별 기록</h3>')
    body = body.replace('<h3 class="title-sidebar blind">최근글과 인기글</h3>', '<h3 class="title-sidebar">최근 학습 글</h3>')
    return '<s_sidebar_element>' + body + '</s_sidebar_element>'


def transform(source):
    source = re.sub(r'<style id="learning-style">.*?</style>\n?', '', source, flags=re.S)
    source = re.sub(r'\n?<!-- learning-home:start -->.*?<!-- learning-home:end -->', '', source, flags=re.S)
    source = re.sub(r'\n?<!-- learning-navigation:start -->.*?<!-- learning-navigation:end -->', '', source, flags=re.S)
    source = re.sub(r'<script id="learning-widgets">.*?</script>\n?', '', source, flags=re.S)
    source = re.sub(r'<script id="learning-extras">.*?</script>\n?', '', source, flags=re.S)
    source = re.sub(r'<meta name="(?:google|naver)-site-verification"[^>]*>\s*', '', source)
    if '</head>' not in source or '<div class="area-main">' not in source:
        raise ValueError('확인된 Odyssey 스킨 구조가 아닙니다')
    source = re.sub(r'<s_sidebar_element>(.*?)</s_sidebar_element>', _sidebar, source, flags=re.S)
    if 'class="learning-cover"' not in source:
        image = '<img src="[##_list_rep_thumbnail_raw_url_##]" class="img-thumbnail" role="presentation">'
        source = source.replace(image, image + COVER, 1)
        source = re.sub(r'(<a\b[^>]*?href="\[##_list_rep_link_##\]"[^>]*)(>\s*<p class="thumbnail")',
                        r'\1 aria-label="[##_list_rep_title_text_##]"\2', source, count=1)
    footer = BLOG_TITLE + ' · 학습과 실습 기록'
    source = source.replace('[##_var_footerCopyright_##]', footer)
    source = source.replace('권성재의 기술노트 · 코드와 함께 쌓는 학습 기록', footer)
    source = source.replace('</head>', VERIFY + '\n' + CSS + '\n</head>', 1)
    if '</h1>' in source and '</header>' in source:
        source = source.replace('</h1>', '</h1>\n' + navigation(), 1)
    elif '</header>' in source:
        source = source.replace('</header>', '</header>\n' + navigation(), 1)
    source = source.replace('<div class="area-main">', '<div class="area-main">\n' + home(), 1)
    return source.replace('</body>', SCRIPT + '\n' + EXTRAS + '\n</body>', 1)
