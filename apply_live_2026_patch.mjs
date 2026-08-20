import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";

const ROOT = path.resolve("C:/Users/tomas/OneDrive/Documents/New project/nfl_all_time");
const TEMPLATE_PATH = path.join(ROOT, "template.html");
const DATA_DIR = path.join(ROOT, "data");
const BROWSER_PAGES_DIR = path.join(ROOT, "data", "browser-pages");
const PATCH_PATH = path.join(ROOT, "live_2026_patch.js");
const START_MARKER = "<!-- LIVE_2026_PATCH_START -->";
const END_MARKER = "<!-- LIVE_2026_PATCH_END -->";
const ROUTE_DATA_START_MARKER = "<!-- LIVE_2026_ROUTE_DATA_START -->";
const ROUTE_DATA_END_MARKER = "<!-- LIVE_2026_ROUTE_DATA_END -->";

function buildPatchBlock() {
  const patchSource = fs.readFileSync(PATCH_PATH, "utf8").trim();
  return `${START_MARKER}\n<script>\n${patchSource}\n</script>\n${END_MARKER}`;
}

function injectPatch(html, patchBlock) {
  const existing = new RegExp(`${START_MARKER}[\\s\\S]*?${END_MARKER}`, "g");
  if (existing.test(html)) {
    return html.replace(existing, patchBlock);
  }
  return html.replace("</body>", `${patchBlock}\n\n</body>`);
}

function readRouteTeamData(slug) {
  const filePath = path.join(DATA_DIR, `${slug}.json`);
  if (!fs.existsSync(filePath)) return null;
  const data = JSON.parse(fs.readFileSync(filePath, "utf8"));
  return {
    slug: data.slug || slug,
    identity: data.identity || {},
    seasons: (data.seasons || []).filter((season) => Number(season.year) === 2026),
    games: (data.games || []).filter((game) => Number(game.season) === 2026),
  };
}

function injectRouteTeamData(html, slug) {
  const data = readRouteTeamData(slug);
  if (!data) return html;
  const payload = JSON.stringify(data).replace(/</g, "\\u003c");
  const block = `${ROUTE_DATA_START_MARKER}\n<script>window.__NFL_ROUTE_TEAM_DATA__=${payload};</script>\n${ROUTE_DATA_END_MARKER}`;
  const existing = new RegExp(`${ROUTE_DATA_START_MARKER}[\\s\\S]*?${ROUTE_DATA_END_MARKER}`, "g");
  if (existing.test(html)) {
    return html.replace(existing, block);
  }
  return html.includes("</head>")
    ? html.replace("</head>", `${block}\n</head>`)
    : `${block}\n${html}`;
}

function encodeBrowserPage(slug, html) {
  return `window.__NFL_RENDERED_TEAM_PAGES__ = window.__NFL_RENDERED_TEAM_PAGES__ || {}; window.__NFL_RENDERED_TEAM_PAGES__[${JSON.stringify(slug)}] = ${JSON.stringify(html)};\n`;
}

function readBrowserPageHtml(filePath, slug) {
  const source = fs.readFileSync(filePath, "utf8");
  const sandbox = { window: {} };
  vm.runInNewContext(source, sandbox, { filename: filePath });
  const html = sandbox.window.__NFL_RENDERED_TEAM_PAGES__?.[slug];
  if (typeof html !== "string") {
    throw new Error(`Could not decode rendered HTML for ${slug}`);
  }
  return html;
}

const patchBlock = buildPatchBlock();

const templateHtml = fs.readFileSync(TEMPLATE_PATH, "utf8");
fs.writeFileSync(TEMPLATE_PATH, injectPatch(injectRouteTeamData(templateHtml, "ravens"), patchBlock), "utf8");

for (const entry of fs.readdirSync(BROWSER_PAGES_DIR)) {
  if (!entry.endsWith(".js")) continue;
  const slug = path.basename(entry, ".js");
  const filePath = path.join(BROWSER_PAGES_DIR, entry);
  const html = readBrowserPageHtml(filePath, slug);
  const patchedHtml = injectPatch(injectRouteTeamData(html, slug), patchBlock);
  fs.writeFileSync(filePath, encodeBrowserPage(slug, patchedHtml), "utf8");
}

console.log("Applied 2026 live-season patch to template and browser pages.");
