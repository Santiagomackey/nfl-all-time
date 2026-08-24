export default async function handler(req, res) {
  const { type, team, event } = req.query || {};
  const base = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl';

  const cleanTeam = String(team || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const cleanEvent = String(event || '').replace(/[^0-9]/g, '');

  let urls = [];
  let cache = 's-maxage=10, stale-while-revalidate=20';

  if (type === 'roster') {
    if (!cleanTeam) return res.status(400).json({ error: 'Missing team' });
    urls = [
      `${base}/teams/${cleanTeam}/roster`,
      `${base}/teams/${cleanTeam}?enable=roster,projection,stats`
    ];
    cache = 's-maxage=1800, stale-while-revalidate=3600';
  } else if (type === 'summary') {
    if (!cleanEvent) return res.status(400).json({ error: 'Missing event' });
    urls = [`${base}/summary?event=${cleanEvent}`];
    cache = 's-maxage=5, stale-while-revalidate=5';
  } else if (type === 'scoreboard') {
    urls = [`${base}/scoreboard`];
    cache = 's-maxage=5, stale-while-revalidate=5';
  } else if (type === 'teams') {
    urls = [`${base}/teams?limit=32`];
    cache = 's-maxage=3600, stale-while-revalidate=7200';
  } else {
    return res.status(400).json({ error: 'Unsupported type' });
  }

  const failures = [];
  for (const url of urls) {
    try {
      const upstream = await fetch(url, {
        headers: {
          'accept': 'application/json,text/plain,*/*',
          'user-agent': 'Blitzbook/1.0'
        }
      });
      if (!upstream.ok) {
        failures.push(`${upstream.status} ${url}`);
        continue;
      }
      const data = await upstream.json();
      res.setHeader('Cache-Control', cache);
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(200).json(data);
    } catch (error) {
      failures.push(String(error?.message || error));
    }
  }

  return res.status(502).json({ error: 'ESPN upstream unavailable', failures });
}
