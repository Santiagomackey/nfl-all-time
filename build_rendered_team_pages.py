from __future__ import annotations

import json
import re
from pathlib import Path

from .pipeline import TEAM_CATALOG, load_bundle_from_data_file, render_team_page

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "data" / "browser-pages"


def build_team_route_map() -> dict[str, str]:
    payload: dict[str, str] = {}
    for slug, meta in TEAM_CATALOG.items():
        route = f"#team={slug}"
        payload[slug] = route
        payload[meta["short_name"].lower()] = route
        payload[meta["team_name"].lower()] = route
        payload[meta["espn_slug"].lower()] = route
    return payload


def patch_rendered_html(html: str, slug: str) -> str:
    route_map = json.dumps(build_team_route_map(), separators=(",", ":"))

    html = html.replace(
        "<head>",
        '<head>\n<base href="NFLHOMEPAGE_fixed_grid.html" target="_top">',
        1,
    )
    html = re.sub(r"const TEAM_PAGE_MAP = \{.*?\};", f"const TEAM_PAGE_MAP = {route_map};", html, count=1, flags=re.S)
    html = html.replace("new URL(page, window.location.href)", "new URL(page, document.baseURI)")
    html = html.replace("new URL('NFLHOMEPAGE_fixed_grid.html', window.location.href)", "new URL('NFLHOMEPAGE_fixed_grid.html', document.baseURI)")
    html = html.replace("</body>", "<script>window.__NFL_IFRAME_TEAM_SLUG__ = " + json.dumps(slug) + ";</script>\n</body>", 1)
    return html


def build_rendered_team_pages() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for slug in sorted(TEAM_CATALOG):
        bundle = load_bundle_from_data_file(slug)
        html = patch_rendered_html(render_team_page(slug, bundle), slug)
        target = OUTPUT_DIR / f"{slug}.js"
        payload = "window.__NFL_RENDERED_TEAM_PAGES__ = window.__NFL_RENDERED_TEAM_PAGES__ || {}; window.__NFL_RENDERED_TEAM_PAGES__[" + json.dumps(slug) + "] = " + json.dumps(html) + ";\n"
        target.write_text(payload, encoding="utf-8")
        print(f"rendered browser page asset: {target}")


if __name__ == "__main__":
    build_rendered_team_pages()
