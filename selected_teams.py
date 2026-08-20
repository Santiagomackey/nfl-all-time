from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import (
    DATA_DIR,
    TEAMS_DIR,
    enrich_bundles_for_matchups,
    load_bundle_from_data_file,
    load_existing_render_bundles,
    load_support_enrichment_bundles,
    refresh_bundle_game_stats,
    scrape_team_dataset,
    write_bundle,
    write_data_bundle,
    write_team_html,
)

SELECTED_TEAM_SLUGS = ["patriots", "rams"]


def _collect_scraped_bundles(refresh_playoff_stats: bool = False) -> dict[str, dict]:
    bundles: dict[str, dict] = {}
    for slug in SELECTED_TEAM_SLUGS:
        bundle = scrape_team_dataset(slug)
        if refresh_playoff_stats:
            refresh_bundle_game_stats(slug, bundle)
        bundles[slug] = bundle
    return bundles


def _collect_existing_bundles(refresh_playoff_stats: bool = False) -> dict[str, dict]:
    bundles: dict[str, dict] = {}
    for slug in SELECTED_TEAM_SLUGS:
        bundle = load_bundle_from_data_file(slug)
        if refresh_playoff_stats:
            refresh_bundle_game_stats(slug, bundle)
        bundles[slug] = bundle
    return bundles


def _enrich_selected_bundles(
    bundles: dict[str, dict],
    support_scrape: bool = False,
    refresh_playoff_stats: bool = False,
) -> dict[str, dict]:
    enrichment_bundles = {**load_existing_render_bundles(set(SELECTED_TEAM_SLUGS)), **bundles}
    if support_scrape:
        enrichment_bundles.update(
            load_support_enrichment_bundles(set(SELECTED_TEAM_SLUGS), refresh_playoff_stats=refresh_playoff_stats)
        )
    enrich_bundles_for_matchups(enrichment_bundles)
    return bundles


def scrape_selected_teams(support_scrape: bool = False, refresh_playoff_stats: bool = False) -> list[tuple[str, Path]]:
    bundles = _collect_scraped_bundles(refresh_playoff_stats=refresh_playoff_stats)
    _enrich_selected_bundles(bundles, support_scrape=support_scrape, refresh_playoff_stats=refresh_playoff_stats)
    results: list[tuple[str, Path]] = []
    for slug in SELECTED_TEAM_SLUGS:
        results.append((slug, write_data_bundle(slug, bundles[slug])))
    return results


def render_selected_teams(support_scrape: bool = False, refresh_playoff_stats: bool = False) -> list[tuple[str, Path]]:
    bundles = _collect_existing_bundles(refresh_playoff_stats=refresh_playoff_stats)
    _enrich_selected_bundles(bundles, support_scrape=support_scrape, refresh_playoff_stats=refresh_playoff_stats)
    results: list[tuple[str, Path]] = []
    for slug in SELECTED_TEAM_SLUGS:
        results.append((slug, write_team_html(slug, bundles[slug])))
    return results


def generate_selected_teams(support_scrape: bool = False, refresh_playoff_stats: bool = False) -> list[tuple[str, Path, Path]]:
    bundles = _collect_scraped_bundles(refresh_playoff_stats=refresh_playoff_stats)
    _enrich_selected_bundles(bundles, support_scrape=support_scrape, refresh_playoff_stats=refresh_playoff_stats)
    results: list[tuple[str, Path, Path]] = []
    for slug in SELECTED_TEAM_SLUGS:
        results.append((slug, *write_bundle(slug, bundles[slug])))
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Patriots and Rams all-time database pages from the Ravens template.")
    parser.add_argument("--scrape-only", action="store_true", help="Only scrape and write data bundles for Patriots and Rams.")
    parser.add_argument("--render-only", action="store_true", help="Only render Patriots and Rams HTML files from existing data bundles.")
    parser.add_argument(
        "--support-scrape",
        action="store_true",
        help="Also load Ravens and Eagles as support-only enrichment sources for matchup context.",
    )
    parser.add_argument(
        "--refresh-playoff-stats",
        action="store_true",
        help="Refresh per-game stat fields from richer StatMuse log queries before writing outputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.scrape_only and args.render_only:
        raise SystemExit("Use either --scrape-only or --render-only, not both.")
    if args.scrape_only:
        for slug, data_path in scrape_selected_teams(
            support_scrape=args.support_scrape,
            refresh_playoff_stats=args.refresh_playoff_stats,
        ):
            print(f"scraped {slug}: {data_path}")
        return 0
    if args.render_only:
        for slug, html_path in render_selected_teams(
            support_scrape=args.support_scrape,
            refresh_playoff_stats=args.refresh_playoff_stats,
        ):
            print(f"rendered {slug}: {html_path}")
        return 0
    for slug, data_path, html_path in generate_selected_teams(
        support_scrape=args.support_scrape,
        refresh_playoff_stats=args.refresh_playoff_stats,
    ):
        print(f"generated {slug}: {data_path} | {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
