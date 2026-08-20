from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HOMEPAGE = ROOT / "teams" / "NFLHOMEPAGE_fixed_grid.html"
BROWSER_PAGES_DIR = ROOT / "data" / "browser-pages"
START_MARKER = "<!-- INLINE_RENDERED_TEAM_PAGES_START -->"
END_MARKER = "<!-- INLINE_RENDERED_TEAM_PAGES_END -->"


def build_inline_block() -> str:
    parts: list[str] = [START_MARKER]
    for path in sorted(BROWSER_PAGES_DIR.glob("*.js")):
        content = path.read_text(encoding="utf-8")
        slug = path.stem
        match = re.search(
            r'window\.__NFL_RENDERED_TEAM_PAGES__\[[^\]]+\]\s*=\s*(?P<payload>"(?:\\.|[^"])*")\s*;',
            content,
            flags=re.S,
        )
        if not match:
            raise RuntimeError(f"Could not extract rendered page payload from {path}.")
        html = json.loads(match.group("payload"))
        json_payload = json.dumps(html).replace("</script>", "<\\/script>")
        parts.append(
            f'<script type="application/json" id="nfl-rendered-page-{slug}">{json_payload}</script>'
        )
    parts.append(END_MARKER)
    return "\n".join(parts)


def bundle_homepage() -> None:
    html = HOMEPAGE.read_text(encoding="utf-8")
    start = html.find(START_MARKER)
    end = html.find(END_MARKER)
    if start == -1 or end == -1 or end < start:
        raise RuntimeError("Inline rendered team page markers were not found in homepage HTML.")

    end += len(END_MARKER)
    bundled = html[:start] + build_inline_block() + html[end:]
    HOMEPAGE.write_text(bundled, encoding="utf-8")
    print(f"Bundled shareable homepage: {HOMEPAGE}")


if __name__ == "__main__":
    bundle_homepage()
