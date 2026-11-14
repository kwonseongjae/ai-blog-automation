"""Odyssey의 글·카테고리·검색·댓글을 보존하는 학습 블로그 화면."""
import re
from pathlib import Path
from urllib.parse import quote

from automation.learning_blog import CATEGORIES, REPOSITORY

CSS = '<style id="learning-style">\n' + Path(__file__).with_suffix('.css').read_text().strip() + '\n</style>'
SCRIPT = '<script id="learning-widgets">\n' + Path(__file__).with_suffix('.js').read_text().strip() + '\n</script>'


def topic_links():
    return ''.join(f'<a href="/category/{quote(name)}">{name}</a>' for name in CATEGORIES)


def navigation():
    topics = ''.join(f'<li><a href="/category/{quote(name)}">{name}</a></li>' for name in CATEGORIES)
    return f"""<!-- learning-navigation:start -->
<nav class="learning-navigation" aria-label="블로그 메뉴"><a href="/">전체 글</a><details class="learning-menu"><summary>주제별 보기</summary><ul>{topics}</ul></details><a href="{REPOSITORY}" target="_blank" rel="noopener">GitHub 코드</a><a href="/rss">RSS</a></nav>
<!-- learning-navigation:end -->"""


def home():
    return f"""<!-- learning-home:start -->
<section id="learning-home" class="learning-home" aria-labelledby="learning-title">
  <h2 id="learning-title">작게 만들고, 실행하며 배웁니다.</h2>
  <p>Python과 API에서 시작하는 기술 학습 노트.<br>실행 코드와 확인 결과, 적용할 때의 한계를 함께 남깁니다.</p>
  <div class="learning-actions"><a href="/1">첫 실습 읽기</a><a href="{REPOSITORY}/tree/main/labs" target="_blank" rel="noopener">예제 코드 보기</a></div>
  <nav class="learning-topics" aria-label="학습 주제">{topic_links()}</nav>
</section>
<!-- learning-home:end -->"""


PROFILE = """<section class="learning-profile" aria-label="블로그 소개"><div class="learning-profile-heading"><span class="learning-monogram" aria-hidden="true">&lt;/&gt;</span><strong>권성재의 학습 노트</strong></div><p>작은 실습으로 기술을 이해하고,<br>코드와 문제 해결 과정을 기록합니다.</p><div class="learning-profile-links"><a href="https://github.com/kwonseongjae" target="_blank" rel="noopener">GitHub 프로필</a><a href="/rss">RSS 구독</a></div></section>"""


def _sidebar(match):
    body = match[1]
    if 'class="box-profile' in body or 'class="learning-profile"' in body:
        body = '<!-- 프로필 -->\n' + PROFILE
    if 'class="box-category' in body and 'learning-category-title' not in body:
        body = re.sub(r'(<div class="box-category[^\"]*">)', r'\1<h3 class="title-sidebar learning-category-title">학습 주제</h3>', body, count=1)
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
    source = source.replace('</head>', CSS + '\n</head>', 1)
    if '</header>' in source:
        source = source.replace('</header>', '</header>\n' + navigation(), 1)
    source = source.replace('<div class="area-main">', '<div class="area-main">\n' + home(), 1)
    return source.replace('</body>', SCRIPT + '\n</body>', 1)
