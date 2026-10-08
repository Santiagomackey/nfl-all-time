"""Build game links from JSONL fetched ONLY from https://www.youtube.com/@NFL/videos.
Refresh: python -m yt_dlp --flat-playlist --lazy-playlist --dump-json --skip-download https://www.youtube.com/@NFL/videos > nfl-videos.jsonl
Then: python scripts/build_highlights.py nfl-videos.jsonl
Ambiguous, partial-game, preview, and non-game videos are deliberately excluded.
"""
import json,re,sys,pathlib,datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
TEAMS=[p.stem for p in (ROOT/'data').glob('*.json') if p.stem not in ['highlights'] and p.stem in '49ers bears bengals bills broncos browns buccaneers cardinals chargers chiefs colts commanders cowboys dolphins eagles falcons giants jaguars jets lions packers panthers patriots raiders rams ravens saints seahawks steelers texans titans vikings'.split()]
def normalize_round(s):
 s=re.sub('[^a-z0-9]','',s.lower());s=s.replace('wildcardround','wildcard').replace('divisionalround','division').replace('divisional','division');s=re.sub('afcchampionship|nfcchampionship','conferencechampionship',s);return re.sub('superbowl.*','superbowl',s)
def opponent(g):
 s=g.get('opponentSlug','');return 'commanders' if s in ['redskins','washington'] else s
def gamekey(team,g):return f"{g.get('season',g.get('year'))}|{'-'.join(sorted([team,opponent(g)]))}|{(g.get('date') or '')[:10]}"
schedule={}
for event in json.loads((ROOT/'data'/'highlight-schedule.json').read_text()):
 if event['type']==2:rnd='week'+str(event['week'])
 elif event['type']==3:rnd={1:'wildcard',2:'division',3:'conferencechampionship',5:'superbowl'}.get(event['week'])
 else:continue
 if rnd:schedule[f"{event['season']}|{'-'.join(event['teams'])}|{rnd}"]=event['date']

valid=set()
for team in TEAMS:
 for g in json.loads((ROOT/'data'/f'{team}.json').read_text())['games']:
  if g['season']>=2015:valid.add(gamekey(team,g))
output={};ambiguous=set();count=0
for line in pathlib.Path(sys.argv[1]).read_text().splitlines():
 try:v=json.loads(line)
 except ValueError:continue
 count+=1;t=v.get('title','');low=t.lower()
 if (v.get('channel_id') or v.get('playlist_channel_id')) != 'UCDVYQ4Zhbm3S2dlz7P1GBDg' or not re.fullmatch(r'[\w-]{11}',v.get('id','')):continue
 if 'highlights' not in low or not re.search(r'\bvs\.?\b| at ',low) or re.search(r'1st half|2nd half|first half|second half|preview|prediction|fantasy|every touchdown|extended|throwback',low):continue
 low=low.replace('redskins','commanders').replace('washington football team','commanders').replace('washington','commanders').replace('bucs','buccaneers')
 teams=[x for x in TEAMS if re.search(r'\b'+x+r'\b',low)]
 if len(teams)!=2:continue
 years=re.findall(r'\b(20[12]\d)\b',t)
 if not years:
  description=v.get('description') or ''
  years=re.findall(r'\b(20[12]\d) (?:NFL )?season\b',description,re.I) or re.findall(r'\b(?:Week \d+,? |NFL )(20[12]\d)\b',description,re.I)
 # No guessed year: legacy titles without season require manual verification.
 if len(set(years))!=1 or int(years[0])<2015:continue
 year=years[0];week=re.search(r'week\s*(\d+)',low)
 if 'preseason' in low:continue
 if 'super bowl' in low:rnd='superbowl'
 elif 'championship' in low:rnd='conferencechampionship'
 elif 'divisional' in low:rnd='division'
 elif 'wild card' in low or 'wildcard' in low:rnd='wildcard'
 elif week:rnd='week'+str(int(week[1]))
 else:continue
 round_key=f"{year}|{'-'.join(sorted(teams))}|{rnd}"
 date=schedule.get(round_key)
 if not date:continue
 key=f"{year}|{'-'.join(sorted(teams))}|{date}"
 if key not in valid:continue
 entry={'videoId':v['id'],'title':t,'source':'https://www.youtube.com/@NFL/videos'}
 if key in output and output[key]['videoId']!=v['id']:ambiguous.add(key)
 else:output[key]=entry
for k in ambiguous:output.pop(k,None)
# Independently verified official NFL game recap, whose older title omits the year.
output['2015|bears-packers|2015-09-13']={'videoId':'P9DhWAmezAg','title':'Packers vs. Bears | Week 1, 2015 | NFL','source':'https://www.youtube.com/watch?v=P9DhWAmezAg'}
result={'source':'https://www.youtube.com/@NFL/videos','builtAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'catalogEntries':count,'linkedGames':len(output),'ambiguousGamesExcluded':len(ambiguous),'games':output}
(ROOT/'data'/'highlights.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='games'})
