const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('automation/technical_skin.js', 'utf8');
for (const bodyId of ['tt-body-index', 'tt-body-category']) {
  const title = {textContent: '전체 글'};
  const counts = ['(0)', '(2)', null, '알 수 없음', '( 0 )', '(1,000)'];
  const rows = counts.map((count, i) => ({
    hidden: false,
    href: 'https://jacks-aiblog.tistory.com/category/topic' + i,
    querySelector: () => count === null ? null : {textContent: count},
    closest() { return this; },
    setAttribute() {},
  }));
  const menu = rows.map(row => ({
    hidden: false, href: row.href,
    closest() { return this; },
    setAttribute() {},
  }));
  const document = {
    body: {id: bodyId},
    querySelector: selector => selector === '.title-search .archives' ? title : null,
    querySelectorAll: selector => {
      if (selector === '.tt_category .link_item') return rows;
      if (selector === '.learning-menu a') return menu;
      return [];
    },
  };
  const context = vm.createContext({document, URL, Set, location: {
    href: 'https://jacks-aiblog.tistory.com/', pathname: '/',
  }});
  vm.runInContext(source, context);
  vm.runInContext(source, context);
  assert.deepEqual(rows.map(row => row.hidden), [true, false, false, false, true, false]);
  assert.deepEqual(menu.map(row => row.hidden), [true, false, false, false, true, false]);
  assert.equal(title.textContent, bodyId === 'tt-body-index' ? '최근 기록' : '전체 글');
}
console.log('카테고리 집계·미확인 값·메뉴 동기화·재실행·목록 제목 확인 통과');
