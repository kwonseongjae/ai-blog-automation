"""Jack의 AI 개발노트의 일일 리포트와 광고·색인 검증 리포트를 텔레그램으로 보낸다."""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

from automation.learning_blog import BLOG, ROOT, kst_day

SITE = f'https://{BLOG}'
TITLE = 'Jack의 AI 개발노트'
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36',
      'Accept-Language': 'ko-KR,ko;q=0.9'}


def _legacy_root():
    return Path(os.environ.get('BLOG_AUTOMATION_ROOT') or Path.home() / 'blog-automation')


def telegram_settings():
    """환경 변수를 먼저 보고 없으면 기존 운영 폴더의 .env에서 두 값만 읽는다. 값은 출력하지 않는다."""
    keys = ('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID')
    found = {k: os.environ.get(k) for k in keys}
    env_file = _legacy_root() / '.env'
    if not all(found.values()) and env_file.is_file():
        for line in env_file.read_text(encoding='utf-8').splitlines():
            key, _, value = line.partition('=')
            if key.strip() in keys and not found[key.strip()]:
                found[key.strip()] = value.strip().strip('"\'')
    if not all(found.values()):
        raise ValueError('TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID not set')
    return found['TELEGRAM_BOT_TOKEN'], found['TELEGRAM_CHAT_ID']


def send(text):
    token, chat = telegram_settings()
    try:
        r = httpx.post(f'https://api.telegram.org/bot{token}/sendMessage', json={'chat_id': chat, 'text': text}, timeout=15)
    except httpx.HTTPError as error:  # 요청 주소에 토큰이 있으므로 예외 본문은 남기지 않는다.
        raise RuntimeError(f'텔레그램 전송 실패: {type(error).__name__}') from None
    if r.status_code != 200:
        raise RuntimeError(f'텔레그램 전송 실패: HTTP {r.status_code}')


def daily_text(posted, catalogue_count, today, timer_next, last_result):
    """발행 상태만 담는다. 방문자·수익은 이 블로그에서 아직 수집하지 않는다."""
    today_posts = [p for p in posted if p.get('date') == today]
    last = posted[-1] if posted else None
    lines = [f'📊 [{TITLE}] 일일 리포트 {today}', '',
             f'✅ 오늘 발행: {len(today_posts)}건' + ''.join(f'\n   └ {p["title"]}' for p in today_posts),
             f'📚 누적 발행 {len(posted)}편 / 준비된 원고 {catalogue_count}편 (남은 원고 {catalogue_count - len(posted)}편)']
    if last:
        lines.append(f'📝 마지막 글: {last["title"]}\n   {last["url"]}')
    lines += [f'⏰ 다음 발행 예정: {timer_next}', f'⚙️ 마지막 발행 서비스 결과: {last_result}',
              '👁️ 방문자·수익: 이 블로그는 아직 수집하지 않음']
    return '\n'.join(lines)


def check_ads(html):
    return {'adsense': 'adsbygoogle' in html or 'googlesyndication' in html,
            'adfit': 'ba.min.js' in html or 't1.daumcdn.net/kas' in html}


def verify_text(results, today):
    lines = [f'📊 [{TITLE}] 광고·색인 검증 {today}', '']
    for r in results:
        g = {True: '✅', False: '❌미색인', None: '❔조회 불가(Search Console 권한 확인)'}[r['google']]
        lines += [f'{"✅" if r["status"] == 200 and r["google"] is not False else "⚠️"} {r["url"]}',
                  f'   접속 {r["status"]} | 광고 코드: AdSense {"있음" if r["ads"]["adsense"] else "없음"}'
                  f' · AdFit {"있음" if r["ads"]["adfit"] else "없음"} | Google {g}', '']
    if not results:
        lines.append('검증할 글을 RSS에서 찾지 못했습니다.')
    lines.append('광고 코드가 없다는 것은 이 블로그에 광고를 아직 붙이지 않았다는 뜻일 수 있어 오류로 세지 않습니다.')
    return '\n'.join(lines)


def recent_urls(count=5):
    rss = httpx.get(f'{SITE}/rss', headers=UA, timeout=15, follow_redirects=True).text
    return list(dict.fromkeys(re.findall(r'<link>(' + re.escape(SITE) + r'/\d+)</link>', rss)))[:count]


def google_indexed(url):
    """기존 운영 폴더의 서비스 계정 토큰으로 Search Console 저장 색인 상태를 읽는다. 권한이 없으면 None."""
    try:
        sys.path.insert(0, str(_legacy_root()))
        import config  # noqa: F401  기존 운영 폴더의 .env를 읽어 서비스 계정 설정을 불러온다.
        from services.search_ping import _get_access_token
        token = _get_access_token()
        if not token:
            return None
        r = httpx.post('https://searchconsole.googleapis.com/v1/urlInspection/index:inspect',
                       headers={'Authorization': f'Bearer {token}'}, timeout=20,
                       json={'inspectionUrl': url, 'siteUrl': SITE + '/', 'languageCode': 'ko-KR'})
        verdict = r.json().get('inspectionResult', {}).get('indexStatusResult', {}).get('verdict') if r.status_code == 200 else None
        return {'PASS': True, 'FAIL': False, 'NEUTRAL': False}.get(verdict)
    except Exception:
        return None


def verify_recent(count=5):
    results = []
    for url in recent_urls(count):
        page = httpx.get(url, headers=UA, timeout=15, follow_redirects=True)
        results.append({'url': url, 'status': page.status_code, 'ads': check_ads(page.text), 'google': google_indexed(url)})
    return results


def systemd_value(unit, prop):
    out = subprocess.run(['systemctl', '--user', 'show', unit, '-p', prop, '--value'], capture_output=True, text=True)
    return out.stdout.strip() or '확인 불가'


def timer_next():
    return systemd_value('technical-blog.timer', 'NextElapseUSecRealtime')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('kind', choices=('daily', 'verify'))
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    today = kst_day(datetime.now(ZoneInfo('Asia/Seoul')))
    if args.kind == 'daily':
        state_dir = Path(os.environ.get('TECH_BLOG_STATE_DIR') or _legacy_root() / 'data/technical_blog')
        posted = json.loads((state_dir / 'state.json').read_text(encoding='utf-8'))['posted']
        catalogue = json.loads((ROOT / 'docs/posts/catalogue.json').read_text(encoding='utf-8'))
        text = daily_text(posted, len(catalogue), today, timer_next(), systemd_value('technical-blog.service', 'Result'))
    else:
        text = verify_text(verify_recent(), today)
    print(text) if args.dry_run else send(text)


if __name__ == '__main__':
    main()
