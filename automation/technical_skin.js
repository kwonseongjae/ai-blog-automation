(function(){
  var article=document.querySelector('.article-view');
  if(article){
    var headings=article.querySelectorAll('h2');
    if(headings.length>=3&&!article.querySelector('.learning-toc')){
      var toc=document.createElement('details');toc.className='learning-toc';
      var summary=document.createElement('summary');summary.textContent='이 글의 목차';toc.appendChild(summary);
      var list=document.createElement('ol');
      headings.forEach(function(h,i){if(!h.id)h.id='learning-section-'+(i+1);var li=document.createElement('li'),a=document.createElement('a');a.href='#'+h.id;a.textContent=h.textContent;li.appendChild(a);list.appendChild(li);});
      toc.appendChild(list);article.insertBefore(toc,article.firstChild);
    }
    article.querySelectorAll('pre').forEach(function(pre){
      if(pre.parentElement.classList.contains('learning-code'))return;
      var wrap=document.createElement('div');wrap.className='learning-code';pre.parentNode.insertBefore(wrap,pre);wrap.appendChild(pre);
      var button=document.createElement('button');button.type='button';button.className='learning-copy';button.textContent='코드 복사';button.setAttribute('aria-live','polite');wrap.appendChild(button);
      button.addEventListener('click',async function(){try{if(!navigator.clipboard)throw new Error('clipboard unavailable');await navigator.clipboard.writeText(pre.textContent);button.textContent='복사됨';}catch(e){var range=document.createRange();range.selectNodeContents(pre);var selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);button.textContent='선택됨 · 직접 복사';}setTimeout(function(){button.textContent='코드 복사';},2200);});
    });
  }
  document.querySelectorAll('.header .searchInput').forEach(function(input){
    input.placeholder='글 검색';input.setAttribute('aria-label','블로그 글 검색');
    if(input.parentElement.querySelector('.learning-search-button'))return;
    var button=document.createElement('button');button.type='button';button.className='learning-search-button';button.textContent='검색';input.parentElement.appendChild(button);
    function search(){var query=input.value.trim();if(query)location.href='/search/'+encodeURIComponent(query);}
    input.removeAttribute('onkeypress');
    input.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();search();}});
    button.addEventListener('click',search);
  });
  if(document.body.id==='tt-body-index'){
    var title=document.querySelector('.title-search .archives');
    if(title)title.textContent='최근 기록';
    var popular=document.querySelectorAll('.box-recent .list-tab a.link-recent'),posts=document.querySelectorAll('.article-type-common');
    if(title&&popular.length&&posts.length>1&&!document.querySelector('.learning-tabs')){
      var byLink={};posts.forEach(function(post){var a=post.querySelector('a[href]');if(a)byLink[a.getAttribute('href')]=post;});
      var first=posts[0],clones=0;
      popular.forEach(function(a){var post=byLink[a.getAttribute('href')];if(!post)return;var copy=post.cloneNode(true);copy.classList.add('learning-clone');first.parentNode.insertBefore(copy,first);clones++;});
      if(clones){
        var tabs=document.createElement('span');tabs.className='learning-tabs';tabs.setAttribute('role','tablist');
        var buttons=[['최근 기록',false],['인기 글',true]].map(function(item){
          var b=document.createElement('button');b.type='button';b.setAttribute('role','tab');b.textContent=item[0];b.setAttribute('aria-selected',item[1]?'false':'true');
          b.addEventListener('click',function(){document.documentElement.classList.toggle('learning-popular-on',item[1]);buttons.forEach(function(o,i){o.setAttribute('aria-selected',(i===1)===item[1]?'true':'false');});});
          tabs.appendChild(b);return b;});
        title.textContent='';title.appendChild(tabs);
      }
    }
  }
  document.querySelectorAll('.img-thumbnail').forEach(function(img){
    var box=img.closest&&img.closest('.thumbnail');
    var hide=function(){img.hidden=true;};
    var ok=function(){if(box)box.classList.add('learning-loaded');};
    if(img.complete){if(img.naturalWidth===0)hide();else ok();}
    else{img.addEventListener('load',function(){if(img.naturalWidth>0)ok();else hide();});img.addEventListener('error',hide);}
  });
  document.querySelectorAll('.learning-cover strong').forEach(function(cover){
    var title=cover.textContent;
    if(title.includes('한국 시간'))cover.textContent='한국 시간\n날짜 기준';
    else if(title.includes('파일')&&title.includes('실행'))cover.textContent='파일 경로\n실행 위치';
    else if(title.includes('AI 에이전트란'))cover.textContent='AI 에이전트\n어디까지 맡길까';
    else if(title.includes('Codex 설치 방법'))cover.textContent='Codex\n처음 쓰는 설정';
    else if(title.includes('Claude Code 설치 방법'))cover.textContent='Claude Code\n처음 쓰는 설정';
  });
  // 큰 글씨 표지로 바꾸기 전에 올린 글(1~5번)은 목록에서 HTML 카드로 보여 준다.
  document.querySelectorAll('.article-type-common').forEach(function(post){
    var a=post.querySelector('a[href]'),box=post.querySelector('.thumbnail');
    if(a&&box&&/^\/[1-5]$/.test(a.getAttribute('href')))box.classList.add('learning-legacy-cover');
  });
  var emptyCategories=new Set();
  document.querySelectorAll('.tt_category .link_item').forEach(function(a){
    var count=a.querySelector('.c_cnt');
    // 집계가 없거나 형식이 달라지면 항목을 유지한다.
    if(count&&/^\s*\(\s*0\s*\)\s*$/.test(count.textContent)){
      emptyCategories.add(new URL(a.href,location.href).pathname);
      a.closest('li').hidden=true;
    }
  });
  document.querySelectorAll('.learning-menu a').forEach(function(a){
    if(emptyCategories.has(new URL(a.href,location.href).pathname))a.closest('li').hidden=true;
  });
  document.querySelectorAll('.learning-topics em[data-count-for]').forEach(function(em){
    var name=decodeURIComponent(em.getAttribute('data-count-for'));
    document.querySelectorAll('.tt_category .link_item').forEach(function(a){
      try{if(decodeURIComponent(new URL(a.href,location.href).pathname)!=='/category/'+name)return;}catch(e){return;}
      var m=a.querySelector('.c_cnt'),n=m&&/\(\s*([\d,]+)\s*\)/.exec(m.textContent);
      if(n)em.textContent=n[1]+'편';
    });
  });
  document.querySelectorAll('.learning-navigation a,.tt_category a').forEach(function(a){
    try{if(decodeURIComponent(new URL(a.href,location.href).pathname)===decodeURIComponent(location.pathname))a.setAttribute('aria-current','page');}catch(e){}
  });
})();
