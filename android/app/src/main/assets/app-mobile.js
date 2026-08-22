
(function () {
  const HOME = 'https://nfl-all-time.vercel.app/';
  const $ = (s, r=document) => r.querySelector(s);
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function ensureViewport() {
    let vp = document.querySelector('meta[name="viewport"]');
    if (!vp) {
      vp = document.createElement('meta');
      vp.name = 'viewport';
      document.head.appendChild(vp);
    }
    vp.content = 'width=device-width,initial-scale=1,maximum-scale=1,viewport-fit=cover';
    document.documentElement.classList.add('bb-apk');
  }

  function installStyles() {
    let st = document.getElementById('bb-apk-v2-style');
    if (st) return;
    st = document.createElement('style');
    st.id = 'bb-apk-v2-style';
    st.textContent = `
      html.bb-apk,html.bb-apk body{min-width:0!important;width:100%!important;max-width:100%!important;overflow-x:hidden!important}
      html.bb-apk body{font-size:14px!important;padding-bottom:0!important}
      html.bb-apk .topnav{display:none!important}
      html.bb-apk .container{width:100%!important;max-width:100%!important;padding-left:18px!important;padding-right:18px!important}
      html.bb-apk .hero{min-height:0!important;height:auto!important;padding:38px 0 34px!important;overflow:hidden!important}
      html.bb-apk .hero .container{display:block!important}
      html.bb-apk .hero-eyebrow{font-size:8px!important;letter-spacing:2.4px!important;margin:0 0 14px!important;white-space:normal!important}
      html.bb-apk .hero h1{display:block!important;width:auto!important;max-width:none!important;overflow:visible!important;white-space:nowrap!important;font-size:52px!important;line-height:.94!important;letter-spacing:.04em!important;margin:0 0 13px!important}
      html.bb-apk .hero h1 *{display:inline!important;max-width:none!important}
      html.bb-apk .hero-sub{font-size:12px!important;line-height:1.55!important;max-width:350px!important;margin:0 0 20px!important}
      html.bb-apk .hero-actions{display:grid!important;grid-template-columns:1fr 1fr!important;gap:10px!important;width:100%!important;max-width:360px!important}
      html.bb-apk .hero-actions .hero-btn{display:flex!important;align-items:center!important;justify-content:center!important;width:100%!important;min-width:0!important;min-height:48px!important;padding:10px 12px!important;font-size:9px!important;line-height:1.25!important;white-space:normal!important;text-align:center!important;border-radius:12px!important}
      html.bb-apk .hero-actions .hero-btn:nth-child(n+3){display:none!important}

      html.bb-apk .section{padding:34px 0!important}
      html.bb-apk .section-header{margin-bottom:17px!important}
      html.bb-apk .section-title{font-size:29px!important;line-height:1!important}
      html.bb-apk .section-subtitle{font-size:11px!important;line-height:1.5!important;max-width:340px!important}
      html.bb-apk #teams .filter-divider,html.bb-apk #teams .filter-group{display:none!important}
      html.bb-apk #teams .filter-bar{display:grid!important;grid-template-columns:minmax(0,1fr) auto!important;gap:9px!important;padding:9px!important;margin-bottom:12px!important;border-radius:14px!important}
      html.bb-apk #teams .filter-search-wrap{width:100%!important;min-width:0!important}
      html.bb-apk #teams .filter-search,html.bb-apk #teams .sort-select{height:44px!important;min-height:44px!important}
      html.bb-apk #teams .sort-select{max-width:150px!important;font-size:8px!important}
      html.bb-apk #teams .grid-count{font-size:10px!important;margin:5px 0 12px!important}
      html.bb-apk #teams .team-grid{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:10px!important}
      html.bb-apk #teams .team-card{display:block!important;min-width:0!important;min-height:155px!important;height:155px!important;perspective:none!important}
      html.bb-apk #teams .team-card-inner{display:block!important;min-height:155px!important;height:155px!important;transform:none!important;transition:none!important;transform-style:flat!important}
      html.bb-apk #teams .team-card-front{display:flex!important;position:relative!important;inset:auto!important;min-height:155px!important;height:155px!important;padding:12px!important;transform:none!important}
      html.bb-apk #teams .team-card-back{display:none!important}
      html.bb-apk #teams .team-logo{width:38px!important;height:38px!important}
      html.bb-apk #teams .team-logo img{width:29px!important;height:29px!important;filter:none!important}
      html.bb-apk #teams .team-name{font-size:15px!important;line-height:1.05!important}
      html.bb-apk #teams .team-division{font-size:7px!important}
      html.bb-apk #teams .team-card-front-meta{gap:6px!important}
      html.bb-apk #teams .team-card-front-meta strong{font-size:12px!important}
      html.bb-apk #teams .team-card-front-meta span,html.bb-apk #teams .team-card-front-hint{font-size:6px!important}

      html.bb-apk #divisions{display:none!important}
      html.bb-apk #divisions + .divider{display:none!important}

      html.bb-apk #universe .franchise-universe-shell{padding:0!important;border-radius:16px!important;box-shadow:none!important}
      html.bb-apk #universe .franchise-universe-header{padding:16px 14px 10px!important}
      html.bb-apk #universe .franchise-universe-filter{margin:0 10px 10px!important;padding:8px!important;display:grid!important;grid-template-columns:minmax(0,1fr) auto!important;gap:7px!important}
      html.bb-apk #universe .franchise-universe-filter .filter-divider,
      html.bb-apk #universe .franchise-universe-filter .filter-group,
      html.bb-apk #universe .franchise-universe-tabs,
      html.bb-apk #universe .franchise-ranking-signal,
      html.bb-apk #universe .team-comparison,
      html.bb-apk #universe .comparison-center,
      html.bb-apk #universe [class*="comparison"]{display:none!important}
      html.bb-apk #universe .franchise-universe-grid{display:block!important;padding:0 10px 10px!important}
      html.bb-apk #universe .franchise-universe-card{display:none!important}
      html.bb-apk #universe .franchise-universe-card-wide{display:block!important;width:100%!important;min-width:0!important;box-shadow:none!important}
      html.bb-apk #universe .franchise-universe-table-wrap{max-height:400px!important;overflow:auto!important}
      html.bb-apk #universe table{font-size:9px!important}
      html.bb-apk #universe th,html.bb-apk #universe td{padding:9px 5px!important}
      html.bb-apk #universe table th:nth-child(n+6),html.bb-apk #universe table td:nth-child(n+6){display:none!important}

      html.bb-apk #live .live-section{border-radius:15px!important;box-shadow:none!important}
      html.bb-apk #live .live-header{display:flex!important;flex-wrap:wrap!important;gap:8px!important;padding:12px!important}
      html.bb-apk #live .live-tabs{width:100%!important;display:grid!important;grid-template-columns:repeat(3,1fr)!important;gap:6px!important}
      html.bb-apk #live .live-tab{min-height:40px!important;padding:8px!important;font-size:8px!important}

      html.bb-apk #season2026 .season-2026-kpis{display:none!important}
      html.bb-apk #season2026 .season-2026-grid{display:block!important}
      html.bb-apk #season2026 .season-2026-grid>.season-2026-card:first-child{display:none!important}
      html.bb-apk #season2026 .season-2026-grid>.season-2026-card:last-child{width:100%!important}
      html.bb-apk #season2026 .season-2026-schedule{max-height:none!important;overflow:visible!important}

      #bb-team-mobile{position:fixed;z-index:2147483000;inset:0;background:#060812;color:#f4f7fb;overflow:auto;-webkit-overflow-scrolling:touch;font-family:Inter,system-ui,sans-serif}
      #bb-team-mobile *{box-sizing:border-box}
      #bb-team-mobile .bbtm-head{position:sticky;top:0;z-index:4;display:flex;align-items:center;gap:12px;padding:14px 16px;background:rgba(6,8,18,.96);backdrop-filter:blur(14px);border-bottom:1px solid rgba(255,255,255,.08)}
      #bb-team-mobile .bbtm-back{width:42px;height:42px;border:1px solid rgba(255,255,255,.12);border-radius:12px;background:#111827;color:#fff;font-size:20px}
      #bb-team-mobile .bbtm-brand{font-size:12px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase}
      #bb-team-mobile .bbtm-wrap{padding:18px 16px 36px}
      #bb-team-mobile .bbtm-hero{position:relative;overflow:hidden;border:1px solid rgba(255,255,255,.10);border-radius:20px;padding:20px;background:linear-gradient(145deg,#111827,#090d18)}
      #bb-team-mobile .bbtm-accent{position:absolute;inset:0 auto 0 0;width:4px;background:var(--team,#d7193f)}
      #bb-team-mobile .bbtm-logo{width:72px;height:72px;object-fit:contain;margin-bottom:15px}
      #bb-team-mobile .bbtm-kicker{font-size:9px;color:#94a3b8;letter-spacing:2px;text-transform:uppercase}
      #bb-team-mobile h1{font-size:34px;line-height:1;margin:7px 0 8px;font-weight:900}
      #bb-team-mobile .bbtm-sub{font-size:12px;color:#a9b4c7;line-height:1.55}
      #bb-team-mobile .bbtm-stats{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:14px 0 22px}
      #bb-team-mobile .bbtm-stat{padding:14px;border:1px solid rgba(255,255,255,.08);border-radius:15px;background:#0e1523}
      #bb-team-mobile .bbtm-stat b{display:block;font-size:23px}
      #bb-team-mobile .bbtm-stat span{display:block;margin-top:4px;font-size:8px;letter-spacing:1.4px;color:#8f9caf;text-transform:uppercase}
      #bb-team-mobile .bbtm-title{font-size:18px;margin:22px 0 10px}
      #bb-team-mobile .bbtm-list{display:grid;gap:9px}
      #bb-team-mobile .bbtm-row{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:13px 14px;border:1px solid rgba(255,255,255,.08);border-radius:14px;background:#0d1421}
      #bb-team-mobile .bbtm-row strong{font-size:13px}
      #bb-team-mobile .bbtm-row span{font-size:10px;color:#98a5b8;text-align:right}
      #bb-team-mobile .bbtm-empty{padding:18px;border:1px dashed rgba(255,255,255,.12);border-radius:14px;color:#94a3b8;font-size:12px}
      #bb-team-mobile .bbtm-loading{padding:60px 20px;text-align:center;color:#94a3b8}
    `;
    document.head.appendChild(st);
  }

  function polishHome() {
    const heroTitle = $('.hero h1');
    if (heroTitle) heroTitle.textContent = 'BLITZBOOK';
    const heroSub = $('.hero-sub');
    if (heroSub) heroSub.textContent = 'Every franchise. Every season. Every game. NFL history in one place.';
  }

  function asArray(v) {
    if (Array.isArray(v)) return v;
    if (!v || typeof v !== 'object') return [];
    return Object.entries(v).map(([year, x]) => ({year, ...(x || {})}));
  }

  function num(v) {
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
  }

  function teamIdentity(d, slug) {
    const i = d.identity || d.TEAM_CONFIG || {};
    return {
      name: i.fullName || i.teamName || i.name || slug.replace(/-/g,' '),
      short: i.shortName || i.teamName || i.name || slug,
      division: i.division || d.division || '',
      conference: i.conference || d.conference || '',
      founded: i.seasonStartYear || i.foundedYear || i.founded || '',
      logo: (i.assets && i.assets.logo) || i.logo || (d.assets && d.assets.logo) || '',
      primary: (i.colors && (i.colors.primary || i.colors.primaryColor)) || i.primaryColor || '#d7193f'
    };
  }

  function getSeasons(d) {
    let rows = asArray(d.seasons || d.SEASON_EXTRA_DATA || d.seasonData);
    rows.sort((a,b) => num(b.year || b.season) - num(a.year || a.season));
    return rows;
  }

  function getGames(d) {
    let rows = asArray(d.games || d.ALL_GAMES || d.gameLog);
    rows.sort((a,b) => {
      const ay = num(a.year || a.season), by = num(b.year || b.season);
      if (ay !== by) return by-ay;
      return String(b.date || '').localeCompare(String(a.date || ''));
    });
    return rows;
  }

  function getStats(d, seasons) {
    const s = d.overviewStats || d.stats || {};
    let wins = s.wins, losses = s.losses, ties = s.ties;
    if (wins == null || losses == null) {
      wins = seasons.reduce((a,x)=>a+num(x.wins),0);
      losses = seasons.reduce((a,x)=>a+num(x.losses),0);
      ties = seasons.reduce((a,x)=>a+num(x.ties),0);
    }
    const sb = s.superBowls ?? s.superBowlWins ?? d.superBowls ?? seasons.filter(x => /super bowl champion|won super bowl|champion/i.test(String(x.playoff_result||x.playoffResult||''))).length;
    return {wins:num(wins), losses:num(losses), ties:num(ties), superBowls:num(sb)};
  }

  function closeTeam(pushBack) {
    const el = document.getElementById('bb-team-mobile');
    if (el) el.remove();
    if (pushBack && location.hash.startsWith('#bbteam=')) history.back();
  }
  window.bbCloseTeam = () => closeTeam(true);

  function openTeam(slug) {
    slug = String(slug || '').trim().toLowerCase();
    if (!slug) return false;
    closeTeam(false);

    const overlay = document.createElement('div');
    overlay.id = 'bb-team-mobile';
    overlay.innerHTML = '<div class="bbtm-loading">Loading franchise…</div>';
    document.body.appendChild(overlay);
    history.pushState({bbTeam:slug}, '', '#bbteam=' + encodeURIComponent(slug));

    fetch('/data/' + encodeURIComponent(slug) + '.json', {cache:'force-cache'})
      .then(r => { if(!r.ok) throw new Error('Team data unavailable'); return r.json(); })
      .then(d => {
        const id = teamIdentity(d, slug);
        const seasons = getSeasons(d);
        const games = getGames(d);
        const st = getStats(d, seasons);
        const recentSeasons = seasons.slice(0,8);
        const recentGames = games.slice(0,8);
        const record = st.wins + '-' + st.losses + (st.ties ? '-' + st.ties : '');

        overlay.style.setProperty('--team', id.primary);
        overlay.innerHTML = `
          <div class="bbtm-head">
            <button class="bbtm-back" aria-label="Back">‹</button>
            <div class="bbtm-brand">Blitzbook · Franchise</div>
          </div>
          <div class="bbtm-wrap">
            <div class="bbtm-hero">
              <div class="bbtm-accent"></div>
              ${id.logo ? `<img class="bbtm-logo" src="${esc(id.logo)}" alt="">` : ''}
              <div class="bbtm-kicker">${esc([id.conference,id.division].filter(Boolean).join(' · '))}</div>
              <h1>${esc(id.name)}</h1>
              <div class="bbtm-sub">${id.founded ? `NFL history since ${esc(id.founded)}.` : 'Complete franchise history.'}</div>
            </div>

            <div class="bbtm-stats">
              <div class="bbtm-stat"><b>${esc(record)}</b><span>All-time record</span></div>
              <div class="bbtm-stat"><b>${esc(st.superBowls)}</b><span>Super Bowls</span></div>
              <div class="bbtm-stat"><b>${esc(seasons.length)}</b><span>Seasons</span></div>
              <div class="bbtm-stat"><b>${esc(games.length)}</b><span>Games in database</span></div>
            </div>

            <h2 class="bbtm-title">Recent seasons</h2>
            <div class="bbtm-list">
              ${recentSeasons.length ? recentSeasons.map(x => `
                <div class="bbtm-row">
                  <strong>${esc(x.year || x.season || '')}</strong>
                  <span>${esc(x.record || [x.wins,x.losses,x.ties].filter(v=>v!==undefined).join('-') || 'Season')}</span>
                </div>`).join('') : '<div class="bbtm-empty">No season summary available.</div>'}
            </div>

            <h2 class="bbtm-title">Recent games</h2>
            <div class="bbtm-list">
              ${recentGames.length ? recentGames.map(g => {
                const opp = g.opponent || g.opponentName || g.opponentCode || 'Opponent';
                const result = g.result || '';
                const score = (g.teamScore != null && g.oppScore != null) ? `${g.teamScore}-${g.oppScore}` : '';
                return `<div class="bbtm-row"><strong>${esc(g.displayDate || g.date || g.year || '')}</strong><span>${esc([result, opp, score].filter(Boolean).join(' · '))}</span></div>`;
              }).join('') : '<div class="bbtm-empty">No recent games available.</div>'}
            </div>
          </div>
        `;
        $('.bbtm-back', overlay)?.addEventListener('click', () => closeTeam(true));
      })
      .catch(err => {
        overlay.innerHTML = `
          <div class="bbtm-head"><button class="bbtm-back">‹</button><div class="bbtm-brand">Blitzbook</div></div>
          <div class="bbtm-wrap"><div class="bbtm-empty">Could not load this franchise right now.</div></div>`;
        $('.bbtm-back', overlay)?.addEventListener('click', () => closeTeam(true));
      });
    return false;
  }

  window.routeToTeam = openTeam;

  // Catch every team link before the site's legacy team-page generator gets it.
  document.addEventListener('click', function(e) {
    const t = e.target.closest('[data-team]');
    if (!t) return;
    const slug = t.dataset.team;
    if (!slug) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    openTeam(slug);
  }, true);

  window.addEventListener('popstate', function() {
    if (!location.hash.startsWith('#bbteam=')) closeTeam(false);
  });

  ensureViewport();
  installStyles();
  polishHome();

  // The home page renders some pieces asynchronously; re-apply only the light polish.
  setTimeout(polishHome, 400);
  setTimeout(polishHome, 1200);
})();
