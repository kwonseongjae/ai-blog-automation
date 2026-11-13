"""저장된 세션으로 지정한 블로그의 편집기만 사용한다. 재로그인은 하지 않는다."""
import os
import html
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from automation.learning_blog import BLOG, validate_url


def normalize_cookies(saved):
    result = []
    for c in saved or []:
        domain = c.get('domain', '').lstrip('.')
        if not c.get('name') or not c.get('value') or not (domain == 'tistory.com' or domain.endswith('.tistory.com')):
            continue
        result.append({'name': c['name'], 'value': c['value'], 'domain': c['domain'],
                       'path': c.get('path') or '/', 'secure': bool(c.get('secure')),
                       'httpOnly': bool(c.get('httpOnly')),
                       'sameSite': c.get('sameSite') if c.get('sameSite') in ('Strict', 'Lax', 'None') else 'Lax'})
    return result


def check_management_url(url):
    p = urlsplit(url)
    if p.scheme != 'https' or p.netloc != BLOG or not p.path.startswith('/manage'):
        raise RuntimeError('새 블로그 관리 화면이 아닙니다. 로그인 상태를 수동 확인하세요')


def load_saved_cookies():
    root = Path(os.environ['BLOG_AUTOMATION_ROOT']).resolve()
    from dotenv import dotenv_values
    from cryptography.fernet import Fernet
    settings = dotenv_values(root / '.env')
    key = os.environ.get('SESSION_ENCRYPT_KEY') or settings.get('SESSION_ENCRYPT_KEY')
    if not key:
        raise RuntimeError('기존 세션을 읽을 암호화 키가 없습니다')
    sessions = Path(os.environ.get('SESSIONS_DIR') or settings.get('SESSIONS_DIR') or root / 'data/sessions')
    if not sessions.is_absolute():
        sessions = root / sessions
    encrypted = (sessions / 'tistory.session').read_bytes()
    saved = json.loads(Fernet(key.encode()).decrypt(encrypted))
    cookies = normalize_cookies(saved)
    if not cookies:
        raise RuntimeError('저장된 로그인 세션이 없습니다. 수동 로그인이 필요합니다')
    return cookies


def verify(url, article):
    import httpx
    from bs4 import BeautifulSoup
    validate_url(url)
    r = httpx.get(url, follow_redirects=False, timeout=25, trust_env=False)
    if r.status_code != 200 or article['title'] not in html.unescape(r.text):
        return False
    actual = BeautifulSoup(r.text, 'html.parser').find(id=article['marker'])
    if actual is None or actual.find('pre') is None:
        return False
    if article.get('html'):
        expected = BeautifulSoup(article['html'], 'html.parser').find(id=article['marker'])
        if re.sub(r'\s+', '', actual.get_text()) != re.sub(r'\s+', '', expected.get_text()):
            return False
        if [c.get_text().strip() for c in actual.find_all('pre')] != [c.get_text().strip() for c in expected.find_all('pre')]:
            return False
    return True


def post_url(result):
    if not isinstance(result, dict):
        raise ValueError('글 저장 응답이 객체가 아닙니다')
    entry = result.get('entryId')
    if not re.fullmatch(r'[1-9][0-9]*', str(entry)):
        raise ValueError('글 번호를 확인하지 못했습니다. 응답 항목: ' + ', '.join(result.keys()))
    return validate_url(f'https://{BLOG}/{entry}')


def publish(article):
    from playwright.sync_api import sync_playwright
    cookies = load_saved_cookies()
    with sync_playwright() as p:
        browser_env = {k: v for k, v in os.environ.items()
                       if k in {'HOME', 'PATH', 'LANG', 'LD_LIBRARY_PATH', 'DISPLAY', 'XDG_RUNTIME_DIR', 'TMPDIR'}}
        browser = p.chromium.launch(headless=True, env=browser_env)
        try:
            context = browser.new_context(viewport={'width': 1440, 'height': 1000}, locale='ko-KR')
            context.add_cookies(cookies)
            page = context.new_page()
            page.set_default_timeout(20000)
            page.on('dialog', lambda dialog: dialog.dismiss())
            page.goto(f'https://{BLOG}/manage/newpost', wait_until='domcontentloaded')
            check_management_url(page.url)
            page.wait_for_function('globalThis.tinyMCE?.activeEditor?.initialized === true', polling=100)
            page.locator('#post-title-inp').fill(article['title'])
            # 이 환경은 화면 프레임 대기가 멈추므로 준비된 DOM의 클릭 이벤트를 사용한다.
            page.locator('#category-btn').evaluate('(el) => el.click()')
            page.get_by_role('option', name=article['category'], exact=True).evaluate('(el) => el.click()')
            page.evaluate('(body) => { tinyMCE.activeEditor.setContent(body); tinyMCE.activeEditor.save(); }', article['html'])
            page.wait_for_function('(marker) => tinyMCE.activeEditor.getContent().includes(marker)', arg=article['marker'], polling=100)
            page.locator('#tagText').fill('Python')
            page.locator('#tagText').press('Enter')
            check_management_url(page.url)
            page.locator('#publish-layer-btn').evaluate('(el) => el.click()')
            page.locator('#open20').evaluate('(el) => el.click()')
            if not page.locator('#open20').is_checked():
                raise RuntimeError('공개 발행 설정을 확인하지 못했습니다')
            # 결과 응답이 없으면 예외를 전파한다. 상위 대장의 pending이 재발행을 막는다.
            with page.expect_response(lambda r: r.request.method == 'POST'
                                      and urlsplit(r.url).netloc == BLOG
                                      and urlsplit(r.url).path == '/manage/post.json', timeout=45000) as response:
                page.locator('#publish-btn').evaluate('(el) => el.click()')
            r = response.value
            if not r.ok:
                raise RuntimeError('글 저장 응답을 확인하지 못했습니다')
            return post_url(r.json())
        finally:
            browser.close()
