const BASE = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/';
const HOSTS = new Set(['site.api.espn.com', 'site.web.api.espn.com', 'sports.core.api.espn.com', 'cdn.espn.com']);
const TEAMS = { '49ers':'sf',bears:'chi',bengals:'cin',bills:'buf',broncos:'den',browns:'cle',buccaneers:'tb',cardinals:'ari',chargers:'lac',chiefs:'kc',colts:'ind',commanders:'wsh',cowboys:'dal',dolphins:'mia',eagles:'phi',falcons:'atl',giants:'nyg',jaguars:'jax',jets:'nyj',lions:'det',packers:'gb',panthers:'car',patriots:'ne',raiders:'lv',rams:'lar',ravens:'bal',saints:'no',seahawks:'sea',steelers:'pit',texans:'hou',titans:'ten',vikings:'min'};
function resolveTarget(query) {
  let target;
  if (query.url) target = new URL(String(query.url));
  else {
    const type = String(query.type || 'scoreboard');
    const team = TEAMS[query.team] || String(query.team || '');
    if (['roster','schedule','team'].includes(type)) {
      if (!/^[a-z0-9]{1,12}$/i.test(team)) throw new Error('Invalid team');
      target = new URL(BASE + 'teams/' + team + (type === 'team' ? '' : '/' + type));
    } else if (type === 'summary') {
      if (!/^\d{1,15}$/.test(String(query.event || ''))) throw new Error('Invalid event');
      target = new URL(BASE + 'summary'); target.searchParams.set('event', query.event);
    } else if (type === 'scoreboard') target = new URL(BASE + 'scoreboard');
    else throw new Error('Unsupported endpoint');
    for (const key of ['dates','season','seasontype','week','limit']) {
      if (query[key] != null) {
        if (!/^[\d-]{1,20}$/.test(String(query[key]))) throw new Error('Invalid ' + key);
        target.searchParams.set(key, query[key]);
      }
    }
  }
  if (target.protocol !== 'https:' || !HOSTS.has(target.hostname) || target.port || target.username || target.password) throw new Error('URL not allowed');
  // ESPN's scoreboard selects historical seasons with dates, not season alone.
  if (target.pathname.endsWith('/scoreboard') && target.searchParams.has('season') && !target.searchParams.has('dates')) target.searchParams.set('dates', target.searchParams.get('season'));
  return target;
}
module.exports = async function handler(req, res) {
  if (req.method && req.method !== 'GET') { res.setHeader('Allow','GET'); return res.status(405).json({error:'Method not allowed'}); }
  let target;
  try { target = resolveTarget(req.query || {}); } catch (e) { return res.status(400).json({error:e.message}); }
  try {
    const response = await fetch(target, {headers:{accept:'application/json'}, signal:AbortSignal.timeout(12000), redirect:'error'});
    if (!response.ok) { res.setHeader('Cache-Control','no-store'); return res.status(response.status).json({error:'ESPN temporarily unavailable',upstreamStatus:response.status}); }
    const body = await response.json();
    res.setHeader('Cache-Control','public, s-maxage=30, stale-while-revalidate=120');
    return res.status(200).json(body);
  } catch (e) {
    res.setHeader('Cache-Control','no-store');
    return res.status(e.name === 'TimeoutError' ? 504 : 502).json({error:'Unable to load ESPN data. Please retry.'});
  }
};
module.exports.resolveTarget = resolveTarget;
