"""검증된 학습 원고를 한국 날짜 기준 하루 한 편 배포한다."""
import argparse
import fcntl
import hashlib
import html
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

BLOG = 'jacks-aiblog.tistory.com'
REPOSITORY = 'https://github.com/kwonseongjae/ai-blog-automation'
CATEGORIES = ('Python·자동화', 'API·백엔드', 'AI·데이터', '오류 해결', '학습 회고')
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


def validate_article(article, root):
    for key in ('id', 'title', 'category', 'markdown', 'lab', 'sources'):
        if not article.get(key):
            raise ValueError(f'원고 필수 항목 누락: {key}')
    if not re.fullmatch(r'[a-z][a-z0-9-]{1,70}', article['id']):
        raise ValueError('원고 식별자가 올바르지 않습니다')
    if article['category'] not in CATEGORIES:
        raise ValueError('허용되지 않은 카테고리입니다')
    path = (root / article['markdown']).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('저장소 내부 원고가 필요합니다')
    if not isinstance(article['sources'], list):
        raise ValueError('공식 출처 목록이 필요합니다')
    for source in article['sources']:
        p = urlsplit(source)
        if p.scheme != 'https' or p.netloc not in {'docs.python.org', 'www.sqlite.org'}:
            raise ValueError('허용된 공식 문서 주소가 아닙니다')
    return path


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
    return re.sub(r'\[([^\]]+)\]\((https://[^\s)]+)\)', r'<a href="\2" rel="noopener">\1</a>', text)


def render_markdown(source):
    parts, code, in_code, in_list = [], [], False, False
    for line in source.splitlines():
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
        digest = hashlib.sha256(source.encode()).hexdigest()
        if digest in {x.get('hash') for x in state['posted']}:
            raise ValueError('이미 발행한 본문입니다')
        marker = f'learning-{article["id"]}-{digest[:12]}'
        body = f'<div id="{marker}">\n{render_markdown(source)}\n</div>'
        revision = article.get('revision')
        if revision:
            if not re.fullmatch(r'[0-9a-f]{40}', revision):
                raise ValueError('공개 코드 버전이 올바르지 않습니다')
            body += (f'<h2>이 글의 코드 버전</h2><p><a href="{REPOSITORY}/blob/{revision}/labs/learning_basics.py">'
                     f'실습 코드 고정 버전</a> · <a href="{REPOSITORY}/blob/{revision}/tests/test_learning_labs.py">'
                     '검증 테스트 고정 버전</a></p>')
        payload = article | {'html': body, 'marker': marker, 'hash': digest}
        if dry_run:
            return {'status': 'ready', 'id': article['id'], 'category': article['category']}
        state['pending'] = {'id': article['id'], 'title': article['title'], 'date': today,
                            'target': BLOG, 'hash': digest, 'marker': marker}
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
        if inspect.getsource(LABS[article['lab']]).rstrip() not in source:
            raise ValueError('실습 코드와 원고의 코드가 다릅니다. 원고를 다시 준비해야 합니다')
        if len(source) < 700 or source.count('\n## ') < 4:
            raise ValueError('실행 방법과 결과·한계를 갖춘 원고가 필요합니다')
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
