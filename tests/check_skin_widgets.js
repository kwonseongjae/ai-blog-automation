const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('automation/technical_skin.js', 'utf8');
for (const bodyId of ['tt-body-index', 'tt-body-category']) {
  const title = {textContent: '전체 글'};
  const covers = ['Python 자동화의 하루 기준을 한국 시간으로 정하는 방법',
    '터미널에서는 되는데 예약 실행에서는 파일을 못 찾는 이유', '새 학습 기록'].map(textContent => ({textContent}));
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
  const makeThumb = (complete, naturalWidth) => {
    const box = {loaded: false, classList: {add(name) { if (name === 'learning-loaded') box.loaded = true; }}};
    return {complete, naturalWidth, hidden: false, listeners: {}, box, closest: () => box,
      addEventListener(name, fn) { this.listeners[name] = fn; }};
  };
  const thumbs = [makeThumb(true, 0), makeThumb(true, 640), makeThumb(false, 0)];
  const document = {
    body: {id: bodyId},
    querySelector: selector => selector === '.title-search .archives' ? title : null,
    querySelectorAll: selector => {
      if (selector === '.tt_category .link_item') return rows;
      if (selector === '.learning-menu a') return menu;
      if (selector === '.learning-cover strong') return covers;
      if (selector === '.img-thumbnail') return thumbs;
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
  assert.deepEqual(thumbs.map(t => t.hidden), [true, false, false]);
  assert.deepEqual(thumbs.map(t => t.box.loaded), [false, true, false]);
  thumbs[2].naturalWidth = 640;
  thumbs[2].listeners.load();
  assert.equal(thumbs[2].box.loaded, true);
  thumbs[2].naturalWidth = 0;
  thumbs[2].listeners.error();
  assert.equal(thumbs[2].hidden, true);
  assert.equal(thumbs[1].hidden, false);
  assert.equal(title.textContent, bodyId === 'tt-body-index' ? '최근 기록' : '전체 글');
  assert.deepEqual(covers.map(cover => cover.textContent), ['한국 시간\n날짜 기준', '파일 경로\n실행 위치', '새 학습 기록']);
}
console.log('카테고리 집계·미확인 값·메뉴 동기화·재실행·목록 제목 확인 통과');

// 추가 기능 스크립트는 필요한 DOM 기능이 없으면 아무것도 하지 않아야 한다.
{
  const extras = fs.readFileSync('automation/technical_skin_extras.js', 'utf8');
  assert.doesNotThrow(() => vm.runInContext(extras, vm.createContext({document: {querySelector: () => null}})));
  console.log('추가 기능 스크립트: DOM이 없을 때 무동작 확인');
}
