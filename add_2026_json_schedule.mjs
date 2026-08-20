import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(__dirname, "data");
const browserDir = path.join(dataDir, "browser");

const NFL_OPPONENT_SOURCE =
  "https://operations.nfl.com/updates/football-ops/2026-opponents-determined/";

const teams = {
  "49ers": { full: "San Francisco 49ers", short: "49ers", abbr: "SF" },
  bears: { full: "Chicago Bears", short: "Bears", abbr: "CHI" },
  bengals: { full: "Cincinnati Bengals", short: "Bengals", abbr: "CIN" },
  bills: { full: "Buffalo Bills", short: "Bills", abbr: "BUF" },
  broncos: { full: "Denver Broncos", short: "Broncos", abbr: "DEN" },
  browns: { full: "Cleveland Browns", short: "Browns", abbr: "CLE" },
  buccaneers: { full: "Tampa Bay Buccaneers", short: "Buccaneers", abbr: "TB" },
  cardinals: { full: "Arizona Cardinals", short: "Cardinals", abbr: "ARI" },
  chargers: { full: "Los Angeles Chargers", short: "Chargers", abbr: "LAC" },
  chiefs: { full: "Kansas City Chiefs", short: "Chiefs", abbr: "KC" },
  colts: { full: "Indianapolis Colts", short: "Colts", abbr: "IND" },
  commanders: { full: "Washington Commanders", short: "Commanders", abbr: "WSH" },
  cowboys: { full: "Dallas Cowboys", short: "Cowboys", abbr: "DAL" },
  dolphins: { full: "Miami Dolphins", short: "Dolphins", abbr: "MIA" },
  eagles: { full: "Philadelphia Eagles", short: "Eagles", abbr: "PHI" },
  falcons: { full: "Atlanta Falcons", short: "Falcons", abbr: "ATL" },
  giants: { full: "New York Giants", short: "Giants", abbr: "NYG" },
  jaguars: { full: "Jacksonville Jaguars", short: "Jaguars", abbr: "JAX" },
  jets: { full: "New York Jets", short: "Jets", abbr: "NYJ" },
  lions: { full: "Detroit Lions", short: "Lions", abbr: "DET" },
  packers: { full: "Green Bay Packers", short: "Packers", abbr: "GB" },
  panthers: { full: "Carolina Panthers", short: "Panthers", abbr: "CAR" },
  patriots: { full: "New England Patriots", short: "Patriots", abbr: "NE" },
  raiders: { full: "Las Vegas Raiders", short: "Raiders", abbr: "LV" },
  rams: { full: "Los Angeles Rams", short: "Rams", abbr: "LAR" },
  ravens: { full: "Baltimore Ravens", short: "Ravens", abbr: "BAL" },
  saints: { full: "New Orleans Saints", short: "Saints", abbr: "NO" },
  seahawks: { full: "Seattle Seahawks", short: "Seahawks", abbr: "SEA" },
  steelers: { full: "Pittsburgh Steelers", short: "Steelers", abbr: "PIT" },
  texans: { full: "Houston Texans", short: "Texans", abbr: "HOU" },
  titans: { full: "Tennessee Titans", short: "Titans", abbr: "TEN" },
  vikings: { full: "Minnesota Vikings", short: "Vikings", abbr: "MIN" },
};

const nameToSlug = new Map(
  Object.entries(teams).flatMap(([slug, team]) => [
    [team.full, slug],
    [team.short, slug],
  ]),
);

const aliases = {
  Arizona: "cardinals",
  Atlanta: "falcons",
  Baltimore: "ravens",
  Buffalo: "bills",
  Carolina: "panthers",
  Chicago: "bears",
  Cincinnati: "bengals",
  Cleveland: "browns",
  Dallas: "cowboys",
  Denver: "broncos",
  Detroit: "lions",
  "Green Bay": "packers",
  Houston: "texans",
  Indianapolis: "colts",
  Jacksonville: "jaguars",
  "Kansas City": "chiefs",
  "Las Vegas": "raiders",
  "L.A. Chargers": "chargers",
  "L.A. Rams": "rams",
  Miami: "dolphins",
  Minnesota: "vikings",
  "New England": "patriots",
  "New Orleans": "saints",
  "N.Y. Giants": "giants",
  "N.Y. Jets": "jets",
  Philadelphia: "eagles",
  Pittsburgh: "steelers",
  "San Francisco": "49ers",
  Seattle: "seahawks",
  "Tampa Bay": "buccaneers",
  Tennessee: "titans",
  Washington: "commanders",
};

for (const [name, slug] of Object.entries(aliases)) {
  nameToSlug.set(name, slug);
}

const divisionOrder = {
  "AFC East": ["bills", "dolphins", "jets", "patriots"],
  "AFC North": ["ravens", "bengals", "browns", "steelers"],
  "AFC South": ["texans", "colts", "jaguars", "titans"],
  "AFC West": ["broncos", "chiefs", "raiders", "chargers"],
  "NFC East": ["cowboys", "eagles", "giants", "commanders"],
  "NFC North": ["bears", "lions", "packers", "vikings"],
  "NFC South": ["buccaneers", "falcons", "panthers", "saints"],
  "NFC West": ["49ers", "cardinals", "rams", "seahawks"],
};

const opponents2026 = {
  patriots: {
    home: ["Buffalo", "Miami", "N.Y. Jets", "Denver", "Green Bay", "Las Vegas", "Minnesota", "Pittsburgh"],
    away: ["Buffalo", "Miami", "N.Y. Jets", "Chicago", "Detroit", "Jacksonville", "Kansas City", "L.A. Chargers", "Seattle"],
  },
  bills: {
    home: ["Miami", "New England", "N.Y. Jets", "Baltimore", "Chicago", "Detroit", "Kansas City", "L.A. Chargers"],
    away: ["Miami", "New England", "N.Y. Jets", "Denver", "Green Bay", "Houston", "Las Vegas", "L.A. Rams", "Minnesota"],
  },
  dolphins: {
    home: ["Buffalo", "New England", "N.Y. Jets", "Chicago", "Cincinnati", "Detroit", "Kansas City", "L.A. Chargers"],
    away: ["Buffalo", "New England", "N.Y. Jets", "Denver", "Indianapolis", "Green Bay", "Las Vegas", "Minnesota", "San Francisco"],
  },
  jets: {
    home: ["Buffalo", "Miami", "New England", "Cleveland", "Denver", "Green Bay", "Las Vegas", "Minnesota"],
    away: ["Buffalo", "Miami", "New England", "Arizona", "Chicago", "Detroit", "Kansas City", "L.A. Chargers", "Tennessee"],
  },
  steelers: {
    home: ["Baltimore", "Cincinnati", "Cleveland", "Atlanta", "Carolina", "Denver", "Houston", "Indianapolis"],
    away: ["Baltimore", "Cincinnati", "Cleveland", "Jacksonville", "New England", "New Orleans", "Philadelphia", "Tampa Bay", "Tennessee"],
  },
  ravens: {
    home: ["Cincinnati", "Cleveland", "Pittsburgh", "Jacksonville", "L.A. Chargers", "New Orleans", "Tampa Bay", "Tennessee"],
    away: ["Cincinnati", "Cleveland", "Pittsburgh", "Atlanta", "Buffalo", "Carolina", "Dallas", "Houston", "Indianapolis"],
  },
  bengals: {
    home: ["Baltimore", "Cleveland", "Pittsburgh", "Jacksonville", "Kansas City", "New Orleans", "Tampa Bay", "Tennessee"],
    away: ["Baltimore", "Cleveland", "Pittsburgh", "Atlanta", "Carolina", "Houston", "Indianapolis", "Miami", "Washington"],
  },
  browns: {
    home: ["Baltimore", "Cincinnati", "Pittsburgh", "Atlanta", "Carolina", "Houston", "Indianapolis", "Las Vegas"],
    away: ["Baltimore", "Cincinnati", "Pittsburgh", "Jacksonville", "New Orleans", "Tampa Bay", "N.Y. Giants", "N.Y. Jets", "Tennessee"],
  },
  jaguars: {
    home: ["Houston", "Indianapolis", "Tennessee", "Cleveland", "New England", "Philadelphia", "Pittsburgh", "Washington"],
    away: ["Houston", "Indianapolis", "Tennessee", "Baltimore", "Chicago", "Cincinnati", "Dallas", "Denver", "N.Y. Giants"],
  },
  texans: {
    home: ["Indianapolis", "Jacksonville", "Tennessee", "Baltimore", "Buffalo", "Cincinnati", "Dallas", "N.Y. Giants"],
    away: ["Indianapolis", "Jacksonville", "Tennessee", "Cleveland", "Green Bay", "L.A. Chargers", "Philadelphia", "Pittsburgh", "Washington"],
  },
  colts: {
    home: ["Houston", "Jacksonville", "Tennessee", "Baltimore", "Cincinnati", "Dallas", "Miami", "N.Y. Giants"],
    away: ["Houston", "Jacksonville", "Tennessee", "Cleveland", "Kansas City", "Minnesota", "Philadelphia", "Pittsburgh", "Washington"],
  },
  titans: {
    home: ["Houston", "Indianapolis", "Jacksonville", "Cleveland", "N.Y. Jets", "Philadelphia", "Pittsburgh", "Washington"],
    away: ["Houston", "Indianapolis", "Jacksonville", "Baltimore", "Cincinnati", "Dallas", "Detroit", "Las Vegas", "N.Y. Giants"],
  },
  broncos: {
    home: ["Kansas City", "Las Vegas", "L.A. Chargers", "Buffalo", "Jacksonville", "L.A. Rams", "Miami", "Seattle"],
    away: ["Kansas City", "Las Vegas", "L.A. Chargers", "Arizona", "Carolina", "New England", "N.Y. Jets", "Pittsburgh", "San Francisco"],
  },
  chargers: {
    home: ["Denver", "Kansas City", "Las Vegas", "Arizona", "Houston", "New England", "N.Y. Jets", "San Francisco"],
    away: ["Denver", "Kansas City", "Las Vegas", "Baltimore", "Buffalo", "L.A. Rams", "Miami", "Seattle", "Tampa Bay"],
  },
  chiefs: {
    home: ["Denver", "Las Vegas", "L.A. Chargers", "Arizona", "Indianapolis", "New England", "N.Y. Jets", "San Francisco"],
    away: ["Denver", "Las Vegas", "L.A. Chargers", "Atlanta", "Buffalo", "Cincinnati", "L.A. Rams", "Miami", "Seattle"],
  },
  raiders: {
    home: ["Denver", "Kansas City", "L.A. Chargers", "Buffalo", "L.A. Rams", "Miami", "Seattle", "Tennessee"],
    away: ["Denver", "Kansas City", "L.A. Chargers", "Arizona", "Cleveland", "New England", "New Orleans", "N.Y. Jets", "San Francisco"],
  },
  eagles: {
    home: ["Dallas", "N.Y. Giants", "Washington", "Carolina", "Houston", "Indianapolis", "L.A. Rams", "Pittsburgh", "Seattle"],
    away: ["Dallas", "N.Y. Giants", "Washington", "Arizona", "Chicago", "Jacksonville", "San Francisco", "Tennessee"],
  },
  cowboys: {
    home: ["N.Y. Giants", "Philadelphia", "Washington", "Arizona", "Baltimore", "Jacksonville", "San Francisco", "Tampa Bay", "Tennessee"],
    away: ["N.Y. Giants", "Philadelphia", "Washington", "Green Bay", "Houston", "Indianapolis", "L.A. Rams", "Seattle"],
  },
  commanders: {
    home: ["Dallas", "N.Y. Giants", "Philadelphia", "Atlanta", "Cincinnati", "Houston", "Indianapolis", "L.A. Rams", "Seattle"],
    away: ["Dallas", "N.Y. Giants", "Philadelphia", "Arizona", "Jacksonville", "Minnesota", "San Francisco", "Tennessee"],
  },
  giants: {
    home: ["Dallas", "Philadelphia", "Washington", "Arizona", "Cleveland", "Jacksonville", "New Orleans", "San Francisco", "Tennessee"],
    away: ["Dallas", "Philadelphia", "Washington", "Detroit", "Houston", "Indianapolis", "L.A. Rams", "Seattle"],
  },
  bears: {
    home: ["Detroit", "Green Bay", "Minnesota", "Jacksonville", "New England", "New Orleans", "N.Y. Jets", "Philadelphia", "Tampa Bay"],
    away: ["Detroit", "Green Bay", "Minnesota", "Atlanta", "Buffalo", "Carolina", "Miami", "Seattle"],
  },
  packers: {
    home: ["Chicago", "Detroit", "Minnesota", "Atlanta", "Buffalo", "Carolina", "Dallas", "Houston", "Miami"],
    away: ["Chicago", "Detroit", "Minnesota", "L.A. Rams", "New England", "New Orleans", "N.Y. Jets", "Tampa Bay"],
  },
  vikings: {
    home: ["Chicago", "Detroit", "Green Bay", "Atlanta", "Buffalo", "Carolina", "Indianapolis", "Miami", "Washington"],
    away: ["Chicago", "Detroit", "Green Bay", "New England", "New Orleans", "N.Y. Jets", "San Francisco", "Tampa Bay"],
  },
  lions: {
    home: ["Chicago", "Green Bay", "Minnesota", "New England", "New Orleans", "N.Y. Giants", "N.Y. Jets", "Tampa Bay", "Tennessee"],
    away: ["Chicago", "Green Bay", "Minnesota", "Arizona", "Atlanta", "Buffalo", "Carolina", "Miami"],
  },
  panthers: {
    home: ["Atlanta", "New Orleans", "Tampa Bay", "Baltimore", "Chicago", "Cincinnati", "Denver", "Detroit", "Seattle"],
    away: ["Atlanta", "New Orleans", "Tampa Bay", "Cleveland", "Green Bay", "Minnesota", "Philadelphia", "Pittsburgh"],
  },
  buccaneers: {
    home: ["Atlanta", "Carolina", "New Orleans", "Cleveland", "Green Bay", "L.A. Chargers", "L.A. Rams", "Minnesota", "Pittsburgh"],
    away: ["Atlanta", "Carolina", "New Orleans", "Baltimore", "Chicago", "Cincinnati", "Dallas", "Detroit"],
  },
  falcons: {
    home: ["Carolina", "New Orleans", "Tampa Bay", "Baltimore", "Chicago", "Cincinnati", "Detroit", "Kansas City", "San Francisco"],
    away: ["Carolina", "New Orleans", "Tampa Bay", "Cleveland", "Green Bay", "Minnesota", "Pittsburgh", "Washington"],
  },
  saints: {
    home: ["Atlanta", "Carolina", "Tampa Bay", "Arizona", "Cleveland", "Green Bay", "Las Vegas", "Minnesota", "Pittsburgh"],
    away: ["Atlanta", "Carolina", "Tampa Bay", "Baltimore", "Chicago", "Cincinnati", "Detroit", "N.Y. Giants"],
  },
  seahawks: {
    home: ["Arizona", "L.A. Rams", "San Francisco", "Chicago", "Dallas", "Kansas City", "L.A. Chargers", "New England", "N.Y. Giants"],
    away: ["Arizona", "L.A. Rams", "San Francisco", "Carolina", "Denver", "Las Vegas", "Philadelphia", "Washington"],
  },
  rams: {
    home: ["Arizona", "San Francisco", "Seattle", "Buffalo", "Dallas", "Green Bay", "Kansas City", "L.A. Chargers", "N.Y. Giants"],
    away: ["Arizona", "San Francisco", "Seattle", "Denver", "Las Vegas", "Philadelphia", "Tampa Bay", "Washington"],
  },
  "49ers": {
    home: ["Arizona", "L.A. Rams", "Seattle", "Denver", "Las Vegas", "Miami", "Minnesota", "Philadelphia", "Washington"],
    away: ["Arizona", "L.A. Rams", "Seattle", "Atlanta", "Dallas", "Kansas City", "L.A. Chargers", "N.Y. Giants"],
  },
  cardinals: {
    home: ["L.A. Rams", "San Francisco", "Seattle", "Denver", "Detroit", "Las Vegas", "N.Y. Jets", "Philadelphia", "Washington"],
    away: ["L.A. Rams", "San Francisco", "Seattle", "Dallas", "Kansas City", "L.A. Chargers", "New Orleans", "N.Y. Giants"],
  },
};

function requireSlug(name) {
  const slug = nameToSlug.get(name);
  if (!slug) throw new Error(`Unknown team name: ${name}`);
  return slug;
}

function getLastSeason(data) {
  return [...(data.seasons || [])]
    .filter((season) => Number(season.year) < 2026)
    .sort((a, b) => Number(b.year) - Number(a.year))[0];
}

function getDivisionStandings(data) {
  const division = data.identity?.division || "";
  return (divisionOrder[division] || [data.slug]).map((slug) => ({
    team: teams[slug]?.full || slug,
    wins: 0,
    losses: 0,
    ties: 0,
    pct: 0,
  }));
}

function createSeason(data) {
  const lastSeason = getLastSeason(data) || {};
  const espnScheduleUrl = lastSeason.sources?.espnSchedule?.url
    ? String(lastSeason.sources.espnSchedule.url).replace(/season\/\d+/, "season/2026")
    : `https://www.espn.com/nfl/team/schedule/_/name/${teams[data.slug].abbr.toLowerCase()}/season/2026`;

  return {
    year: 2026,
    record: "0-0",
    wins: 0,
    losses: 0,
    ties: 0,
    coach: lastSeason.coach ?? null,
    quarterback: lastSeason.quarterback ?? null,
    finish: "TBD",
    division: data.identity?.division || null,
    divisionRank: null,
    playoffResult: "Pending",
    notableSeason: false,
    teamStats: {
      GP: 0,
      PTS: 0,
      YDS: 0,
      PLY: 0,
      AVG: 0,
      "RUSH YDS": 0,
      "RUSH ATT": 0,
      "RUSH AVG": 0,
      "PASS YDS": 0,
      "PASS ATT": 0,
      "PASS AVG": 0,
      SCK: 0,
      SCKY: 0,
      "1DWN": 0,
      "RUSH 1DWN": 0,
      "PASS 1DWN": 0,
      "PEN 1DWN": 0,
      PEN: 0,
      "PEN YDS": 0,
    },
    leaders: [],
    standings: getDivisionStandings(data),
    sources: {
      nflOpponents: {
        url: NFL_OPPONENT_SOURCE,
        status: "official-opponents",
      },
      espnSchedule: {
        url: espnScheduleUrl,
        status: "waiting-for-dates",
      },
      note:
        "2026 opponents are official. Dates, kickoff times, scores, final stats, and video summaries will update once the NFL schedule and completed games are available.",
    },
  };
}

function createGame(data, name, homeAway, index) {
  const opponentSlug = requireSlug(name);
  const opponent = teams[opponentSlug];
  const team = teams[data.slug];
  const matchup =
    homeAway === "home"
      ? `${team.full} vs ${opponent.full}`
      : `${team.full} at ${opponent.full}`;
  return {
    id: `2026-${data.slug}-${String(index + 1).padStart(2, "0")}-${opponentSlug}`,
    season: 2026,
    date: null,
    displayDate: "TBD",
    round: `Game ${index + 1}`,
    competition: "Regular Season",
    opponent: opponent.short,
    opponentSlug,
    homeAway,
    location: homeAway === "home" ? "Home" : "Away",
    result: "Scheduled",
    teamScore: null,
    opponentScore: null,
    overtime: false,
    isPlayoff: false,
    stadium: null,
    stats: {},
    links: {
      youtubeSummary: `https://www.youtube.com/results?search_query=${encodeURIComponent(
        `2026 ${matchup} highlights`,
      )}`,
    },
    detail: null,
  };
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

const touched = [];
for (const slug of Object.keys(teams).sort()) {
  const schedule = opponents2026[slug];
  if (!schedule) throw new Error(`Missing 2026 schedule for ${slug}`);
  const filePath = path.join(dataDir, `${slug}.json`);
  const data = JSON.parse(fs.readFileSync(filePath, "utf8"));

  data.games = (data.games || []).filter((game) => Number(game.season) !== 2026);
  const homeGames = schedule.home.map((name, index) => createGame(data, name, "home", index));
  const awayGames = schedule.away.map((name, index) =>
    createGame(data, name, "away", schedule.home.length + index),
  );
  const seasonGames = [...homeGames, ...awayGames];
  data.games.push(...seasonGames);

  const season2026 = createSeason(data);
  season2026.games = seasonGames;
  data.seasons = (data.seasons || []).filter((season) => Number(season.year) !== 2026);
  data.seasons.push(season2026);
  data.seasons.sort((a, b) => Number(a.year) - Number(b.year));

  fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + "\n", "utf8");
  syncBrowserData(slug, data);
  touched.push(`${slug}: ${seasonGames.length}`);
}

console.log(`Updated ${touched.length} teams with 2026 seasons and scheduled games.`);
console.log(touched.join("\n"));
