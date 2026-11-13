"""Odyssey 스킨의 기존 글·검색·댓글을 유지하며 학습 대문을 덧붙인다."""
import re
from urllib.parse import quote

from automation.learning_blog import CATEGORIES, REPOSITORY

CSS = '''
<style id="learning-style">
:root{--learn-ink:#18324d;--learn-link:#245d99;--learn-line:#dce4ed;--learn-paper:#f7f9fc}
body{background:var(--learn-paper);color:var(--learn-ink)}
a:focus-visible,button:focus-visible,summary:focus-visible{outline:3px solid #245d99;outline-offset:4px}
.learning-home{display:none;max-width:1120px;margin:12px auto 50px;padding:40px 32px 30px;box-sizing:border-box;background:#fff;border-top:4px solid var(--learn-link)}
#tt-body-index .learning-home{display:block}
.learning-home h2{max-width:830px;margin:0 0 20px;font-size:clamp(28px,3.8vw,48px);font-weight:750;line-height:1.38;letter-spacing:-1.6px;word-break:keep-all;color:var(--learn-ink)}
.learning-home p{max-width:720px;margin:0 0 22px;color:#4c6075;font-size:17px;line-height:1.85;word-break:keep-all}
.learning-actions{display:flex;gap:12px;flex-wrap:wrap;margin:26px 0 32px}
.learning-actions a{display:inline-block;padding:12px 18px;border:1px solid var(--learn-link);border-radius:4px;font-size:15px;font-weight:650;color:var(--learn-link);text-decoration:none}
.learning-actions a:first-child{background:var(--learn-link);color:white}
.learning-topics{display:flex;flex-wrap:wrap;gap:12px 22px;padding:20px 0;border-top:1px solid var(--learn-line);border-bottom:1px solid var(--learn-line)}
.learning-topics a{font-size:15px;color:var(--learn-ink);text-decoration:underline;text-underline-offset:5px}
.learning-path{margin:30px 0 10px;scroll-margin-top:90px}
.learning-path h3{font-size:19px;margin:0 0 16px;color:var(--learn-ink)}
.learning-path ol{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:26px;margin:0;padding:0;list-style:none;counter-reset:learning-step}
.learning-path li{counter-increment:learning-step;font-size:14px;line-height:1.9;color:#4c6075;border-left:2px solid var(--learn-line);padding-left:16px}
.learning-path li:before{content:counter(learning-step) ". ";font-weight:700;color:var(--learn-link)}
.learning-path strong{display:inline;color:var(--learn-ink)}
.learning-about{margin-top:24px;padding-top:20px;border-top:1px solid var(--learn-line);font-size:14px;line-height:1.85;color:#4c6075}
.learning-about p{font-size:14px;margin:0}
.article-view,.area-main,.area-view,.tt_article_useless_p_margin{min-width:0}
.article-view pre,.tt_article_useless_p_margin pre{max-width:100%;box-sizing:border-box;overflow-x:auto;padding:20px!important;background:#edf2f8!important;border:1px solid #dce4ed;border-radius:4px;font-size:14px;line-height:1.75;tab-size:4;color:#1c3046!important}
.article-view pre code,.tt_article_useless_p_margin pre code{white-space:pre!important;word-break:normal;background:transparent;padding:0;font-family:Consolas,'Liberation Mono',monospace;color:inherit}
.article-view :not(pre)>code,.tt_article_useless_p_margin :not(pre)>code{background:#edf2f8;padding:2px 5px;border-radius:3px;color:#1b4e82;overflow-wrap:anywhere}
.article-view p,.tt_article_useless_p_margin p{line-height:1.95;word-break:keep-all;overflow-wrap:break-word}
.article-view h2,.tt_article_useless_p_margin h2{margin-top:2em;line-height:1.5;color:var(--learn-ink)}
.article-view a,.tt_article_useless_p_margin a{color:var(--learn-link);text-underline-offset:4px}
@media(max-width:767px){.learning-home{margin:0 0 28px;padding:28px 20px 24px}.learning-home h2{letter-spacing:-.8px}.learning-home p{font-size:15px}.learning-path ol{grid-template-columns:1fr;gap:16px}.learning-actions{margin:22px 0}.learning-topics{gap:14px 18px}.learning-topics a{font-size:14px}.article-view pre,.tt_article_useless_p_margin pre{padding:14px!important;font-size:12px}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{scroll-behavior:auto!important;animation:none!important;transition:none!important}}
</style>
'''.strip()


def home():
    topics = ''.join(f'<a href="/category/{quote(name)}">{name}</a>' for name in CATEGORIES)
    return f'''<!-- learning-home:start -->
<section id="learning-home" class="learning-home" aria-labelledby="learning-title">
  <h2 id="learning-title">배운 기술을 코드로 확인하고,<br>실패한 과정까지 기록합니다.</h2>
  <p>Python과 API, 자동화를 작은 예제로 익히는 학습 노트입니다. 실행 방법과 확인 결과, 적용할 때의 한계를 함께 남깁니다.</p>
  <div class="learning-actions"><a href="#learning-path">처음부터 읽기</a><a href="{REPOSITORY}" target="_blank" rel="noopener">GitHub에서 코드 보기</a></div>
  <nav class="learning-topics" aria-label="학습 주제">{topics}</nav>
  <div id="learning-path" class="learning-path"><h3>작은 실습부터 시작하기</h3>
    <ol><li><strong>Python 기초</strong><br>시간대와 경로, 입력값을 정확하게 다룹니다.</li><li><strong>안전한 자동화</strong><br>저장 실패와 중복 요청, 대기 시간을 확인합니다.</li><li><strong>설명과 재현</strong><br>공식 문서와 코드를 연결하고 한계를 적습니다.</li></ol>
  </div>
  <div id="learning-about" class="learning-about"><p>이 블로그는 권성재의 기술 학습 기록입니다. 각 글은 한 가지 질문을 다루며, 예제 코드와 공식 출처를 통해 다시 확인할 수 있도록 정리합니다.</p></div>
</section>
<!-- learning-home:end -->'''


def transform(source):
    source = re.sub(r'<style id="learning-style">.*?</style>\n?', '', source, flags=re.S)
    source = re.sub(r'\n?<!-- learning-home:start -->.*?<!-- learning-home:end -->', '', source, flags=re.S)
    if '</head>' not in source or '<div class="area-main">' not in source:
        raise ValueError('확인된 Odyssey 스킨 구조가 아닙니다')
    source = source.replace('</head>', CSS + '\n</head>', 1)
    return source.replace('<div class="area-main">', '<div class="area-main">\n' + home(), 1)
