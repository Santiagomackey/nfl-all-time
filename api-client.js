/* Same-origin ESPN transport shared by the homepage and franchise frames. */
(function () {
  if (window.__NFL_TRANSPORT__) return;
  window.__NFL_TRANSPORT__ = true;
  const nativeFetch = window.fetch.bind(window);
  const pending = new Map(), cache = new Map();
  window.fetch = function (input, options) {
    const raw = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
    let url;
    try { url = new URL(raw, location.href); } catch (_) { return nativeFetch(input, options); }
    if (!['site.api.espn.com','site.web.api.espn.com','sports.core.api.espn.com','cdn.espn.com'].includes(url.hostname) && !url.pathname.endsWith('/api/espn')) return nativeFetch(input, options);
    if ((options?.method || input?.method || 'GET') !== 'GET') return nativeFetch(input, options);
    if (url.pathname.endsWith('/scoreboard') && url.searchParams.has('season') && !url.searchParams.has('dates')) url.searchParams.set('dates', url.searchParams.get('season'));
    const requestUrl = url.pathname.endsWith('/api/espn') || location.protocol === 'file:' ? url.href : '/api/espn?url=' + encodeURIComponent(url.href);
    if (options?.signal) return nativeFetch(requestUrl, options);
    const hit = cache.get(requestUrl);
    if (hit && hit.until > Date.now()) return Promise.resolve(hit.response.clone());
    if (!pending.has(requestUrl)) {
      const request = nativeFetch(requestUrl, {...options, signal:AbortSignal.timeout(15000)}).then(response => {
        if (response.ok) {
          if (cache.size > 100) cache.delete(cache.keys().next().value);
          cache.set(requestUrl, {response:response.clone(),until:Date.now()+15000});
        }
        return response;
      }).finally(() => pending.delete(requestUrl));
      pending.set(requestUrl, request);
    }
    return pending.get(requestUrl).then(response => response.clone());
  };
})();
