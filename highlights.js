/* Only show direct video links from the official NFL catalog, matched to a game. */
(function(){
  let catalogPromise;
  const base = new URL('.', document.currentScript.src);
  const catalog = () => catalogPromise || (catalogPromise = fetch(new URL('data/highlights.json',base)).then(r => {if(!r.ok)throw Error('Catalog unavailable');return r.json();}).catch(() => {catalogPromise=null;return {games:{}};}));
  const gameDate = value => !value ? '' : String(value).includes('T') ? new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(value)) : String(value).slice(0,10);
  const key = (team,game) => [Number(game.season||game.year),[team,slug(game.opponentSlug||game.opponent)].sort().join('-'),gameDate(game.date)].join('|');
  const slug = name => {const s=String(name||'').toLowerCase().replace(/[^a-z0-9]/g,'');if(/redskins|washington|commanders/.test(s))return 'commanders';return ['49ers','bears','bengals','bills','broncos','browns','buccaneers','cardinals','chargers','chiefs','colts','cowboys','dolphins','eagles','falcons','giants','jaguars','jets','lions','packers','panthers','patriots','raiders','rams','ravens','saints','seahawks','steelers','texans','titans','vikings'].find(x=>s.endsWith(x))||s;};
  function round(value){return String(value||'').toLowerCase().replace(/[^a-z0-9]/g,'').replace('wildcardround','wildcard').replace('divisionalround','division').replace('divisional','division').replace(/afcchampionship|nfcchampionship/,'conferencechampionship').replace(/superbowl.*/,'superbowl');}
  function install(win,team,data){
    const doc=win.document;if(doc.__NFL_HIGHLIGHTS__)return;doc.__NFL_HIGHLIGHTS__=true;
    let scheduled=false,revision=0;
    async function update(){
      scheduled=false;
      const modal=doc.querySelector('#matchModal.open');if(!modal)return;
      let game;
      try {game=win.eval("window.__NFL_SELECTED_GAME__ || (typeof ALL_GAMES!=='undefined' && typeof state!=='undefined' ? ALL_GAMES[state.selectedMatchIndex] : null)");}catch(_){}
      if(!game)return;
      const season=Number(game.season||game.year), gameKey=key(team,game);
      const host=modal.querySelector('#modalBody,.modal-body')||modal;
      let panel=host.querySelector('.nfl-highlights');
      if(panel?.dataset.game===gameKey)return;
      if(!panel){panel=doc.createElement('div');panel.className='nfl-highlights';host.insertBefore(panel,host.querySelector('.detail-grid')||host.firstChild);}
      panel.dataset.game=gameKey;panel.textContent='';
      if(season<2015){panel.textContent='Official video catalog covers the 2015 season onward.';return;}
      if(['TBD','PRE'].includes(String(game.result||'').toUpperCase())||new Date(game.date)>new Date()){panel.textContent='Highlights will be available after the game.';return;}
      const request=++revision;
      panel.textContent='Checking official NFL highlights…';
      const db=await catalog();if(request!==revision||!panel.isConnected||panel.dataset.game!==gameKey)return;
      panel.textContent='';
      const item=db.games[gameKey];
      if(item && /^[\w-]{11}$/.test(item.videoId)){
        const a=doc.createElement('a');a.href='https://www.youtube.com/watch?v='+item.videoId;a.target='_blank';a.rel='noopener noreferrer';a.textContent='Watch NFL highlights';panel.append(a);
        const note=doc.createElement('small');note.textContent=item.title;panel.append(note);
      }else{
        const note=doc.createElement('small');note.textContent='No verified NFL video is linked for this game yet.';panel.append(note);
        const a=doc.createElement('a');a.href='https://www.youtube.com/@NFL/search?query='+encodeURIComponent(`${season} ${team} ${game.opponent} ${game.round} highlights`);a.target='_blank';a.rel='noopener noreferrer';a.textContent='Search NFL channel';panel.append(a);
      }
    }
    new win.MutationObserver(()=>{if(!scheduled){scheduled=true;win.requestAnimationFrame(update);}}).observe(doc.body,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
    update();
  }
  async function mount(host,team,game){
    const doc=host.ownerDocument,panel=doc.createElement('div');panel.className='nfl-highlights';host.append(panel);
    if(game.status!=='final'){panel.textContent='Highlights will be available after the game.';return;}
    panel.textContent='Checking official NFL highlights…';
    const db=await catalog();if(!panel.isConnected)return;
    const item=db.games[key(team,game)];panel.textContent='';
    const a=doc.createElement('a');a.target='_blank';a.rel='noopener noreferrer';
    a.href=item?'https://www.youtube.com/watch?v='+item.videoId:'https://www.youtube.com/@NFL/search?query='+encodeURIComponent(`${game.season} ${team} ${game.opponentSlug} ${game.week} highlights`);
    a.textContent=item?'Watch NFL highlights':'Search NFL channel';panel.append(a);
    const note=doc.createElement('small');note.textContent=item?item.title:'No verified NFL video is linked for this game yet.';panel.append(note);
  }
  window.NFLHighlights={install,mount,key,slug,round};
})();
