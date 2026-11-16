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

// 인기 글 탭: 인기 순서대로 복제본을 만들고, 탭을 누르면 표시 상태 클래스가 바뀐다.
{
  const inserted = [];
  const parent = {insertBefore: (node, ref) => inserted.push([node, ref])};
  const makePost = href => {
    const post = {parentNode: parent, classList: {added: [], add(n) { this.added.push(n); }},
      querySelector: () => ({getAttribute: () => href, classList: {add() {}}}),
      cloneNode() { return {...post, classList: {added: [], add(n) { this.added.push(n); }}, href}; }};
    return post;
  };
  const posts = ['/1', '/2', '/3'].map(makePost);
  const title = {textContent: '전체 글', children: [], appendChild(node) { this.children.push(node); }};
  const state = new Set();
  const make = () => ({children: [], attrs: {}, listeners: {}, appendChild(c) { this.children.push(c); },
    setAttribute(k, v) { this.attrs[k] = v; }, addEventListener(n, f) { this.listeners[n] = f; }});
  const document = {
    body: {id: 'tt-body-index'},
    documentElement: {classList: {toggle: (n, on) => on ? state.add(n) : state.delete(n)}},
    createElement: make,
    querySelector: s => s === '.title-search .archives' ? title : null,
    querySelectorAll: s => s === '.box-recent .list-tab a.link-recent'
      ? ['/3', '/9', '/1'].map(h => ({getAttribute: () => h}))
      : s === '.article-type-common' ? posts : [],
  };
  vm.runInContext(source, vm.createContext({document, URL, Set, location: {href: 'https://jacks-aiblog.tistory.com/', pathname: '/'}}));
  assert.deepEqual(inserted.map(([node]) => node.href), ['/3', '/1'], '목록에 없는 글은 건너뛰고 인기 순서를 따른다');
  assert.ok(inserted.every(([node, ref]) => node.classList.added.includes('learning-clone') && ref === posts[0]));
  const [recent, popular] = title.children[0].children;
  assert.equal(recent.attrs['aria-selected'], 'true');
  popular.listeners.click();
  assert.ok(state.has('learning-popular-on'));
  assert.equal(popular.attrs['aria-selected'], 'true');
  recent.listeners.click();
  assert.ok(!state.has('learning-popular-on'));
  console.log('인기 글 탭: 순서·복제·전환 확인 통과');
}
