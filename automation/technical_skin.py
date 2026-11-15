"""Odyssey의 글·카테고리·검색·댓글을 보존하는 학습 블로그 화면."""
import re
from pathlib import Path
from urllib.parse import quote

from automation.learning_blog import CATEGORIES, REPOSITORY

BLOG_TITLE = 'Jack의 AI 개발노트'
CSS = '<style id="learning-style">\n' + Path(__file__).with_suffix('.css').read_text().strip() + '\n</style>'
SCRIPT = '<script id="learning-widgets">\n' + Path(__file__).with_suffix('.js').read_text().strip() + '\n</script>'


def navigation():
    topics = ''.join(f'<li><a href="/category/{quote(name)}">{name}</a></li>' for name in CATEGORIES)
    return f"""<!-- learning-navigation:start -->
<nav class="learning-navigation" aria-label="블로그 메뉴"><a href="/">전체 글</a><details class="learning-menu"><summary>주제별 보기</summary><ul>{topics}</ul></details><a href="{REPOSITORY}" target="_blank" rel="noopener">GitHub 코드</a><a href="/rss">RSS</a></nav>
<!-- learning-navigation:end -->"""


def home():
    return f"""<!-- learning-home:start -->
<section id="learning-home" class="learning-home" aria-labelledby="learning-title">
  <h2 id="learning-title">개발하면서 배운 것들을 적습니다.</h2>
  <p>AI 도구를 직접 써보고, Python으로 자동화를 만듭니다.<br>설정 방법부터 프로젝트에서 막힌 이유까지 코드와 그림으로 정리합니다.</p>
  <div class="learning-actions"><a href="{REPOSITORY}" target="_blank" rel="noopener">GitHub 실습 코드</a><a href="https://github.com/kwonseongjae" target="_blank" rel="noopener">GitHub 프로필</a></div>
</section>
<!-- learning-home:end -->"""


PROFILE = """<section class="learning-profile" aria-label="블로그 소개"><h3 class="title-sidebar">Jack</h3><p>AI 도구 활용과 Python 자동화.<br>직접 만든 프로젝트를 이해하고<br>다른 작업에도 적용해봅니다.</p><p>실행한 내용과 예시를 구분하고,<br>코드와 참고 문서를 남깁니다.</p></section>"""

COVER = '<span class="learning-cover" aria-hidden="true"><span class="learning-cover-category">[##_list_rep_category_##]</span><strong>[##_list_rep_title_text_##]</strong></span>'


def _sidebar(match):
    body = match[1]
    if 'class="box-profile' in body or 'class="learning-profile"' in body:
        body = '<!-- 프로필 -->\n' + PROFILE
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
