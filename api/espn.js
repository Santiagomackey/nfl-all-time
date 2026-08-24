module.exports = async function handler(req, res) {
  const raw = String(req.query.url || '');
  let target;
  try { target = new URL(raw); } catch {
    res.status(400).json({ error: 'Invalid URL' }); return;
  }
  const allowed = new Set([
    'site.api.espn.com',
    'site.web.api.espn.com',
    'sports.core.api.espn.com',
    'cdn.espn.com'
  ]);
  if (!allowed.has(target.hostname)) {
    res.status(403).json({ error: 'Host not allowed' }); return;
  }
  try {
    const response = await fetch(target.toString(), {
      headers: {
        'accept': 'application/json,text/plain,*/*',
        'user-agent': 'Mozilla/5.0 Blitzbook/1.0'
      },
      cache: 'no-store'
    });
    const body = await response.text();
    res.status(response.status);
    res.setHeader('content-type', response.headers.get('content-type') || 'application/json; charset=utf-8');
    res.setHeader('cache-control', 'public, s-maxage=60, stale-while-revalidate=300');
    res.send(body);
  } catch (error) {
    res.status(502).json({ error: 'ESPN request failed' });
  }
};