const { spawnSync } = require("child_process");
const path = require("path");

const SELECTED_TEAMS = ["patriots", "rams"];
const PROJECT_ROOT = path.resolve(__dirname, "..");

function runPythonModule(moduleName, extraArgs = []) {
  const commandCandidates = [
    { command: process.env.PYTHON, prefix: [] },
    { command: "python", prefix: [] },
    { command: "py", prefix: ["-3"] },
  ].filter((candidate) => candidate.command);

  let lastError = null;
  for (const candidate of commandCandidates) {
    const result = spawnSync(
      candidate.command,
      [...candidate.prefix, "-m", moduleName, ...extraArgs],
      {
        cwd: PROJECT_ROOT,
        stdio: "inherit",
      }
    );

    if (!result.error) {
      if (result.status !== 0) {
        throw new Error(`${candidate.command} exited with status ${result.status}`);
      }
      return;
    }

    if (result.error.code !== "ENOENT") {
      throw result.error;
    }
    lastError = result.error;
  }

  throw lastError || new Error("Unable to find a Python runtime.");
}

function generateSelectedTeams(options = {}) {
  const args = [];
  if (options.supportScrape) {
    args.push("--support-scrape");
  }
  if (options.refreshPlayoffStats) {
    args.push("--refresh-playoff-stats");
  }
  runPythonModule("nfl_all_time.selected_teams", args);
}

module.exports = {
  SELECTED_TEAMS,
  generateSelectedTeams,
};

if (require.main === module) {
  generateSelectedTeams({
    supportScrape: process.argv.includes("--support-scrape"),
    refreshPlayoffStats: process.argv.includes("--refresh-playoff-stats"),
  });
}
