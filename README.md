# NFL All-Time Team Generator

This folder contains the standalone generation pipeline for the NFL all-time database pages built from the Ravens master template.

It generates:

- `data/<team>.js`
- `teams/<team>.html`

For the Patriots/Rams workflow in this project, use:

- `scraper.js`
  Scrapes and writes only `data/patriots.js` and `data/rams.js`
- `generator.js`
  Runs the full one-command workflow for only `patriots` and `rams`, writing both data bundles and standalone HTML pages

Default output excludes:

- `ravens`
- `eagles`
- `patriots`
- `rams`

Those teams stay in the catalog for rivalry lookups and source metadata, but they are not rendered unless you explicitly override that behavior.

## Structure

- `template.html`
  Ravens master template used as the layout and interaction source.
- `config.py`
  Franchise catalog, palettes, identity copy, rivalry defaults, and output targeting rules.
- `pipeline.py`
  Scraper, dataset builder, and HTML renderer.
- `generate_all.py`
  CLI entry point.
- `selected_teams.py`
  Patriots/Rams-only Python orchestration layer.
- `scraper.js`
  Node wrapper for the Patriots/Rams scrape-only workflow.
- `generator.js`
  Node wrapper for the Patriots/Rams full generation workflow.
- `cache/`
  Cached StatMuse responses.
- `data/`
  Generated JS data bundles.
- `teams/`
  Generated standalone HTML team pages.

## Data Shape

Each generated `data/<team>.js` file exports:

- `TEAM_CONFIG`
- `ALL_GAMES`
- `SEASON_EXTRA_DATA`
- `MATCH_DETAILS`
- `RIVALRY_DATA`
- `PLAYER_FEATURES_BY_SEASON`
- `FEATURED_GAMES`
- `TIMELINE_COPY`
- `TEAM_LOGO_MAP`

Notable fields included in the generated data:

- `ALL_GAMES`
  Includes `date`, `displayDate`, `opponent`, `opponentCode`, `location`, `result`, `teamScore`, `ravensScore` (template compatibility), `oppScore`, `round`, `year`, `isPlayoff`, and available box-score style stat fields.
- `SEASON_EXTRA_DATA`
  Includes `record`, `wins`, `losses`, `ties`, `division`, `division_rank`, `division_finish`, `playoff_result`, `notable_season`, standings, leaders, and source references.

## Sources

The live pipeline currently uses StatMuse as the main automated source for:

- franchise seasons
- standings
- team leaders
- game logs
- playoff round labels

ESPN and Pro Football Reference links are attached into the generated season metadata as source references.

Notes:

- ESPN pages are reachable from this environment, but are not fully season-scraped in the default run to keep generation time practical.
- Pro Football Reference is currently Cloudflare-protected from this environment, so the pipeline stores canonical PFR source links rather than live-scraping those pages here.
- When a StatMuse team landing page is missing or inconsistent, the pipeline falls back to direct StatMuse ask queries for season snapshots, leaders, and game logs.
- Historical division labels are normalized after scraping so pre-merger eras do not inherit modern division names.
- Ravens template color tokens are rewritten at render time so generated pages keep the original UI while using each franchise's own palette.

## Commands

Generate only Patriots and Rams with one command:

```bash
node nfl_all_time/generator.js
```

Scrape only the Patriots and Rams datasets:

```bash
node nfl_all_time/scraper.js
```

Render only the Patriots and Rams HTML pages from existing data:

```bash
python -m nfl_all_time.selected_teams --render-only
```

Generate one team:

```bash
python -m nfl_all_time.generate_all --team chiefs
```

Generate the full 28-team batch:

```bash
python -m nfl_all_time.generate_all
```

Resume a long batch and skip already-generated teams:

```bash
python -m nfl_all_time.generate_all --skip-existing
```

Re-render all 28 team pages from the saved data bundles without scraping again:

```bash
python -m nfl_all_time.generate_all --render-only
```

Re-render a single team page from its existing data file:

```bash
python -m nfl_all_time.generate_all --team chiefs --render-only
```

If you want the heavier support-only scrape for Ravens, Eagles, Patriots, and Rams to help fill more cross-team matchup stats, add:

```bash
python -m nfl_all_time.generate_all --render-only --support-scrape
```

Start from a specific team in batch mode:

```bash
python -m nfl_all_time.generate_all --start-from dolphins --skip-existing
```

Generate an otherwise excluded team on purpose:

```bash
python -m nfl_all_time.generate_all --team ravens --include-excluded
```

## Output Example

Sample generated files:

- `data/chiefs.js`
- `teams/chiefs.html`

## Behavior

- Reuses the Ravens layout and interactions instead of redesigning the page.
- Swaps team identity, colors, logos, copy, and franchise data at generation time.
- Preserves the premium archive feel while keeping each page team-specific through config and dataset injection.
- Uses cached source responses to make repeat runs faster.

## Known Gaps

- `49ers` seasons `1946-1949` still resolve as unavailable in this environment.
- `browns` seasons `1946-1949` still resolve as unavailable in this environment.
- `steelers` seasons `1943-1944` still resolve as unavailable in this environment.

Those seasons are left in the output with `source_unavailable: true` instead of failing the full batch.


## GitHub + Vercel Deployment

This repository has been cleaned for static deployment. The multi-gigabyte scraper cache and duplicate browser data bundles are intentionally excluded from Git.

### Production files

- `index.html` — root homepage used by Vercel.
- `teams/NFLHOMEPAGE_fixed_grid.html` — original homepage path retained for compatibility.
- `data/*.json` — 32 franchise datasets plus manifests and 2026 season data.
- `data/browser-pages/*.js` — 32 rendered franchise page assets loaded by the homepage.
- `vercel.json` — caching headers for large static data assets.

### Files intentionally not committed

- `cache/` — scraper response cache; regenerable and several gigabytes uncompressed.
- `data/browser/` — duplicate hosted-data fallback bundles; hosted HTTP deployments use the JSON files directly.
- `data/*.js` — duplicate generated data bundles; JSON is the production source on Vercel.
- `__pycache__/`, local environments, build folders, `.env*`, and `.vercel/`.

### Local preview

From this directory:

```bash
node serve_app.mjs
```

Then open `http://127.0.0.1:8765/`.

### Vercel

Import the GitHub repository in Vercel. This is a static site, so no build command or framework preset is required. The repository root is the output directory.
