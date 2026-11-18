"""검증된 학습 원고를 한국 날짜 기준 하루 한 편 배포한다."""
import argparse
import base64
import fcntl
import hashlib
import html
import json
import os
import re
import subprocess
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

BLOG = 'jacks-aiblog.tistory.com'
REPOSITORY = 'https://github.com/kwonseongjae/ai-blog-automation'
CATEGORIES = ('AI 시작하기', '도구·모델 비교', '프로젝트 적용기', 'Python·자동화')
ROOT = Path(__file__).resolve().parents[1]


def kst_day(now):
    if now.tzinfo is None:
        raise ValueError('시간대가 있는 시각이 필요합니다')
    return now.astimezone(ZoneInfo('Asia/Seoul')).date().isoformat()


def validate_url(url):
    p = urlsplit(url)
    if (p.scheme != 'https' or p.netloc != BLOG or p.query or p.fragment
            or not re.fullmatch(r'/[1-9][0-9]*', p.path)):
        raise ValueError('대상 블로그의 공개 글 주소가 아닙니다')
    return url


MOBILE_PARAGRAPH_MAX = 150  # 모바일 본문은 한 줄 약 23자, 6~7줄 이하
MOBILE_TABLE_COLUMNS_MAX = 4
MOBILE_RULE_FROM = '2026-11-17'  # 이전 글은 그대로 두고 새 글부터 적용


def mobile_issues(source):
    issues, in_code = [], False
    for line in source.splitlines():
        if line.startswith('```'):
            in_code = not in_code
        elif in_code:
            continue
        elif line.startswith('|'):
            wide = f'표 열이 {MOBILE_TABLE_COLUMNS_MAX}개를 넘습니다'
            if line.count('|') - 1 > MOBILE_TABLE_COLUMNS_MAX and wide not in issues:
                issues.append(wide)
        elif len(line) > MOBILE_PARAGRAPH_MAX and not line.startswith(('#', '!', '>')):
            issues.append(f'문단이 {len(line)}자입니다: {line[:20]}…')
    return issues


def validate_article(article, root):
    for key in ('id', 'title', 'category', 'markdown', 'sources'):
        if not article.get(key):
            raise ValueError(f'원고 필수 항목 누락: {key}')
    if not re.fullmatch(r'[a-z][a-z0-9-]{1,70}', article['id']):
        raise ValueError('원고 식별자가 올바르지 않습니다')
    if article['category'] not in CATEGORIES:
        raise ValueError('허용되지 않은 카테고리입니다')
    if not isinstance(article['sources'], list):
        raise ValueError('공식 출처 목록이 필요합니다')
    kind = article.get('kind', 'lab')
    if kind not in {'lab', 'guide'} or (kind == 'lab' and not article.get('lab')):
        raise ValueError('실습 또는 안내 원고 형식이 필요합니다')
    if kind == 'guide':
        date.fromisoformat(article.get('checked_on', ''))
        if (not article.get('verification') or len(article['sources']) < 2
                or not article.get('assets', {}).get('cover')):
            raise ValueError('안내 원고에는 확인 범위·공식 출처 두 개·표지가 필요합니다')
    path = (root / article['markdown']).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('저장소 내부 원고가 필요합니다')
    if kind == 'guide' and article['checked_on'] >= MOBILE_RULE_FROM:
        issues = mobile_issues(path.read_text(encoding='utf-8'))
        if issues:
            raise ValueError('모바일에서 읽기 어려운 원고입니다: ' + '; '.join(issues[:3]))
    for source in article['sources']:
        p = urlsplit(source)
        official = p.netloc in {'docs.python.org', 'www.sqlite.org', 'learn.chatgpt.com',
                               'developers.openai.com', 'code.claude.com', 'www.anthropic.com'}
        official_repo = p.netloc == 'github.com' and any(
            p.path == repo or p.path.startswith(repo + '/') for repo in
            ('/openai/codex', '/anthropics/claude-code', '/anthropics/skills',
             '/anthropics/claude-plugins-official', '/kwonseongjae/ai-blog-automation'))
        if p.scheme != 'https' or not (official or official_repo):
            raise ValueError('허용된 공식 문서 주소가 아닙니다')
    tags = article.get('tags')
    if (tags is not None or kind == 'guide') and not (
            isinstance(tags, list) and 3 <= len(tags) <= 6
            and all(isinstance(t, str) and t.strip() for t in tags)):
        raise ValueError('태그는 비어 있지 않은 3~6개가 필요합니다')
    related = article.get('related', [])
    if not (isinstance(related, list) and len(related) <= 3 and all(isinstance(r, str) for r in related)):
        raise ValueError('관련 글은 식별자 3개 이하의 목록이어야 합니다')
    if article.get('project') is not None:
        validate_project(article['project'])
    read_assets(article, root)
    return path


def read_assets(article, root):
    assets = article.get('assets', {})
    if not isinstance(assets, dict):
        raise ValueError('이미지 목록 형식이 올바르지 않습니다')
    result = {}
    for name, relative in assets.items():
        if not re.fullmatch(r'[a-z][a-z0-9-]*', name) or not isinstance(relative, str):
            raise ValueError('이미지 식별자와 경로가 올바르지 않습니다')
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file() or path.stat().st_size > 2_000_000:
            raise ValueError('저장소 내부 2MB 이하 PNG가 필요합니다')
        data = path.read_bytes()
        if not data.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('PNG 이미지가 아닙니다')
        result[name] = 'data:image/png;base64,' + base64.b64encode(data).decode('ascii')
    return result


def validate_project(project):
    if not isinstance(project, dict) or not all(isinstance(project.get(k), str) and project[k].strip()
                                                for k in ('name', 'url', 'role', 'result')):
        raise ValueError('프로젝트 항목에는 이름·주소·역할·결과가 필요합니다')
    if not project['url'].startswith('https://github.com/kwonseongjae/'):
        raise ValueError('프로젝트 주소는 본인 저장소여야 합니다')


def project_box(project):
    validate_project(project)
    e = html.escape
    return (f'<h2>이 글의 프로젝트</h2><p><a href="{e(project["url"], quote=True)}">{e(project["name"])}</a></p>'
            f'<ul><li>내가 한 일: {e(project["role"])}</li><li>확인한 결과: {e(project["result"])}</li></ul>')


def reading_minutes(source):
    return max(1, -(-len(source) // 500))


def related_box(related_ids, posted):
    if not related_ids:
        return ''
    by_id = {x['id']: x for x in posted}
    items = []
    for rid in related_ids:
        if rid not in by_id:
            raise ValueError('아직 발행하지 않은 글은 관련 글로 연결할 수 없습니다')
        items.append(f'<li><a href="{html.escape(validate_url(by_id[rid]["url"]), quote=True)}">'
                     f'{html.escape(by_id[rid]["title"])}</a></li>')
    return '<h2>관련 글</h2><ul>' + ''.join(items) + '</ul>'


def validate_catalogue(catalogue, root):
    if not isinstance(catalogue, list):
        raise ValueError('원고 목록이 필요합니다')
    ids, paths = set(), set()
    for article in catalogue:
        path = validate_article(article, root)
        if article['id'] in ids or path in paths:
            raise ValueError('중복된 원고 식별자 또는 경로입니다')
        ids.add(article['id'])
        paths.add(path)


def _inline(text):
    if re.search(r'<\s*(script|iframe|style|svg|object|embed)\b|\]\(\s*(?!https://)', text, re.I):
        raise ValueError('실행 태그와 HTTPS 이외의 링크는 허용하지 않습니다')
    text = html.escape(text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    return re.sub(r'\[([^\]]+)\]\((https://[^\s)]+)\)', r'<a href="\2" rel="noopener">\1</a>', text)


def render_markdown(source, assets=None):
    parts, code, in_code, in_list = [], [], False, False
    lines = source.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if line.startswith('```'):
            if in_list:
                parts.append('</ul>')
                in_list = False
            if in_code:
                parts.append('<pre><code>' + html.escape('\n'.join(code)) + '</code></pre>')
                code = []
            in_code = not in_code
            continue
        if in_code:
            code.append(line)
            continue
        if not line.strip():
            if in_list:
                parts.append('</ul>')
                in_list = False
            continue
        if line.startswith('# '):
            continue
        if line.startswith('- '):
            if not in_list:
                parts.append('<ul>')
                in_list = True
            parts.append('<li>' + _inline(line[2:]) + '</li>')
            continue
        if in_list:
            parts.append('</ul>')
            in_list = False
        image = re.fullmatch(r'!\[([^\]]+)\]\(asset:([a-z][a-z0-9-]*)\)', line)
        if image:
            if image[2] not in (assets or {}):
                raise ValueError('등록되지 않은 이미지입니다')
            alt = html.escape(image[1], quote=True)
            parts.append(f'<figure class="learning-figure"><img src="{assets[image[2]]}" alt="{alt}"><figcaption>{alt}</figcaption></figure>')
            continue
        if '![' in line:
            raise ValueError('등록된 내부 이미지만 사용할 수 있습니다')
        if line.startswith('|') and index < len(lines) and re.fullmatch(r'\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?', lines[index]):
            def cells(row):
                return [cell.strip().replace(r'\|', '|') for cell in re.split(r'(?<!\\)\|', row.strip().strip('|'))]
            headers = cells(line)
            if len(cells(lines[index])) != len(headers):
                raise ValueError('표의 열 개수가 다릅니다')
            index += 1
            parts.append('<div class="learning-table" role="region" aria-label="비교표" tabindex="0"><table><thead><tr>'
                         + ''.join('<th scope="col">' + _inline(cell) + '</th>' for cell in headers) + '</tr></thead><tbody>')
            while index < len(lines) and lines[index].startswith('|'):
                values = cells(lines[index])
                if len(values) != len(headers):
                    raise ValueError('표의 열 개수가 다릅니다')
                parts.append('<tr>' + ''.join('<td>' + _inline(cell) + '</td>' for cell in values) + '</tr>')
                index += 1
            parts.append('</tbody></table></div>')
            continue
        heading = re.match(r'^(#{2,3}) (.+)$', line)
        tag, text = (f'h{len(heading[1])}', heading[2]) if heading else ('p', line)
        parts.append(f'<{tag}>' + _inline(text) + f'</{tag}>')
    if in_code:
        raise ValueError('닫히지 않은 코드블록입니다')
    if in_list:
        parts.append('</ul>')
    return '\n'.join(parts)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as f:
            name = f.name
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def publish_daily(state_dir, catalogue, *, root, publish, verify, now=None, dry_run=False):
    fixed_time = now is not None
    now = now or datetime.now(timezone.utc)
    today = kst_day(now)
    state_dir.mkdir(parents=True, exist_ok=True)
    with (state_dir / 'publish.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'busy'}
        path = state_dir / 'state.json'
        state = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'posted': []}
        if not isinstance(state, dict) or not isinstance(state.get('posted'), list):
            raise ValueError('발행 상태가 손상되었습니다')
        if state.get('pending'):
            return {'status': 'needs_confirmation', 'pending': state['pending']}
        if any(x['date'] == today for x in state['posted']):
            return {'status': 'already_published'}
        posted = {x['id'] for x in state['posted']}
        article = next((a for a in catalogue if a['id'] not in posted), None)
        if article is None:
            return {'status': 'empty'}
        source = validate_article(article, root).read_text(encoding='utf-8')
        assets = read_assets(article, root)
        digest = hashlib.sha256((source + (json.dumps(assets, sort_keys=True) if assets else '')).encode()).hexdigest()
        if digest in {x.get('hash') for x in state['posted']}:
            raise ValueError('이미 발행한 본문입니다')
        marker = f'learning-{article["id"]}-{digest[:12]}'
        illustrated = source
        if 'cover' in assets:
            cover = f'![{article["title"]}](asset:cover)\n\n'
            illustrated = source.replace('\n## ', '\n' + cover + '## ', 1) if '\n## ' in source else cover + source
        meta = f'<p class="learning-meta">읽는 시간 약 {reading_minutes(source)}분</p>'
        head = f'<p class="learning-correction">정정 안내: {html.escape(article["correction"])}</p>' if article.get('correction') else ''
        # 검색 설명(스니펫)이 "읽는 시간"으로 시작하거나 도입 문단 사이에 끼지 않도록 첫 그림·소제목 앞에 둔다.
        rendered = render_markdown(illustrated, assets)
        at = re.search(r'<figure|<h2', rendered)
        rendered = rendered[:at.start()] + meta + rendered[at.start():] if at else rendered + meta
        body = f'<div id="{marker}">\n{head}{rendered}\n</div>'
        body += related_box(article.get('related', []), state['posted'])
        if article.get('project'):
            body += project_box(article['project'])
        revision = article.get('revision')
        if revision:
            if not re.fullmatch(r'[0-9a-f]{40}', revision):
                raise ValueError('공개 코드 버전이 올바르지 않습니다')
            if article.get('kind', 'lab') == 'lab':
                body += (f'<h2>이 글의 코드 버전</h2><p><a href="{REPOSITORY}/blob/{revision}/labs/learning_basics.py">'
                         f'실습 코드 고정 버전</a> · <a href="{REPOSITORY}/blob/{revision}/tests/test_learning_labs.py">'
                         '검증 테스트 고정 버전</a></p>')
            else:
                body += f'<p><a href="{REPOSITORY}/blob/{revision}/{article["markdown"]}">이 글의 원문 고정 버전</a></p>'
        payload = article | {'html': body, 'marker': marker, 'hash': digest}
        if dry_run:
            return {'status': 'ready', 'id': article['id'], 'category': article['category']}
        state['pending'] = {'id': article['id'], 'title': article['title'], 'date': today,
                            'target': BLOG, 'hash': digest, 'marker': marker}
        from automation.tistory_publisher import body_signature
        state['pending']['kind'] = article.get('kind', 'lab')
        state['pending']['expected_body'] = body_signature(body, marker)
        save_json(path, state)
        url = validate_url(publish(payload))
        state['pending']['url'] = url
        save_json(path, state)
        if not verify(url, payload):
            raise RuntimeError('공개 글 검증 실패: 자동 재발행을 보류합니다')
        finished_day = kst_day(now if fixed_time else datetime.now(timezone.utc))
        state['posted'].append(state.pop('pending') | {'url': url, 'date': finished_day})
        save_json(path, state)
        remaining = len([a for a in catalogue if a['id'] not in {x['id'] for x in state['posted']}])
        return {'status': 'published', 'url': url, 'remaining': remaining}


def resolve_pending(state_dir, url=None, *, clear=False, verify=None, now=None):
    with (state_dir / 'publish.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = state_dir / 'state.json'
        state = json.loads(path.read_text(encoding='utf-8'))
        pending = state.get('pending')
        if not pending or pending.get('target') != BLOG:
            raise ValueError('확인 대기 중인 새 블로그 원고가 없습니다')
        if clear:
            if pending.get('url'):
                raise ValueError('공개 주소가 있는 기록은 확인 없이 지울 수 없습니다')
        else:
            validate_url(url)
            if not verify or not verify(url, pending):
                raise RuntimeError('공개 본문을 확인하지 못했습니다')
            state['posted'].append(pending | {'url': url, 'date': kst_day(now or datetime.now(timezone.utc))})
        state.pop('pending')
        save_json(path, state)
        return {'status': 'confirmed' if not clear else 'cleared'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--confirm-url')
    action.add_argument('--clear-pending', action='store_true')
    parser.add_argument('--confirmed-not-published', action='store_true')
    args = parser.parse_args()
    state_dir = Path(os.environ['TECH_BLOG_STATE_DIR'])
    from automation.tistory_publisher import publish, verify
    if args.confirm_url or args.clear_pending:
        if args.clear_pending and not args.confirmed_not_published:
            raise ValueError('관리 화면에서 미발행을 확인한 경우에만 --confirmed-not-published를 지정하세요')
        result = resolve_pending(state_dir, args.confirm_url, clear=args.clear_pending, verify=verify)
        save_json(state_dir / 'status.json', result | {'checked_at': datetime.now(timezone.utc).isoformat()})
        print(json.dumps(result, ensure_ascii=False))
        return
    catalogue = json.loads((ROOT / 'docs/posts/catalogue.json').read_text())
    validate_catalogue(catalogue, ROOT)
    # 배포한 원본과 다른 파일이 조용히 발행되지 않도록 변경·미추적 파일을 확인한다.
    tracked = ['docs/posts', 'labs', 'automation']
    dirty = subprocess.check_output(['git', 'status', '--porcelain', '--', *tracked], cwd=ROOT, text=True)
    if dirty.strip():
        raise RuntimeError('원고·실습·발행 코드의 변경을 먼저 저장소에 반영해야 합니다')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    remote = subprocess.check_output(['git', 'ls-remote', '--exit-code', 'origin', 'refs/heads/main'],
                                     cwd=ROOT, text=True, timeout=30).split()[0]
    if remote != revision:
        raise RuntimeError('현재 원본이 공개 저장소 기본 브랜치에 반영되지 않았습니다')
    catalogue = [a | {'revision': revision} for a in catalogue]
    import inspect
    from labs.learning_basics import LABS, run_lab
    for article in catalogue:
        source = validate_article(article, ROOT).read_text(encoding='utf-8')
        if len(source) < 700 or source.count('\n## ') < 4:
            raise ValueError('실행 방법과 결과·한계를 갖춘 원고가 필요합니다')
        if article.get('kind', 'lab') == 'lab':
            if inspect.getsource(LABS[article['lab']]).rstrip() not in source:
                raise ValueError('실습 코드와 원고의 코드가 다릅니다. 원고를 다시 준비해야 합니다')
            run_lab(article['lab'])
    result = publish_daily(state_dir, catalogue, root=ROOT, publish=publish, verify=verify,
                           dry_run=args.dry_run)
    save_json(state_dir / 'status.json', result | {'checked_at': datetime.now(timezone.utc).isoformat()})
    print(json.dumps(result, ensure_ascii=False))
    if result['status'] == 'needs_confirmation':
        raise SystemExit(2)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        result = {'status': 'error', 'error': type(error).__name__, 'message': str(error)[:400],
                  'checked_at': datetime.now(timezone.utc).isoformat()}
        if os.environ.get('TECH_BLOG_STATE_DIR'):
            save_json(Path(os.environ['TECH_BLOG_STATE_DIR']) / 'status.json', result)
        print(json.dumps(result, ensure_ascii=False))
        raise SystemExit(1)
