"""Odyssey의 글·카테고리·검색·댓글을 보존하는 학습 블로그 화면."""
import re
from pathlib import Path
from urllib.parse import quote

from automation.learning_blog import CATEGORIES, REPOSITORY, validate_url

BLOG_TITLE = 'Jack의 AI 개발노트'
# 먼저 읽을 글: 입문 순서대로 직접 고른다. 새 입문 글이 발행되면 한 줄 추가한다.
START_HERE = (('AI 에이전트란? 챗봇과 다른 점과 처음 맡길 일 3가지', 'https://jacks-aiblog.tistory.com/3'),)
# 대문 주제 카드: 분류 이름(CATEGORIES 앞 세 개)과 한 줄 설명
TOPIC_NOTES = ('설치, 로그인, 지침 파일, 권한 같은 첫 설정', '같은 과제를 맡겨 보고 차이를 기록합니다', '직접 만든 프로젝트에 쓴 방법과 결과')
PRINCIPLES = ('하루 최대 한 편', '직접 실행해 확인한 내용', '확인일과 공식 출처 표기')
# 사이드바 안내 상자: 입문 글 모음으로 보내고, 공개 프로젝트가 생기면 저장소 주소로 바꾼다.
SIDE_PROMO = ('AI 도구를 처음 쓰신다면 여기부터', 'https://jacks-aiblog.tistory.com/3')
CSS = '<style id="learning-style">\n' + Path(__file__).with_suffix('.css').read_text().strip() + '\n</style>'
SCRIPT = '<script id="learning-widgets">\n' + Path(__file__).with_suffix('.js').read_text().strip() + '\n</script>'


def navigation():
    topics = ''.join(f'<li><a href="/category/{quote(name)}">{name}</a></li>' for name in CATEGORIES)
    return f"""<!-- learning-navigation:start -->
<nav class="learning-navigation" aria-label="블로그 메뉴"><a href="/">전체 글</a><details class="learning-menu"><summary>주제별 보기</summary><ul>{topics}</ul></details><a href="{REPOSITORY}" target="_blank" rel="noopener">GitHub 코드</a><a href="/rss">RSS</a></nav>
<!-- learning-navigation:end -->"""


def side_promo():
    text, url = SIDE_PROMO
    if not url.startswith(REPOSITORY):
        validate_url(url)
    return f'<section class="learning-promo"><a href="{url}">{text} →</a></section>'


def start_here():
    items = ''.join(f'<li><a href="{validate_url(url)}">{title}</a></li>' for title, url in START_HERE)
    return f'<div class="learning-start"><h3>먼저 읽을 글</h3><ol>{items}</ol></div>'


def home():
    cards = ''.join(f'<a href="/category/{quote(name)}"><strong>{name}</strong><span>{note}</span></a>'
                    for name, note in zip(CATEGORIES[:3], TOPIC_NOTES))
    principles = ''.join(f'<li>{text}</li>' for text in PRINCIPLES)
    return f"""<!-- learning-home:start -->
<section id="learning-home" class="learning-home" aria-labelledby="learning-title">
  <p class="learning-eyebrow">AI 입문 개발노트</p>
  <h2 id="learning-title">AI를 처음 쓰는 개발자를 위한 설정·비교·적용 기록</h2>
  <p class="learning-lead">도구 설치와 설정, 에이전트·모델 고르는 기준, 직접 만든 프로젝트에 적용한 과정을<br>실행 결과와 함께 적습니다.</p>
  <ul class="learning-principles">{principles}</ul>
  <nav class="learning-cards" aria-label="주제">{cards}</nav>
  {start_here()}
  <div class="learning-actions"><a href="{REPOSITORY}" target="_blank" rel="noopener">GitHub 실습 코드</a><a href="https://github.com/kwonseongjae" target="_blank" rel="noopener">GitHub 프로필</a></div>
</section>
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
    source = source.replace('</head>', CSS + '\n</head>', 1)
    if '</h1>' in source and '</header>' in source:
        source = source.replace('</h1>', '</h1>\n' + navigation(), 1)
    elif '</header>' in source:
        source = source.replace('</header>', '</header>\n' + navigation(), 1)
    source = source.replace('<div class="area-main">', '<div class="area-main">\n' + home(), 1)
    return source.replace('</body>', SCRIPT + '\n</body>', 1)
