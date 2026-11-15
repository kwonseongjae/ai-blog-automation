"""저장된 세션으로 지정한 블로그의 편집기만 사용한다. 재로그인은 하지 않는다."""
import os
import html
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urlsplit

from automation.learning_blog import BLOG, ROOT, read_assets, validate_url


def default_tags(category):
    return ['Python', '자동화'] if category == 'Python·자동화' else ['AI 활용']


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
    document = BeautifulSoup(r.text, 'html.parser')
    actual = document.find(id=article['marker'])
    if actual is None or (article.get('kind', 'lab') == 'lab' and actual.find('pre') is None):
        return False
    expected_signature = article.get('expected_body') or (
        body_signature(article['html'], article['marker']) if article.get('html') else None)
    if expected_signature and body_signature(str(actual), article['marker']) != expected_signature:
        return False
    images = actual.find_all('img')
    if any(not valid_image_url(image.get('src', '')) for image in images):
        return False
    if article.get('html'):
        expected = BeautifulSoup(article['html'], 'html.parser').find(id=article['marker'])
        for image, original in zip(images, expected.find_all('img')):
            if urlsplit(image['src']).path != urlsplit(original['src']).path:
                return False
    if images:
        cover = document.find('meta', property='og:image')
        if not cover or not valid_image_url(cover.get('content', '')):
            return False
        from urllib.parse import parse_qs
        cover_url = cover['content']
        cover_url = parse_qs(urlsplit(cover_url).query).get('fname', [cover_url])[0]
        if urlsplit(cover_url).path != urlsplit(images[0]['src']).path:
            return False
    return True


def body_signature(body, marker):
    from bs4 import BeautifulSoup
    node = BeautifulSoup(body, 'html.parser').find(id=marker)
    if node is None:
        raise ValueError('본문 식별자가 없습니다')
    return {'text': hashlib.sha256(re.sub(r'\s+', '', node.get_text()).encode()).hexdigest(),
            'code': [pre.get_text().strip() for pre in node.find_all('pre')],
            'tables': [[[cell.name, cell.get_text().strip()] for cell in row.select('th,td')]
                       for table in node.find_all('table') for row in table.find_all('tr')],
            'images': [image.get('alt', '') for image in node.find_all('img')]}


def valid_image_url(url):
    p = urlsplit(url)
    return (p.scheme == 'https' and not p.username and not p.password
            and (p.netloc.endswith('.kakaocdn.net') or p.netloc.endswith('.daumcdn.net')
                 or p.netloc == 'cfile.tistory.com'))


def new_image_url(previous, current):
    old_paths = {urlsplit(url).path for url in previous}
    uploaded = [url for url in current if valid_image_url(url) and urlsplit(url).path not in old_paths]
    if len(uploaded) != 1:
        raise RuntimeError('새로 업로드한 이미지 하나를 구분하지 못했습니다')
    return uploaded[0]


def validate_posts(result):
    if not isinstance(result, dict) or not isinstance(result.get('items'), list):
        raise ValueError('글 관리 목록의 응답 형식이 올바르지 않습니다')
    for item in result['items']:
        if (not isinstance(item, dict) or not re.fullmatch(r'[1-9][0-9]*', str(item.get('id')))
                or not isinstance(item.get('title'), str)
                or item.get('visibility') not in {'PUBLIC', 'PRIVATE', 'PROTECTED'}):
            raise ValueError('글 관리 목록의 식별자·제목·공개 상태를 확인할 수 없습니다')
    return result['items']


def read_posts(cookies):
    import httpx
    jar = {c['name']: c['value'] for c in cookies}
    r = httpx.get(f'https://{BLOG}/manage/posts.json', cookies=jar,
                  follow_redirects=False, timeout=25, trust_env=False)
    r.raise_for_status()
    return validate_posts(r.json())


def upload_article_images(page, article):
    from bs4 import BeautifulSoup
    assets = read_assets(article, ROOT)
    if not assets:
        return
    # 표지부터 올려 편집기가 첫 이미지를 대표 이미지 후보로 등록하게 한다.
    page.evaluate('tinyMCE.activeEditor.setContent("")')
    body = article['html']
    for name in sorted(assets, key=lambda key: (key != 'cover', key)):
        previous = page.evaluate('[...tinyMCE.activeEditor.getBody().querySelectorAll("img")].map(i=>i.src)')
        page.locator('#mceu_0-open').evaluate('(el) => el.click()')
        with page.expect_file_chooser(timeout=15000) as chooser:
            page.get_by_text('사진', exact=True).evaluate('(el) => el.click()')
        chooser.value.set_files(str(ROOT / article['assets'][name]))
        page.wait_for_function('''(previous) => {
            const images = tinyMCE.activeEditor.getBody().querySelectorAll('img');
            return [...images].some(i => i.src.startsWith('https://') && !previous.includes(i.src));
        }''', arg=previous, polling=100, timeout=45000)
        current = page.evaluate('[...tinyMCE.activeEditor.getBody().querySelectorAll("img")].map(i=>i.src)')
        url = new_image_url(previous, current)
        body = body.replace(assets[name], html.escape(url, quote=True))
    images = BeautifulSoup(body, 'html.parser').find_all('img')
    if not images or any(not valid_image_url(image.get('src', '')) for image in images):
        raise RuntimeError('업로드되지 않은 이미지가 남아 있습니다')
    article['html'] = body


def publish(article):
    from playwright.sync_api import sync_playwright
    cookies = load_saved_cookies()
    previous = {item['id'] for item in read_posts(cookies)}
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
            page.wait_for_function('(name) => document.querySelector("#category-btn").textContent.includes(name)',
                                   arg=article['category'], polling=100)
            upload_article_images(page, article)
            page.evaluate('(body) => { tinyMCE.activeEditor.setContent(body); tinyMCE.activeEditor.save(); }', article['html'])
            page.wait_for_function('(marker) => tinyMCE.activeEditor.getContent().includes(marker)', arg=article['marker'], polling=100)
            for tag in article.get('tags', default_tags(article['category'])):
                page.locator('#tagText').fill(tag)
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
            # 화면 이동으로 저장 응답 본문이 사라질 수 있어 새 ID와 공개 본문을 직접 대조한다.
            for _ in range(3):
                for item in read_posts(cookies):
                    if item['id'] not in previous and item['title'] == article['title'] and item['visibility'] == 'PUBLIC':
                        url = validate_url(f'https://{BLOG}/{item["id"]}')
                        if verify(url, article):
                            return url
                time.sleep(1)
            raise RuntimeError('새 공개 글의 본문을 확인하지 못했습니다. 자동 재발행을 보류합니다')
        finally:
            browser.close()
