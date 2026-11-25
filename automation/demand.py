"""원고의 목표 검색어와 수요 근거를 확인한다.

등급: A 관측(서치콘솔에 실제 노출) · B+ 추이(데이터랩·트렌드) · B 단서(자동완성) · C 가설(근거 없음).
자동완성은 "이 말로 검색한 사람이 있다"까지만 알려 주므로 B까지만 자동으로 매기고, A·B+는 사람이 근거와 함께 적는다.
"""
import math
import re
import sys
import time
from datetime import date

GRADES = ('A', 'B+', 'B', 'C')
EDITORIAL_RULE_FROM = '2026-11-25'
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36'}


def _norm(text):
    return re.sub(r'\s+', '', text).lower()


def editorial_issues(article, source):
    """새 안내 글과 교정 대상으로 지정한 원고에 검색 표현을 확인한다."""
    if 'search_anchor' not in article and article.get('checked_on', '') < EDITORIAL_RULE_FROM:
        return []
    issues = []
    title = article['title']
    anchor = article.get('search_anchor')
    if not isinstance(anchor, str) or not anchor.strip() or anchor.lower() not in title[:20].lower():
        issues.append('제목 첫 20자 안에 정확한 검색 표현(search_anchor)을 넣어야 합니다')
    paragraphs = source.strip().split('\n\n')
    opening = next((part for part in paragraphs if not part.startswith('#')), '')
    first_section = re.split(r'^## ', source, maxsplit=1, flags=re.M)[0]
    if re.search(r'^\s*(?:확인일|확인 범위|공식 출처)\s*[:：]', first_section, re.M):
        issues.append('확인일·확인 범위·공식 출처는 본문 검증 절이나 하단에 둬야 합니다')
    intro = f'{title} {opening}'.lower()
    for name, korean in (('codex', '코덱스'), ('claude code', '클로드 코드')):
        if re.search(rf'\b{re.escape(name)}\b', intro, re.ASCII) and korean not in intro:
            issues.append(f'제목 또는 첫 문단에 {name}와(과) {korean}를 함께 써야 합니다')
    return issues


def suggestions(query, client=None):
    """구글·네이버 자동완성을 가져온다. 한쪽이 실패해도 다른 쪽 결과는 남긴다."""
    import httpx
    client = client or httpx
    found = {'google': [], 'naver': []}
    try:
        r = client.get('https://suggestqueries.google.com/complete/search',
                       params={'client': 'firefox', 'q': query, 'hl': 'ko'}, headers=UA, timeout=15)
        found['google'] = [s for s in r.json()[1] if isinstance(s, str)]
    except Exception:
        pass
    try:
        r = client.get('https://ac.search.naver.com/nx/ac',
                       params={'q': query, 'con': 0, 'frm': 'nv', 'ans': 2, 'r_format': 'json', 'r_enc': 'UTF-8',
                               'r_unicode': 0, 't_koreng': 1, 'run': 2, 'rev': 4, 'q_enc': 'UTF-8', 'st': 100},
                       headers=UA, timeout=15)
        found['naver'] = [item[0] for item in r.json()['items'][0] if isinstance(item[0], str)]
    except Exception:
        pass
    return found


def find_basis(query, found, today=None):
    """검색어와 같은 표현이 자동완성에 있으면 근거 문장을, 없으면 None을 돌려준다."""
    today = today or date.today().isoformat()
    want = _norm(query)
    for source, label in (('google', '구글'), ('naver', '네이버')):
        for suggestion in found.get(source, []):
            if _norm(suggestion).startswith(want):
                return f"{label} 자동완성 {today}: '{suggestion}'"
    return None


def demand_issues(article, source):
    """목표 검색어가 제목과 첫 문단에 있고 수요 근거가 검색어를 그대로 인용하는지 확인한다."""
    query = article.get('target_query')
    demand = article.get('demand')
    if not isinstance(query, str) or not query.strip() or not isinstance(demand, dict):
        return ['목표 검색어(target_query)와 수요 근거(demand)가 필요합니다']
    issues = []
    tokens = query.lower().split()
    title = article['title'].lower()
    missing = [t for t in tokens if t not in title]
    if missing:
        issues.append('제목에 목표 검색어가 없습니다: ' + ' '.join(missing))
    lead = next((line for line in source.splitlines()
                 if line.strip() and not line.startswith(('#', '```', '|', '!', '>', '-'))), '').lower()
    if sum(t in lead for t in tokens) < math.ceil(len(tokens) / 2):
        issues.append('첫 문단에 목표 검색어가 충분히 들어 있지 않습니다')
    if demand.get('grade') not in GRADES:
        issues.append('수요 등급은 A, B+, B, C 중 하나여야 합니다')
    if not isinstance(demand.get('basis'), str) or not demand['basis'].strip():
        issues.append('수요 근거(basis)가 비어 있습니다')
    elif demand.get('grade') in ('A', 'B+', 'B') and _norm(query) not in _norm(demand['basis']):
        issues.append('수요 근거에 목표 검색어가 그대로 인용되어 있지 않습니다')
    try:
        date.fromisoformat(demand.get('checked_on', ''))
    except ValueError:
        issues.append('수요 확인일(checked_on)이 올바르지 않습니다')
    return issues


def main(queries):
    for query in queries:
        found = suggestions(query)
        basis = find_basis(query, found)
        print(f"{'B' if basis else 'C'} | {query} | {basis or '자동완성에 같은 표현 없음'}")
        if not basis:
            print('   참고:', ' / '.join((found['google'] + found['naver'])[:5]) or '(결과 없음)')
        time.sleep(0.5)


if __name__ == '__main__':
    main(sys.argv[1:])
