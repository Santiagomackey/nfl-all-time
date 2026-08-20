import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve("C:/Users/tomas/OneDrive/Documents/New project/nfl_all_time");
const TEAMS_DIR = path.join(ROOT, "teams");
const DATA_DIR = path.join(ROOT, "data");

const TEAM_CONNECTIONS = [
  { slug: "49ers", teamName: "San Francisco 49ers", indexPage: "49ers.html", databasePage: "49ersdatabase.html", aliases: [] },
  { slug: "bears", teamName: "Chicago Bears", indexPage: "bears.html", databasePage: "bearsdatabase.html", aliases: ["bearssdatabase.html"] },
  { slug: "bengals", teamName: "Cincinnati Bengals", indexPage: "bengals.html", databasePage: "bengalsdatabase.html", aliases: [] },
  { slug: "bills", teamName: "Buffalo Bills", indexPage: "bills.html", databasePage: "billsdatabase.html", aliases: [] },
  { slug: "broncos", teamName: "Denver Broncos", indexPage: "broncos.html", databasePage: "broncosdatabase.html", aliases: [] },
  { slug: "browns", teamName: "Cleveland Browns", indexPage: "browns.html", databasePage: "brownsdatabase.html", aliases: [] },
  { slug: "buccaneers", teamName: "Tampa Bay Buccaneers", indexPage: "buccaneers.html", databasePage: "buccaneersdatabase.html", aliases: [] },
  { slug: "cardinals", teamName: "Arizona Cardinals", indexPage: "cardinals.html", databasePage: "cardinals.html", aliases: ["cardinalsdatabase.html"] },
  { slug: "chargers", teamName: "Los Angeles Chargers", indexPage: "chargers.html", databasePage: "chargersdatabase.html", aliases: ["chartgersdatabase.html"] },
  { slug: "chiefs", teamName: "Kansas City Chiefs", indexPage: "chiefs.html", databasePage: "chiefsdatabase.html", aliases: [] },
  { slug: "colts", teamName: "Indianapolis Colts", indexPage: "colts.html", databasePage: "coltsdatabase.html", aliases: [] },
  { slug: "commanders", teamName: "Washington Commanders", indexPage: "commanders.html", databasePage: "commandersdatabase.html", aliases: [] },
  { slug: "cowboys", teamName: "Dallas Cowboys", indexPage: "cowboys.html", databasePage: "cowboysdatabase.html", aliases: ["cowboyssdatabase.html"] },
  { slug: "dolphins", teamName: "Miami Dolphins", indexPage: "dolphins.html", databasePage: "dolphinsdatabase.html", aliases: [] },
  { slug: "eagles", teamName: "Philadelphia Eagles", indexPage: "eagles.html", databasePage: "eaglesdatabase.html", aliases: [] },
  { slug: "falcons", teamName: "Atlanta Falcons", indexPage: "falcons.html", databasePage: "falconsdatabase.html", aliases: [] },
  { slug: "giants", teamName: "New York Giants", indexPage: "giants.html", databasePage: "giantsdatabase.html", aliases: [] },
  { slug: "jaguars", teamName: "Jacksonville Jaguars", indexPage: "jaguars.html", databasePage: "jaguarsdatabase.html", aliases: [] },
  { slug: "jets", teamName: "New York Jets", indexPage: "jets.html", databasePage: "jetsdatabase.html", aliases: [] },
  { slug: "lions", teamName: "Detroit Lions", indexPage: "lions.html", databasePage: "lionsdatabase.html", aliases: ["lionssdatabase.html"] },
  { slug: "packers", teamName: "Green Bay Packers", indexPage: "packers.html", databasePage: "packersdatabase.html", aliases: [] },
  { slug: "panthers", teamName: "Carolina Panthers", indexPage: "panthers.html", databasePage: "panthersdatabase.html", aliases: [] },
  { slug: "patriots", teamName: "New England Patriots", indexPage: "patriots.html", databasePage: "patriots.html", aliases: ["patriotsdatabase.html"] },
  { slug: "raiders", teamName: "Las Vegas Raiders", indexPage: "raiders.html", databasePage: "raidersdatabase.html", aliases: [] },
  { slug: "rams", teamName: "Los Angeles Rams", indexPage: "rams.html", databasePage: "rams.html", aliases: ["ramsdatabase.html"] },
  { slug: "ravens", teamName: "Baltimore Ravens", indexPage: "ravens.html", databasePage: "ravensdatabase.html", aliases: [] },
  { slug: "saints", teamName: "New Orleans Saints", indexPage: "saints.html", databasePage: "saintsdatabase.html", aliases: [] },
  { slug: "seahawks", teamName: "Seattle Seahawks", indexPage: "seahawks.html", databasePage: "seahawksdatabase.html", aliases: [] },
  { slug: "steelers", teamName: "Pittsburgh Steelers", indexPage: "steelers.html", databasePage: "steelersdatabase.html", aliases: [] },
  { slug: "texans", teamName: "Houston Texans", indexPage: "texans.html", databasePage: "texansdatabase.html", aliases: [] },
  { slug: "titans", teamName: "Tennessee Titans", indexPage: "titans.html", databasePage: "titansdatabase.html", aliases: [] },
  { slug: "vikings", teamName: "Minnesota Vikings", indexPage: "vikings.html", databasePage: "vikingsdatabase.html", aliases: [] }
];

function assertExists(relativeFile) {
  const filePath = path.join(TEAMS_DIR, relativeFile);
  if (!fs.existsSync(filePath)) {
    throw new Error(`Missing expected team page: ${relativeFile}`);
  }
}

function aliasHtml(targetFile, title) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="0; url=${targetFile}">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${title}</title>
<script>window.location.replace(${JSON.stringify(targetFile)});</script>
</head>
<body>
<p>Redirecting to <a href="${targetFile}">${targetFile}</a>…</p>
</body>
</html>
`;
}

const routing = TEAM_CONNECTIONS.map((team) => {
  assertExists(team.indexPage);
  assertExists(team.databasePage);
  return {
    slug: team.slug,
    teamName: team.teamName,
    indexPage: `teams/${team.indexPage}`,
    databasePage: `teams/${team.databasePage}`,
    dataFile: `data/${team.slug}.json`,
    aliases: team.aliases.map((alias) => `teams/${alias}`)
  };
});

for (const team of TEAM_CONNECTIONS) {
  for (const alias of team.aliases) {
    fs.writeFileSync(
      path.join(TEAMS_DIR, alias),
      aliasHtml(team.databasePage, `${team.teamName} Database Redirect`)
    );
  }
}

fs.writeFileSync(
  path.join(DATA_DIR, "team-page-routing.json"),
  JSON.stringify({ schemaVersion: "1.0.0", teams: routing }, null, 2)
);

console.log(`Connected ${routing.length} team routes and wrote alias pages.`);
