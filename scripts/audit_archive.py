import json,pathlib,csv
root=pathlib.Path(__file__).resolve().parents[1]
rows=[]
for f in sorted((root/'data').glob('*.json')):
 try: d=json.loads(f.read_text(encoding='utf-8-sig'))
 except Exception: continue
 if not isinstance(d,dict) or not isinstance(d.get('seasons'),list) or 'identity' not in d:continue
 seasons=d['seasons']; games=d.get('games',[]); overview=d.get('overviewStats',{}); historical=[s for s in seasons if int(s.get('year',0))<2026]; issues=[]
 if len({s.get('year') for s in seasons})!=len(seasons):issues.append('duplicate season years')
 if overview.get('games') is not None and games and int(overview['games'])!=len([g for g in games if int(g.get('season',g.get('year',0)))<2026]):issues.append('overview game count differs from game rows')
 for s in historical:
  if all(k in s for k in ('wins','losses','ties')) and s.get('record') and s['record']!=f"{s['wins']}-{s['losses']}"+(f"-{s['ties']}" if s['ties'] else ''):issues.append(f"{s['year']} season record mismatch")
 if any(s.get('year')==2026 and s.get('record')=='0-0' for s in seasons):issues.append('2026 placeholder record; requires live sync')
 rows.append({'team':d['identity'].get('teamName'),'file':f.name,'seasons':len(historical),'games':len(games),'issues':'; '.join(issues)})
with (root/'ARCHIVE_AUDIT.csv').open('w',newline='',encoding='utf-8') as out:
 w=csv.DictWriter(out,fieldnames=['team','file','seasons','games','issues']);w.writeheader();w.writerows(rows)
print('Audited teams:',len(rows),'Teams with flags:',sum(bool(r['issues']) for r in rows))
