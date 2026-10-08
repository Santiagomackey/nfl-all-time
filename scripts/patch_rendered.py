import json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
old=(root/'template.html').read_text()
# propagate precise source modifications to prebuilt browser pages
replacements=[
('const titles = franchiseTimelineData().filter(x => /super bowl/i.test(x.title)).length;', 'const routeData = window.__NFL_ROUTE_TEAM_DATA__ || {};\n  const titles = Number(routeData.overviewStats?.superBowls ?? routeData.overviewStats?.championships ?? 0);'),
('const topSeason = records.byWinPct;', 'const topSeason = YEARS.filter(y => Number(y) < 2026).map(y => ({year:String(y),sum:seasonSummary(String(y))})).filter(x => x.sum.reg.w + x.sum.reg.l > 0).sort((a,b) => (b.sum.reg.w/(b.sum.reg.w+b.sum.reg.l+b.sum.reg.t/2)) - (a.sum.reg.w/(a.sum.reg.w+a.sum.reg.l+a.sum.reg.t/2)) || b.sum.reg.w-a.sum.reg.w)[0] || records.byWinPct;'),
('const seasons = YEARS.length;\n  const totalGames = ALL_GAMES.length;', 'const historicalYears = YEARS.filter(y => Number(y) < 2026);\n  const seasons = historicalYears.length;\n  const totalGames = ALL_GAMES.filter(g => Number(g.year) < 2026 && [\'W\',\'L\',\'T\'].includes(g.result)).length;'),
('From 1996 through ${YEARS[YEARS.length - 1]}','From ${historicalYears[0]} through ${historicalYears[historicalYears.length - 1]}'),
("const target = typeof teamPageUrl === 'function' ? teamPageUrl(slug, {year: LIVE_SEASON_YEAR}) : '';\n          if (target) window.location.href = target + (target.includes('#') ? '&' : '#') + 'game=' + encodeURIComponent(event.id);", "const target = typeof teamPageUrl === 'function' ? teamPageUrl(slug, {year: LIVE_SEASON_YEAR, espnGame: event.id}) : '';\n          if (target) window.top.location.href = target;")]
addon=old[old.index('<script>\n(function(){\n  function eventId()'):old.index('</script>',old.index('<script>\n(function(){\n  function eventId()'))+9]
count=0
for p in (root/'data/browser-pages').glob('*.js'):
 src=p.read_text();prefix,encoded=src.split(' = ',2)[0:2],None
 # use first = following team map assignment
 anchor=' = '+json.dumps(p.stem)+' ] = '
 pos=src.find('] = ')
 if pos<0:continue
 head=src[:pos+4]; html=json.loads(src[pos+4:].strip().rstrip(';'))
 for a,b in replacements:html=html.replace(a,b)
 html=html.replace('</body>',addon+'</body>',1)
 p.write_text(head+json.dumps(html,ensure_ascii=False)+';\n')
 count+=1
print('Updated rendered team pages:',count)
