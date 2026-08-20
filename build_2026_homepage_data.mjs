import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(__dirname, "data");
const browserDir = path.join(dataDir, "browser");
const seasonYear = 2026;
const scheduleDisplayTimeZone = "America/New_York";

const opponentSourceUrl = "https://operations.nfl.com/updates/football-ops/2026-opponents-determined/";
const releasedScheduleSourceUrl = "https://www.espn.com/nfl/schedule";

const teamFiles = fs
  .readdirSync(dataDir)
  .filter((file) => file.endsWith(".json"))
  .filter((file) => !["team.schema.json", "teams-manifest.json", "team-page-routing.json", "season-2026.json"].includes(file))
  .sort();

const teamData = teamFiles.map((file) => JSON.parse(fs.readFileSync(path.join(dataDir, file), "utf8")));
const teamBySlug = new Map(teamData.map((team) => [team.slug, team]));

function teamName(slug) {
  return teamBySlug.get(slug)?.identity?.teamName || slug;
}

function teamShort(slug) {
  return teamBySlug.get(slug)?.identity?.shortName || teamName(slug);
}

function teamDivision(slug) {
  return teamBySlug.get(slug)?.identity?.division || "";
}

function teamConference(slug) {
  return teamBySlug.get(slug)?.identity?.conference || "";
}

function toValidDate(value) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatScheduleDay(date) {
  return new Intl.DateTimeFormat("en-US", {
    timeZone: scheduleDisplayTimeZone,
    weekday: "long",
  }).format(date);
}

function formatScheduleTime(date) {
  return new Intl.DateTimeFormat("en-US", {
    timeZone: scheduleDisplayTimeZone,
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function hasReleasedMatchupWindow(game) {
  const date = String(game?.date || game?.displayDate || "").trim().toLowerCase();
  const day = String(game?.day || "").trim().toLowerCase();
  const time = String(game?.time || "").trim().toLowerCase();
  return Boolean(date && date !== "tbd" && day && day !== "day tbd" && time && time !== "tbd");
}

function buildMatchup(game, homeData) {
  const homeSlug = game.homeAway === "home" ? homeData.slug : game.opponentSlug;
  const awaySlug = game.homeAway === "home" ? game.opponentSlug : homeData.slug;
  const date = game.date || null;
  const dateObject = toValidDate(date);
  const validDate = Boolean(dateObject);

  return {
    id: `${seasonYear}-${awaySlug}-at-${homeSlug}`,
    week: game.round || "Schedule Release Pending",
    weekNumber: Number(String(game.round || "").match(/\d+/)?.[0]) || null,
    day: game.day || (validDate ? formatScheduleDay(dateObject) : "Day TBD"),
    date,
    displayDate: game.displayDate || "TBD",
    time: game.time || (validDate ? formatScheduleTime(dateObject) : "TBD"),
    awaySlug,
    awayTeam: teamName(awaySlug),
    awayShort: teamShort(awaySlug),
    homeSlug,
    homeTeam: teamName(homeSlug),
    homeShort: teamShort(homeSlug),
    stadium: game.stadium || "TBD",
    network: game.links?.broadcast || game.broadcast || "TBD",
    status: game.result === "Scheduled" || game.result === "TBD" ? "upcoming" : "final",
    statusLabel: game.result === "Scheduled" ? "Scheduled" : game.result || "TBD",
    awayScore: game.homeAway === "home" ? null : game.teamScore,
    homeScore: game.homeAway === "home" ? game.teamScore : null,
    sourceTeamSlug: homeData.slug,
  };
}

const matchupMap = new Map();
for (const team of teamData) {
  for (const game of team.games || []) {
    if (Number(game.season) !== seasonYear) continue;
    if (game.homeAway !== "home") continue;
    matchupMap.set(`${game.opponentSlug}-at-${team.slug}`, buildMatchup(game, team));
  }
}

function formatPct(wins, losses, ties) {
  const total = wins + losses + ties;
  if (!total) return ".000";
  const pct = ((wins + ties * 0.5) / total).toFixed(3);
  return pct.startsWith("0") ? pct.slice(1) : pct;
}

const standings = teamData
  .map((team) => {
    const season = (team.seasons || []).find((entry) => Number(entry.year) === seasonYear) || {};
    const wins = Number(season.wins || 0);
    const losses = Number(season.losses || 0);
    const ties = Number(season.ties || 0);
    const stats = season.teamStats || {};
    return {
      slug: team.slug,
      team: team.identity?.teamName || team.slug,
      shortName: team.identity?.shortName || team.slug,
      conference: team.identity?.conference || "",
      division: team.identity?.division || "",
      wins,
      losses,
      ties,
      record: season.record || `${wins}-${losses}${ties ? `-${ties}` : ""}`,
      pct: formatPct(wins, losses, ties),
      pointsFor: Number(stats.PTS || 0),
      pointsAgainst: Number(season.pointsAgainst || stats.PA || 0),
      streak: season.streak || "0",
      divisionRank: null,
      conferenceRank: null,
      leagueRank: null,
    };
  })
  .sort((left, right) => left.team.localeCompare(right.team));

function sortStandings(rows) {
  return rows.sort((left, right) => {
    const pctDiff = Number(`0${right.pct}`) - Number(`0${left.pct}`);
    if (pctDiff) return pctDiff;
    if (right.wins !== left.wins) return right.wins - left.wins;
    return left.team.localeCompare(right.team);
  });
}

for (const division of new Set(standings.map((row) => row.division))) {
  sortStandings(standings.filter((row) => row.division === division)).forEach((row, index) => {
    row.divisionRank = index + 1;
  });
}

for (const conference of new Set(standings.map((row) => row.conference))) {
  sortStandings(standings.filter((row) => row.conference === conference)).forEach((row, index) => {
    row.conferenceRank = index + 1;
  });
}

sortStandings([...standings]).forEach((row, index) => {
  row.leagueRank = index + 1;
});

const schedule = [...matchupMap.values()].sort((left, right) => {
  if (left.date && right.date) return String(left.date).localeCompare(String(right.date));
  if (left.weekNumber && right.weekNumber && left.weekNumber !== right.weekNumber) return left.weekNumber - right.weekNumber;
  return `${left.awayTeam} ${left.homeTeam}`.localeCompare(`${right.awayTeam} ${right.homeTeam}`);
});

const releasedScheduleCount = schedule.filter(hasReleasedMatchupWindow).length;
const remainingScheduleCount = Math.max(schedule.length - releasedScheduleCount, 0);
const scheduleStatus =
  releasedScheduleCount === 0
    ? "official-opponents-dates-pending"
    : remainingScheduleCount > 0
    ? "official-schedule-partial"
    : "official-schedule-released";
const source =
  releasedScheduleCount === 0
    ? {
        label: "NFL Operations: 2026 Opponents Determined",
        url: opponentSourceUrl,
      }
    : {
        label: "ESPN NFL 2026 Schedule",
        url: releasedScheduleSourceUrl,
      };
const notes =
  releasedScheduleCount === 0
    ? [
        "Official 2026 opponents are loaded for all 32 teams.",
        "Exact dates, kickoff times, stadium assignments, TV networks, final scores, and stats remain TBD until the NFL and live data feeds publish them.",
      ]
    : remainingScheduleCount > 0
    ? [
        `Official 2026 schedule windows are loaded for ${releasedScheduleCount} of ${schedule.length} games.`,
        `${remainingScheduleCount} flex or TBD slots remain and will keep updating as ESPN finalizes them.`,
      ]
    : [
        `Official 2026 schedule windows are loaded for all ${schedule.length} games.`,
        "Dates, kickoff times, and stadiums are now coming from ESPN's released 2026 schedule feed.",
      ];

const payload = {
  season: seasonYear,
  generatedAt: new Date().toISOString(),
  scheduleStatus,
  source,
  notes,
  summary: {
    teams: teamData.length,
    games: schedule.length,
    conferences: new Set(standings.map((row) => row.conference)).size,
    divisions: new Set(standings.map((row) => row.division)).size,
  },
  schedule,
  standings: standings.sort((left, right) => left.team.localeCompare(right.team)),
};

const json = `${JSON.stringify(payload, null, 2)}\n`;
fs.writeFileSync(path.join(dataDir, "season-2026.json"), json, "utf8");
fs.writeFileSync(path.join(browserDir, "season-2026.mjs"), `export default ${json}`, "utf8");
fs.writeFileSync(
  path.join(browserDir, "season-2026.js"),
  `window.__NFL_SEASON_2026__ = ${json}`,
  "utf8",
);

console.log(`Built 2026 homepage data: ${payload.summary.teams} teams, ${payload.summary.games} games.`);
