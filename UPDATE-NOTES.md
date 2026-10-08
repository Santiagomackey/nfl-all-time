# Packaging and card-style correction

The archive was rebuilt and verified by extracting every entry. Homepage team boxes use the rounded, colored-border flip-card styling from the supplied NFLHOMEPAGE_fixed_grid HTML. The API, complete game data, and highlight fixes remain included.

# Blitzbook 5.7

Open `index.html` through the server (`npm start` or `start_nfl_all_time.bat`). Upload the entire extracted project to the existing Vercel repository, keeping index.html, api/, data/ and the new CSS/JS files at the project root. No build step or new API key is needed. Do not upload just index.html.

## Changes

- Restrained styling: flat charcoal surfaces, simpler borders, readable text and tabular numbers, preserved franchise colors. Responsive and reduced-motion rules are included.
- All 68 original data assets are byte-for-byte unchanged. Franchise pages now hydrate all games from those assets instead of relying on prebuilt snapshots that omitted playoff games.
- Repaired malformed generated script tags and shared season renderer bindings.
- Fixed navigation initialization errors caused by inserting controls before elements belonging to a different parent.
- ESPN supports both URL-based and named requests; historical season selection is normalized; the local server now serves the API too. Added timeouts, request deduplication, short successful-response caching and retryable error responses. Failed responses are not cached.
- Fixed array-index joins between different game collections, disappearing zero stats, and stale responses overwriting newly selected game details.
- 2,490 official NFL game highlights matched by season, both franchises, and game date. ESPN calendar weeks resolve the old archive's game-number/week mismatch. Search results are never presented as verified direct videos. Renamed Washington teams share one franchise identity for video matching.
- Highlights appear in archived game details and the homepage game center. Unmatched games provide a labeled NFL-channel search. Scheduled games show a pending message.
- Windows launchers now open the current homepage.

## Validation and limits

Five API regression tests pass (`npm test`). Live upstream checks returned rosters, the current scoreboard, the 2015 postseason and a complete two-team box score. DOM execution checks found all 32 homepage cards, no homepage initialization errors, valid generated team scripts, and a working Packers 2015 game modal linking the official NFL video. The Packers page now contains all 1,551 stored games, including its two 2015 playoff games.

Full browser visual testing could not run because browser execution is restricted in the editing environment. DOM checks do not replace desktop/mobile visual QA. The site has not been deployed by this update.

Video coverage is not exhaustive, especially for 2015–2016 uploads whose metadata omits the season. No missing statistics were invented, and existing historical source data was not rewritten. ESPN availability and YouTube availability/region restrictions remain external dependencies.

The static video catalog must be refreshed to add future uploads. `scripts/build_highlights.py` documents the official-channel export command. `scripts/refresh_highlight_schedule.py` refreshes the schedule used for date matching; run it from the project root before rebuilding the catalog. No YouTube API key is used.
