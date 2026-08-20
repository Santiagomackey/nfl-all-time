import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(__dirname, "data");
const browserDir = path.join(dataDir, "browser");

const SEASON_YEAR = 2026;
const SEASON_TYPE = 2;
const DISPLAY_TIME_ZONE = "America/New_York";
const ESPN_SCHEDULE_HUB_URL = "https://www.espn.com/nfl/schedule";
const NFL_OPPONENT_SOURCE =
  "https://operations.nfl.com/updates/football-ops/2026-opponents-determined/";

const TEAM_FILE_EXCLUSIONS = new Set([
  "team.schema.json",
  "teams-manifest.json",
  "team-page-routing.json",
  "season-2026.json",
]);

const displayDateFormatter = new Intl.DateTimeFormat("en-US", {
  timeZone: DISPLAY_TIME_ZONE,
  month: "short",
  day: "numeric",
  year: "numeric",
});

const displayDayFormatter = new Intl.DateTimeFormat("en-US", {
  timeZone: DISPLAY_TIME_ZONE,
  weekday: "long",
});

const displayTimeFormatter = new Intl.DateTimeFormat("en-US", {
  timeZone: DISPLAY_TIME_ZONE,
  hour: "numeric",
  minute: "2-digit",
});

function listTeamFiles() {
  return fs
    .readdirSync(dataDir)
    .filter((file) => file.endsWith(".json"))
    .filter((file) => !TEAM_FILE_EXCLUSIONS.has(file))
    .sort();
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, value) {
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function readTeamConfig(slug) {
  const modulePath = path.join(dataDir, `${slug}.js`);
  const source = fs.readFileSync(modulePath, "utf8");
  const match = source.match(/export const TEAM_CONFIG = (.*?);(?:\r?\n)?export const ALL_GAMES =/s);
  if (!match) {
    throw new Error(`Could not parse TEAM_CONFIG from ${modulePath}`);
  }
  return JSON.parse(match[1]);
}

function syncBrowserData(slug, data) {
  const serialized = `${JSON.stringify(data, null, 2)}\n`;
  fs.writeFileSync(path.join(browserDir, `${slug}.mjs`), `export default ${serialized}`, "utf8");
  fs.writeFileSync(
    path.join(browserDir, `${slug}.js`),
    `window.__NFL_TEAM_DATA__ = window.__NFL_TEAM_DATA__ || {}; window.__NFL_TEAM_DATA__["${slug}"] = ${serialized}`,
    "utf8",
  );
}

function normalizeKey(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function addNameVariant(map, value, slug) {
  const normalized = normalizeKey(value);
  if (normalized && !map.has(normalized)) {
    map.set(normalized, slug);
  }
}

function buildTeamContexts() {
  return listTeamFiles().map((file) => {
    const slug = file.replace(/\.json$/i, "");
    const filePath = path.join(dataDir, file);
    const data = readJson(filePath);
    const config = readTeamConfig(slug);
    return {
      slug,
      filePath,
      data,
      config,
    };
  });
}

const teamContexts = buildTeamContexts();
const teamBySlug = new Map(teamContexts.map((team) => [team.slug, team]));
const teamIdToSlug = new Map(
  teamContexts
    .map((team) => [String(team.config.espnTeamId || "").trim(), team.slug])
    .filter(([teamId]) => teamId),
);

const teamNameToSlug = new Map();
for (const team of teamContexts) {
  const identity = team.data.identity || {};
  const shortName = identity.shortName || team.config.shortName || identity.nickname || "";
  const fullName = identity.teamName || identity.fullName || team.config.teamName || "";
  const city = identity.city || "";
  const locationName = city && shortName ? `${city} ${shortName}` : "";

  [
    team.slug,
    fullName,
    shortName,
    identity.nickname,
    identity.fullName,
    city,
    locationName,
    team.config.teamName,
    team.config.shortName,
    team.config.mascotName,
    team.config.espnSlug,
    team.config.nflSlug,
  ].forEach((value) => addNameVariant(teamNameToSlug, value, team.slug));

  if (city === "Los Angeles" && shortName) addNameVariant(teamNameToSlug, `L.A. ${shortName}`, team.slug);
  if (city === "New York" && shortName) addNameVariant(teamNameToSlug, `N.Y. ${shortName}`, team.slug);
}

function scheduleUrl(teamId) {
  return `https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/${encodeURIComponent(
    teamId,
  )}/schedule?season=${SEASON_YEAR}&seasontype=${SEASON_TYPE}`;
}

async function fetchJson(url) {
  const response = await fetch(url, {
    headers: {
      "user-agent": "Mozilla/5.0 (compatible; NFLArchiveScheduleSync/1.0)",
      accept: "application/json,text/plain,*/*",
    },
  });
  if (!response.ok) {
    throw new Error(`Request failed for ${url}: ${response.status} ${response.statusText}`);
  }
  return response.json();
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

function toValidDate(value) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatDisplayDate(date) {
  return displayDateFormatter.format(date);
}

function formatDisplayDay(date) {
  return displayDayFormatter.format(date);
}

function formatDisplayTime(date) {
  return displayTimeFormatter.format(date);
}

function getEventWeekLabel(event, index) {
  const competition = event?.competitions?.[0] || {};
  const weekNumber = Number(event?.week?.number ?? competition?.week?.number);
  if (Number.isFinite(weekNumber) && weekNumber > 0) return `Week ${weekNumber}`;
  return (
    event?.week?.text ||
    competition?.week?.text ||
    event?.week?.label ||
    competition?.type?.abbreviation ||
    event?.shortName ||
    `Week ${index + 1}`
  );
}

function getCompetition(event) {
  return event?.competitions?.[0] || {};
}

function getCompetitors(event) {
  return getCompetition(event)?.competitors || event?.competitors || [];
}

function getBroadcastLabel(competition) {
  const directNames = competition?.broadcasts?.[0]?.names;
  if (Array.isArray(directNames) && directNames.length) return directNames.join(", ");

  const geoBroadcast = competition?.geoBroadcasts?.[0];
  if (geoBroadcast?.media?.shortName) return geoBroadcast.media.shortName;
  if (geoBroadcast?.media?.name) return geoBroadcast.media.name;

  return "";
}

function getStatusText(event) {
  const competitionStatus = getCompetition(event)?.status?.type || {};
  const eventStatus = event?.status?.type || {};
  return [competitionStatus.detail, competitionStatus.shortDetail, eventStatus.detail, eventStatus.shortDetail]
    .filter(Boolean)
    .join(" ");
}

function hasExplicitTbdWindow(event) {
  const text = getStatusText(event).toLowerCase();
  if (!text) return false;
  return /\btbd\b/.test(text) || /flex game/i.test(text);
}

function getOpponentSlug(opponent) {
  const teamId = String(opponent?.team?.id || "").trim();
  if (teamId && teamIdToSlug.has(teamId)) {
    return teamIdToSlug.get(teamId);
  }

  const candidates = [
    opponent?.team?.displayName,
    opponent?.team?.shortDisplayName,
    opponent?.team?.name,
    opponent?.team?.location && opponent?.team?.name
      ? `${opponent.team.location} ${opponent.team.name}`
      : "",
    opponent?.team?.slug,
    opponent?.team?.abbreviation,
  ];

  for (const value of candidates) {
    const normalized = normalizeKey(value);
    if (normalized && teamNameToSlug.has(normalized)) {
      return teamNameToSlug.get(normalized);
    }
  }

  throw new Error(`Could not map opponent to local slug: ${JSON.stringify(candidates.filter(Boolean))}`);
}

function buildYouTubeSummaryUrl(team, opponent, homeAway) {
  const teamName = team.data.identity?.teamName || team.config.teamName || team.slug;
  const opponentName =
    opponent?.data?.identity?.teamName || opponent?.config?.teamName || opponent?.data?.identity?.shortName || "Opponent";
  const matchup = homeAway === "home" ? `${teamName} vs ${opponentName}` : `${teamName} at ${opponentName}`;
  return `https://www.youtube.com/results?search_query=${encodeURIComponent(`${SEASON_YEAR} ${matchup} highlights`)}`;
}

function cloneGame(game) {
  return {
    ...game,
    stats: { ...(game.stats || {}) },
    links: { ...(game.links || {}) },
  };
}

function hasFirmScheduleWindow(game) {
  const date = String(game?.date || game?.displayDate || "").trim().toLowerCase();
  const day = String(game?.day || "").trim().toLowerCase();
  const time = String(game?.time || "").trim().toLowerCase();
  return Boolean(date && date !== "tbd" && day && day !== "day tbd" && time && time !== "tbd");
}

function parseScheduleGame(team, event, index) {
  const competition = getCompetition(event);
  const competitors = getCompetitors(event);
  const currentTeam = competitors.find(
    (competitor) => String(competitor?.team?.id || "").trim() === String(team.config.espnTeamId || "").trim(),
  );
  if (!currentTeam) return null;

  const opponentCompetitor = competitors.find((competitor) => competitor !== currentTeam);
  if (!opponentCompetitor) return null;

  const opponentSlug = getOpponentSlug(opponentCompetitor);
  const opponentTeam = teamBySlug.get(opponentSlug);
  const homeAway = String(currentTeam?.homeAway || "").toLowerCase() === "home" ? "home" : "away";
  const hasTbdWindow = hasExplicitTbdWindow(event);
  const rawDate = hasTbdWindow ? "" : String(competition?.date || event?.date || "").trim();
  const validDate = toValidDate(rawDate);
  const broadcast = getBroadcastLabel(competition);
  const detail =
    competition?.status?.type?.detail ||
    competition?.status?.type?.shortDetail ||
    event?.status?.type?.detail ||
    event?.status?.type?.shortDetail ||
    "";

  const game = {
    id: `${SEASON_YEAR}-${team.slug}-${String(index + 1).padStart(2, "0")}-${opponentSlug}`,
    season: SEASON_YEAR,
    date: validDate ? rawDate : null,
    displayDate: validDate ? formatDisplayDate(validDate) : "TBD",
    day: validDate ? formatDisplayDay(validDate) : "Day TBD",
    time: validDate ? formatDisplayTime(validDate) : "TBD",
    round: getEventWeekLabel(event, index),
    competition: "Regular Season",
    opponent: opponentTeam?.data?.identity?.shortName || opponentCompetitor?.team?.shortDisplayName || "Opponent",
    opponentSlug,
    opponentCode:
      opponentCompetitor?.team?.abbreviation ||
      String(opponentTeam?.config?.espnSlug || opponentSlug || "")
        .slice(0, 3)
        .toUpperCase(),
    homeAway,
    location: homeAway === "home" ? "Home" : "Away",
    result: "Scheduled",
    teamScore: null,
    opponentScore: null,
    overtime: false,
    isPlayoff: false,
    stadium: competition?.venue?.fullName || null,
    broadcast: broadcast || null,
    stats: {},
    links: {
      youtubeSummary: buildYouTubeSummaryUrl(team, opponentTeam, homeAway),
      ...(broadcast ? { broadcast } : {}),
      ...(event?.id ? { recap: `https://www.espn.com/nfl/game/_/gameId/${encodeURIComponent(event.id)}` } : {}),
    },
    detail: detail || null,
  };

  if (!validDate) {
    game.stadium = game.stadium || null;
  }

  return game;
}

function buildSourceNote(games) {
  const releasedGames = games.filter(hasFirmScheduleWindow).length;
  const remainingGames = Math.max(games.length - releasedGames, 0);

  if (!releasedGames) {
    return {
      status: "waiting-for-dates",
      note:
        "2026 opponents are official. Dates, kickoff times, scores, final stats, and video summaries will update once the NFL schedule and completed games are available.",
    };
  }

  if (remainingGames > 0) {
    return {
      status: "released-schedule-flex-pending",
      note: `Official 2026 schedule is live. ${releasedGames} of ${games.length} games have published date and kickoff windows, while ${remainingGames} flex or TBD slots will keep updating as ESPN finalizes them.`,
    };
  }

  return {
    status: "released-schedule",
    note:
      "Official 2026 schedule is live. Exact dates, kickoff windows, and stadiums are now loaded from ESPN. Scores, final stats, and video summaries will update after each game is played.",
  };
}

function ensureSeasonRecord(team) {
  const season = (team.data.seasons || []).find((entry) => Number(entry.year) === SEASON_YEAR);
  if (!season) {
    throw new Error(`Team ${team.slug} does not have a season ${SEASON_YEAR} shell to update.`);
  }
  return season;
}

async function updateTeam(team) {
  const schedulePayload = await fetchJson(scheduleUrl(team.config.espnTeamId));
  const seasonGames = extractEvents(schedulePayload)
    .map((event, index) => parseScheduleGame(team, event, index))
    .filter(Boolean);

  if (!seasonGames.length) {
    throw new Error(`No ${SEASON_YEAR} regular-season games returned for ${team.slug}.`);
  }

  const season = ensureSeasonRecord(team);
  const sourceInfo = buildSourceNote(seasonGames);

  team.data.games = (team.data.games || []).filter((game) => Number(game.season) !== SEASON_YEAR);
  team.data.games.push(...seasonGames.map(cloneGame));

  season.games = seasonGames.map(cloneGame);
  season.sources = {
    ...(season.sources || {}),
    nflOpponents: {
      url: NFL_OPPONENT_SOURCE,
      status: "official-opponents",
    },
    espnSchedule: {
      ...((season.sources && season.sources.espnSchedule) || {}),
      url: scheduleUrl(team.config.espnTeamId),
      pageUrl:
        season.sources?.espnSchedule?.url ||
        team.config.externalLinks?.espn?.replace(/\/season\/\d+/i, `/season/${SEASON_YEAR}`) ||
        `https://www.espn.com/nfl/team/schedule/_/name/${team.config.espnSlug}/season/${SEASON_YEAR}`,
      status: sourceInfo.status,
      syncedAt: new Date().toISOString(),
    },
    note: sourceInfo.note,
  };

  writeJson(team.filePath, team.data);
  syncBrowserData(team.slug, team.data);

  const releasedGames = seasonGames.filter(hasFirmScheduleWindow).length;
  const remainingGames = Math.max(seasonGames.length - releasedGames, 0);
  return `${team.slug}: ${releasedGames}/${seasonGames.length} exact windows${remainingGames ? `, ${remainingGames} TBD` : ""}`;
}

async function main() {
  const summary = [];
  for (const team of teamContexts) {
    summary.push(await updateTeam(team));
  }

  console.log(`Updated ${teamContexts.length} teams with released ${SEASON_YEAR} schedule data.`);
  console.log(`Source hub: ${ESPN_SCHEDULE_HUB_URL}`);
  console.log(summary.join("\n"));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
