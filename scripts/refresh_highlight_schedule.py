import urllib.request,json,concurrent.futures,pathlib,datetime,zoneinfo
ROOT=pathlib.Path(__file__).resolve().parents[1]/'data'
alias={}
for p in ROOT.glob('*.json'):
 try:
  d=json.loads(p.read_text()); identity=d['identity'];logo=identity['assets']['logo'];ab=logo.rsplit('/',1)[-1].split('.')[0];alias[ab]=p.stem
 except (KeyError,TypeError):pass
alias.update({'oak':'raiders','sd':'chargers','stl':'rams','was':'commanders'})
def get(y):
 u=f'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={y}&limit=1000'
 with urllib.request.urlopen(u,timeout=30) as r:d=json.load(r)
 result=[]
 for e in d.get('events',[]):
  teams=[alias.get(c['team']['abbreviation'].lower()) for c in e['competitions'][0]['competitors']]
  if len(teams)!=2 or None in teams:continue
  date=datetime.datetime.fromisoformat(e['date'].replace('Z','+00:00')).astimezone(zoneinfo.ZoneInfo('America/New_York')).date().isoformat()
  result.append({'season':e.get('season',{}).get('year',y),'date':date,'teams':sorted(teams),'week':e.get('week',{}).get('number'),'type':e.get('season',{}).get('type'),'name':e['name']})
 print(y,len(result),flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:rows=sum(ex.map(get,range(2015,datetime.datetime.now().year+1)),[])
(ROOT/'highlight-schedule.json').write_text(json.dumps(rows,indent=2))
