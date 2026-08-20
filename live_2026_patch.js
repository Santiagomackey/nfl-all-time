(function () {
  if (window.__NFL_LIVE_2026_PATCH__) return;
  window.__NFL_LIVE_2026_PATCH__ = true;

  const LIVE_SEASON_YEAR = "2026";
  const SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard";
  const STANDINGS_URL = `https://site.api.espn.com/apis/site/v2/sports/football/nfl/standings?season=${LIVE_SEASON_YEAR}&seasontype=2`;
  const SCHEDULE_URL = (teamId) =>
    `https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/${encodeURIComponent(teamId)}/schedule?season=${LIVE_SEASON_YEAR}&seasontype=2`;
  const SUMMARY_URL = (eventId) =>
    `https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event=${encodeURIComponent(eventId)}`;
  const GAMECAST_URL = (eventId) => `https://www.espn.com/nfl/game/_/gameId/${encodeURIComponent(eventId)}`;
  const SEASON_REFRESH_MS = 60000;
  const LIVE_CENTER_REFRESH_MS = 15000;
  const LIVE_CENTER_FALLBACK_TEXT = "Waiting for a live NFL game.";
  const LIVE_2026_ASSET_VERSION = "2026-live-v2";
  const NFL_LIVE_STORAGE_KEY = "nfl-live-2026-state-v1";

  const currentYear = typeof state !== "undefined" && state ? String(state.selectedYear) : "";
  const htmlEscape =
    typeof escapeHtml === "function"
      ? escapeHtml
      : (value) =>
          String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");

  const liveSeasonState = {
    loading: false,
    loaded: false,
    error: "",
    season: null,
    lastUpdatedLabel: "",
    summaryCache: new Map(),
    summaryPending: new Map(),
    seasonRefreshHandle: null,
    liveCenterRefreshHandle: null,
  };

  function safeNormalize(value) {
    if (typeof normalizeSearch === "function") return normalizeSearch(value);
    return String(value || "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  function safeTeamKey(value) {
    if (typeof normalizeTeamName === "function") return normalizeTeamName(value);
    return safeNormalize(value);
  }

  function getCurrentTeamInfo() {
    const config = typeof TEAM_CONFIG !== "undefined" && TEAM_CONFIG ? TEAM_CONFIG : {};
    const teamName = config.teamName || config.fullName || document.title.replace(/\s+All-Time.*/, "").trim() || "This Team";
    const shortName = config.shortName || teamName.split(" ").slice(-1)[0] || teamName;
    const meta = typeof teamMeta === "function" ? teamMeta(shortName) : null;
    const espnLink =
      (config.externalLinks && (config.externalLinks.espn || config.externalLinks.ESPN)) || "";
    const espnTeamIdMatch = String(espnLink).match(/\/name\/(\d+)\/|\/id\/(\d+)\/|\/team\/_\/name\/[a-z0-9-]+\/(\d+)/i);
    const espnTeamId =
      (config.espnTeamId != null && String(config.espnTeamId)) ||
      (espnTeamIdMatch && (espnTeamIdMatch[1] || espnTeamIdMatch[2] || espnTeamIdMatch[3])) ||
      "";
    const espnSlug =
      String(config.espnSlug || "")
        .trim()
        .toLowerCase() ||
      String(espnLink).match(/\/name\/([a-z0-9-]+)\//i)?.[1] ||
      "";
    const keys = new Set(
      [
        teamName,
        shortName,
        config.mascotName,
        config.nickname,
        config.teamSlug,
        config.slug,
        espnSlug,
        meta && meta.abbr,
      ]
        .filter(Boolean)
        .flatMap((value) => {
          const raw = String(value || "").trim();
          return [raw, safeNormalize(raw), safeTeamKey(raw)];
        })
    );

    return {
      teamName,
      shortName,
      abbr: (meta && meta.abbr) || String(shortName).slice(0, 3).toUpperCase(),
      espnTeamId,
      espnSlug,
      division: config.division || "",
      conference: config.conference || "",
      headCoach: config.headCoach || "TBD",
      keys,
    };
  }

  const TEAM_INFO = getCurrentTeamInfo();

  function teamLabel() {
    return TEAM_INFO.shortName || TEAM_INFO.teamName;
  }

  function isCurrentTeamCompetitor(competitor) {
    const team = competitor && competitor.team ? competitor.team : {};
    const values = [
      team.id,
      team.slug,
      team.abbreviation,
      team.displayName,
      team.shortDisplayName,
      team.name,
      team.location && team.name ? `${team.location} ${team.name}` : "",
    ];

    if (TEAM_INFO.espnTeamId && String(team.id || "") === TEAM_INFO.espnTeamId) return true;
    return values.some((value) => {
      if (!value) return false;
      const raw = String(value).trim();
      return TEAM_INFO.keys.has(raw) || TEAM_INFO.keys.has(safeNormalize(raw)) || TEAM_INFO.keys.has(safeTeamKey(raw));
    });
  }

  function formatPct(wins, losses, ties) {
    const total = Number(wins) + Number(losses) + Number(ties);
    if (!total) return ".000";
    const pct = ((Number(wins) + Number(ties) * 0.5) / total).toFixed(3);
    return pct.startsWith("0") ? pct.slice(1) : pct;
  }

  function formatSignedNumber(value) {
    const numeric = Number(value || 0);
    if (!Number.isFinite(numeric)) return "—";
    return numeric > 0 ? `+${numeric}` : String(numeric);
  }

  function formatDateTime(dateValue) {
    if (!dateValue) return "Date TBD";
    const date = new Date(dateValue);
    if (Number.isNaN(date.getTime())) return "Date TBD";
    return date.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  }

  function fetchJson(url) {
    return fetch(url, { cache: "no-store" }).then((response) => {
      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }
      return response.json();
    });
  }

  function extractEvents(payload) {
    if (!payload) return [];
    if (Array.isArray(payload.events)) return payload.events.slice();
    const queue = [payload];
    const seen = new Set();
    const events = [];

    while (queue.length) {
      const node = queue.shift();
      if (!node || typeof node !== "object" || seen.has(node)) continue;
      seen.add(node);

      if (Array.isArray(node.events)) {
        node.events.forEach((event) => {
          if (event && !events.includes(event)) events.push(event);
        });
      }

      Object.values(node).forEach((value) => {
        if (Array.isArray(value)) {
          value.forEach((entry) => {
            if (entry && typeof entry === "object") queue.push(entry);
          });
        } else if (value && typeof value === "object") {
          queue.push(value);
        }
      });
    }

    return events;
  }

  function getCompetitorsFromEvent(event) {
    return event?.competitions?.[0]?.competitors || event?.competitors || [];
  }

  function getEventStatus(event) {
    return event?.competitions?.[0]?.status?.type || event?.status?.type || {};
  }

  function getEventWeekLabel(event, index) {
    const competition = event?.competitions?.[0] || {};
    return (
      event?.week?.text ||
      competition?.week?.text ||
      event?.week?.label ||
      competition?.type?.abbreviation ||
      event?.shortName ||
      `Game ${index + 1}`
    );
  }

  function getOpponentName(competitor) {
    return (
      competitor?.team?.shortDisplayName ||
      competitor?.team?.displayName ||
      competitor?.team?.name ||
      "Opponent"
    );
  }

  function getOpponentAbbr(name, competitor) {
    const team = competitor && competitor.team ? competitor.team : {};
    if (team.abbreviation) return team.abbreviation;
    return typeof teamMeta === "function" ? teamMeta(name).abbr : String(name || "OPP").slice(0, 3).toUpperCase();
  }

  function getEventLink(eventId) {
    return eventId ? GAMECAST_URL(eventId) : "https://www.espn.com/nfl/scoreboard";
  }

  function getYouTubeSearchUrl(game) {
    const query = `${LIVE_SEASON_YEAR} ${TEAM_INFO.teamName} vs ${game.opponent} highlights`;
    return `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`;
  }

  function parseScheduleGame(event, index) {
    const competition = event?.competitions?.[0] || {};
    const competitors = getCompetitorsFromEvent(event);
    const team = competitors.find(isCurrentTeamCompetitor);
    if (!team) return null;

    const opponent = competitors.find((competitor) => competitor !== team) || null;
    const status = getEventStatus(event);
    const stateKey = String(status?.state || "").toLowerCase();
    const isLive = stateKey === "in";
    const isFinal = stateKey === "post" || Boolean(status?.completed);
    const location = String(team?.homeAway || "").toLowerCase() === "home" ? "Home" : "Away";
    const teamScore = Number(team?.score ?? 0);
    const oppScore = Number(opponent?.score ?? 0);
    const result = isFinal
      ? teamScore > oppScore
        ? "W"
        : teamScore < oppScore
        ? "L"
        : "T"
      : isLive
      ? teamScore > oppScore
        ? "W"
        : teamScore < oppScore
        ? "L"
        : "T"
      : "TBD";

    return {
      year: LIVE_SEASON_YEAR,
      eventId: String(event?.id || competition?.id || `${LIVE_SEASON_YEAR}-${index}`),
      round: getEventWeekLabel(event, index),
      opponent: getOpponentName(opponent),
      opponentAbbr: getOpponentAbbr(getOpponentName(opponent), opponent),
      ravensScore: teamScore,
      oppScore: oppScore,
      location,
      result,
      isPlayoff: /wild card|divisional|conference|super bowl|playoff/i.test(getEventWeekLabel(event, index)),
      state: isFinal ? "post" : isLive ? "in" : "pre",
      statusLabel: status?.detail || status?.shortDetail || status?.description || (isFinal ? "Final" : isLive ? "Live" : "Scheduled"),
      scheduledDate: competition?.date || event?.date || "",
      venue: competition?.venue?.fullName || "",
      venueCity: competition?.venue?.address?.city || "",
      broadcast:
        competition?.broadcasts?.[0]?.names?.join(", ") ||
        competition?.geoBroadcasts?.[0]?.media?.shortName ||
        "",
      recapUrl: getEventLink(event?.id || competition?.id),
      youtubeSummaryUrl: getYouTubeSearchUrl({ opponent: getOpponentName(opponent) }),
      sortValue: competition?.date || event?.date || String(index).padStart(2, "0"),
      note: isFinal ? "Final" : isLive ? "Live now" : formatDateTime(competition?.date || event?.date || ""),
    };
  }

  function aggregateRecord(games, includeLiveProjection) {
    let wins = 0;
    let losses = 0;
    let ties = 0;
    let pf = 0;
    let pa = 0;
    const home = { wins: 0, losses: 0, ties: 0 };
    const away = { wins: 0, losses: 0, ties: 0 };
    const recent = [];

    games
      .slice()
      .sort((a, b) => String(a.sortValue).localeCompare(String(b.sortValue)))
      .forEach((game) => {
        const counts = game.state === "post" || (includeLiveProjection && game.state === "in" && game.ravensScore !== game.oppScore);
        if (!counts) return;
        const result = game.ravensScore > game.oppScore ? "W" : game.ravensScore < game.oppScore ? "L" : "T";
        if (result === "W") wins += 1;
        if (result === "L") losses += 1;
        if (result === "T") ties += 1;
        pf += Number(game.ravensScore || 0);
        pa += Number(game.oppScore || 0);
        const bucket = game.location === "Home" ? home : away;
        if (result === "W") bucket.wins += 1;
        if (result === "L") bucket.losses += 1;
        if (result === "T") bucket.ties += 1;
        recent.push(`${result}${game.state === "in" ? "*" : ""}`);
      });

    return {
      wins,
      losses,
      ties,
      pf,
      pa,
      diff: pf - pa,
      pct: formatPct(wins, losses, ties),
      label: `${wins}-${losses}${ties ? `-${ties}` : ""}`,
      homeLabel: `${home.wins}-${home.losses}${home.ties ? `-${home.ties}` : ""}`,
      awayLabel: `${away.wins}-${away.losses}${away.ties ? `-${away.ties}` : ""}`,
      lastFive: recent.slice(-5).join(" ") || "Awaiting kickoff",
    };
  }

  function extractStandingsRows(payload) {
    const divisionKey = safeNormalize(TEAM_INFO.division);
    const groups = [];

    function walk(node) {
      if (!node || typeof node !== "object") return;
      if (Array.isArray(node)) {
        node.forEach(walk);
        return;
      }
      if (Array.isArray(node.entries)) {
        groups.push(node);
      }
      Object.values(node).forEach((value) => {
        if (value && typeof value === "object") walk(value);
      });
    }

    walk(payload);

    const preferred =
      groups.find((group) => safeNormalize(group?.name || group?.displayName || "").includes(divisionKey)) ||
      groups.find((group) =>
        (group?.entries || []).some((entry) => {
          const name = entry?.team?.displayName || entry?.team?.shortDisplayName || entry?.team?.name;
          return safeTeamKey(name) === safeTeamKey(TEAM_INFO.shortName) || safeNormalize(name) === safeNormalize(TEAM_INFO.teamName);
        })
      ) ||
      null;

    const entries = preferred?.entries || [];

    return entries
      .map((entry) => {
        const stats = new Map(
          (entry?.stats || []).map((stat) => [
            safeNormalize(stat?.name || stat?.displayName || stat?.shortDisplayName || stat?.abbreviation),
            stat?.displayValue ?? stat?.value,
          ])
        );
        const teamName = entry?.team?.displayName || entry?.team?.shortDisplayName || entry?.team?.name;
        const wins = Number(stats.get("wins") ?? stats.get("w") ?? 0);
        const losses = Number(stats.get("losses") ?? stats.get("l") ?? 0);
        const ties = Number(stats.get("ties") ?? stats.get("t") ?? 0);
        const pctValue = stats.get("win percent") ?? stats.get("winpercentage") ?? stats.get("pct");

        return {
          team: teamName,
          wins,
          losses,
          ties,
          pct: pctValue != null && pctValue !== "" ? String(pctValue) : formatPct(wins, losses, ties),
          isCurrentTeam: safeTeamKey(teamName) === safeTeamKey(TEAM_INFO.shortName) || safeNormalize(teamName) === safeNormalize(TEAM_INFO.teamName),
          liveProjection: false,
        };
      })
      .filter((row) => row.team);
  }

  function applyLiveStandingsProjection(rows, scoreboardPayload) {
    if (!rows.length) return rows;
    const projected = rows.map((row) => ({ ...row }));
    const rowMap = new Map(projected.map((row) => [safeTeamKey(row.team), row]));

    extractEvents(scoreboardPayload).forEach((event) => {
      const status = getEventStatus(event);
      if (String(status?.state || "").toLowerCase() !== "in") return;
      const competitors = getCompetitorsFromEvent(event);
      if (competitors.length < 2) return;
      const home = competitors.find((entry) => String(entry?.homeAway || "").toLowerCase() === "home") || competitors[0];
      const away = competitors.find((entry) => String(entry?.homeAway || "").toLowerCase() === "away") || competitors[1];
      const homeRow = rowMap.get(safeTeamKey(getOpponentName(home)));
      const awayRow = rowMap.get(safeTeamKey(getOpponentName(away)));
      if (!homeRow && !awayRow) return;

      const homeScore = Number(home?.score ?? 0);
      const awayScore = Number(away?.score ?? 0);
      if (homeScore === awayScore) return;

      const winner = homeScore > awayScore ? homeRow : awayRow;
      const loser = homeScore > awayScore ? awayRow : homeRow;

      if (winner) {
        winner.wins += 1;
        winner.liveProjection = true;
      }
      if (loser) {
        loser.losses += 1;
        loser.liveProjection = true;
      }
    });

    projected.forEach((row) => {
      row.pct = formatPct(row.wins, row.losses, row.ties);
    });

    projected.sort((left, right) => {
      const leftPct = Number(`0${String(left.pct).replace(/[^0-9.]/g, "")}`);
      const rightPct = Number(`0${String(right.pct).replace(/[^0-9.]/g, "")}`);
      if (rightPct !== leftPct) return rightPct - leftPct;
      if (right.wins !== left.wins) return right.wins - left.wins;
      return safeNormalize(left.team).localeCompare(safeNormalize(right.team));
    });

    return projected;
  }

  function buildSeasonInsights(games) {
    const finals = games.filter((game) => game.state === "post");
    const live = games.filter((game) => game.state === "in");
    const sortedFinals = finals.slice().sort((left, right) => String(left.sortValue).localeCompare(String(right.sortValue)));
    const nextGame = games.find((game) => game.state === "pre") || null;
    const lastGame = sortedFinals[sortedFinals.length - 1] || live[0] || null;
    const bestOffense = finals.slice().sort((left, right) => right.ravensScore - left.ravensScore)[0] || null;
    const bestDefense = finals.slice().sort((left, right) => left.oppScore - right.oppScore)[0] || null;
    const closestFinish = finals.slice().sort((left, right) => Math.abs(left.ravensScore - left.oppScore) - Math.abs(right.ravensScore - right.oppScore))[0] || null;

    return {
      nextGame,
      lastGame,
      bestOffense,
      bestDefense,
      closestFinish,
      liveCount: live.length,
      finalCount: finals.length,
    };
  }

  function getRouteTeamData() {
    const data = window.__NFL_ROUTE_TEAM_DATA__;
    return data && typeof data === "object" ? data : null;
  }

  function normalizeRouteGameForLegacy(game, index) {
    const rawResult = String(game?.result || "").toUpperCase();
    const result = rawResult === "W" || rawResult === "L" || rawResult === "T" ? rawResult : "TBD";
    const teamScore = Number(game?.teamScore ?? game?.ravensScore ?? 0);
    const oppScore = Number(game?.opponentScore ?? game?.oppScore ?? 0);
    const stats = game?.stats || {};
    return {
      year: Number(LIVE_SEASON_YEAR),
      season: Number(LIVE_SEASON_YEAR),
      opponent: game?.opponent || "Opponent",
      opponentCode: game?.opponentCode || game?.opponentSlug || "",
      ravensScore: teamScore,
      teamScore,
      oppScore,
      opponentScore: oppScore,
      location: game?.location || (game?.homeAway === "away" ? "Away" : "Home"),
      result,
      round: game?.round || `Game ${index + 1}`,
      competition: game?.competition || "Regular Season",
      isPlayoff: Boolean(game?.isPlayoff),
      date: game?.date || "",
      displayDate: game?.displayDate || "TBD",
      totalYards: stats.totalYards || "",
      passingYards: stats.passingYards || "",
      rushingYards: stats.rushingYards || "",
      turnovers: stats.turnovers || "",
      firstDowns: stats.firstDowns || "",
      possession: stats.timeOfPossession || stats.possession || "",
      stadium: game?.stadium || "",
      youtubeSummaryUrl: game?.links?.youtubeSummary || getYouTubeSearchUrl({ opponent: game?.opponent || "Opponent" }),
      youtubeSummaryLabel: "Watch on YouTube",
    };
  }

  function installRoute2026SeasonIntoLegacyData() {
    const routeData = getRouteTeamData();
    const routeGames = Array.isArray(routeData?.games) ? routeData.games : [];
    if (!routeGames.length) return;

    try {
      if (typeof ALL_GAMES !== "undefined" && Array.isArray(ALL_GAMES)) {
        const has2026Games = ALL_GAMES.some((game) => Number(game.year || game.season) === Number(LIVE_SEASON_YEAR));
        if (!has2026Games) {
          routeGames.map(normalizeRouteGameForLegacy).forEach((legacyGame) => {
            const gameIndex = ALL_GAMES.push(legacyGame) - 1;
            if (typeof seasons !== "undefined" && seasons && typeof seasons === "object") {
              seasons[LIVE_SEASON_YEAR] = seasons[LIVE_SEASON_YEAR] || [];
              seasons[LIVE_SEASON_YEAR].push({ ...legacyGame, _index: gameIndex });
            }
          });
        }
      }

      if (typeof YEARS !== "undefined" && Array.isArray(YEARS) && !YEARS.some((year) => String(year) === LIVE_SEASON_YEAR)) {
        YEARS.push(Number(LIVE_SEASON_YEAR));
        YEARS.sort((left, right) => Number(left) - Number(right));
      }

      if (typeof SEASON_EXTRA_DATA !== "undefined" && SEASON_EXTRA_DATA && typeof SEASON_EXTRA_DATA === "object") {
        const season = (routeData.seasons || []).find((entry) => String(entry.year) === LIVE_SEASON_YEAR) || {};
        if (!SEASON_EXTRA_DATA[LIVE_SEASON_YEAR]) {
          SEASON_EXTRA_DATA[LIVE_SEASON_YEAR] = {
            record: season.record || "Record: 0-0",
            division: season.division || TEAM_INFO.division || "",
            division_rank: season.divisionRank || null,
            stats: season.teamStats || {},
            standings: (season.standings || []).map((row) => ({
              team: row.team || "",
              W: Number(row.wins || row.W || 0),
              L: Number(row.losses || row.L || 0),
              T: Number(row.ties || row.T || 0),
              PCT: Number(row.pct || row.PCT || 0),
            })),
          };
        }
      }
    } catch (error) {
      console.warn(`Could not install ${LIVE_SEASON_YEAR} route season data.`, error);
    }
  }

  function parseLocalScheduleGame(game, index) {
    if (!game || Number(game.season) !== Number(LIVE_SEASON_YEAR)) return null;
    const teamScore = game.teamScore == null ? 0 : Number(game.teamScore || 0);
    const oppScore = game.opponentScore == null ? Number(game.oppScore || 0) : Number(game.opponentScore || 0);
    const rawResult = String(game.result || "").toUpperCase();
    const isFinal = rawResult === "W" || rawResult === "L" || rawResult === "T";
    const location = game.location || (game.homeAway === "home" ? "Home" : "Away");

    return {
      year: LIVE_SEASON_YEAR,
      eventId: String(game.id || `${LIVE_SEASON_YEAR}-local-${index}`),
      round: game.round || `Game ${index + 1}`,
      opponent: game.opponent || "Opponent",
      opponentAbbr: typeof teamMeta === "function" ? teamMeta(game.opponent || "Opponent").abbr : String(game.opponent || "OPP").slice(0, 3).toUpperCase(),
      ravensScore: teamScore,
      oppScore,
      location,
      result: isFinal ? rawResult : "TBD",
      isPlayoff: Boolean(game.isPlayoff),
      state: isFinal ? "post" : "pre",
      statusLabel: isFinal ? "Final" : "Scheduled",
      scheduledDate: game.date || "",
      venue: game.stadium || "",
      venueCity: "",
      broadcast: "",
      recapUrl: game.links?.espnGamecast || "https://www.espn.com/nfl/scoreboard",
      youtubeSummaryUrl: game.links?.youtubeSummary || getYouTubeSearchUrl({ opponent: game.opponent || "Opponent" }),
      sortValue: game.date || String(index).padStart(2, "0"),
      note: isFinal ? "Final" : "Date TBD",
    };
  }

  function readSharedLiveData() {
    try {
      if (window.parent && window.parent !== window && window.parent.NFL_LIVE_DATA) {
        return window.parent.NFL_LIVE_DATA;
      }
    } catch (error) {}

    try {
      if (window.NFL_LIVE_DATA) return window.NFL_LIVE_DATA;
    } catch (error) {}

    try {
      return JSON.parse(localStorage.getItem(NFL_LIVE_STORAGE_KEY) || "null");
    } catch (error) {
      return null;
    }
  }

  function currentTeamMatchesSharedGame(game, side) {
    const teamName = side === "home" ? game.homeTeam : game.awayTeam;
    const teamShort = side === "home" ? game.homeName : game.awayName;
    const teamSlug = side === "home" ? game.homeSlug : game.awaySlug;
    const values = [teamName, teamShort, teamSlug].filter(Boolean);
    return values.some((value) => TEAM_INFO.keys.has(String(value)) || TEAM_INFO.keys.has(safeNormalize(value)) || TEAM_INFO.keys.has(safeTeamKey(value)));
  }

  function convertSharedLiveGame(game, index) {
    const isHome = currentTeamMatchesSharedGame(game, "home");
    const isAway = currentTeamMatchesSharedGame(game, "away");
    if (!isHome && !isAway) return null;

    const teamScore = isHome ? game.homeScore : game.awayScore;
    const opponentScore = isHome ? game.awayScore : game.homeScore;
    const opponent = isHome ? game.awayTeam : game.homeTeam;
    const opponentShort = isHome ? game.awayName : game.homeName;
    const status = String(game.status || "").toLowerCase();
    const state = status === "final" || status === "post" ? "post" : status === "live" || status === "in" ? "in" : "pre";
    const hasScore = teamScore !== null && teamScore !== undefined && opponentScore !== null && opponentScore !== undefined;
    const result =
      state === "pre" || !hasScore
        ? "TBD"
        : Number(teamScore) > Number(opponentScore)
        ? "W"
        : Number(teamScore) < Number(opponentScore)
        ? "L"
        : "T";

    return {
      year: LIVE_SEASON_YEAR,
      eventId: String(game.id || `shared-${LIVE_SEASON_YEAR}-${index}`),
      round: game.week || `Game ${index + 1}`,
      opponent: opponent || "Opponent",
      opponentAbbr: opponentShort || (typeof teamMeta === "function" ? teamMeta(opponent || "Opponent").abbr : String(opponent || "OPP").slice(0, 3).toUpperCase()),
      ravensScore: Number(teamScore || 0),
      oppScore: Number(opponentScore || 0),
      location: isHome ? "Home" : "Away",
      result,
      isPlayoff: false,
      state,
      statusLabel: game.statusTxt || (state === "post" ? "Final" : state === "in" ? "Live" : "Scheduled"),
      scheduledDate: game.date || "",
      venue: game.venue || "",
      venueCity: "",
      broadcast: game.channel || "",
      recapUrl: game.id ? GAMECAST_URL(game.id) : "https://www.espn.com/nfl/scoreboard",
      youtubeSummaryUrl: getYouTubeSearchUrl({ opponent: opponent || "Opponent" }),
      sortValue: game.date || String(index).padStart(2, "0"),
      note: state === "post" ? "Final" : state === "in" ? "Live now" : "Scheduled",
      stats: isHome ? game.stats?.home : game.stats?.away,
      opponentStats: isHome ? game.stats?.away : game.stats?.home,
    };
  }

  function mergeSharedLiveGames(games) {
    const shared = readSharedLiveData();
    const sharedGames = Array.isArray(shared?.games) ? shared.games : [];
    if (!sharedGames.length) return games;

    const merged = games.slice();
    sharedGames
      .map(convertSharedLiveGame)
      .filter(Boolean)
      .forEach((sharedGame) => {
        const existingIndex = merged.findIndex((game) => String(game.eventId) === String(sharedGame.eventId));
        if (existingIndex >= 0) {
          merged[existingIndex] = { ...merged[existingIndex], ...sharedGame };
        } else {
          merged.push(sharedGame);
        }
      });

    return merged.sort((left, right) => String(left.sortValue).localeCompare(String(right.sortValue)));
  }

  function buildLocalStandings(teamData) {
    const season = (teamData?.seasons || []).find((entry) => Number(entry.year) === Number(LIVE_SEASON_YEAR));
    return (season?.standings || []).map((row) => {
      const wins = Number(row.wins || 0);
      const losses = Number(row.losses || 0);
      const ties = Number(row.ties || 0);
      const team = row.team || "";
      return {
        team,
        wins,
        losses,
        ties,
        pct: row.pct != null && row.pct !== "" ? (Number(row.pct) ? formatPct(wins, losses, ties) : ".000") : formatPct(wins, losses, ties),
        isCurrentTeam: safeTeamKey(team) === safeTeamKey(TEAM_INFO.shortName) || safeNormalize(team) === safeNormalize(TEAM_INFO.teamName),
        liveProjection: false,
      };
    });
  }

  function buildLocal2026Season() {
    const teamData = getRouteTeamData();
    let games = (teamData?.games || [])
      .map(parseLocalScheduleGame)
      .filter(Boolean)
      .sort((left, right) => String(left.sortValue).localeCompare(String(right.sortValue)));
    games = mergeSharedLiveGames(games);
    if (!games.length) return null;

    const record = aggregateRecord(games, true);
    const standings = buildLocalStandings(teamData);
    const insights = buildSeasonInsights(games);
    const updated = formatDateTime(new Date());
    return {
      year: LIVE_SEASON_YEAR,
      label: `${LIVE_SEASON_YEAR} Live Season`,
      summaryNote:
        `${games.length} official ${LIVE_SEASON_YEAR} opponents loaded from the local team database. Dates, kickoff times, scores, stats, and video summaries will update after the NFL schedule and completed games are posted.`,
      home: games.filter((game) => game.location === "Home").map((game) => game.opponent),
      away: games.filter((game) => game.location === "Away").map((game) => game.opponent),
      games,
      record,
      standings,
      currentTeamStanding: standings.find((row) => row.isCurrentTeam) || null,
      insights,
      releasedOn: updated,
    };
  }

  function buildPlaceholderSeason() {
    const localSeason = buildLocal2026Season();
    if (localSeason) {
      return {
        ...localSeason,
        summaryNote: liveSeasonState.error || localSeason.summaryNote,
      };
    }

    const updated = liveSeasonState.lastUpdatedLabel || formatDateTime(new Date());
    return {
      year: LIVE_SEASON_YEAR,
      label: `${LIVE_SEASON_YEAR} Live Season`,
      summaryNote:
        liveSeasonState.error ||
        `As of ${updated}, ESPN has not exposed a full ${LIVE_SEASON_YEAR} ${TEAM_INFO.shortName} schedule feed yet. The season shell is ready and will populate automatically once games are posted.`,
      home: [],
      away: [],
      games: [],
      record: {
        wins: 0,
        losses: 0,
        ties: 0,
        pct: ".000",
        label: "0-0",
        pf: 0,
        pa: 0,
        diff: 0,
        homeLabel: "0-0",
        awayLabel: "0-0",
        lastFive: "Awaiting kickoff",
      },
      standings: [],
      insights: {
        nextGame: null,
        lastGame: null,
        bestOffense: null,
        bestDefense: null,
        closestFinish: null,
        liveCount: 0,
        finalCount: 0,
      },
      releasedOn: updated,
    };
  }

  function buildSeasonPayload(schedulePayload, standingsPayload, scoreboardPayload) {
    const games = extractEvents(schedulePayload)
      .map(parseScheduleGame)
      .filter(Boolean)
      .sort((left, right) => String(left.sortValue).localeCompare(String(right.sortValue)));

    if (!games.length) {
      const localSeason = buildLocal2026Season();
      if (localSeason) return localSeason;
    }

    const record = aggregateRecord(games, true);
    const standings = applyLiveStandingsProjection(extractStandingsRows(standingsPayload), scoreboardPayload);
    const insights = buildSeasonInsights(games);
    const currentTeamStanding = standings.find((row) => row.isCurrentTeam) || null;
    const updated = formatDateTime(new Date());
    const summaryNote = games.length
      ? `${games.length} scheduled games loaded from ESPN. Final scores, team stats, and summary links refresh automatically when ESPN posts the game summary.`
      : `The ${LIVE_SEASON_YEAR} schedule feed is not available yet. This section will fill itself automatically as soon as ESPN publishes the games.`;

    return {
      year: LIVE_SEASON_YEAR,
      label: `${LIVE_SEASON_YEAR} Live Season`,
      summaryNote,
      home: games.filter((game) => game.location === "Home").map((game) => game.opponent),
      away: games.filter((game) => game.location === "Away").map((game) => game.opponent),
      games,
      record,
      standings,
      currentTeamStanding,
      insights,
      releasedOn: updated,
    };
  }

  function ensureLiveSeasonPreview() {
    if (!liveSeasonState.season) {
      liveSeasonState.season = buildPlaceholderSeason();
    }
    return liveSeasonState.season;
  }

  function selectLiveSeasonYearIfHelpful() {
    if (typeof state === "undefined" || !state) return;
    const selectedYear = String(state.selectedYear || "");
    const latestHistoricalYear = Array.isArray(YEARS) && YEARS.length ? String(YEARS[YEARS.length - 1]) : "";
    if (!selectedYear || selectedYear === latestHistoricalYear || selectedYear === currentYear) {
      state.selectedYear = LIVE_SEASON_YEAR;
      state.selectedMatchIndex = null;
      state.isHistorical = false;
    }
  }

  function revealActiveLiveSeasonButton() {
    const wrap = document.getElementById("seasonStrip");
    const activeButton = wrap && wrap.querySelector(`.season-btn[data-year="${LIVE_SEASON_YEAR}"]`);
    if (!activeButton || typeof activeButton.scrollIntoView !== "function") return;
    activeButton.scrollIntoView({ inline: "end", block: "nearest", behavior: "auto" });
  }

  function renderLiveSeason2026TopStats(preview) {
    const cards = [
      { label: "Regular Season", value: preview.record.label, color: "#c8aa32" },
      { label: "Live Games", value: preview.insights.liveCount ? String(preview.insights.liveCount) : "0", color: preview.insights.liveCount ? "#7be495" : "#f0e8f8" },
      { label: "Win %", value: preview.record.pct, color: "#f0e8f8" },
      { label: "Points For", value: String(preview.record.pf), color: "#f0e8f8" },
      { label: "Points Against", value: String(preview.record.pa), color: "#8a7a9a" },
      { label: "Point Diff", value: formatSignedNumber(preview.record.diff), color: preview.record.diff >= 0 ? "#7be495" : "#ff7b7b" },
    ];

    document.getElementById("seasonStatsGrid").innerHTML = cards
      .map(
        (card, index) => `
        <div class="stat-card ${index === 0 ? "active-stat" : ""}" title="${htmlEscape(card.label)}">
          <div class="stat-label">${htmlEscape(card.label)}</div>
          <div class="stat-value" style="color:${card.color}">${htmlEscape(card.value)}</div>
        </div>
      `
      )
      .join("");
  }

  function renderLiveSeason2026Info(preview) {
    document.getElementById("seasonTitle").textContent = `${LIVE_SEASON_YEAR} ${TEAM_INFO.teamName}`;
    document.getElementById("seasonSummaryLine").textContent = `${preview.games.length || 0} games | record ${preview.record.label} | ${preview.insights.finalCount} final | ${preview.insights.liveCount} live`;
    document.getElementById("seasonMeta").innerHTML = `
      <div class="chip">Search filter: ${htmlEscape(state.search || "none")}</div>
      <div class="chip">Division: ${htmlEscape(TEAM_INFO.division || "NFL")}</div>
      <div class="chip">Auto refresh: every 60s</div>
      <div class="chip">Last sync: ${htmlEscape(preview.releasedOn || "pending")}</div>
    `;
  }

  function gameResultBadge(game) {
    if (game.state === "post") {
      const cls = game.result === "W" ? "green" : game.result === "L" ? "red" : "muted";
      return `<span class="result-badge ${cls}">${htmlEscape(game.result)}</span>`;
    }
    if (game.state === "in") {
      return `<span class="result-badge" style="background:rgba(123,228,149,0.12);border:1px solid rgba(123,228,149,0.22);color:#7be495;">LIVE</span>`;
    }
    return `<span class="result-badge" style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.08);color:var(--muted);">SCHEDULED</span>`;
  }

  function renderLiveSeason2026Matches(preview) {
    const rows = preview.games;
    const html = rows.length
      ? `
      <div class="panel-note preview-schedule-note">${htmlEscape(preview.summaryNote)}</div>
      <table>
        <thead><tr><th>Round</th><th>Opponent</th><th>Loc</th><th>${htmlEscape(TEAM_INFO.abbr)}</th><th>OPP</th><th>Margin</th><th>Status</th></tr></thead>
        <tbody>
          ${rows
            .map((game, index) => {
              const margin =
                game.state === "pre"
                  ? "—"
                  : formatSignedNumber(Number(game.ravensScore || 0) - Number(game.oppScore || 0));
              return `
                <tr class="match-row" data-live-2026-index="${index}">
                  <td><strong>${htmlEscape(game.round)}</strong><div class="muted" style="margin-top:4px;font-size:11px">${htmlEscape(game.state === "pre" ? formatDateTime(game.scheduledDate) : game.statusLabel)}</div></td>
                  <td><span class="team-cell"><img class="team-logo" src="${teamLogo(game.opponent)}" alt="${htmlEscape(game.opponent)} logo"><strong>${htmlEscape(game.opponent)}</strong></span></td>
                  <td>${game.location === "Home" ? '<span class="purple">HOME</span>' : '<span class="muted">AWAY</span>'}</td>
                  <td>${game.state === "pre" ? "—" : htmlEscape(game.ravensScore)}</td>
                  <td class="muted">${game.state === "pre" ? "—" : htmlEscape(game.oppScore)}</td>
                  <td class="muted"><strong>${htmlEscape(margin)}</strong></td>
                  <td>${gameResultBadge(game)}</td>
                </tr>
              `;
            })
            .join("")}
        </tbody>
      </table>
    `
      : `<div class="panel-note preview-schedule-note">${htmlEscape(preview.summaryNote)}</div><div class="empty">No ${LIVE_SEASON_YEAR} games are visible in the schedule feed yet.</div>`;

    document.getElementById("matchesWrap").innerHTML = html;
    document.querySelectorAll("[data-live-2026-index]").forEach((row) => {
      row.addEventListener("click", () => openLiveSeasonGameModal(Number(row.getAttribute("data-live-2026-index"))));
    });
  }

  function renderLiveSeason2026Extra(preview) {
    const currentStanding = preview.currentTeamStanding;
    const nextGame = preview.insights.nextGame;
    const lastGame = preview.insights.lastGame;
    const standingsRows = preview.standings.length
      ? preview.standings
          .map((row, index) => {
            const highlight = row.isCurrentTeam ? "background:rgba(200,170,50,0.10)" : "";
            const note = row.liveProjection ? " | Live projection" : "";
            return `
              <tr style="${highlight}">
                <td><span class="team-cell"><img class="team-logo" src="${teamLogo(row.team)}" alt="${htmlEscape(row.team)} logo"><strong style="color:${row.isCurrentTeam ? "#c8aa32" : "#e8e0f0"}">${htmlEscape(row.team)}</strong></span></td>
                <td>${row.wins}</td>
                <td>${row.losses}</td>
                <td>${row.ties}</td>
                <td>${htmlEscape(row.pct)}</td>
                <td class="muted">${index + 1}${note}</td>
              </tr>
            `;
          })
          .join("")
      : `<tr><td colspan="6" class="muted">Division standings will appear here as soon as ESPN posts them for ${LIVE_SEASON_YEAR}.</td></tr>`;

    document.getElementById("seasonExtra").innerHTML = `
      <div class="panel-note" style="margin-bottom:10px">${htmlEscape(preview.summaryNote)}</div>
      <div class="season-extra-grid" style="margin-bottom:16px">
        <div class="extra-card"><span>Record</span><strong>${htmlEscape(preview.record.label)}</strong></div>
        <div class="extra-card"><span>Division</span><strong>${htmlEscape(TEAM_INFO.division || "NFL")}</strong></div>
        <div class="extra-card"><span>Division Rank</span><strong>${currentStanding ? preview.standings.findIndex((row) => row.isCurrentTeam) + 1 : "—"}</strong></div>
        <div class="extra-card"><span>Coach</span><strong>${htmlEscape(TEAM_INFO.headCoach || "TBD")}</strong></div>
        <div class="extra-card"><span>Home</span><strong>${htmlEscape(preview.record.homeLabel)}</strong></div>
        <div class="extra-card"><span>Away</span><strong>${htmlEscape(preview.record.awayLabel)}</strong></div>
        <div class="extra-card"><span>PF / PA</span><strong>${preview.record.pf} / ${preview.record.pa}</strong></div>
        <div class="extra-card"><span>Point Diff</span><strong>${htmlEscape(formatSignedNumber(preview.record.diff))}</strong></div>
        <div class="extra-card"><span>Last 5</span><strong>${htmlEscape(preview.record.lastFive)}</strong></div>
        <div class="extra-card"><span>Refresh</span><strong>${htmlEscape(preview.releasedOn || "Pending")}</strong></div>
      </div>
      <div class="panel-note" style="margin-bottom:10px">2026 division table</div>
      <div class="table-wrap" style="margin-bottom:14px">
        <table>
          <thead><tr><th>Division Team</th><th>W</th><th>L</th><th>T</th><th>PCT</th><th>Note</th></tr></thead>
          <tbody>${standingsRows}</tbody>
        </table>
      </div>
      <div class="panel-note" style="margin:14px 0 10px">Season pulse</div>
      <div class="season-insight-grid">
        <div class="insight-pill"><span>Next Game</span><strong>${htmlEscape(nextGame ? `${nextGame.round} vs ${nextGame.opponent}` : "Waiting for schedule")}</strong><em>${htmlEscape(nextGame ? formatDateTime(nextGame.scheduledDate) : preview.releasedOn)}</em></div>
        <div class="insight-pill"><span>Last Result</span><strong>${htmlEscape(lastGame ? `${lastGame.result} ${lastGame.ravensScore}-${lastGame.oppScore}` : "No final yet")}</strong><em>${htmlEscape(lastGame ? `${lastGame.round} vs ${lastGame.opponent}` : "2026 season not started")}</em></div>
        <div class="insight-pill"><span>Best Offense</span><strong>${htmlEscape(preview.insights.bestOffense ? `${preview.insights.bestOffense.ravensScore} pts` : "Pending")}</strong><em>${htmlEscape(preview.insights.bestOffense ? `${preview.insights.bestOffense.round} vs ${preview.insights.bestOffense.opponent}` : "Need a final game")}</em></div>
        <div class="insight-pill"><span>Best Defense</span><strong>${htmlEscape(preview.insights.bestDefense ? `${preview.insights.bestDefense.oppScore} allowed` : "Pending")}</strong><em>${htmlEscape(preview.insights.bestDefense ? `${preview.insights.bestDefense.round} vs ${preview.insights.bestDefense.opponent}` : "Need a final game")}</em></div>
        <div class="insight-pill"><span>Closest Finish</span><strong>${htmlEscape(preview.insights.closestFinish ? `${Math.abs(preview.insights.closestFinish.ravensScore - preview.insights.closestFinish.oppScore)} pts` : "Pending")}</strong><em>${htmlEscape(preview.insights.closestFinish ? `${preview.insights.closestFinish.round} vs ${preview.insights.closestFinish.opponent}` : "Need a final game")}</em></div>
        <div class="insight-pill"><span>Live Games</span><strong>${preview.insights.liveCount}</strong><em>${htmlEscape(preview.insights.liveCount ? "Division table is projecting live results" : "No team game live right now")}</em></div>
      </div>
    `;
  }

  function extractSummaryTeamBox(summaryData, predicate) {
    const boxes = Array.isArray(summaryData?.boxscore?.teams) ? summaryData.boxscore.teams : [];
    return boxes.find((box) => predicate(box?.team || {})) || null;
  }

  function mapSummaryStats(teamBox) {
    const stats = new Map();
    (teamBox?.statistics || []).forEach((stat) => {
      const keys = [
        stat?.displayName,
        stat?.name,
        stat?.label,
        stat?.shortDisplayName,
      ].filter(Boolean);
      keys.forEach((key) => {
        stats.set(safeNormalize(key), stat?.displayValue ?? stat?.value ?? "—");
      });
    });
    return stats;
  }

  function preferredSummaryRows(summaryData, game) {
    const currentBox =
      extractSummaryTeamBox(summaryData, (team) => isCurrentTeamCompetitor({ team })) ||
      (Array.isArray(summaryData?.boxscore?.teams) ? summaryData.boxscore.teams[0] : null);
    const opponentBox =
      extractSummaryTeamBox(
        summaryData,
        (team) =>
          safeTeamKey(team?.shortDisplayName || team?.displayName || team?.name) === safeTeamKey(game.opponent) &&
          !isCurrentTeamCompetitor({ team })
      ) ||
      (Array.isArray(summaryData?.boxscore?.teams) ? summaryData.boxscore.teams.find((box) => box !== currentBox) : null);

    if (!currentBox || !opponentBox) return null;

    const leftStats = mapSummaryStats(currentBox);
    const rightStats = mapSummaryStats(opponentBox);
    const statKeys = [
      ["Total Yards", ["total yards", "totalyards"]],
      ["Passing Yards", ["passing yards", "passingyards"]],
      ["Rushing Yards", ["rushing yards", "rushingyards"]],
      ["First Downs", ["first downs", "firstdowns"]],
      ["Third Down", ["third down efficiency", "thirddownconversions"]],
      ["Fourth Down", ["fourth down efficiency", "fourthdownconversions"]],
      ["Turnovers", ["turnovers"]],
      ["Possession", ["possession", "time of possession"]],
      ["Sacks", ["sacks"]],
      ["Penalties", ["penalties"]],
    ];

    const rows = statKeys
      .map(([label, keys]) => {
        const left = keys.map((key) => leftStats.get(key)).find((value) => value != null);
        const right = keys.map((key) => rightStats.get(key)).find((value) => value != null);
        if (left == null && right == null) return null;
        return {
          stat: label,
          left: left ?? "—",
          right: right ?? "—",
          leftTeam: currentBox?.team?.abbreviation || TEAM_INFO.abbr,
          rightTeam: opponentBox?.team?.abbreviation || game.opponentAbbr || getOpponentAbbr(game.opponent),
        };
      })
      .filter(Boolean);

    return rows.length ? rows : null;
  }

  function extractSummaryLeaders(summaryData) {
    const leaders = Array.isArray(summaryData?.leaders) ? summaryData.leaders : [];
    return leaders
      .map((leader) => {
        const top = Array.isArray(leader?.leaders) ? leader.leaders[0] : null;
        if (!top) return null;
        return {
          label: leader?.displayName || leader?.name || "Leader",
          value: top?.displayValue || top?.value || "—",
          athlete: top?.athlete?.displayName || top?.athlete?.shortName || "",
          team: top?.team?.abbreviation || "",
        };
      })
      .filter(Boolean)
      .slice(0, 6);
  }

  function fetchLiveSeasonSummary(game) {
    if (!game?.eventId) return Promise.resolve(null);
    if (liveSeasonState.summaryCache.has(game.eventId)) {
      return Promise.resolve(liveSeasonState.summaryCache.get(game.eventId));
    }
    if (liveSeasonState.summaryPending.has(game.eventId)) {
      return liveSeasonState.summaryPending.get(game.eventId);
    }

    const pending = fetchJson(SUMMARY_URL(game.eventId))
      .then((payload) => {
        liveSeasonState.summaryCache.set(game.eventId, payload);
        liveSeasonState.summaryPending.delete(game.eventId);
        return payload;
      })
      .catch((error) => {
        liveSeasonState.summaryPending.delete(game.eventId);
        throw error;
      });

    liveSeasonState.summaryPending.set(game.eventId, pending);
    return pending;
  }

  function renderLiveSeasonGamePanels(game, host) {
    if (!host) return;
    if (game.state === "pre") {
      host.innerHTML = `
        <div class="mini-panel">
          <h3>Game Status</h3>
          <div class="inside">
            <div class="muted">${htmlEscape(game.round)} is scheduled for ${htmlEscape(formatDateTime(game.scheduledDate))}. The result, team stats, and matchup summary will appear here automatically once ESPN posts the final game summary.</div>
            <div class="season-extra-grid season-snapshot-grid" style="margin-top:12px">
              <div class="extra-card"><span>Kickoff</span><strong>${htmlEscape(formatDateTime(game.scheduledDate))}</strong></div>
              <div class="extra-card"><span>Venue</span><strong>${htmlEscape(game.venue || "TBD")}</strong></div>
              <div class="extra-card"><span>Broadcast</span><strong>${htmlEscape(game.broadcast || "TBD")}</strong></div>
              <div class="extra-card"><span>YouTube</span><strong>Waiting for final</strong></div>
            </div>
          </div>
        </div>
      `;
      return;
    }

    host.innerHTML = `
      <div class="mini-panel">
        <h3>Loading Game Summary</h3>
        <div class="inside"><div class="muted">Pulling the ESPN box score, leaders, and final team stats for this matchup…</div></div>
      </div>
    `;

    fetchLiveSeasonSummary(game)
      .then((summaryData) => {
        const rows = preferredSummaryRows(summaryData, game);
        const leaders = extractSummaryLeaders(summaryData);
        const competition = summaryData?.header?.competitions?.[0] || null;
        const attendance =
          competition?.attendance != null && competition?.attendance !== ""
            ? Number(competition.attendance).toLocaleString()
            : "—";

        host.innerHTML = `
          <div class="mini-panel"><h3>Team Stats</h3><div class="inside">
            ${
              rows && rows.length
                ? `<div class="compare-stack">${rows
                    .map(
                      (row) => `
                    <div class="compare-stat-card ${row.stat === "Possession" ? "compare-row-possession" : ""}">
                      <span class="compare-stat-label">${htmlEscape(row.stat)}</span>
                      <div class="compare-stat-values">
                        <div class="compare-stat-team">
                          <span class="compare-stat-team-name">${htmlEscape(row.leftTeam)}</span>
                          <strong class="compare-value${row.stat === "Possession" ? " compare-value-time" : ""}${typeof compareValueClass === "function" ? compareValueClass(row.stat, row.left, row.right, "left") : ""}">${htmlEscape(row.left)}</strong>
                        </div>
                        <div class="compare-stat-team">
                          <span class="compare-stat-team-name">${htmlEscape(row.rightTeam)}</span>
                          <strong class="compare-value${row.stat === "Possession" ? " compare-value-time" : ""}${typeof compareValueClass === "function" ? compareValueClass(row.stat, row.left, row.right, "right") : ""}">${htmlEscape(row.right)}</strong>
                        </div>
                      </div>
                    </div>
                  `
                    )
                    .join("")}</div>`
                : `<div class="muted">ESPN has not published the detailed team stat table for this game yet.</div>`
            }
          </div></div>
          <div class="mini-panel season-snapshot-panel"><h3>Game Details</h3><div class="inside"><div class="season-extra-grid season-snapshot-grid">
            <div class="extra-card"><span>Status</span><strong>${htmlEscape(game.statusLabel)}</strong></div>
            <div class="extra-card"><span>Venue</span><strong>${htmlEscape(game.venue || "TBD")}</strong></div>
            <div class="extra-card"><span>Attendance</span><strong>${htmlEscape(attendance)}</strong></div>
            <div class="extra-card"><span>Broadcast</span><strong>${htmlEscape(game.broadcast || "TBD")}</strong></div>
          </div></div></div>
          <div class="mini-panel"><h3>Top Performers</h3><div class="inside">
            ${
              leaders.length
                ? `<div class="season-extra-grid season-snapshot-grid">${leaders
                    .map(
                      (leader) => `
                    <div class="extra-card">
                      <span>${htmlEscape(leader.label)}</span>
                      <strong>${htmlEscape(leader.athlete || leader.team || "Leader")}</strong>
                      <em style="display:block;margin-top:6px;color:#a69ab2;font-size:11px">${htmlEscape(leader.value)}</em>
                    </div>
                  `
                    )
                    .join("")}</div>`
                : `<div class="muted">Leader data has not been posted for this game yet.</div>`
            }
          </div></div>
        `;
        if (typeof cleanVisibleText === "function") cleanVisibleText(host);
      })
      .catch(() => {
        host.innerHTML = `
          <div class="mini-panel">
            <h3>Game Summary</h3>
            <div class="inside"><div class="muted">The ESPN summary feed is not available for this matchup yet. The final score and YouTube search link are already in place, and the stat sheet will appear automatically once ESPN publishes it.</div></div>
          </div>
        `;
      });
  }

  function openLiveSeasonGameModal(gameIndex) {
    const preview = ensureLiveSeasonPreview();
    const game = preview.games[gameIndex];
    if (!game) return;

    const modal = document.getElementById("matchModal");
    const modalBody = document.getElementById("modalBody");
    if (!modal || !modalBody) return;

    const margin = Number(game.ravensScore || 0) - Number(game.oppScore || 0);
    const gamecastUrl = game.recapUrl || getEventLink(game.eventId);
    const youtubeUrl = game.state === "pre" ? "" : game.youtubeSummaryUrl || getYouTubeSearchUrl(game);
    const allGames = preview.games;
    const prevGame = allGames[gameIndex - 1] || null;
    const nextGame = allGames[gameIndex + 1] || null;
    const opponentPageUrl = typeof teamPageUrl === "function" ? teamPageUrl(game.opponent, { year: LIVE_SEASON_YEAR }) : "";

    document.getElementById("modalTitle").textContent = `${LIVE_SEASON_YEAR} | ${game.round}`;
    document.getElementById("modalSub").textContent = `${game.isPlayoff ? "Playoff game" : "Regular season game"} | ${game.location} | ESPN summary data syncs automatically after the game ends | Tap outside this panel or the × button to close`;

    modalBody.innerHTML = `
      <div class="game-summary-strip">
        <span class="summary-pill"><strong>${htmlEscape(game.state === "pre" ? "TBD" : game.result)}</strong> ${game.state === "pre" ? "—" : `${game.ravensScore}-${game.oppScore}`}</span>
        <span class="summary-pill">${htmlEscape(game.round)}</span>
        <span class="summary-pill">${htmlEscape(game.location)}</span>
        <span class="summary-pill">${game.isPlayoff ? "Playoffs" : "Regular Season"}</span>
        <span class="summary-pill">vs ${htmlEscape(game.opponent)}</span>
      </div>
      <div class="scoreline">
        <div class="team-box">
          <div class="score-team-head">
            <img class="score-team-logo" src="${teamLogo(TEAM_INFO.shortName)}" alt="${htmlEscape(teamLabel())} logo">
            <div class="score-team-name">${htmlEscape(teamLabel())}</div>
          </div>
          <div class="score">${game.state === "pre" ? "—" : htmlEscape(game.ravensScore)}</div>
          <div class="meta">${htmlEscape(game.location)} | ${htmlEscape(game.state === "pre" ? formatDateTime(game.scheduledDate) : margin > 0 ? `Leading/Won by ${margin}` : margin < 0 ? `Trailing/Lost by ${Math.abs(margin)}` : "Tied game")}</div>
        </div>
        <div class="versus">VS</div>
        <div class="team-box">
          <div class="score-team-head">
            <img class="score-team-logo" src="${teamLogo(game.opponent)}" alt="${htmlEscape(game.opponent)} logo">
            <div class="score-team-name">${htmlEscape(game.opponent)}</div>
          </div>
          <div class="score">${game.state === "pre" ? "—" : htmlEscape(game.oppScore)}</div>
          <div class="meta">${htmlEscape(game.isPlayoff ? "Postseason" : "Regular season")} | <span class="${game.result === "W" ? "green" : game.result === "L" ? "red" : "muted"}">${htmlEscape(game.state === "pre" ? "Scheduled" : game.result)}</span></div>
        </div>
      </div>
      <div class="season-meta" style="margin-bottom:16px">
        <div class="chip">Round: ${htmlEscape(game.round)}</div>
        <div class="chip">Kickoff: ${htmlEscape(formatDateTime(game.scheduledDate))}</div>
        <div class="chip">Status: ${htmlEscape(game.statusLabel)}</div>
        <div class="chip">Venue: ${htmlEscape(game.venue || "TBD")}</div>
      </div>
      <div class="modal-action-strip">
        ${
          youtubeUrl
            ? `<a class="modal-link-btn youtube-btn" href="${youtubeUrl}" target="_blank" rel="noopener noreferrer">${game.state === "post" ? "YouTube Summary Search" : "YouTube Search"}</a>`
            : `<span class="modal-link-btn youtube-btn is-disabled" aria-disabled="true">YouTube Summary Pending</span>`
        }
        <a class="modal-link-btn" href="${gamecastUrl}" target="_blank" rel="noopener noreferrer">ESPN Gamecast</a>
        ${
          opponentPageUrl
            ? `<a class="modal-link-btn secondary-action-btn" id="opponentPageBtn" href="${opponentPageUrl}" onclick="return routeToRival(${JSON.stringify(game.opponent)})">Go to opponent page</a>`
            : `<span class="modal-link-btn secondary-action-btn is-disabled" aria-disabled="true">Go to opponent page</span>`
        }
        <button class="modal-nav-btn" id="prevMatchBtn">← Previous Game</button>
        <button class="modal-nav-btn" id="nextMatchBtn">Next Game →</button>
      </div>
      <div class="detail-grid detail-grid-modal">
        <div id="modalDeferredPanels" class="modal-deferred-panels">
          <div class="mini-panel">
            <h3>Loading</h3>
            <div class="inside"><div class="muted">Preparing the ${LIVE_SEASON_YEAR} matchup details…</div></div>
          </div>
        </div>
      </div>
    `;

    const prevBtn = document.getElementById("prevMatchBtn");
    const nextBtn = document.getElementById("nextMatchBtn");
    if (prevBtn) {
      prevBtn.disabled = !prevGame;
      prevBtn.onclick = () => prevGame && openLiveSeasonGameModal(gameIndex - 1);
    }
    if (nextBtn) {
      nextBtn.disabled = !nextGame;
      nextBtn.onclick = () => nextGame && openLiveSeasonGameModal(gameIndex + 1);
    }

    modal.classList.add("open");
    renderLiveSeasonGamePanels(game, document.getElementById("modalDeferredPanels"));
    if (typeof cleanVisibleText === "function") cleanVisibleText(modal);
  }

  function refreshLiveSeasonPreview() {
    if (liveSeasonState.loading) return Promise.resolve(ensureLiveSeasonPreview());
    if (!TEAM_INFO.espnTeamId) {
      liveSeasonState.error = `The ${TEAM_INFO.shortName} page does not have an ESPN team id configured yet, so the live ${LIVE_SEASON_YEAR} schedule cannot be fetched.`;
      liveSeasonState.season = buildPlaceholderSeason();
      if (typeof render === "function" && String(state.selectedYear) === LIVE_SEASON_YEAR) render();
      return Promise.resolve(liveSeasonState.season);
    }

    liveSeasonState.loading = true;
    return Promise.allSettled([
      fetchJson(SCHEDULE_URL(TEAM_INFO.espnTeamId)),
      fetchJson(STANDINGS_URL),
      fetchJson(SCOREBOARD_URL),
    ])
      .then(([scheduleResult, standingsResult, scoreboardResult]) => {
        const schedulePayload = scheduleResult.status === "fulfilled" ? scheduleResult.value : null;
        const standingsPayload = standingsResult.status === "fulfilled" ? standingsResult.value : null;
        const scoreboardPayload = scoreboardResult.status === "fulfilled" ? scoreboardResult.value : null;

        if (!schedulePayload) {
          throw new Error("Schedule feed unavailable");
        }

        liveSeasonState.error = "";
        liveSeasonState.lastUpdatedLabel = formatDateTime(new Date());
        liveSeasonState.season = buildSeasonPayload(schedulePayload, standingsPayload, scoreboardPayload);
        liveSeasonState.loaded = true;
        if (typeof render === "function" && String(state.selectedYear) === LIVE_SEASON_YEAR) render();
        return liveSeasonState.season;
      })
      .catch((error) => {
        liveSeasonState.error = `Could not sync the live ${LIVE_SEASON_YEAR} data right now. ${error.message || ""}`.trim();
        liveSeasonState.lastUpdatedLabel = formatDateTime(new Date());
        liveSeasonState.season = buildPlaceholderSeason();
        if (typeof render === "function" && String(state.selectedYear) === LIVE_SEASON_YEAR) render();
        return liveSeasonState.season;
      })
      .finally(() => {
        liveSeasonState.loading = false;
      });
  }

  function mountLiveCenterMarkup() {
    const panel = document.getElementById("liveCenter2026");
    if (!panel) return null;
    const title = panel.querySelector(".panel-title");
    const body = panel.querySelector(".panel-body");
    if (title) {
      title.innerHTML = `<span class="live-status-dot"></span> ${LIVE_SEASON_YEAR} Live ${htmlEscape(teamLabel())} Game Center`;
    }
    if (body) {
      body.innerHTML = `
        <div class="live-api-note">Live game status, score, and quick stats are pulled from ESPN&apos;s public endpoints. If ${htmlEscape(teamLabel())} is not live, this panel falls back to another live NFL game instead of freezing.</div>
        <div class="live-topbar">
          <span class="live-chip"><span class="live-status-dot"></span><strong>Live Feed</strong></span>
          <span class="live-chip">Updates every <strong>15s</strong></span>
          <span class="live-chip">Season <strong>${LIVE_SEASON_YEAR}</strong></span>
        </div>
        <div class="live-scoreboard">
          <div class="live-team">
            <div class="live-team-name" id="liveHomeName">${htmlEscape(teamLabel())}</div>
            <div class="live-team-score" id="liveHomeScore">0</div>
            <div class="live-team-sub" id="liveHomeRecord">Home</div>
          </div>
          <div class="live-mid">
            <div class="live-qtr" id="liveQuarter">Waiting</div>
            <div class="live-clock" id="liveClock">--:--</div>
            <div class="live-down" id="liveDownDist">${htmlEscape(LIVE_CENTER_FALLBACK_TEXT)}</div>
          </div>
          <div class="live-team">
            <div class="live-team-name" id="liveAwayName">Opponent</div>
            <div class="live-team-score" id="liveAwayScore">0</div>
            <div class="live-team-sub" id="liveAwayRecord">Away</div>
          </div>
        </div>
        <div class="live-meta-grid">
          <div class="live-meta-card"><div class="live-meta-label">Possession</div><div class="live-meta-value" id="livePossession">—</div></div>
          <div class="live-meta-card"><div class="live-meta-label">Key Stat</div><div class="live-meta-value" id="liveScoringPlay">Waiting for kickoff</div></div>
          <div class="live-meta-card"><div class="live-meta-label">Venue</div><div class="live-meta-value" id="liveDrive">—</div></div>
          <div class="live-meta-card"><div class="live-meta-label">State</div><div class="live-meta-value" id="liveGameState">Idle</div></div>
        </div>
        <div class="live-last-play"><span class="label">Last Update</span><div class="text" id="liveLastPlay">${htmlEscape(LIVE_CENTER_FALLBACK_TEXT)}</div></div>
        <div class="playbyplay" id="playFeed"><div class="play-row"><span class="play-time">--:--</span><span class="play-text">${htmlEscape(LIVE_CENTER_FALLBACK_TEXT)}</span></div></div>
        <div class="live-controls">
          <button class="live-control-btn" id="liveToggleBtn" type="button">Refresh</button>
        </div>
      `;
    }
    return panel;
  }

  function updateLiveCenterFromEvent(event, summaryData) {
    const competitors = getCompetitorsFromEvent(event);
    const home = competitors.find((entry) => String(entry?.homeAway || "").toLowerCase() === "home") || competitors[0];
    const away = competitors.find((entry) => String(entry?.homeAway || "").toLowerCase() === "away") || competitors[1];
    const status = getEventStatus(event);
    const lastPlay = summaryData?.drives?.current?.plays?.slice(-1)[0] || summaryData?.drives?.previous?.[0]?.plays?.slice(-1)[0] || null;
    const keyStats = preferredSummaryRows(summaryData || {}, parseScheduleGame(event, 0) || { opponent: getOpponentName(home) });

    const setText = (id, value) => {
      const el = document.getElementById(id);
      if (el) el.textContent = value;
    };

    setText("liveHomeName", home?.team?.shortDisplayName || home?.team?.displayName || "Home");
    setText("liveAwayName", away?.team?.shortDisplayName || away?.team?.displayName || "Away");
    setText("liveHomeScore", String(home?.score ?? "0"));
    setText("liveAwayScore", String(away?.score ?? "0"));
    setText("liveQuarter", status?.period ? `Q${status.period}` : status?.shortDetail || "Live");
    setText("liveClock", event?.status?.displayClock || event?.competitions?.[0]?.status?.displayClock || "--:--");
    setText("liveDownDist", event?.competitions?.[0]?.situation?.downDistanceText || status?.detail || "Live");
    setText("livePossession", event?.competitions?.[0]?.situation?.possession || "—");
    setText("liveScoringPlay", keyStats && keyStats[0] ? `${keyStats[0].stat}: ${keyStats[0].left} - ${keyStats[0].right}` : "Live stats incoming");
    setText("liveDrive", event?.competitions?.[0]?.venue?.fullName || "Live venue");
    setText("liveGameState", status?.detail || status?.description || "Live");
    setText("liveLastPlay", lastPlay?.text || `${TEAM_INFO.shortName} are not live right now. Showing another live NFL game.`);

    const feed = document.getElementById("playFeed");
    if (feed) {
      const plays = [];
      if (lastPlay?.text) {
        plays.push({ time: lastPlay.clock?.displayValue || "Live", text: lastPlay.text });
      }
      if (summaryData?.drives?.previous?.[0]?.plays?.length) {
        const recent = summaryData.drives.previous[0].plays.slice(-3).reverse();
        recent.forEach((play) => plays.push({ time: play.clock?.displayValue || "Live", text: play.text || "Play update" }));
      }
      feed.innerHTML =
        plays.length > 0
          ? plays
              .slice(0, 4)
              .map(
                (play) => `<div class="play-row"><span class="play-time">${htmlEscape(play.time)}</span><span class="play-text">${htmlEscape(play.text)}</span></div>`
              )
              .join("")
          : `<div class="play-row"><span class="play-time">--:--</span><span class="play-text">${htmlEscape(LIVE_CENTER_FALLBACK_TEXT)}</span></div>`;
    }
  }

  function showIdleLiveCenter(message) {
    const setText = (id, value) => {
      const el = document.getElementById(id);
      if (el) el.textContent = value;
    };
    setText("liveHomeName", teamLabel());
    setText("liveAwayName", "Opponent");
    setText("liveHomeScore", "0");
    setText("liveAwayScore", "0");
    setText("liveQuarter", "Waiting");
    setText("liveClock", "--:--");
    setText("liveDownDist", "No live NFL game");
    setText("livePossession", "—");
    setText("liveScoringPlay", "Waiting for kickoff");
    setText("liveDrive", "—");
    setText("liveGameState", "Idle");
    setText("liveLastPlay", message || LIVE_CENTER_FALLBACK_TEXT);
    const feed = document.getElementById("playFeed");
    if (feed) {
      feed.innerHTML = `<div class="play-row"><span class="play-time">--:--</span><span class="play-text">${htmlEscape(message || LIVE_CENTER_FALLBACK_TEXT)}</span></div>`;
    }
  }

  function refreshLiveCenter() {
    if (!document.getElementById("liveCenter2026")) return Promise.resolve();
    return fetchJson(SCOREBOARD_URL)
      .then((payload) => {
        const events = extractEvents(payload);
        const liveGames = events.filter((event) => String(getEventStatus(event)?.state || "").toLowerCase() === "in");
        const preferred =
          liveGames.find((event) => getCompetitorsFromEvent(event).some(isCurrentTeamCompetitor)) ||
          liveGames[0] ||
          null;

        if (!preferred) {
          showIdleLiveCenter(`No live ${LIVE_SEASON_YEAR} NFL game is active right now.`);
          return null;
        }

        return fetchJson(SUMMARY_URL(preferred.id))
          .then((summaryData) => {
            updateLiveCenterFromEvent(preferred, summaryData);
          })
          .catch(() => {
            updateLiveCenterFromEvent(preferred, null);
          });
      })
      .catch(() => {
        showIdleLiveCenter("Could not load the live ESPN feed right now.");
      });
  }

  function attachSeasonOverrides() {
    const originalPreviewSeasonFor = previewSeasonFor;
    const originalPreviewSeasonMatchesSearch = previewSeasonMatchesSearch;
    const originalRenderSeasonTopStats = renderSeasonTopStats;
    const originalRenderSeasonInfo = renderSeasonInfo;
    const originalRenderMatches = renderMatches;
    const originalRenderSeasonExtra = renderSeasonExtra;

    previewSeasonFor = function patchedPreviewSeasonFor(year) {
      if (String(year) === LIVE_SEASON_YEAR) {
        return ensureLiveSeasonPreview();
      }
      return originalPreviewSeasonFor(year);
    };

    previewSeasonMatchesSearch = function patchedPreviewSeasonMatchesSearch(preview, query) {
      if (preview && String(preview.year) === LIVE_SEASON_YEAR) {
        const q = safeNormalize(query);
        if (!q) return true;
        const haystack = [
          preview.year,
          preview.label,
          preview.summaryNote,
          ...(preview.games || []).flatMap((game) => [game.round, game.opponent, game.location, game.statusLabel]),
        ]
          .map(safeNormalize)
          .join(" ");
        return haystack.includes(q);
      }
      return originalPreviewSeasonMatchesSearch(preview, query);
    };

    visibleSeasonYears = function patchedVisibleSeasonYears() {
      const realYears = YEARS.map((year) => String(year)).filter((year) => seasonSearchHit(year, state.search));
      const livePreview = previewSeasonFor(LIVE_SEASON_YEAR);
      const previewYears = livePreview && previewSeasonMatchesSearch(livePreview, state.search) ? [LIVE_SEASON_YEAR] : [];
      return [...new Set([...realYears, ...previewYears])].sort((a, b) => Number(a) - Number(b));
    };

    renderSeasonStrip = function patchedRenderSeasonStrip2026() {
      const wrap = document.getElementById("seasonStrip");
      const years = visibleSeasonYears();
      wrap.innerHTML = years
        .map((year) => {
          const preview = previewSeasonFor(year);
          const active = String(year) === String(state.selectedYear) ? "active" : "";
          if (preview && String(preview.year) === LIVE_SEASON_YEAR) {
            return `<button class="season-btn preview-season-btn ${active}" data-year="${year}">
              <span class="year">${year}</span>
              <span class="mini">${htmlEscape(preview.record.label)} | ${preview.insights.liveCount} live</span>
              <span class="mini-meter"><span class="mini-meter-fill" style="width:${Math.max(6, Math.min(100, preview.games.length ? (preview.insights.finalCount / preview.games.length) * 100 : 6))}%;"></span></span>
            </button>`;
          }

          const sum = seasonSummary(String(year));
          const record = `${sum.reg.w}-${sum.reg.l}${sum.reg.t ? "-" + sum.reg.t : ""}`;
          const playoffText = sum.post.games ? `${sum.post.w}-${sum.post.l} ` : "";
          return `<button class="season-btn ${active}" data-year="${year}">
            <span class="year">${year}</span>
            <span class="mini">${record} | ${playoffText}<span class="mini-playoff-dot ${sum.post.games ? "on" : ""}"></span></span>
            <span class="mini-meter"><span class="mini-meter-fill" style="width:${sum.winPct}%;"></span></span>
          </button>`;
        })
        .join("");

      wrap.querySelectorAll(".season-btn").forEach((button) => {
        button.addEventListener("click", () => {
          state.selectedYear = button.dataset.year;
          state.selectedMatchIndex = null;
          state.isHistorical = false;
          render();
        });
      });

      if (String(state.selectedYear) === LIVE_SEASON_YEAR) {
        requestAnimationFrame(revealActiveLiveSeasonButton);
      }
    };

    renderSeasonTopStats = function patchedRenderSeasonTopStats2026(year) {
      const preview = previewSeasonFor(year);
      if (preview && String(preview.year) === LIVE_SEASON_YEAR) {
        renderLiveSeason2026TopStats(preview);
        return;
      }
      originalRenderSeasonTopStats(year);
    };

    renderSeasonInfo = function patchedRenderSeasonInfo2026(year) {
      const preview = previewSeasonFor(year);
      if (preview && String(preview.year) === LIVE_SEASON_YEAR) {
        renderLiveSeason2026Info(preview);
        return;
      }
      originalRenderSeasonInfo(year);
    };

    renderMatches = function patchedRenderMatches2026(year) {
      const preview = previewSeasonFor(year);
      if (preview && String(preview.year) === LIVE_SEASON_YEAR) {
        renderLiveSeason2026Matches(preview);
        return;
      }
      originalRenderMatches(year);
    };

    renderSeasonExtra = function patchedRenderSeasonExtra2026(year) {
      const preview = previewSeasonFor(year);
      if (preview && String(preview.year) === LIVE_SEASON_YEAR) {
        renderLiveSeason2026Extra(preview);
        return;
      }
      originalRenderSeasonExtra(year);
    };

    window.openLiveSeasonGameModal = openLiveSeasonGameModal;
    if (typeof render === "function") render();
  }

  function refreshFromSharedLiveData() {
    liveSeasonState.season = buildPlaceholderSeason();
    if (typeof render === "function" && String(state.selectedYear) === LIVE_SEASON_YEAR) {
      render();
    } else if (typeof renderSeasonStrip === "function") {
      renderSeasonStrip();
    }
  }

  function bootLiveSeason2026() {
    installRoute2026SeasonIntoLegacyData();
    ensureLiveSeasonPreview();
    mountLiveCenterMarkup();
    attachSeasonOverrides();
    selectLiveSeasonYearIfHelpful();
    refreshLiveSeasonPreview();
    refreshLiveCenter();

    const refreshButton = document.getElementById("liveToggleBtn");
    if (refreshButton) {
      refreshButton.addEventListener("click", () => {
        refreshLiveSeasonPreview();
        refreshLiveCenter();
      });
    }

    if (liveSeasonState.seasonRefreshHandle) clearInterval(liveSeasonState.seasonRefreshHandle);
    if (liveSeasonState.liveCenterRefreshHandle) clearInterval(liveSeasonState.liveCenterRefreshHandle);

    liveSeasonState.seasonRefreshHandle = setInterval(refreshLiveSeasonPreview, SEASON_REFRESH_MS);
    liveSeasonState.liveCenterRefreshHandle = setInterval(refreshLiveCenter, LIVE_CENTER_REFRESH_MS);
    window.addEventListener("nfl-live-data-updated", refreshFromSharedLiveData);
    window.addEventListener("nfl-live-teams-updated", refreshFromSharedLiveData);
    window.addEventListener("storage", (event) => {
      if (event.key === NFL_LIVE_STORAGE_KEY) refreshFromSharedLiveData();
    });
  }

  bootLiveSeason2026();
})();
