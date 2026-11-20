(function(){
  if(!document.createElement||!document.documentElement||!document.addEventListener)return;
  var root=document.documentElement,KEY='learning-theme';
  function read(){try{return localStorage.getItem(KEY);}catch(e){return null;}}
  function write(v){try{localStorage.setItem(KEY,v);}catch(e){}}
  var saved=read();
  var dark=saved?saved==='dark':!!(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches);
  var toggles=[];
  function apply(){
    root.setAttribute('data-learning-theme',dark?'dark':'light');
    toggles.forEach(function(b){b.textContent=b.getAttribute('data-short')?(dark?'라이트':'다크'):(dark?'라이트 모드':'다크 모드');b.setAttribute('aria-pressed',dark?'true':'false');});
  }
  function makeToggle(short){
    var b=document.createElement('button');b.type='button';b.className='learning-theme-toggle';b.setAttribute('aria-label','화면 색상 전환');
    if(short)b.setAttribute('data-short','1');
    b.addEventListener('click',function(){dark=!dark;write(dark?'dark':'light');apply();});
    toggles.push(b);return b;
  }
  var nav=document.querySelector('.learning-navigation');
  if(nav&&!nav.querySelector('.learning-theme-toggle'))nav.appendChild(makeToggle(false));
  var article=document.querySelector('.article-view');
  if(article&&!document.querySelector('.learning-progress')){
    var bar=document.createElement('div');bar.className='learning-progress';bar.setAttribute('aria-hidden','true');document.body.appendChild(bar);
    var update=function(){var h=document.documentElement.scrollHeight-window.innerHeight;bar.style.width=(h>0?Math.min(100,Math.max(0,window.scrollY/h*100)):0)+'%';};
    window.addEventListener('scroll',update,{passive:true});update();
  }
  if(!document.querySelector('.learning-floating')){
    var box=document.createElement('div');box.className='learning-floating';
    var top=document.createElement('button');top.type='button';top.textContent='위로';top.setAttribute('aria-label','맨 위로');top.hidden=true;
    top.addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'});});
    var toc=article&&document.querySelector('.learning-toc');
    if(toc){
      var tb=document.createElement('button');tb.type='button';tb.textContent='목차';tb.setAttribute('aria-label','목차 열기');
      tb.addEventListener('click',function(){toc.open=true;toc.scrollIntoView({behavior:'smooth',block:'start'});});box.appendChild(tb);
    }
    if(article){
      var cp=document.createElement('button');cp.type='button';cp.textContent='링크';cp.setAttribute('aria-label','글 주소 복사');
      cp.addEventListener('click',async function(){
        try{if(!navigator.clipboard)throw new Error('clipboard unavailable');await navigator.clipboard.writeText(location.href.split('#')[0]);cp.textContent='복사됨';}
        catch(e){cp.textContent='실패';}
        setTimeout(function(){cp.textContent='링크';},1600);
      });box.appendChild(cp);
    }
    box.appendChild(makeToggle(true));box.appendChild(top);document.body.appendChild(box);
    window.addEventListener('scroll',function(){top.hidden=window.scrollY<400;},{passive:true});
  }
  document.addEventListener('click',function(e){
    var a=e.target&&e.target.closest&&e.target.closest('.layer_tool a.link_list');
    if(!a||a.textContent.trim()!=='로그인')return;
    e.preventDefault();e.stopImmediatePropagation();
    var base=(window.appInfo&&window.appInfo.loginUrl)||'https://www.tistory.com/auth/login';
    location.href=base+'/?redirectUrl='+encodeURIComponent(location.href.split('#')[0]);
  },true);
  // GA4: 직접 설치(gtag). 자동 브라우저와 ?ga_internal=1로 표시한 내 기기는 GA4를 아예 불러오지 않아 통계에서 빠진다(?ga_internal=0으로 해제).
  (function(){
    var GA='G-KYEEZVW0X2',internal=false;
    try{
      if(/[?&]ga_internal=1(&|$)/.test(location.search))localStorage.setItem('ga_internal','1');
      if(/[?&]ga_internal=0(&|$)/.test(location.search))localStorage.removeItem('ga_internal');
      internal=localStorage.getItem('ga_internal')==='1';
    }catch(e){}
    if(navigator.webdriver||/HeadlessChrome/.test(navigator.userAgent))internal=true;
    if(internal)return;
    window.dataLayer=window.dataLayer||[];
    function gtag(){dataLayer.push(arguments);}
    gtag('js',new Date());
    gtag('config',GA);
    var s=document.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id='+GA;document.head.appendChild(s);
    var art=document.getElementById('article-view'),seen={};
    if(art)window.addEventListener('scroll',function(){
      var r=art.getBoundingClientRect(),read=(innerHeight-r.top)/Math.max(r.height,1)*100;
      [25,50,75,100].forEach(function(p){if(read>=p&&!seen[p]){seen[p]=1;gtag('event','scroll_depth',{percent:p});}});
    },{passive:true});
    document.addEventListener('click',function(e){
      var a=e.target&&e.target.closest&&e.target.closest('a[href]');
      if(!a||a.hostname!==location.hostname||a.closest('.layer_tool'))return;
      gtag('event','internal_link_click',{link_url:a.pathname,link_text:a.textContent.trim().slice(0,60),area:art&&art.contains(a)?'article':'other'});
    },true);
    document.addEventListener('copy',function(){
      var n=getSelection&&getSelection().anchorNode,el=n&&(n.nodeType===1?n:n.parentElement);
      if(el&&el.closest&&el.closest('pre'))gtag('event','code_copy',{page_path:location.pathname});
    });
  })();
  apply();
})();
