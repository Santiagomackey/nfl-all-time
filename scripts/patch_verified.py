from pathlib import Path
p=Path(__file__).resolve().parents[1]/'template.html'
s=p.read_text()
s=s.replace('const titles = franchiseTimelineData().filter(x => /super bowl/i.test(x.title)).length;', '''const routeData = window.__NFL_ROUTE_TEAM_DATA__ || {};
  const titles = Number(routeData.overviewStats?.superBowls ?? routeData.overviewStats?.championships ?? 0);''')
s=s.replace('const topSeason = records.byWinPct;', '''const topSeason = YEARS.filter(y => Number(y) < 2026).map(y => ({year:String(y),sum:seasonSummary(String(y))})).filter(x => x.sum.reg.w + x.sum.reg.l > 0).sort((a,b) => (b.sum.reg.w/(b.sum.reg.w+b.sum.reg.l+b.sum.reg.t/2)) - (a.sum.reg.w/(a.sum.reg.w+a.sum.reg.l+a.sum.reg.t/2)) || b.sum.reg.w-a.sum.reg.w)[0] || records.byWinPct;''')
s=s.replace('const seasons = YEARS.length;\n  const totalGames = ALL_GAMES.length;', '''const historicalYears = YEARS.filter(y => Number(y) < 2026);
  const seasons = historicalYears.length;
  const totalGames = ALL_GAMES.filter(g => Number(g.year) < 2026 && ['W','L','T'].includes(g.result)).length;''')
s=s.replace('From 1996 through ${YEARS[YEARS.length - 1]}','From ${historicalYears[0]} through ${historicalYears[historicalYears.length - 1]}')
s=s.replace("const target = typeof teamPageUrl === 'function' ? teamPageUrl(slug, {year: LIVE_SEASON_YEAR}) : '';\n          if (target) window.location.href = target + (target.includes('#') ? '&' : '#') + 'game=' + encodeURIComponent(event.id);", """const target = typeof teamPageUrl === 'function' ? teamPageUrl(slug, {year: LIVE_SEASON_YEAR, espnGame: event.id}) : '';
          if (target) window.top.location.href = target;""")
# Preserve the ESPN game identifier on route navigation, and display its game detail within the selected team page.
addon='''
<script>
(function(){
  function eventId(){
    try { return new URLSearchParams(window.top.location.search).get('espnGame') || new URLSearchParams(location.search).get('espnGame'); }catch(e){return new URLSearchParams(location.search).get('espnGame');}
  }
  const id=eventId();
  if(!id || !/^\\d{6,12}$/.test(id))return;
  const style=document.createElement('style');style.textContent='#bb-game-detail{position:fixed;inset:6vh max(12px,8vw);z-index:999999;background:#101a19;color:#f6f4eb;border:1px solid #bc981f;border-radius:10px;box-shadow:0 0 0 100vmax #000a;display:flex;flex-direction:column;overflow:hidden}#bb-game-detail header{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:#172c24;font:700 14px monospace}#bb-game-detail iframe{width:100%;flex:1;border:0;background:white}#bb-game-detail button{padding:7px 12px;background:#bc981f;color:#101a19;border:0;cursor:pointer}';document.head.appendChild(style);
  function show(){if(document.getElementById('bb-game-detail'))return;const el=document.createElement('div');el.id='bb-game-detail';el.innerHTML='<header><span>GAME DETAILS · ESPN BOX SCORE & STATS</span><button type="button">Close</button></header><iframe title="Game statistics" loading="lazy" referrerpolicy="no-referrer"></iframe>';document.body.appendChild(el);el.querySelector('iframe').src='https://www.espn.com/nfl/game/_/gameId/'+id;el.querySelector('button').onclick=()=>{el.remove();try{const u=new URL(window.top.location.href);u.searchParams.delete('espnGame');window.top.history.replaceState(null,'',u)}catch(e){}};}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',show,{once:true});else show();
})();
</script>
'''
# External iframe can be blocked by ESPN: provide fallback clickable link.
addon=addon.replace("el.querySelector('button').onclick=", "el.querySelector('iframe').onerror=()=>{el.querySelector('iframe').replaceWith(Object.assign(document.createElement('a'),{href:'https://www.espn.com/nfl/game/_/gameId/'+id,textContent:'Open verified game statistics at ESPN',target:'_blank'}));};el.querySelector('button').onclick=")
s=s.replace('</body>',addon+'</body>',1)
p.write_text(s)
print('Patched template')
