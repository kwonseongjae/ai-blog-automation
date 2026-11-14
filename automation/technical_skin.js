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
  document.querySelectorAll('.learning-navigation a,.tt_category a,.learning-topics a').forEach(function(a){
    try{if(decodeURIComponent(new URL(a.href,location.href).pathname)===decodeURIComponent(location.pathname))a.setAttribute('aria-current','page');}catch(e){}
  });
})();
