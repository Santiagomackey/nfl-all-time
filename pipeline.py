from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup, Tag

from .config import EXCLUDED_RENDER_SLUGS, SUPPORT_COPYRIGHT_YEAR, TARGET_TEAM_SLUGS, TEAM_CATALOG, build_team_config, team_meta

ROOT = Path(__file__).resolve().parent
TEMPLATE_PATH = ROOT / "template.html"
DATA_DIR = ROOT / "data"
TEAMS_DIR = ROOT / "teams"
CACHE_DIR = ROOT / "cache"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

TEAM_NAME_ALIASES = {
    "ARI": "Cardinals",
    "ARZ": "Cardinals",
    "ATL": "Falcons",
    "BAL": "Ravens",
    "BUF": "Bills",
    "CAR": "Panthers",
    "CHI": "Bears",
    "CIN": "Bengals",
    "CLE": "Browns",
    "CLT": "Colts",
    "DAL": "Cowboys",
    "DEN": "Broncos",
    "DET": "Lions",
    "DLT": "Chiefs",
    "GB": "Packers",
    "GNB": "Packers",
    "HOU": "Texans",
    "HTX": "Texans",
    "IND": "Colts",
    "JAC": "Jaguars",
    "JAX": "Jaguars",
    "KAN": "Chiefs",
    "KC": "Chiefs",
    "LA": "Rams",
    "LAC": "Chargers",
    "LAR": "Rams",
    "LV": "Raiders",
    "MIA": "Dolphins",
    "MIN": "Vikings",
    "NE": "Patriots",
    "NO": "Saints",
    "NOR": "Saints",
    "NYG": "Giants",
    "NYJ": "Jets",
    "OAK": "Raiders",
    "PHI": "Eagles",
    "PHX": "Cardinals",
    "PIT": "Steelers",
    "RAM": "Rams",
    "SD": "Chargers",
    "SDG": "Chargers",
    "SEA": "Seahawks",
    "SF": "49ers",
    "SFO": "49ers",
    "STL": "Rams",
    "TB": "Buccaneers",
    "TEN": "Titans",
    "WAS": "Commanders",
    "WSH": "Commanders",
}

HISTORIC_CODE_NAME_ALIASES = {
    "BOS": "Patriots",
    "CLT": "Colts",
    "DLT": "Chiefs",
    "GNB": "Packers",
    "KAN": "Chiefs",
    "LA": "Rams",
    "LAC": "Chargers",
    "LAR": "Rams",
    "LV": "Raiders",
    "NE": "Patriots",
    "NOR": "Saints",
    "NYG": "Giants",
    "NYJ": "Jets",
    "NYT": "Jets",
    "OAK": "Raiders",
    "PHX": "Cardinals",
    "RAI": "Raiders",
    "RAM": "Rams",
    "SD": "Chargers",
    "SDG": "Chargers",
    "SFO": "49ers",
    "STL": "Rams",
    "WAS": "Commanders",
}

DIVISION_HISTORY: dict[str, tuple[tuple[int, int | None, str], ...]] = {
    "49ers": ((1946, 1949, "AAFC West"), (1950, 1966, "Western Conference"), (1967, 1969, "Coastal Division"), (1970, None, "NFC West")),
    "bears": ((1920, 1932, "NFL"), (1933, 1966, "Western Conference"), (1967, 1969, "Central Division"), (1970, 2001, "NFC Central"), (2002, None, "NFC North")),
    "bengals": ((1968, 1969, "AFL West"), (1970, 2001, "AFC Central"), (2002, None, "AFC North")),
    "bills": ((1960, 1969, "AFL East"), (1970, None, "AFC East")),
    "broncos": ((1960, 1969, "AFL West"), (1970, None, "AFC West")),
    "browns": ((1946, 1949, "AAFC West"), (1950, 1966, "Eastern Conference"), (1967, 1969, "Century Division"), (1970, 1995, "AFC Central"), (1999, 2001, "AFC Central"), (2002, None, "AFC North")),
    "buccaneers": ((1976, 1976, "AFC West"), (1977, 2001, "NFC Central"), (2002, None, "NFC South")),
    "cardinals": ((1920, 1932, "NFL"), (1933, 1966, "Eastern Conference"), (1967, 1969, "Century Division"), (1970, 2001, "NFC East"), (2002, None, "NFC West")),
    "chargers": ((1960, 1969, "AFL West"), (1970, None, "AFC West")),
    "chiefs": ((1960, 1969, "AFL West"), (1970, None, "AFC West")),
    "colts": ((1953, 1966, "Western Conference"), (1967, 1969, "Coastal Division"), (1970, 2001, "AFC East"), (2002, None, "AFC South")),
    "commanders": ((1932, 1932, "NFL"), (1933, 1966, "Eastern Conference"), (1967, 1969, "Capitol Division"), (1970, None, "NFC East")),
    "cowboys": ((1960, 1966, "Eastern Conference"), (1967, 1969, "Capitol Division"), (1970, None, "NFC East")),
    "dolphins": ((1966, 1969, "AFL East"), (1970, None, "AFC East")),
    "falcons": ((1966, 1966, "Eastern Conference"), (1967, 1969, "Coastal Division"), (1970, 2001, "NFC West"), (2002, None, "NFC South")),
    "giants": ((1925, 1932, "NFL"), (1933, 1966, "Eastern Conference"), (1967, 1967, "Century Division"), (1968, 1968, "Capitol Division"), (1969, 1969, "Century Division"), (1970, None, "NFC East")),
    "jaguars": ((1995, 2001, "AFC Central"), (2002, None, "AFC South")),
    "jets": ((1960, 1969, "AFL East"), (1970, None, "AFC East")),
    "lions": ((1930, 1932, "NFL"), (1933, 1966, "Western Conference"), (1967, 1969, "Central Division"), (1970, 2001, "NFC Central"), (2002, None, "NFC North")),
    "packers": ((1921, 1932, "NFL"), (1933, 1966, "Western Conference"), (1967, 1969, "Central Division"), (1970, 2001, "NFC Central"), (2002, None, "NFC North")),
    "panthers": ((1995, 2001, "NFC West"), (2002, None, "NFC South")),
    "raiders": ((1960, 1969, "AFL West"), (1970, None, "AFC West")),
    "saints": ((1967, 1967, "Capitol Division"), (1968, 1968, "Century Division"), (1969, 1969, "Capitol Division"), (1970, 2001, "NFC West"), (2002, None, "NFC South")),
    "seahawks": ((1976, 1976, "NFC West"), (1977, 2001, "AFC West"), (2002, None, "NFC West")),
    "steelers": ((1933, 1966, "Eastern Conference"), (1967, 1969, "Century Division"), (1970, 2001, "AFC Central"), (2002, None, "AFC North")),
    "texans": ((2002, None, "AFC South"),),
    "titans": ((1960, 1969, "AFL East"), (1970, 2001, "AFC Central"), (2002, None, "AFC South")),
    "vikings": ((1961, 1966, "Western Conference"), (1967, 1969, "Central Division"), (1970, 2001, "NFC Central"), (2002, None, "NFC North")),
}


class CachedHttpClient:
    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.session = requests.Session()

    def _path(self, namespace: str, key: str) -> Path:
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        folder = self.cache_dir / namespace
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{digest}.txt"

    def get_text(self, url: str, namespace: str, key: str | None = None, timeout: int = 30, allow_error: bool = False) -> str:
        cache_path = self._path(namespace, key or url)
        if cache_path.exists():
            return cache_path.read_text(encoding="utf-8")
        try:
            response = self.session.get(url, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
            text = response.text
        except Exception as exc:
            if not allow_error:
                raise
            text = json.dumps({"error": str(exc), "url": url})
        cache_path.write_text(text, encoding="utf-8")
        return text


client = CachedHttpClient(CACHE_DIR)


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def clean_key(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]+", "", clean(value).upper())


def compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    cleaned = value.lstrip("#")
    if len(cleaned) != 6:
        raise ValueError(f"Unsupported hex color: {value}")
    return int(cleaned[0:2], 16), int(cleaned[2:4], 16), int(cleaned[4:6], 16)


def rgba_from_hex(value: str, alpha: str) -> str:
    red, green, blue = hex_to_rgb(value)
    return f"rgba({red},{green},{blue},{alpha})"


def mix_hex(base: str, overlay: str, overlay_ratio: float) -> str:
    overlay_ratio = max(0.0, min(1.0, overlay_ratio))
    base_rgb = hex_to_rgb(base)
    overlay_rgb = hex_to_rgb(overlay)
    mixed = tuple(
        round(base_channel * (1 - overlay_ratio) + overlay_channel * overlay_ratio)
        for base_channel, overlay_channel in zip(base_rgb, overlay_rgb)
    )
    return "#{:02X}{:02X}{:02X}".format(*mixed)


def relative_luminance(value: str) -> float:
    def channel_luminance(channel: int) -> float:
        normalized = channel / 255
        if normalized <= 0.03928:
            return normalized / 12.92
        return ((normalized + 0.055) / 1.055) ** 2.4

    red, green, blue = hex_to_rgb(value)
    return 0.2126 * channel_luminance(red) + 0.7152 * channel_luminance(green) + 0.0722 * channel_luminance(blue)


def replace_hex_token(text: str, old_hex: str, new_hex: str) -> str:
    return re.sub(re.escape(old_hex), new_hex, text, flags=re.I)


def replace_rgba_family(text: str, rgbs: tuple[str, ...], target_hex: str) -> str:
    updated = text
    for legacy_rgb in rgbs:
        channels = [part.strip() for part in legacy_rgb.split(",")]
        pattern = (
            r"rgba\(\s*"
            + r"\s*,\s*".join(re.escape(channel) for channel in channels)
            + r"\s*,\s*([0-9.]+)\s*\)"
        )
        updated = re.sub(pattern, lambda match: rgba_from_hex(target_hex, match.group(1)), updated, flags=re.I)
    return updated


def ordinal(value: int) -> str:
    if 10 <= value % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"


def ask_url(query: str) -> str:
    return f"https://www.statmuse.com/nfl/ask/{slugify(query)}"


def ask_soup(query: str, allow_error: bool = False) -> BeautifulSoup:
    return BeautifulSoup(client.get_text(ask_url(query), "statmuse_ask", query, allow_error=allow_error), "html.parser")


def parse_table(table: Tag | None) -> list[list[str]]:
    if not table:
        return []
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        row = [cell.get_text(" ", strip=True) for cell in tr.find_all(["th", "td"])]
        if row:
            rows.append(row)
    return rows


def find_team_season_link(display_name: str, year: int) -> tuple[str, str]:
    soup = ask_soup(f"{display_name} season in {year}")
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if href.startswith("/nfl/team/") and href.endswith(f"/{year}"):
            return "https://www.statmuse.com" + href, clean(anchor.get_text(" ", strip=True))
    raise RuntimeError(f"Could not resolve team page for {display_name} {year}")


def fetch_team_page(url: str) -> tuple[BeautifulSoup, str]:
    html = client.get_text(url, "statmuse_team_page", url)
    return BeautifulSoup(html, "html.parser"), html


def table_after_heading(soup: BeautifulSoup, heading: str) -> Tag | None:
    for h3 in soup.find_all("h3"):
        if clean(h3.get_text(" ", strip=True)) == heading:
            box = h3.find_parent("div", class_="rounded-2xl")
            return box.find("table") if box else None
    return None


def block_after_heading(soup: BeautifulSoup, heading: str) -> Tag | None:
    for h3 in soup.find_all("h3"):
        if clean(h3.get_text(" ", strip=True)) == heading:
            return h3.parent.parent.parent
    return None


def title_from_cell(cell: Tag) -> str:
    link = cell.find("a")
    if link and link.get("title"):
        return re.sub(r"^\d{4}\s+", "", clean(link["title"]))
    return clean(cell.get_text(" ", strip=True))


def parse_date_token(token: str, season_year: int) -> str:
    cleaned = clean(token)
    for day in ("Sun ", "Mon ", "Tue ", "Wed ", "Thu ", "Fri ", "Sat "):
        cleaned = cleaned.replace(day, "")
    month, day = [int(part) for part in cleaned.split("/")]
    actual_year = season_year + 1 if month <= 2 else season_year
    return f"{actual_year:04d}-{month:02d}-{day:02d}"


def parse_schedule_rows(table: Tag | None, season_year: int) -> list[dict[str, Any]]:
    if not table or not table.find("tbody"):
        return []
    rows: list[dict[str, Any]] = []
    for tr in table.find("tbody").find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 4:
            continue
        score_text = clean(cells[3].get_text(" ", strip=True))
        match = re.match(r"([WLT])\s+(\d+)-(\d+)", score_text)
        if not match:
            continue
        rows.append(
            {
                "date": parse_date_token(clean(cells[0].get_text(" ", strip=True)), season_year),
                "displayDate": clean(cells[0].get_text(" ", strip=True)),
                "opponent": title_from_cell(cells[2]),
                "location": "Home" if clean(cells[1].get_text(" ", strip=True)).lower() == "vs" else "Away",
                "result": match.group(1),
                "ravensScore": int(match.group(2)),
                "oppScore": int(match.group(3)),
            }
        )
    rows.sort(key=lambda row: row["date"])
    return rows


def extract_division_name(raw_html: str, heading_text: str) -> str | None:
    marker = f">{heading_text}</h3>"
    index = raw_html.find(marker)
    if index == -1:
        return None
    snippet = raw_html[index:index + 5000]
    match = re.search(r"sticky left-0 bg-gray-8 dark:bg-gray-3\">([^<]+)</th>", snippet)
    if match:
        text = clean(match.group(1))
        if text and text.upper() != "TEAM":
            return text
    return None


def parse_stats_table(table: Tag | None) -> dict[str, Any]:
    rows = parse_table(table)
    if len(rows) < 2:
        return {}
    stats: dict[str, Any] = {}
    for header, value in zip(rows[0][1:], rows[1][1:]):
        text = clean(value).replace(",", "")
        if not text:
            continue
        if re.fullmatch(r"-?\d+(?:\.\d+)?", text):
            number = float(text)
            stats[header] = int(number) if number.is_integer() else number
        else:
            stats[header] = value
    return stats


def parse_standings_table(table: Tag | None) -> list[dict[str, Any]]:
    rows = parse_table(table)
    if len(rows) < 2:
        return []
    headers = rows[0]
    standings: list[dict[str, Any]] = []
    for row in rows[1:]:
        if len(row) != len(headers):
            continue
        entry = dict(zip(headers, row))
        team = clean(entry.get("TEAM"))
        if not team:
            continue
        pct_text = str(entry.get("PCT") or "0")
        pct_value = float(pct_text.replace(".", "0.", 1)) if pct_text.startswith(".") else float(pct_text)
        standings.append({"team": team, "W": int(entry.get("W") or 0), "L": int(entry.get("L") or 0), "T": int(entry.get("T") or 0), "PCT": pct_value})
    return standings


def parse_team_leaders(soup: BeautifulSoup) -> list[dict[str, str]]:
    block = block_after_heading(soup, "Team Leaders")
    if not block:
        return []
    lines = [line for line in block.get_text("\n", strip=True).splitlines() if line and line not in {"See roster", "Team Leaders"}]
    leaders: list[dict[str, str]] = []
    for idx in range(0, min(len(lines), 9), 3):
        if idx + 2 >= len(lines):
            break
        leaders.append({"metric": lines[idx], "value": lines[idx + 1], "name": lines[idx + 2]})
    return leaders


def first_nonempty_table_row(query: str) -> tuple[str, dict[str, str]]:
    soup = ask_soup(query, allow_error=True)
    table = soup.find("table")
    rows = parse_table(table)
    if len(rows) < 2:
        raise RuntimeError(f"No tabular data returned for query: {query}")
    headers = rows[0]
    first_row = rows[1]
    payload: dict[str, str] = {}
    for header, value in zip(headers, first_row):
        header_text = clean(header)
        value_text = clean(value)
        if header_text and header_text not in payload:
            payload[header_text] = value_text
    heading = clean(soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else "")
    return heading, payload


def parse_finish_from_heading(text: str) -> tuple[str | None, int | None]:
    match = re.search(r"finished\s+(\d+)(?:st|nd|rd|th)\s+in\s+the\s+([^.,]+)", text, re.I)
    if match:
        return normalize_division_label(match.group(2)), int(match.group(1))
    return None, None


def normalize_division_label(value: str | None) -> str | None:
    text = clean(value)
    if not text:
        return None
    text = re.sub(r"\s+and\s+\d+(?:st|nd|rd|th)\s+in\s+the\s+.+$", "", text, flags=re.I)
    return clean(text)


def infer_historic_division(slug: str, year: int) -> str | None:
    for start, end, label in DIVISION_HISTORY.get(slug, ()):
        if year >= start and (end is None or year <= end):
            return label
    return None


def can_derive_division_rank(division_name: str | None, division_name_inferred: bool) -> bool:
    if division_name_inferred:
        return False
    cleaned = clean(division_name)
    if not cleaned or cleaned == "NFL" or cleaned.startswith("AFL "):
        return False
    return True


def clean_leader_name(value: str) -> str:
    text = clean(value)
    return re.sub(r"\s+[A-Z]\.\s+.+$", "", text)


def fallback_team_leaders(team_name: str, year: int) -> list[dict[str, str]]:
    query_map = {
        "PASS YDS": f"who led {team_name} in passing yards in {year}",
        "RUSH YDS": f"who led {team_name} in rushing yards in {year}",
        "REC YDS": f"who led {team_name} in receiving yards in {year}",
    }
    value_column_map = {
        "PASS YDS": "YDS",
        "RUSH YDS": "RUSH YDS",
        "REC YDS": "REC YDS",
    }
    leaders: list[dict[str, str]] = []
    for metric, query in query_map.items():
        try:
            _, row = first_nonempty_table_row(query)
        except Exception:
            continue
        name = clean_leader_name(row.get("NAME", ""))
        value = clean(row.get(value_column_map[metric], ""))
        if name and value:
            leaders.append({"metric": metric, "value": value, "name": name})
    return leaders


def fallback_season_snapshot(meta: dict[str, Any], year: int) -> tuple[str, dict[str, Any], str | None, int | None]:
    heading, row = first_nonempty_table_row(f"{meta['team_name']} stats {year}")
    wins = int(clean(row.get("W", "0")) or 0)
    losses = int(clean(row.get("L", "0")) or 0)
    ties = int(clean(row.get("T", "0")) or 0)
    stats: dict[str, Any] = {}
    for key, value in row.items():
        text = clean(value).replace(",", "")
        if not text or key in {"TEAM", "SEASON"}:
            continue
        if re.fullmatch(r"-?\d+(?:\.\d+)?", text):
            number = float(text)
            stats[key] = int(number) if number.is_integer() else number
        else:
            stats[key] = value
    season_name = clean(row.get("TEAM")) or meta["short_name"]
    division_name, division_rank = parse_finish_from_heading(heading)
    return season_name, {"record": f"{wins}-{losses}" + (f"-{ties}" if ties else ""), "wins": wins, "losses": losses, "ties": ties, "stats": stats, "heading": heading}, division_name, division_rank


def parse_game_log_rows(query: str, season_year: int) -> list[dict[str, Any]]:
    def header_index(headers: list[str], *names: str) -> int:
        normalized = {clean_key(header): idx for idx, header in enumerate(headers)}
        for name in names:
            idx = normalized.get(clean_key(name))
            if idx is not None:
                return idx
        return -1

    def parse_game_log_table(table: Tag | None) -> list[dict[str, Any]]:
        rows = parse_table(table)
        if len(rows) < 2:
            return []
        headers = rows[0]
        is_playoff_log = "ROUND" in headers
        try:
            date_idx = headers.index("DATE")
            opp_idx = headers.index("OPP")
            result_idx = headers.index("RESULT")
        except ValueError:
            return []
        loc_idx = opp_idx - 1
        round_idx = headers.index("ROUND") if is_playoff_log else -1
        total_yards_idx = header_index(headers, "OFF", "YDS")
        opp_total_yards_idx = header_index(headers, "OPP OFF")
        pass_idx = header_index(headers, "PASS YDS")
        rush_idx = header_index(headers, "RUSH YDS")
        tov_idx = header_index(headers, "TOV")
        first_downs_idx = header_index(headers, "1DWN")
        top_idx = header_index(headers, "TOP")
        plays_idx = header_index(headers, "PLY")
        ypp_idx = header_index(headers, "YDS/PLY")
        yards_per_pass_idx = header_index(headers, "AVG")
        punts_idx = header_index(headers, "PUNT")
        interceptions_idx = header_index(headers, "INT")
        fumbles_lost_idx = header_index(headers, "LOST")
        penalties_idx = header_index(headers, "PEN")
        sacks_idx = header_index(headers, "SCK")
        pass_attempts_idx = header_index(headers, "PASS ATT", "ATT")
        rush_attempts_idx = header_index(headers, "RUSH ATT")
        parsed_rows: list[dict[str, Any]] = []
        for row in rows[1:]:
            if len(row) != len(headers):
                continue
            result = clean(row[result_idx])
            match = re.match(r"([WLT])\s+(\d+)-(\d+)", result)
            if not match or not clean(row[date_idx]):
                continue
            parsed_rows.append(
                {
                    "date": datetime.strptime(clean(row[date_idx]), "%m/%d/%Y").strftime("%Y-%m-%d"),
                    "result": match.group(1),
                    "ravensScore": int(match.group(2)),
                    "teamScore": int(match.group(2)),
                    "oppScore": int(match.group(3)),
                    "displayDate": clean(row[date_idx]),
                    "location": "Home" if clean(row[loc_idx]).lower() == "vs" else "Away",
                    "opponent": normalize_opponent(row[opp_idx], season_year),
                    "opponentCode": clean(row[opp_idx]),
                    "round": clean(row[round_idx]) if round_idx >= 0 else "",
                    "totalYards": clean(row[total_yards_idx]) if total_yards_idx >= 0 else "",
                    "opponentTotalYards": clean(row[opp_total_yards_idx]) if opp_total_yards_idx >= 0 else "",
                    "passingYards": clean(row[pass_idx]) if pass_idx >= 0 else "",
                    "rushingYards": clean(row[rush_idx]) if rush_idx >= 0 else "",
                    "turnovers": clean(row[tov_idx]) if tov_idx >= 0 else "",
                    "firstDowns": clean(row[first_downs_idx]) if first_downs_idx >= 0 else "",
                    "possession": clean(row[top_idx]) if top_idx >= 0 else "",
                    "totalPlays": clean(row[plays_idx]) if plays_idx >= 0 else "",
                    "yardsPerPlay": clean(row[ypp_idx]) if ypp_idx >= 0 else "",
                    "yardsPerPass": clean(row[yards_per_pass_idx]) if yards_per_pass_idx >= 0 else "",
                    "punts": clean(row[punts_idx]) if punts_idx >= 0 else "",
                    "interceptionsThrown": clean(row[interceptions_idx]) if interceptions_idx >= 0 else "",
                    "fumblesLost": clean(row[fumbles_lost_idx]) if fumbles_lost_idx >= 0 else "",
                    "penalties": clean(row[penalties_idx]) if penalties_idx >= 0 else "",
                    "sacks": clean(row[sacks_idx]) if sacks_idx >= 0 else "",
                    "passAttempts": clean(row[pass_attempts_idx]) if pass_attempts_idx >= 0 else "",
                    "rushAttempts": clean(row[rush_attempts_idx]) if rush_attempts_idx >= 0 else "",
                }
            )
        return parsed_rows

    base_rows = parse_game_log_table(ask_soup(query, allow_error=True).find("table"))
    supplemental_rows: list[dict[str, Any]] = []
    if " including " in query:
        query_prefix = query.split(" including ", 1)[0]
        supplemental_query = (
            f"{query_prefix} including total plays yards per play punts interceptions thrown "
            "fumbles lost penalties sacks rush attempts pass attempts"
        )
        supplemental_rows = parse_game_log_table(ask_soup(supplemental_query, allow_error=True).find("table"))

    merged_rows: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    for row in base_rows + supplemental_rows:
        key = (
            clean(row.get("date")),
            clean(row.get("opponentCode")) or clean(row.get("opponent")),
            int(row.get("ravensScore", 0)),
            int(row.get("oppScore", 0)),
        )
        target = merged_rows.setdefault(key, {})
        for field, value in row.items():
            if clean(value):
                target[field] = value
        target.setdefault("date", row.get("date"))
        target.setdefault("opponent", row.get("opponent"))
        target.setdefault("opponentCode", row.get("opponentCode"))
        target.setdefault("displayDate", row.get("displayDate"))
        target.setdefault("location", row.get("location"))
        target.setdefault("result", row.get("result"))
        target.setdefault("ravensScore", row.get("ravensScore"))
        target.setdefault("teamScore", row.get("teamScore"))
        target.setdefault("oppScore", row.get("oppScore"))
        target.setdefault("round", row.get("round"))
    output = list(merged_rows.values())
    output.sort(key=lambda row: row["date"])
    return output


def normalize_historic_code(code: str, season_year: int) -> str | None:
    raw = clean(code).upper()
    if not raw:
        return None
    if raw == "STL":
        if 1960 <= season_year <= 1987:
            return "Cardinals"
        if 1995 <= season_year <= 2015:
            return "Rams"
    if raw == "HOU":
        return "Oilers" if season_year < 2002 else "Texans"
    if raw in {"TEN", "OTI"}:
        return "Oilers" if season_year < 1999 else "Titans"
    if raw in {"WSH", "WAS"}:
        return "Redskins" if season_year < 2022 else "Commanders"
    return HISTORIC_CODE_NAME_ALIASES.get(raw)


def normalize_opponent(value: str, season_year: int | None = None) -> str:
    raw = clean(value)
    if raw in TEAM_CATALOG:
        return raw
    code_key = raw.upper()
    if season_year is not None:
        historic_name = normalize_historic_code(code_key, season_year)
        if historic_name:
            return historic_name
    return TEAM_NAME_ALIASES.get(code_key, raw)


def build_match_key(game: dict[str, Any]) -> str:
    return "|".join(
        [
            str(game["year"]),
            clean(game["round"]),
            game["opponent"],
            game["location"],
            f"{game['ravensScore']}-{game['oppScore']}",
        ]
    )


def build_player_features(leaders: list[dict[str, str]], season_name: str, icons: list[str]) -> list[dict[str, Any]]:
    role_map = {"PASS YDS": "QB", "RUSH YDS": "RB", "REC YDS": "WR"}
    features: list[dict[str, Any]] = []
    for item in leaders:
        metric = clean(item["metric"])
        features.append(
            {
                "slug": slugify(item["name"]),
                "name": item["name"],
                "role": role_map.get(metric, metric),
                "subtitle": f"{metric} leader",
                "mini": f"{season_name} leader: {item['value']} {metric.lower()}.",
                "era": season_name,
                "kpis": [role_map.get(metric, metric), item["value"], "Season leader"],
                "facts": [
                    f"Led the team in {metric.lower()}.",
                    f"Produced {item['value']} in {season_name}.",
                    "Pulled directly from the StatMuse team leader card.",
                ],
            }
        )
    while len(features) < 3 and icons:
        name = icons[len(features) % len(icons)]
        features.append(
            {
                "slug": slugify(name),
                "name": name,
                "role": "ICON",
                "subtitle": "Franchise touchstone",
                "mini": f"Useful anchor for the {season_name} archive view.",
                "era": season_name,
                "kpis": ["Franchise", "Icon", "Fallback"],
                "facts": [
                    f"Used as a fallback face for {season_name}.",
                    "Keeps the player panel populated when a leader card is missing.",
                    "Part of the manually curated franchise identity set.",
                ],
            }
        )
    return features[:3]


def replace_once(text: str, pattern: str, replacement: str) -> str:
    updated, count = re.subn(pattern, lambda _match: replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Replacement failed: {pattern}")
    return updated


def replace_chunk(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    pattern = re.escape(start_marker) + r".*?(?=" + re.escape(end_marker) + r")"
    return replace_once(text, pattern, replacement)


def build_theme_css(config: dict[str, Any]) -> str:
    accent = config["secondaryColor"] if relative_luminance(config["secondaryColor"]) >= 0.2 else mix_hex(config["primaryColor"], config["textOnDark"], 0.38)
    light_accent = config["lightThemePrimary"] if relative_luminance(config["lightThemePrimary"]) >= 0.2 else mix_hex(config["lightThemePrimary"], config["primaryColor"], 0.22)
    light_text = mix_hex("#172033", config["lightThemePrimary"], 0.18)
    light_muted = mix_hex("#5f6b7c", config["lightThemePrimary"], 0.24)
    light_placeholder = mix_hex("#7b8795", config["lightThemePrimary"], 0.22)
    light_title_accent = accent
    if relative_luminance(light_title_accent) > 0.78:
        light_title_accent = config["lightThemePrimary"]
    elif relative_luminance(light_title_accent) < 0.18:
        light_title_accent = mix_hex(light_title_accent, "#ffffff", 0.38)
    primary_05 = rgba_from_hex(config["primaryColor"], "0.05")
    primary_07 = rgba_from_hex(config["primaryColor"], "0.07")
    primary_10 = rgba_from_hex(config["primaryColor"], "0.10")
    accent_08 = rgba_from_hex(accent, "0.08")
    accent_10 = rgba_from_hex(accent, "0.10")
    accent_12 = rgba_from_hex(accent, "0.12")
    accent_16 = rgba_from_hex(accent, "0.16")
    accent_18 = rgba_from_hex(accent, "0.18")
    accent_24 = rgba_from_hex(accent, "0.24")
    timeline_win_top = mix_hex(accent, config["textOnDark"], 0.18)
    timeline_win_bottom = mix_hex(config["primaryColor"], accent, 0.42)
    timeline_loss_top = mix_hex(config["darkBgMid"], config["primaryColor"], 0.28)
    timeline_loss_bottom = mix_hex(config["darkBgEnd"], config["primaryColor"], 0.18)
    timeline_tie_top = mix_hex(config["tertiaryColor"], accent, 0.34)
    timeline_tie_bottom = mix_hex(accent, config["primaryColor"], 0.26)
    hero_overlay_start = rgba_from_hex(config["darkBgStart"], "0.96")
    hero_overlay_mid = rgba_from_hex(config["darkBgMid"], "0.88")
    hero_overlay_end = rgba_from_hex(config["darkBgEnd"], "0.56")
    card_floor = rgba_from_hex(config["darkBgMid"], "0.92")
    button_floor = rgba_from_hex(config["darkBgEnd"], "0.92")
    button_surface = rgba_from_hex(config["darkBgMid"], "0.94")
    light_button_surface = rgba_from_hex(config["lightThemePrimary"], "0.10")
    return f"""
/* Auto-generated team theme override */
body {{
  background:
    radial-gradient(circle at 14% 10%, color-mix(in srgb, {accent} 10%, transparent) 0%, transparent 30%),
    radial-gradient(circle at 84% 8%, color-mix(in srgb, {config['primaryColor']} 9%, transparent) 0%, transparent 24%),
    linear-gradient(
      165deg,
      color-mix(in srgb, {config['primaryColor']} 11%, {config['darkBgStart']}) 0%,
      color-mix(in srgb, {accent} 6%, {config['darkBgMid']}) 36%,
      color-mix(in srgb, {config['primaryColor']} 14%, {config['darkBgEnd']}) 72%,
      color-mix(in srgb, {accent} 8%, color-mix(in srgb, {config['primaryColor']} 10%, {config['darkBgEnd']})) 100%
    ) !important;
  color: {config['textOnDark']} !important;
}}
h1,.footer-brand {{ background: linear-gradient(135deg, {config['textOnDark']} 0%, {accent} 44%, {config['primaryColor']} 100%) !important; -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important; }}
.footer-brand {{
  background: none !important;
  background-image: none !important;
  -webkit-background-clip: border-box !important;
  background-clip: border-box !important;
  -webkit-text-fill-color: {config['textOnDark']} !important;
  color: {config['textOnDark']} !important;
  text-shadow: none !important;
}}
.subtitle,.panel-note,.muted,.footer-brand-meta,.hero-note,.historical-summary-sub,.player-sub,.roster-line,.chart-meta,.chart-row-label,.team-box .meta,.search-hints,.search-hints strong {{ color: {config['mutedOnDark']} !important; }}
.footer-copy,.footer-block p,.footer-block li,.hero-text {{ color: color-mix(in srgb, {config['textOnDark']} 94%, {accent} 6%) !important; }}
.badge {{ border-color: color-mix(in srgb, {accent} 34%, transparent) !important; color: {accent} !important; background: linear-gradient(180deg, {accent_08} 0%, rgba(255,255,255,0.02) 100%) !important; }}
.toggle.active,.season-btn.active,.chip,.summary-pill,.footer-meta-pill,.note-pill {{ background: color-mix(in srgb, {accent} 12%, transparent) !important; color: {accent} !important; }}
.hero-kicker,.footer-block span,.footer-meta-pill,.note-pill,.stat-label,.ad-slot-label,.feature-card span,.chart-card span,.hero-stat-card span,.hosting-card span {{ color: {accent} !important; }}
.hero-title,.panel-title,.mini-panel h3,.modal-title,.roster-name,.player-name,.anchor-card strong,.feature-card strong,.chart-card strong,.hero-stat-card strong,.hosting-card strong {{ color: {config['textOnDark']} !important; }}
.back-top-btn {{
  border-color: color-mix(in srgb, {accent} 32%, transparent) !important;
  background: linear-gradient(180deg, color-mix(in srgb, {accent} 18%, {button_floor}) 0%, color-mix(in srgb, {config['primaryColor']} 16%, {button_floor}) 100%) !important;
  color: {config['textOnDark']} !important;
  box-shadow: 0 12px 26px color-mix(in srgb, {config['primaryColor']} 24%, rgba(0,0,0,0.28)) !important;
}}
.back-top-btn:hover {{
  transform: translateY(-2px) !important;
  border-color: color-mix(in srgb, {accent} 52%, transparent) !important;
  box-shadow: 0 16px 30px color-mix(in srgb, {accent} 16%, rgba(0,0,0,0.24)) !important;
}}
.header-team-logo {{
  display: block !important;
  width: clamp(72px, 9vw, 104px) !important;
  height: clamp(72px, 9vw, 104px) !important;
  margin: 14px auto 12px !important;
  object-fit: contain !important;
  filter: drop-shadow(0 12px 24px color-mix(in srgb, {config['primaryColor']} 28%, rgba(0,0,0,0.32))) !important;
}}
.hero-kicker {{ border-color: {accent_24} !important; background: linear-gradient(180deg, {accent_12} 0%, rgba(255,255,255,0.03) 100%) !important; }}
.timeline-pill.win {{ background: linear-gradient(180deg, {timeline_win_top}, {timeline_win_bottom}) !important; }}
.timeline-pill.loss {{ background: linear-gradient(180deg, {timeline_loss_top}, {timeline_loss_bottom}) !important; }}
.timeline-pill.tie {{ background: linear-gradient(180deg, {timeline_tie_top}, {timeline_tie_bottom}) !important; }}
.timeline-pill.playoff {{ box-shadow: 0 0 0 1px {accent_24}, 0 0 10px {accent_12} !important; }}
.timeline-legend .leg-win::before {{ background: {timeline_win_top} !important; }}
.timeline-legend .leg-loss::before {{ background: {timeline_loss_top} !important; }}
.timeline-legend .leg-tie::before {{ background: {timeline_tie_top} !important; }}
.timeline-legend .leg-playoff::before {{ background: transparent !important; box-shadow: inset 0 0 0 1px {accent} !important; }}
.hero-side > .hero-stat-card,
.hero-side > .hero-balance-card {{
  width: 100% !important;
  min-height: 34px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
}}
.hero-side > .hero-stat-card .hero-note,
.hero-side > .hero-balance-card .hero-note {{
  display: block !important;
  width: 100% !important;
  min-height: 1px !important;
  margin: 0 !important;
}}
.hero-balance-card {{
  border-radius: 14px !important;
  border: 1px solid color-mix(in srgb, {accent} 16%, transparent) !important;
  background: linear-gradient(180deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.02) 100%) !important;
  box-shadow: none !important;
}}
.hero-panel {{
  background:
    linear-gradient(
      120deg,
      color-mix(in srgb, {config['primaryColor']} 14%, {config['darkBgStart']}) 0%,
      color-mix(in srgb, {accent} 6%, {config['darkBgMid']}) 45%,
      color-mix(in srgb, {config['primaryColor']} 12%, {config['darkBgEnd']}) 100%
    ) !important;
  border-color: color-mix(in srgb, {accent} 16%, transparent) !important;
  box-shadow: 0 24px 48px color-mix(in srgb, {config['primaryColor']} 8%, rgba(0,0,0,0.22)) !important;
}}
.hero-panel::before {{
  background:
    linear-gradient(90deg, {hero_overlay_start} 0%, {hero_overlay_mid} 42%, {hero_overlay_end} 100%),
    radial-gradient(circle at 100% 0%, {accent_16}, transparent 38%) !important;
}}
.hero-panel::after {{
  background:
    radial-gradient(circle at 100% 0%, {accent_24}, transparent 38%) !important;
}}
.hero-stat-card:empty,
.stat-card:empty,
.extra-card:empty {{
  display: none !important;
}}
.hero-stat-card,
.stat-card,
.extra-card,
.feature-card,
.rivalry-card,
.hosting-card,
.roster-card,
.player-card,
.team-chip,
.search-shell,
.panel,
.mini-panel,
.ad-slot,
.modal-card,
.table-wrap,
.toolbar,
.season-strip {{
  background:
    linear-gradient(
      180deg,
      {primary_05} 0%,
      {card_floor} 100%
    ) !important;
  border-color: color-mix(in srgb, {accent} 14%, transparent) !important;
}}
.feature-card,
.hero-sim-card {{
  display: flex !important;
  flex-direction: column !important;
}}
.tool-btn,
.season-btn,
.toggle,
.action-btn,
.hero-btn,
.back-season-btn,
.search-input {{
  background: linear-gradient(180deg, color-mix(in srgb, {accent} 4%, {button_surface}) 0%, color-mix(in srgb, {config['primaryColor']} 3%, {button_surface}) 100%) !important;
  border-color: color-mix(in srgb, {accent} 14%, transparent) !important;
  color: color-mix(in srgb, {config['textOnDark']} 78%, {accent} 22%) !important;
  box-shadow: none !important;
}}
.tool-btn:hover,
.season-btn:hover,
.toggle:hover,
.action-btn:hover,
.hero-btn:hover,
.back-season-btn:hover {{
  background: color-mix(in srgb, {accent} 10%, rgba(255,255,255,0.04)) !important;
}}
.feature-card .hero-btn,
.hero-sim-card .hero-btn {{
  margin-top: auto !important;
  width: 100% !important;
  min-height: 42px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  text-align: center !important;
}}
.season-btn::after,
.season-btn.active::after {{
  content: none !important;
  display: none !important;
}}
.season-btn,
.toggle,
.tool-btn,
.hero-btn,
.back-season-btn,
.action-btn {{
  min-height: 42px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
}}
.season-btn {{
  align-items: flex-start !important;
  justify-content: flex-start !important;
}}
.search-input {{
  min-height: 42px !important;
}}
.header {{
  text-align: center !important;
  margin-bottom: 26px !important;
  position: relative !important;
}}
.badge {{
  display: inline-block !important;
  padding: 6px 18px !important;
  border-radius: 3px !important;
  margin-bottom: 12px !important;
  font-size: 11px !important;
  letter-spacing: 3px !important;
  text-transform: uppercase !important;
}}
h1 {{
  font-size: clamp(34px, 6vw, 58px) !important;
  line-height: 1.02 !important;
  letter-spacing: 2px !important;
  margin-bottom: 8px !important;
}}
.home-btn-corner,
.theme-toggle-corner {{
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 8px !important;
  padding: 10px 14px !important;
  border-radius: 999px !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
  min-height: auto !important;
}}
.theme-icon {{
  width: 18px !important;
  text-align: center !important;
  font-size: 14px !important;
  line-height: 1 !important;
}}
.theme-label {{
  line-height: 1 !important;
}}
.search-input {{
  padding: 12px 14px !important;
  border-radius: 8px !important;
  font-size: 13px !important;
  min-height: auto !important;
}}
.toggle {{
  padding: 10px 14px !important;
  border-radius: 8px !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
  min-height: auto !important;
}}
.tool-btn {{
  padding: 10px 12px !important;
  border-radius: 8px !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
  min-height: auto !important;
}}
.season-btn {{
  min-width: 88px !important;
  padding: 12px 14px !important;
  border-radius: 8px !important;
  text-align: left !important;
  min-height: auto !important;
  display: block !important;
}}
.back-season-btn {{
  padding: 9px 12px !important;
  border-radius: 999px !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
  min-height: auto !important;
}}
.hero-btn {{
  padding: 12px 16px !important;
  border-radius: 12px !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
  min-height: auto !important;
}}
.action-btn {{
  padding: 9px 11px !important;
  border-radius: 999px !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
  min-height: auto !important;
}}
.header,.footer,.panel-head,.mini-panel h3,.modal-head {{
  background: linear-gradient(
    90deg,
    color-mix(in srgb, {config['primaryColor']} 12%, {config['darkBgMid']}) 0%,
    color-mix(in srgb, {accent} 8%, color-mix(in srgb, {config['primaryColor']} 10%, {config['darkBgEnd']})) 100%
  ) !important;
}}
.header,.footer,#seasonMetricsPanel {{
  border-color: color-mix(in srgb, {accent} 16%, transparent) !important;
}}
.footer,#siteFooter {{
  background:
    linear-gradient(
      180deg,
      color-mix(in srgb, {accent} 7%, {config['darkBgMid']}) 0%,
      color-mix(in srgb, {config['primaryColor']} 12%, {config['darkBgEnd']}) 100%
    ) !important;
  color: {config['textOnDark']} !important;
}}
#seasonMetricsPanel,
.panel.season-metrics-panel {{
  background:
    linear-gradient(
      180deg,
      color-mix(in srgb, {accent} 8%, {config['darkBgMid']}) 0%,
      color-mix(in srgb, {config['primaryColor']} 14%, {config['darkBgEnd']}) 100%
    ) !important;
  border-color: color-mix(in srgb, {accent} 16%, transparent) !important;
  box-shadow: 0 18px 40px color-mix(in srgb, {config['primaryColor']} 10%, rgba(0,0,0,0.18)) !important;
}}
#seasonMetricsPanel .panel-head,
#seasonMetricsPanel .panel-body {{
  background: transparent !important;
}}
#seasonMetricsPanel,
#seasonMetricsPanel .panel-body,
#seasonMetricsPanel .table-wrap td,
#seasonMetricsPanel .table-wrap th,
#seasonMetricsPanel .historical-summary-main,
#seasonMetricsPanel .historical-summary-stat,
#seasonMetricsPanel .extra-card,
#seasonMetricsPanel .stat-card {{
  color: {config['textOnDark']} !important;
}}
#seasonMetricsPanel .panel-title,
#seasonMetricsPanel .note-pill,
#seasonMetricsPanel .panel-note,
#seasonMetricsPanel .stat-label,
#seasonMetricsPanel .historical-summary-sub {{
  color: {accent} !important;
}}
#seasonMetricsPanel .metric-value,
#seasonMetricsPanel .stat-value,
#seasonMetricsPanel strong {{
  color: {config['textOnDark']} !important;
}}
.footer {{
  border-color: color-mix(in srgb, {accent} 16%, transparent) !important;
}}
.theme-toggle-corner,.toggle,.season-btn,.search-input,.mini-panel,.modal-card,.note-pill,.footer-meta-pill {{
  border-color: color-mix(in srgb, {accent} 14%, transparent) !important;
}}
.theme-toggle-corner,.toggle,.season-btn,.compare-table td:nth-child(2),.compare-table td:nth-child(4),.footer {{
  color: color-mix(in srgb, {config['textOnDark']} 72%, {accent} 28%) !important;
}}
.theme-toggle-corner:hover,.toggle:hover,.season-btn:hover,.search-input:focus,.mini-panel:hover {{
  border-color: color-mix(in srgb, {accent} 28%, transparent) !important;
  box-shadow: 0 0 0 1px color-mix(in srgb, {accent} 14%, transparent) inset !important;
}}
.panel-title,.mini-panel h3,.modal-title,.compare-table tr:hover td:nth-child(3),.gold,.purple {{
  color: {accent} !important;
}}
.compare-table td:nth-child(3),.modal-sub strong {{
  color: {config['textOnDark']} !important;
}}
.season-btn .year {{
  color: color-mix(in srgb, {config['textOnDark']} 96%, white 4%) !important;
}}
.season-btn.active .year {{
  color: color-mix(in srgb, {accent} 18%, {config['textOnDark']} 82%) !important;
}}
.live-game-center,
.live-game-center.sticky-live-center,
.live-scoreboard,
.live-meta-card,
.live-last-play,
.live-topbar,
.live-chip,
.live-control-btn,
.live-center-wrap,
.live-center-score,
.live-center-team,
.live-center-stat,
.live-play-item {{
  color: {config['textOnDark']} !important;
  border-color: color-mix(in srgb, {accent} 16%, transparent) !important;
}}
.live-game-center,
.live-game-center.sticky-live-center {{
  background:
    linear-gradient(
      180deg,
      color-mix(in srgb, {config['primaryColor']} 12%, {config['darkBgMid']}) 0%,
      color-mix(in srgb, {accent} 5%, {config['darkBgEnd']}) 100%
    ) !important;
}}
.live-scoreboard,
.live-meta-card,
.live-last-play,
.live-chip,
.live-control-btn,
.live-center-wrap,
.live-center-score,
.live-center-team,
.live-center-stat,
.live-play-item {{
  background: linear-gradient(180deg, color-mix(in srgb, {accent} 4%, {button_surface}) 0%, color-mix(in srgb, {config['primaryColor']} 3%, {card_floor}) 100%) !important;
}}
.live-game-center .panel-title,
.live-team-name,
.live-team-score,
.live-qtr,
.live-clock,
.live-down,
.live-meta-value,
.live-last-play .text,
.live-center-team strong,
.live-center-stat strong,
.live-play-item strong {{
  color: {config['textOnDark']} !important;
}}
.live-team-sub,
.live-meta-label,
.live-last-play .label,
.live-center-meta,
.live-center-stat span,
.live-play-item span,
.live-api-note,
.live-api-note code {{
  color: color-mix(in srgb, {config['textOnDark']} 88%, {accent} 12%) !important;
}}
.live-chip strong,
.live-status-dot,
.live-dot {{
  color: {accent} !important;
}}
.live-control-btn:hover,
.live-chip:hover {{
  background: color-mix(in srgb, {accent} 10%, rgba(255,255,255,0.04)) !important;
}}
.compare-table tr:hover {{
  background: color-mix(in srgb, {config['primaryColor']} 7%, transparent) !important;
}}
.compare-table tr::after,.panel-head::after {{
  background: linear-gradient(90deg, transparent, color-mix(in srgb, {accent} 34%, transparent), color-mix(in srgb, {config['primaryColor']} 18%, transparent), transparent) !important;
}}
body.theme-light {{ background: linear-gradient(180deg, #ffffff 0%, color-mix(in srgb, {config['lightThemePrimary']} 7%, white) 100%) !important; color: #0f1724 !important; }}
body.theme-light .badge {{ color: {config['lightThemePrimary']} !important; border-color: color-mix(in srgb, {config['lightThemePrimary']} 20%, transparent) !important; }}
body.theme-light .header,
body.theme-light .footer,
body.theme-light .panel-head,
body.theme-light .mini-panel h3,
body.theme-light .modal-head,
body.theme-light .theme-toggle-corner {{
  background: linear-gradient(90deg, color-mix(in srgb, {config['lightThemePrimary']} 12%, white) 0%, color-mix(in srgb, {light_accent} 8%, white) 100%) !important;
  color: color-mix(in srgb, {config['lightThemePrimary']} 66%, #223046) !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 18%, transparent) !important;
  box-shadow: none !important;
}}
body.theme-light #seasonMetricsPanel,
body.theme-light .panel.season-metrics-panel,
body.theme-light #siteFooter {{
  background:
    linear-gradient(180deg, color-mix(in srgb, {config['lightThemePrimary']} 9%, white) 0%, color-mix(in srgb, {light_accent} 6%, white) 100%) !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 16%, transparent) !important;
}}
body.theme-light #seasonMetricsPanel .panel-head,
body.theme-light #seasonMetricsPanel .panel-body {{
  background: transparent !important;
}}
body.theme-light .subtitle,
body.theme-light .panel-note,
body.theme-light .muted,
body.theme-light .hero-text,
body.theme-light .hero-note,
body.theme-light .footer-block p,
body.theme-light .footer-block li,
body.theme-light .footer-copy,
body.theme-light .footer-brand-meta {{
  color: color-mix(in srgb, {config['lightThemePrimary']} 48%, #334155) !important;
}}
body.theme-light .hero-panel,
body.theme-light .hero-stat-card,
body.theme-light .stat-card,
body.theme-light .extra-card,
body.theme-light .feature-card,
body.theme-light .rivalry-card,
body.theme-light .hosting-card,
body.theme-light .roster-card,
body.theme-light .player-card,
body.theme-light .team-chip,
body.theme-light .search-shell,
body.theme-light .panel,
body.theme-light .mini-panel,
body.theme-light .ad-slot,
body.theme-light .modal-card,
body.theme-light .table-wrap,
body.theme-light .toolbar,
body.theme-light .season-strip {{
  background:
    linear-gradient(
      180deg,
      color-mix(in srgb, {config['lightThemePrimary']} 8%, white) 0%,
      color-mix(in srgb, {light_accent} 6%, white) 100%
    ) !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 14%, transparent) !important;
}}
body.theme-light .tool-btn,
body.theme-light .season-btn,
body.theme-light .toggle,
body.theme-light .action-btn,
body.theme-light .hero-btn,
body.theme-light .back-season-btn,
body.theme-light .search-input,
body.theme-light .team-chip,
body.theme-light .hero-btn.gold {{
  background: linear-gradient(180deg, color-mix(in srgb, {config['lightThemePrimary']} 9%, white) 0%, color-mix(in srgb, {light_accent} 5%, white) 100%) !important;
  color: color-mix(in srgb, {config['lightThemePrimary']} 60%, #334155) !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 14%, transparent) !important;
  box-shadow: none !important;
}}
body.theme-light .back-top-btn {{
  background: linear-gradient(180deg, color-mix(in srgb, {light_accent} 16%, white) 0%, color-mix(in srgb, {config['lightThemePrimary']} 10%, white) 100%) !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 20%, transparent) !important;
  color: {light_text} !important;
  box-shadow: 0 14px 24px color-mix(in srgb, {config['lightThemePrimary']} 10%, rgba(15,23,36,0.12)) !important;
}}
body.theme-light .back-top-btn:hover {{
  border-color: color-mix(in srgb, {light_accent} 32%, transparent) !important;
}}
body.theme-light .footer-block span,
body.theme-light .footer-copy,
body.theme-light .note-pill,
body.theme-light .footer-meta-pill {{
  color: {light_accent} !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 18%, transparent) !important;
}}
body.theme-light .footer-brand {{
  color: {light_text} !important;
  background: none !important;
  background-image: none !important;
  -webkit-background-clip: border-box !important;
  background-clip: border-box !important;
  -webkit-text-fill-color: {light_text} !important;
  text-fill-color: {light_text} !important;
}}
body.theme-light .note-pill,
body.theme-light .footer-meta-pill {{
  background: color-mix(in srgb, {light_accent} 8%, white) !important;
}}
body.theme-light .badge,
body.theme-light .hero-kicker {{
  background: linear-gradient(180deg, color-mix(in srgb, {config['lightThemePrimary']} 8%, white) 0%, white 100%) !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 18%, transparent) !important;
}}
body.theme-light .hero-panel,
body.theme-light .season-btn,
body.theme-light .toggle,
body.theme-light .tool-btn,
body.theme-light .hero-btn,
body.theme-light .back-season-btn,
body.theme-light .action-btn,
body.theme-light .team-chip,
body.theme-light .search-input,
body.theme-light .theme-toggle-corner {{
  box-shadow: none !important;
}}
body.theme-light .hero-kicker,
body.theme-light .footer-block span,
body.theme-light .panel-title,
body.theme-light .feature-card span,
body.theme-light .chart-card span,
body.theme-light .stat-label,
body.theme-light .note-pill,
body.theme-light .footer-meta-pill,
body.theme-light #seasonMetricsPanel .panel-title,
body.theme-light #seasonMetricsPanel .note-pill,
body.theme-light #seasonMetricsPanel .panel-note,
body.theme-light #seasonMetricsPanel .stat-label {{
  color: {light_accent} !important;
}}
body.theme-light h1 {{
  color: {light_title_accent} !important;
  background: linear-gradient(135deg, {light_title_accent} 0%, {light_title_accent} 58%, {config['primaryColor']} 100%) !important;
  background-image: linear-gradient(135deg, {light_title_accent} 0%, {light_title_accent} 58%, {config['primaryColor']} 100%) !important;
  -webkit-background-clip: text !important;
  background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  text-fill-color: transparent !important;
  text-shadow: none !important;
}}
body.theme-light .hero-title,
body.theme-light .footer-brand,
body.theme-light .panel-title,
body.theme-light .mini-panel h3,
body.theme-light .modal-title,
body.theme-light .team-box .name,
body.theme-light .team-box .score,
body.theme-light .score-team-name,
body.theme-light .live-game-center .panel-title {{
  color: {light_text} !important;
  background: none !important;
  background-image: none !important;
  -webkit-background-clip: border-box !important;
  background-clip: border-box !important;
  -webkit-text-fill-color: {light_text} !important;
  text-fill-color: {light_text} !important;
  text-shadow: none !important;
}}
body.theme-light td,
body.theme-light th,
body.theme-light .compare-table td:nth-child(3) {{
  color: {light_text} !important;
  background: none !important;
  background-image: none !important;
  -webkit-background-clip: border-box !important;
  background-clip: border-box !important;
  -webkit-text-fill-color: {light_text} !important;
  text-fill-color: {light_text} !important;
  text-shadow: none !important;
}}
body.theme-light .subtitle,
body.theme-light .panel-note,
body.theme-light .muted,
body.theme-light .hero-note,
body.theme-light .hero-text,
body.theme-light .modal-sub,
body.theme-light .team-box .meta,
body.theme-light .historical-summary-sub,
body.theme-light .player-sub,
body.theme-light .roster-line,
body.theme-light .search-hints,
body.theme-light .footer-copy,
body.theme-light .footer-block p,
body.theme-light .footer-block li,
body.theme-light .stat-label,
body.theme-light .extra-card span,
body.theme-light .chip,
body.theme-light .live-link,
body.theme-light .season-btn .mini,
body.theme-light .season-btn .mini-badge,
body.theme-light .compare-table td:nth-child(2),
body.theme-light .compare-table td:nth-child(4),
body.theme-light .players-note,
body.theme-light .player-answer .answer-label {{
  color: {light_muted} !important;
}}
body.theme-light .search-input::placeholder,
body.theme-light .modal-actions::after {{
  color: {light_placeholder} !important;
}}
body.theme-light .live-game-center,
body.theme-light .live-game-center.sticky-live-center,
body.theme-light .live-scoreboard,
body.theme-light .live-meta-card,
body.theme-light .live-last-play,
body.theme-light .live-topbar,
body.theme-light .live-chip,
body.theme-light .live-control-btn,
body.theme-light .live-center-wrap,
body.theme-light .live-center-score,
body.theme-light .live-center-team,
body.theme-light .live-center-stat,
body.theme-light .live-play-item {{
  color: {light_text} !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 16%, transparent) !important;
}}
body.theme-light .live-game-center,
body.theme-light .live-game-center.sticky-live-center {{
  background: linear-gradient(180deg, color-mix(in srgb, {config['lightThemePrimary']} 9%, white) 0%, color-mix(in srgb, {light_accent} 6%, white) 100%) !important;
}}
body.theme-light .live-scoreboard,
body.theme-light .live-meta-card,
body.theme-light .live-last-play,
body.theme-light .live-chip,
body.theme-light .live-control-btn,
body.theme-light .live-center-wrap,
body.theme-light .live-center-score,
body.theme-light .live-center-team,
body.theme-light .live-center-stat,
body.theme-light .live-play-item {{
  background: linear-gradient(180deg, color-mix(in srgb, {config['lightThemePrimary']} 9%, white) 0%, color-mix(in srgb, {light_accent} 5%, white) 100%) !important;
}}
body.theme-light .live-game-center .panel-title,
body.theme-light .live-team-name,
body.theme-light .live-team-score,
body.theme-light .live-qtr,
body.theme-light .live-clock,
body.theme-light .live-down,
body.theme-light .live-meta-value,
body.theme-light .live-last-play .text,
body.theme-light .live-center-team strong,
body.theme-light .live-center-stat strong,
body.theme-light .live-play-item strong {{
  color: {light_text} !important;
}}
body.theme-light .live-team-sub,
body.theme-light .live-meta-label,
body.theme-light .live-last-play .label,
body.theme-light .live-center-meta,
body.theme-light .live-center-stat span,
body.theme-light .live-play-item span,
body.theme-light .live-api-note,
body.theme-light .live-api-note code {{
  color: {light_muted} !important;
}}
body.theme-light .modal-link-btn,
body.theme-light .modal-nav-btn,
body.theme-light .action-btn,
body.theme-light .tool-btn,
body.theme-light .toggle,
body.theme-light .back-season-btn,
body.theme-light .home-btn-corner,
body.theme-light .theme-toggle-corner,
body.theme-light .chip,
body.theme-light .live-link,
body.theme-light .player-prompt,
body.theme-light .team-chip {{
  background: linear-gradient(180deg, color-mix(in srgb, {config['lightThemePrimary']} 9%, white) 0%, color-mix(in srgb, {light_accent} 5%, white) 100%) !important;
  color: {light_text} !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 16%, transparent) !important;
}}
body.theme-light .modal-link-btn:hover,
body.theme-light .modal-nav-btn:hover,
body.theme-light .action-btn:hover,
body.theme-light .tool-btn:hover,
body.theme-light .toggle:hover,
body.theme-light .back-season-btn:hover,
body.theme-light .home-btn-corner:hover,
body.theme-light .theme-toggle-corner:hover,
body.theme-light .team-chip:hover {{
  background: linear-gradient(180deg, color-mix(in srgb, {config['lightThemePrimary']} 12%, white) 0%, color-mix(in srgb, {light_accent} 8%, white) 100%) !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 24%, transparent) !important;
}}
body.theme-light .modal-link-btn[disabled],
body.theme-light .modal-nav-btn:disabled,
body.theme-light .action-btn:disabled,
body.theme-light .tool-btn:disabled {{
  color: {light_muted} !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 12%, transparent) !important;
}}
body.theme-light .team-box {{
  background: linear-gradient(180deg, white 0%, color-mix(in srgb, {config['lightThemePrimary']} 4%, white) 100%) !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 14%, transparent) !important;
  box-shadow: 0 10px 22px color-mix(in srgb, {config['lightThemePrimary']} 8%, rgba(15, 23, 36, 0.10)) !important;
}}
body.theme-light .close-btn {{
  background: linear-gradient(180deg, color-mix(in srgb, {config['lightThemePrimary']} 8%, white) 0%, white 100%) !important;
  color: {light_text} !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 14%, transparent) !important;
}}
body.theme-light tbody tr:nth-child(even) {{
  background: color-mix(in srgb, {config['lightThemePrimary']} 3%, white) !important;
}}
body.theme-light tbody tr:hover,
body.theme-light .compare-table tr:hover {{
  background: color-mix(in srgb, {config['lightThemePrimary']} 7%, white) !important;
}}
body.theme-light th {{
  background: color-mix(in srgb, {config['lightThemePrimary']} 6%, white) !important;
  color: {light_text} !important;
}}
body.theme-light .hero-btn:hover,
body.theme-light .action-btn:hover,
body.theme-light .team-chip:hover,
body.theme-light .season-btn:hover,
body.theme-light .tool-btn:hover,
body.theme-light .toggle:hover,
body.theme-light .theme-toggle-corner:hover,
body.theme-light .back-season-btn:hover {{
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 26%, transparent) !important;
  background: linear-gradient(180deg, color-mix(in srgb, {config['lightThemePrimary']} 12%, white) 0%, color-mix(in srgb, {light_accent} 7%, white) 100%) !important;
  box-shadow: none !important;
}}
body.theme-light .header {{
  background:
    linear-gradient(
      180deg,
      rgba(255,255,255,0.98) 0%,
      rgba(255,255,255,0.95) 100%
    ) !important;
  color: {light_text} !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 14%, transparent) !important;
  box-shadow: none !important;
}}
body.theme-light .hero-panel {{
  background:
    linear-gradient(
      180deg,
      rgba(255,255,255,0.98) 0%,
      rgba(255,255,255,0.96) 100%
    ) !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 14%, transparent) !important;
  box-shadow: none !important;
}}
body.theme-light .hero-panel::before,
body.theme-light .hero-panel::after {{
  opacity: 0 !important;
  background: none !important;
}}
body.theme-light .hero-stat-card,
body.theme-light .hero-stat-card-ghost,
body.theme-light .hero-balance-card {{
  background:
    linear-gradient(
      180deg,
      rgba(255,255,255,0.97) 0%,
      rgba(255,255,255,0.94) 100%
    ) !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 14%, transparent) !important;
  box-shadow: none !important;
  visibility: visible !important;
  opacity: 1 !important;
}}
body.theme-light .hero-stat-card-ghost,
body.theme-light .hero-balance-card {{
  min-height: 34px !important;
  height: 34px !important;
  border-color: color-mix(in srgb, {config['lightThemePrimary']} 18%, transparent) !important;
  background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(255,255,255,0.95) 100%) !important;
}}
body.theme-light .hero-kicker,
body.theme-light .badge {{
  background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(255,255,255,0.92) 100%) !important;
}}
body.theme-light .season-strip {{
  scrollbar-color: color-mix(in srgb, {config['lightThemePrimary']} 34%, white) rgba(0,0,0,0.05) !important;
  scrollbar-width: thin !important;
}}
body.theme-light .season-strip::-webkit-scrollbar {{
  height: 8px !important;
}}
body.theme-light .season-strip::-webkit-scrollbar-track {{
  background: rgba(0,0,0,0.06) !important;
  border-radius: 999px !important;
}}
body.theme-light .season-strip::-webkit-scrollbar-thumb {{
  background: color-mix(in srgb, {config['lightThemePrimary']} 34%, white) !important;
  border-radius: 999px !important;
}}
body.theme-light .season-strip::-webkit-scrollbar-thumb:hover {{
  background: color-mix(in srgb, {config['lightThemePrimary']} 46%, white) !important;
}}
body.theme-light .badge {{
  display: inline-block !important;
  padding: 6px 18px !important;
  border-radius: 3px !important;
  margin-bottom: 12px !important;
  font-size: 11px !important;
  letter-spacing: 3px !important;
}}
body.theme-light .home-btn-corner,
body.theme-light .theme-toggle-corner {{
  gap: 8px !important;
  padding: 10px 14px !important;
  border-radius: 999px !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  min-height: auto !important;
}}
body.theme-light .theme-icon {{
  width: 18px !important;
  font-size: 14px !important;
  line-height: 1 !important;
}}
body.theme-light .theme-label {{
  line-height: 1 !important;
}}
body.theme-light .search-input {{
  padding: 12px 14px !important;
  border-radius: 8px !important;
  font-size: 13px !important;
  min-height: auto !important;
}}
body.theme-light .toggle {{
  padding: 10px 14px !important;
  border-radius: 8px !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  min-height: auto !important;
}}
body.theme-light .tool-btn {{
  padding: 10px 12px !important;
  border-radius: 8px !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  min-height: auto !important;
}}
body.theme-light .season-btn {{
  min-width: 88px !important;
  padding: 12px 14px !important;
  border-radius: 8px !important;
  text-align: left !important;
  min-height: auto !important;
  display: block !important;
}}
body.theme-light .season-btn .year {{
  color: {light_text} !important;
}}
body.theme-light .season-btn.active .year {{
  color: {light_text} !important;
}}
body.theme-light .back-season-btn {{
  padding: 9px 12px !important;
  border-radius: 999px !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  min-height: auto !important;
}}
body.theme-light .hero-btn {{
  padding: 12px 16px !important;
  border-radius: 12px !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  min-height: auto !important;
}}
body.theme-light .action-btn {{
  padding: 9px 11px !important;
  border-radius: 999px !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  min-height: auto !important;
}}
@media (max-width: 900px) {{
  .header-team-logo {{
    width: 64px !important;
    height: 64px !important;
    margin: 12px auto 10px !important;
  }}
  .home-btn-corner,
  .theme-toggle-corner,
  body.theme-light .home-btn-corner,
  body.theme-light .theme-toggle-corner {{
    top: -4px !important;
    padding: 10px 12px !important;
    font-size: 10px !important;
  }}
  .home-btn-corner .theme-label,
  .theme-toggle-corner .theme-label,
  body.theme-light .home-btn-corner .theme-label,
  body.theme-light .theme-toggle-corner .theme-label {{
    display: none !important;
  }}
  .header {{
    padding-top: 10px !important;
  }}
}}
body.theme-light #seasonMetricsPanel,
body.theme-light #seasonMetricsPanel .panel-body,
body.theme-light #seasonMetricsPanel .table-wrap td,
body.theme-light #seasonMetricsPanel .table-wrap th,
body.theme-light #seasonMetricsPanel .historical-summary-main,
body.theme-light #seasonMetricsPanel .historical-summary-stat {{
  color: #172033 !important;
}}
body.theme-light #seasonMetricsPanel .panel-title,
body.theme-light #seasonMetricsPanel .note-pill,
body.theme-light #seasonMetricsPanel .panel-note,
body.theme-light #seasonMetricsPanel .stat-label {{
  color: {light_accent} !important;
}}
"""


def build_team_specific_css(slug: str, config: dict[str, Any]) -> str:
    if slug != "patriots":
        return ""

    accent = config["secondaryColor"]
    primary = config["primaryColor"]
    accent_10 = rgba_from_hex(accent, "0.10")
    accent_12 = rgba_from_hex(accent, "0.12")
    accent_18 = rgba_from_hex(accent, "0.18")
    accent_22 = rgba_from_hex(accent, "0.22")
    return f"""
/* Patriots-specific detail accents */
.hero-panel {{
  border-color: color-mix(in srgb, {accent} 18%, transparent) !important;
}}
.hero-panel::after {{
  background:
    radial-gradient(circle at 100% 0%, {accent_18}, transparent 30%) !important;
}}
.badge,
.hero-kicker,
.hero-btn.gold {{
  box-shadow: 0 0 0 1px color-mix(in srgb, {accent} 10%, transparent), 0 0 10px {accent_10} !important;
}}
.hero-btn.gold {{
  background: linear-gradient(135deg, {accent_18}, color-mix(in srgb, {primary} 16%, transparent)) !important;
  border-color: {accent_22} !important;
}}
.toggle.active,
.season-btn.active {{
  background: linear-gradient(180deg, {accent_12} 0%, color-mix(in srgb, {primary} 10%, transparent) 100%) !important;
  border-color: {accent_18} !important;
}}
"""


def apply_team_palette_tokens(text: str, config: dict[str, Any]) -> str:
    updated = text
    light_accent = config["lightThemePrimary"] if relative_luminance(config["lightThemePrimary"]) >= 0.2 else mix_hex(config["lightThemePrimary"], config["primaryColor"], 0.22)
    light_text = mix_hex("#172033", config["lightThemePrimary"], 0.18)
    light_muted = mix_hex("#5f6b7c", config["lightThemePrimary"], 0.24)
    light_placeholder = mix_hex("#7b8795", config["lightThemePrimary"], 0.22)
    static_replacements = {
        "#090012": config["darkBgStart"],
        "#180826": config["darkBgMid"],
        "#12021f": config["darkBgEnd"],
        "#030006": config["darkBgEnd"],
        "#c8aa32": config["secondaryColor"],
        "#d8b03e": config["secondaryColor"],
        "#d9b94f": config["secondaryColor"],
        "#f6f0ff": config["textOnDark"],
        "#f2ebfa": config["textOnDark"],
        "#f1eaf8": config["textOnDark"],
        "#efe7f8": config["textOnDark"],
        "#fff2c4": config["secondaryColor"],
        "#f0e8f8": config["textOnDark"],
        "#d6cfde": config["mutedOnDark"],
        "#cfc5d8": config["mutedOnDark"],
        "#c2b7cd": config["mutedOnDark"],
        "#8d7f99": config["mutedOnDark"],
        "#8e819a": config["mutedOnDark"],
        "#8a7a9a": config["mutedOnDark"],
        "#5d4d6d": config["mutedOnDark"],
        "#463655": config["mutedOnDark"],
        "#9b59b6": config["primaryColor"],
        "#e8e0f0": config["textOnDark"],
        "#7f4aa0": config["primaryColor"],
        "#24125F": config["primaryColor"],
        "#552a88": config["lightThemePrimary"],
        "#7a4cad": light_accent,
        "#4a2f6f": light_text,
        "#4f3375": light_text,
        "#3f2a63": light_text,
        "#2a1844": light_text,
        "#6f5f86": light_muted,
        "#6c5a85": light_muted,
        "#66557f": light_muted,
        "#5c4d73": light_muted,
        "#7c6b97": light_placeholder,
        "#7a6a92": light_placeholder,
        "#8d7aa5": light_placeholder,
        "#6e5d87": light_muted,
    }
    for old, new in static_replacements.items():
        updated = replace_hex_token(updated, old, new)
    updated = replace_rgba_family(updated, ("200,170,50", "216,176,62", "185,150,63", "166,124,0"), config["secondaryColor"])
    updated = replace_rgba_family(updated, ("8,2,15",), config["darkBgStart"])
    updated = replace_rgba_family(updated, ("24,8,38",), config["darkBgMid"])
    updated = replace_rgba_family(updated, ("9,0,18",), config["darkBgStart"])
    updated = replace_rgba_family(
        updated,
        ("155,89,182", "111,71,171", "36,18,95", "95,70,180", "108,64,166", "91,58,140", "126,87,194", "49,34,78", "111,71,171", "122,76,173", "91,58,140"),
        config["primaryColor"],
    )
    updated = replace_rgba_family(updated, ("111,71,171", "122,76,173", "91,58,140", "95,50,168", "108,66,178"), config["lightThemePrimary"])
    return updated


def render_team_page(slug: str, bundle: dict[str, Any]) -> str:
    meta = team_meta(slug)
    config = bundle["TEAM_CONFIG"]
    team_page_map = build_team_page_map()
    team_name = config["teamName"]
    team_short = config["shortName"]
    abbr = meta["espn_slug"].upper()
    first_rival = config["rivalryTeams"][0] if config["rivalryTeams"] else "Steelers"
    archive_seasons = max(1, config["seasonStartYear"] and (max(int(str(year)) for year in bundle["SEASON_EXTRA_DATA"].keys() if str(year).isdigit()) - config["seasonStartYear"] + 1))
    subtitle = f"Founded {config['foundedYear']} • {config['conference']} • {config['division']} • {archive_seasons} seasons archived"
    detail_pills_html = (
        f'<span class="note-pill">Founded {config["foundedYear"]}</span>'
        f'<span class="note-pill">{config["division"]}</span>'
        f'<span class="note-pill">{len(config["featuredSeasons"])} featured seasons</span>'
    )

    html = TEMPLATE_PATH.read_text(encoding="utf-8", errors="replace")
    html = apply_team_palette_tokens(html, config)
    html = replace_once(html, r"<title>.*?</title>", f"<title>{team_short} All-Time Database - Season Explorer</title>")
    html = html.replace(
        "</title>",
        f"</title>\n<link rel=\"icon\" type=\"image/png\" href=\"{config['favicon']}\">\n<link rel=\"apple-touch-icon\" href=\"{config['favicon']}\">",
        1,
    )
    html = html.replace('content="Complete Baltimore Ravens all-time game database with season explorer, featured games, and visual season trends since 1996."', f'content="Complete {team_name} all-time game database with season explorer, featured games, and visual season trends since {config["seasonStartYear"]}."')
    html = html.replace('content="Baltimore Ravens, Ravens all-time database, Ravens history, Ravens seasons, NFL stats, Ravens records"', f'content="{team_name}, {team_short} all-time database, {team_short} history, NFL stats, {team_short} records"')
    html = html.replace('content="#12021f"', f'content="{config["darkBgEnd"]}"')
    html = html.replace('content="Baltimore Ravens All-Time Database"', f'content="{team_name} All-Time Database"')
    html = html.replace('content="Explore every Ravens season, matchup, featured game, and visual trend since 1996."', f'content="Explore every {team_short} season, matchup, featured game, and visual trend since {config["seasonStartYear"]}."')
    html = replace_once(html, r'<div class="loader-badge">.*?</div>', f'<div class="loader-badge">{team_name}</div>')
    html = replace_once(
        html,
        r'<div class="badge">.*?</div>',
        f'<div class="badge">{config["badgeText"]}</div>\n    <img class="header-team-logo" src="{config["logoMain"]}" alt="{team_short} logo">',
    )
    html = replace_once(html, r'<p class="subtitle">.*?</p>', f'<p class="subtitle">{subtitle}</p>')
    html = replace_once(html, r'<div class="hero-kicker">.*?</div>', f'<div class="hero-kicker">{config["heroKicker"]}</div>')
    html = replace_once(html, r'<div class="hero-title">.*?</div>', f'<div class="hero-title">{config["heroTitle"]}</div>')
    html = replace_once(html, r'<p class="hero-text">.*?</p>', f'<p class="hero-text">{config["heroText"]}</p>')
    html = html.replace('<div class="eyebrow">Ravens Archive</div>', f'<div class="eyebrow">{team_short} Archive</div>')
    html = replace_once(
        html,
        r'<div class="section-note-row">\s*<span class="note-pill">Full schedule</span>\s*<span class="note-pill">Season metrics</span>\s*<span class="note-pill">Records & trends</span>\s*</div>',
        f'<div class="section-note-row">{detail_pills_html}</div>',
    )
    html = replace_once(html, r'<div class="footer-brand">.*?</div>', f'<div class="footer-brand">{team_name}<br>All-Time Database</div>')
    html = html.replace("© 2026 Ravens Game Archive • Built by Santi", f"© {SUPPORT_COPYRIGHT_YEAR} {config['copyrightLabel']} • Built by Santi")
    html = html.replace("It is also not affiliated with the Baltimore Ravens organization or any official partner.", f"It is also not affiliated with the {team_name} organization or any official partner.")
    html = html.replace(
        "This version uses ESPN&apos;s public, unofficial endpoints. It now only shows truly live NFL games. If the Ravens are not live, it falls back to another live game instead of showing idle placeholders.",
        f"This version uses ESPN&apos;s public, unofficial endpoints. It now only shows truly live NFL games. If the {team_short} are not live, it falls back to another live game instead of showing idle placeholders.",
    )
    html = html.replace('<div class="live-team-name" id="liveHomeName">Ravens</div>', f'<div class="live-team-name" id="liveHomeName">{team_short}</div>')
    html = html.replace('<div class="live-meta-value" id="livePossession">Ravens</div>', f'<div class="live-meta-value" id="livePossession">{team_short}</div>')
    html = html.replace("</style>", build_theme_css(config) + build_team_specific_css(slug, config) + "\n</style>", 1)

    html = replace_once(html, r"const ALL_GAMES = .*?;", "const TEAM_CONFIG = " + compact(bundle["TEAM_CONFIG"]) + ";\nconst ALL_GAMES = " + compact(bundle["ALL_GAMES"]) + ";")
    html = replace_once(html, r"const YEARS = .*?;", "const YEARS = [...new Set([...ALL_GAMES.map(g => g.year), ...Object.keys(SEASON_EXTRA_DATA).map(Number)])].sort((a,b) => a-b);")
    html = replace_once(html, r"const MATCH_DETAILS = .*?;", "const MATCH_DETAILS = " + compact(bundle["MATCH_DETAILS"]) + ";")
    html = replace_once(html, r"const SEASON_EXTRA_DATA = .*?;", "const SEASON_EXTRA_DATA = " + compact(bundle["SEASON_EXTRA_DATA"]) + ";")
    html = replace_once(
        html,
        r"const SEASON_PLAYERS = \{",
        "const RIVALRY_DATA = " + compact(bundle["RIVALRY_DATA"]) + ";\n"
        + "const PLAYER_FEATURES_BY_SEASON = " + compact(bundle["PLAYER_FEATURES_BY_SEASON"]) + ";\n"
        + "const FEATURED_GAMES = " + compact(bundle["FEATURED_GAMES"]) + ";\n"
        + "const TIMELINE_COPY = " + compact(bundle["TIMELINE_COPY"]) + ";\n"
        + "const TEAM_LOGO_MAP = " + compact(bundle["TEAM_LOGO_MAP"]) + ";\n"
        + "const TEAM_PAGE_MAP = " + compact(team_page_map) + ";\n"
        + "const SEASON_PLAYERS = {",
    )
    html = replace_once(html, r"const SEASON_PLAYERS = \{.*?\};\s*\nconst PLAYER_FALLBACK = \{.*?\};", "const SEASON_PLAYERS = PLAYER_FEATURES_BY_SEASON;\nconst PLAYER_FALLBACK = {};")
    html = replace_once(html, r"const PREVIEW_SEASON_DATA = \{.*?\};", "const PREVIEW_SEASON_DATA = {};")
    html = replace_chunk(
        html,
        "const ROSTER_2025 = [",
        "\n\nfunction renderPlayers(year) {",
        """const ROSTER_2025 = (PLAYER_FEATURES_BY_SEASON['2025'] || []).map((player) => ({
  slug: player.slug,
  name: player.name,
  role: player.role,
  img: teamLogo(TEAM_CONFIG.shortName),
  line1: player.subtitle || 'Featured player',
  line2: (player.facts || []).slice(0, 2).join(' • ')
}));

function renderRoster2025() {
  const summary = document.getElementById('playerSeasonSummary');
  const prompts = document.getElementById('playerPrompts');
  const cards = document.getElementById('playerCards');
  const detail = document.getElementById('playerDetail');

  summary.innerHTML = `2025 StatMuse roster preview: <strong>${ROSTER_2025.map(p => p.name).join(', ')}</strong>.`;
  prompts.innerHTML = `<div class="roster-subhead">2025 player cards pulled from the 2025 ${TEAM_CONFIG.shortName} StatMuse team stats page.</div>`;
  cards.innerHTML = `<div class="roster-grid">
    ${ROSTER_2025.map(p => `
      <div class="roster-card">
        <img src="${p.img}" alt="${p.name}">
        <div class="roster-meta">
          <div class="roster-role">${p.role}</div>
          <div class="roster-name">${p.name}</div>
          <div class="roster-line">${p.line1}</div>
          <div class="roster-line">${p.line2}</div>
        </div>
      </div>
    `).join('')}
  </div>`;
  detail.innerHTML = '';
}
""",
    )
    html = replace_chunk(html, "function franchiseTimelineData() {", "\n\nfunction renderFranchiseInsights() {", "function franchiseTimelineData() {\n  return TIMELINE_COPY;\n}\n")
    html = replace_chunk(
        html,
        "function teamMeta(name) {",
        "\n\nfunction formatRecord(games) {",
        """function teamMeta(name) {
  const n = normalizeTeamName(name);
  return TEAM_META[n] || {abbr: String(name || '?').slice(0,3).toUpperCase(), bg: TEAM_CONFIG.primaryColor, fg: TEAM_CONFIG.textOnDark};
}
function fallbackLogoDataUri(name) {
  const raw = String(name || '?').trim();
  const label = (raw.match(/[A-Za-z0-9]+/g) || ['?']).slice(0, 3).map((part) => part[0]).join('').slice(0, 3).toUpperCase() || '?';
  const bg = encodeURIComponent(TEAM_CONFIG.primaryColor || '#1f2937');
  const fg = encodeURIComponent(TEAM_CONFIG.textOnDark || '#ffffff');
  const ring = encodeURIComponent(TEAM_CONFIG.secondaryColor || '#cbd5e1');
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="18" fill="${bg}"/><rect x="3" y="3" width="58" height="58" rx="15" fill="none" stroke="${ring}" stroke-width="3"/><text x="32" y="39" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="${fg}">${label}</text></svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}
function teamLogo(name) {
  const key = normalizeTeamName(name);
  return TEAM_LOGO_MAP[key] || TEAM_LOGO_MAP[String(name || '').trim()] || fallbackLogoDataUri(name);
}
function teamPageUrl(teamName, params = {}) {
  if (typeof TEAM_PAGE_MAP === 'undefined') return '';
  const key = normalizeTeamName(teamName);
  const page = TEAM_PAGE_MAP[key] || TEAM_PAGE_MAP[String(teamName || '').trim()] || '';
  if (!page) return '';
  const url = new URL(page, window.location.href);
  Object.entries(params).forEach(([paramKey, value]) => {
    if (value !== null && value !== undefined && String(value).trim()) {
      url.searchParams.set(paramKey, String(value));
    }
  });
  return url.toString();
}
function compareSearchQueryFor(game) {
  const teamLabel = typeof TEAM_CONFIG !== 'undefined' ? (TEAM_CONFIG.shortName || TEAM_CONFIG.teamName || 'Ravens') : 'Ravens';
  return `vs ${teamLabel} ${game.year}${game.isPlayoff ? ' playoffs' : ''}`;
}
function leagueWideSearchUrlFor(game) {
  const teamLabel = typeof TEAM_CONFIG !== 'undefined' ? (TEAM_CONFIG.shortName || TEAM_CONFIG.teamName || 'Ravens') : 'Ravens';
  const query = `${teamLabel} vs ${game.opponent} ${game.year} ${game.round}`;
  return `https://www.statmuse.com/nfl/ask?q=${encodeURIComponent(query)}`;
}
function applyUrlStateFromLocation() {
  const params = new URLSearchParams(window.location.search);
  const searchParam = String(params.get('search') || '').trim();
  const yearParam = String(params.get('year') || '').trim();
  const viewParam = String(params.get('view') || '').trim();

  if (searchParam) {
    state.search = searchParam;
    state.isHistorical = false;
  }
  if (yearParam && YEARS.includes(Number(yearParam))) {
    state.selectedYear = yearParam;
  }
  if (['all', 'regular', 'playoffs'].includes(viewParam)) {
    state.filterMode = viewParam;
  }

  const searchInput = document.getElementById('seasonSearch');
  if (searchInput) searchInput.value = state.search;
  document.querySelectorAll('.toggle').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.view === state.filterMode);
  });
}
""",
    )
    html = replace_chunk(
        html,
        "function getFeaturedGames() {",
        "\n\nfunction renderFeaturedGames() {",
        """function getFeaturedGames() {
  return FEATURED_GAMES.map((pick) => ALL_GAMES.find((game) => [game.year, game.round.trim(), game.opponent, game.location, `${game.ravensScore}-${game.oppScore}`].join('|') === pick.key)).filter(Boolean);
}
""",
    )
    html = replace_chunk(
        html,
        "function seasonCoach(year) {",
        "\n\nfunction seasonOutcomeLabel(year) {",
        """function seasonCoach(year) {
  return TEAM_CONFIG.headCoach || '—';
}
""",
    )
    html = replace_once(html, r"const RAVENS_HIGHLIGHT_LINKS = .*?;", "const RAVENS_HIGHLIGHT_LINKS = {};")
    html = replace_once(html, r"const RAVENS_RECAP_LINKS = .*?;", "const RAVENS_RECAP_LINKS = {};")
    html = replace_chunk(html, "const VENUE_MAP = {", "\nvar timelineInterval = null;", "const VENUE_MAP = " + compact({k: v for k, v in {"49ers": {"city": "San Francisco", "badge": "NFC West"}, "Bears": {"city": "Chicago", "badge": "NFC North"}, "Bengals": {"city": "Cincinnati", "badge": "AFC North"}, "Bills": {"city": "Buffalo", "badge": "AFC East"}, "Broncos": {"city": "Denver", "badge": "AFC West"}, "Browns": {"city": "Cleveland", "badge": "AFC North"}, "Buccaneers": {"city": "Tampa Bay", "badge": "NFC South"}, "Cardinals": {"city": "Arizona / St. Louis / Chicago", "badge": "Historic Franchise"}, "Chargers": {"city": "Los Angeles / San Diego", "badge": "AFC West"}, "Chiefs": {"city": "Kansas City", "badge": "AFC West"}, "Colts": {"city": "Indianapolis / Baltimore", "badge": "AFC South"}, "Commanders": {"city": "Washington", "badge": "NFC East"}, "Cowboys": {"city": "Dallas", "badge": "NFC East"}, "Dolphins": {"city": "Miami", "badge": "AFC East"}, "Eagles": {"city": "Philadelphia", "badge": "NFC East"}, "Falcons": {"city": "Atlanta", "badge": "NFC South"}, "Giants": {"city": "New York", "badge": "NFC East"}, "Jaguars": {"city": "Jacksonville", "badge": "AFC South"}, "Jets": {"city": "New York", "badge": "AFC East"}, "Lions": {"city": "Detroit", "badge": "NFC North"}, "Packers": {"city": "Green Bay", "badge": "NFC North"}, "Panthers": {"city": "Charlotte", "badge": "NFC South"}, "Patriots": {"city": "Foxborough", "badge": "AFC East"}, "Raiders": {"city": "Las Vegas / Oakland / Los Angeles", "badge": "AFC West"}, "Rams": {"city": "Los Angeles / St. Louis / Cleveland", "badge": "NFC West"}, "Ravens": {"city": "Baltimore", "badge": "AFC North"}, "Saints": {"city": "New Orleans", "badge": "NFC South"}, "Seahawks": {"city": "Seattle", "badge": "NFC West"}, "Steelers": {"city": "Pittsburgh", "badge": "AFC North"}, "Texans": {"city": "Houston", "badge": "AFC South"}, "Titans": {"city": "Tennessee / Houston", "badge": "AFC South"}, "Vikings": {"city": "Minnesota", "badge": "NFC North"}}.items()}) + ";\n\nvar rivalryState = '" + first_rival + "';\n")
    html = html.replace("return `${year}'s headline Raven here is <strong>${first.name}</strong>, the cleanest quick answer for this season's identity.`;", "return `${year}'s headline player here is <strong>${first.name}</strong>, the cleanest quick answer for this season's identity.`;")
    html = html.replace("document.getElementById('seasonTitle').textContent = `${year} Baltimore Ravens`;", "document.getElementById('seasonTitle').textContent = `${year} ${SEASON_EXTRA_DATA[String(year)]?.team_name || TEAM_CONFIG.teamName}`;")
    html = html.replace("<thead><tr><th>Round</th><th>Opponent</th><th>Loc</th><th>BAL</th><th>OPP</th><th>Margin</th><th>Result</th></tr></thead>", f"<thead><tr><th>Round</th><th>Opponent</th><th>Loc</th><th>{abbr}</th><th>OPP</th><th>Margin</th><th>Result</th></tr></thead>")
    html = html.replace("<thead><tr>${usingSearchResults ? '<th>Year</th>' : ''}<th>Round</th><th>Opponent</th><th>Loc</th><th>BAL</th><th>OPP</th><th>Margin</th><th>Result</th></tr></thead><tbody>", f"<thead><tr>${{usingSearchResults ? '<th>Year</th>' : ''}}<th>Round</th><th>Opponent</th><th>Loc</th><th>{abbr}</th><th>OPP</th><th>Margin</th><th>Result</th></tr></thead><tbody>")
    html = html.replace("<img class=\"score-team-logo\" src=\"${teamLogo('Ravens')}\" alt=\"Ravens logo\">", f"<img class=\"score-team-logo\" src=\"${{teamLogo(TEAM_CONFIG.shortName)}}\" alt=\"{team_short} logo\">")
    html = html.replace("<div class=\"score-team-name\">Ravens</div>", f"<div class=\"score-team-name\">{team_short}</div>")
    html = html.replace("<strong>Ravens ${sim.ravensScore}-${sim.oppScore} ${sim.opponent}</strong>", f"<strong>{team_short} ${{sim.ravensScore}}-${{sim.oppScore}} ${{sim.opponent}}</strong>")
    html = html.replace("<div class=\"extra-card\"><span>Coach</span><strong>John Harbaugh</strong></div>", "<div class=\"extra-card\"><span>Coach</span><strong>${TEAM_CONFIG.headCoach || '—'}</strong></div>")
    html = html.replace("setText(els.homeName, 'Ravens');", f"setText(els.homeName, '{team_short}');")
    html = html.replace("setText(els.down, 'No live Ravens game');", f"setText(els.down, 'No live {team_short} game');")
    html = html.replace("setText(els.last, 'Waiting for a live Ravens game.');", f"setText(els.last, 'Waiting for a live {team_short} game.');")
    html = html.replace("return name === 'baltimore ravens' || shortName === 'ravens' || abbrev === 'bal';", f"return name === '{team_name.lower()}' || shortName === '{team_short.lower()}' || abbrev === '{meta['espn_slug']}';")
    html = html.replace("const ravens = teams.find(t => String(t?.team?.abbreviation || '').toLowerCase() === 'bal' || String(t?.team?.displayName || '').toLowerCase() === 'baltimore ravens') || null;", f"const ravens = teams.find(t => String(t?.team?.abbreviation || '').toLowerCase() === '{meta['espn_slug']}' || String(t?.team?.displayName || '').toLowerCase() === '{team_name.lower()}') || null;")
    html = html.replace('<div class="live-center-meta">Ravens</div>', f'<div class="live-center-meta">{team_short}</div>')
    html = html.replace("Every meeting between Baltimore and ${team}, with click-to-jump back to the original season game.", f"Every meeting between {team_name} and ${{team}}, with click-to-jump back to the original season game.")
    html = html.replace("<thead><tr><th>Year</th><th>Round</th><th>Loc</th><th>BAL</th><th>OPP</th><th>Result</th></tr></thead><tbody>", f"<thead><tr><th>Year</th><th>Round</th><th>Loc</th><th>{abbr}</th><th>OPP</th><th>Result</th></tr></thead><tbody>")
    html = html.replace("const isRavens = row.team === 'Ravens';", f"const isRavens = row.team === '{team_short}';")
    html = html.replace(
        "As of March 16, 2026, the Ravens' exact week-by-week schedule has not been released yet, so game cards stay in preview mode for now. These links still take you to the main live score hubs once the season is posted.",
        f"As of March 16, 2026, the {team_short} exact week-by-week schedule has not been released yet, so game cards stay in preview mode for now. These links still take you to the main live score hubs once the season is posted.",
    )
    copy_replacements = {
        "Ravens vs Teams — Historical Match Browser": f"{team_short} vs Teams — Historical Match Browser",
        "<strong>Ravens vs ${team}</strong>": f"<strong>{team_short} vs ${{team}}</strong>",
        "Lower is better here, so these are the stingiest Ravens defenses.": f"Lower is better here, so these are the stingiest {team_short} defenses.",
        "One of the biggest Ravens wins in the file.": f"One of the biggest {team_short} wins in the file.",
        "A strong Ravens game worth surfacing on the homepage.": f"A signature {team_short} game worth surfacing on the homepage.",
        "<span>Biggest Ravens win</span>": f"<span>Biggest {team_short} win</span>",
        "<span>Worst Ravens loss</span>": f"<span>Worst {team_short} loss</span>",
        "<strong>Ravens ${g.ravensScore}-${g.oppScore} ${g.opponent}</strong>": f"<strong>{team_short} ${{g.ravensScore}}-${{g.oppScore}} ${{g.opponent}}</strong>",
        "A fan-made historical archive to browse every Ravens season, matchup, and game result in one place.": f"A fan-made historical archive to browse every {team_short} season, matchup, and game result in one place.",
        "Showing live Ravens coverage.": f"Showing live {team_short} coverage.",
        "Ravens are not live right now — showing this live NFL game: ": f"{team_short} are not live right now — showing this live NFL game: ",
    }
    for old, new in copy_replacements.items():
        html = html.replace(old, new)
    html = html.replace(
        "renderFooter();",
        """function pruneEmptyCards() {
  document.querySelectorAll('.hero-stat-card, .stat-card, .extra-card').forEach((card) => {
    if (!card.textContent.trim()) {
      card.remove();
    }
  });
}

renderFooter();
pruneEmptyCards();""",
        1,
    )
    return html


def build_rivalry_data(all_games: list[dict[str, Any]], rivals: list[str]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for rival in rivals:
        games = [game for game in all_games if game["opponent"] == rival]
        if not games:
            continue
        wins = sum(1 for game in games if game["result"] == "W")
        losses = sum(1 for game in games if game["result"] == "L")
        ties = sum(1 for game in games if game["result"] == "T")
        payload[rival] = {
            "games": len(games),
            "record": f"{wins}-{losses}" + (f"-{ties}" if ties else ""),
            "recent": games[-5:][::-1],
            "firstMeeting": games[0],
            "lastMeeting": games[-1],
        }
    return payload


def build_featured_games(all_games: list[dict[str, Any]], featured_years: list[int]) -> list[dict[str, Any]]:
    picks: list[dict[str, Any]] = []
    for year in featured_years:
        season_games = [game for game in all_games if game["year"] == year]
        if not season_games:
            continue
        postseason = [game for game in season_games if game["isPlayoff"]]
        target = postseason[-1] if postseason else max(season_games, key=lambda game: abs(game["ravensScore"] - game["oppScore"]))
        picks.append({"key": build_match_key(target), **target})
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for game in picks:
        if game["key"] in seen:
            continue
        seen.add(game["key"])
        unique.append(game)
    if len(unique) < 4:
        filler_games = sorted(
            all_games,
            key=lambda game: (
                1 if game.get("isPlayoff") else 0,
                abs(int(game.get("ravensScore", 0)) - int(game.get("oppScore", 0))),
                int(game.get("year", 0)),
            ),
            reverse=True,
        )
        for game in filler_games:
            key = build_match_key(game)
            if key in seen:
                continue
            seen.add(key)
            unique.append({"key": key, **game})
            if len(unique) == 4:
                break
    return unique[:4]


def derive_playoff_result(playoff_games: list[dict[str, Any]]) -> str:
    if not playoff_games:
        return "Missed playoffs"
    last_game = playoff_games[-1]
    round_name = clean(last_game.get("round"))
    result = clean(last_game.get("result"))
    if "Super Bowl" in round_name:
        return "Won Super Bowl" if result == "W" else "Lost Super Bowl"
    if "Conference Championship" in round_name:
        return "Won conference" if result == "W" else "Lost conference championship"
    if "Divisional" in round_name:
        return "Reached conference championship" if result == "W" else "Lost divisional round"
    if "Wild Card" in round_name:
        return "Reached divisional round" if result == "W" else "Lost wild card round"
    return f"{round_name} ({result})" if round_name else "Made playoffs"


def build_timeline_copy(team_name: str, season_extra: dict[str, Any], featured_games: list[dict[str, Any]], identity_note: str) -> list[dict[str, Any]]:
    years = sorted(int(year) for year in season_extra)
    if not years:
        return []
    timeline = [
        {
            "year": str(years[0]),
            "title": "Opening chapter",
            "copy": f"{team_name} enters the archive in {years[0]}. {identity_note}",
        }
    ]
    for game in featured_games[:5]:
        timeline.append(
            {
                "year": str(game["year"]),
                "title": f"{game['round']} vs {game['opponent']}",
                "copy": f"Final score: {game['ravensScore']}-{game['oppScore']} ({game['result']}). One of the signature games surfaced automatically from the franchise file.",
            }
        )
    return timeline


def build_team_logo_map() -> dict[str, str]:
    payload: dict[str, str] = {}
    for slug, meta in TEAM_CATALOG.items():
        url = f"https://a.espncdn.com/i/teamlogos/nfl/500/{meta['espn_slug']}.png"
        payload[slug] = url
        payload[meta["short_name"].lower()] = url
        payload[meta["team_name"].lower()] = url
        payload[meta["espn_slug"].lower()] = url
    for alias, alias_slug in FRANCHISE_NAME_ALIASES.items():
        if alias_slug not in payload:
            continue
        payload[alias] = payload[alias_slug]
        compact_alias = alias.replace(".", "")
        if compact_alias != alias:
            payload[compact_alias] = payload[alias_slug]
    for code_map in (TEAM_NAME_ALIASES, HISTORIC_CODE_NAME_ALIASES):
        for code, team_name in code_map.items():
            alias_slug = resolve_franchise_slug(team_name)
            if not alias_slug or alias_slug not in payload:
                continue
            payload[code.lower()] = payload[alias_slug]
    return payload


def build_team_page_map() -> dict[str, str]:
    payload: dict[str, str] = {}
    for slug, meta in TEAM_CATALOG.items():
        filename = f"{slug}.html"
        legacy_filename = f"{slug}database.html"
        if not (TEAMS_DIR / filename).exists() and (TEAMS_DIR / legacy_filename).exists():
            filename = legacy_filename
        payload[slug] = filename
        payload[meta["short_name"].lower()] = filename
        payload[meta["team_name"].lower()] = filename
        payload[meta["espn_slug"].lower()] = filename
    return payload


def build_franchise_name_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for slug, meta in TEAM_CATALOG.items():
        aliases[meta["short_name"].lower()] = slug
        aliases[meta["team_name"].lower()] = slug
    aliases.update(
        {
            "redskins": "commanders",
            "washington redskins": "commanders",
            "washington football team": "commanders",
            "football team": "commanders",
            "oilers": "titans",
            "houston oilers": "titans",
            "tennessee oilers": "titans",
            "oakland raiders": "raiders",
            "los angeles raiders": "raiders",
            "st. louis rams": "rams",
            "los angeles rams": "rams",
            "st. louis cardinals": "cardinals",
            "phoenix cardinals": "cardinals",
            "san diego chargers": "chargers",
            "boston patriots": "patriots",
        }
    )
    return aliases


FRANCHISE_NAME_ALIASES = build_franchise_name_aliases()


def resolve_franchise_slug(name: str) -> str | None:
    cleaned = clean(name)
    slug = FRANCHISE_NAME_ALIASES.get(cleaned.lower())
    if slug:
        return slug
    code = cleaned.upper()
    mapped = TEAM_NAME_ALIASES.get(code) or HISTORIC_CODE_NAME_ALIASES.get(code)
    return FRANCHISE_NAME_ALIASES.get(clean(mapped).lower()) if mapped else None


def resolve_game_opponent_slug(name: str, season_year: int | None = None) -> str | None:
    if season_year is not None:
        normalized = normalize_opponent(name, season_year)
        slug = resolve_franchise_slug(normalized)
        if slug:
            return slug
    return resolve_franchise_slug(name)


def stat_team_abbreviation(name: str, season_year: int | None = None, fallback_code: str = "") -> str:
    code = clean(fallback_code).upper()
    if code and re.fullmatch(r"[A-Z0-9]{2,4}", code):
        return code
    slug = resolve_game_opponent_slug(name, season_year)
    if slug:
        return team_meta(slug)["espn_slug"].upper()
    cleaned = clean(name)
    initials = "".join(part[0] for part in re.findall(r"[A-Za-z0-9]+", cleaned)[:3]).upper()
    return initials or cleaned[:3].upper() or "NFL"


def build_youtube_summary_url(team_name: str, game: dict[str, Any]) -> str:
    query = " ".join(
        part
        for part in [str(game.get("year") or ""), team_name, "vs", game.get("opponent") or "", game.get("round") or "", "NFL highlights", "site:youtube.com/watch"]
        if clean(part)
    )
    return f"https://www.google.com/search?btnI=I&q={quote_plus(query)}"


def parse_box_stat_number(value: Any) -> int | None:
    text = clean(value).replace(",", "")
    return int(text) if text.isdigit() else None


def normalize_box_count(value: Any) -> str:
    number = parse_box_stat_number(value)
    return str(number) if number is not None else ""


def parse_box_stat_float(value: Any) -> float | None:
    text = clean(value).replace(",", "")
    if not text or not re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        return None
    return float(text)


def normalize_box_stat(value: Any) -> str:
    return clean(value) or ""


def format_box_rate(value: float | None) -> str:
    if value is None:
        return ""
    rounded = round(value, 1)
    if rounded.is_integer():
        return str(int(rounded))
    return f"{rounded:.1f}"


def resolve_total_yards(total: Any, passing: Any, rushing: Any) -> str:
    passing_num = parse_box_stat_number(passing)
    rushing_num = parse_box_stat_number(rushing)
    if passing_num is not None and rushing_num is not None:
        return str(passing_num + rushing_num)
    total_num = parse_box_stat_number(total)
    if total_num is not None:
        return str(total_num)
    total_text = normalize_box_stat(total)
    return total_text if total_text else ""


def resolve_total_plays(total_plays: Any, pass_attempts: Any, rush_attempts: Any, total_yards: Any = None, yards_per_play: Any = None) -> str:
    pass_attempts_num = parse_box_stat_number(pass_attempts)
    rush_attempts_num = parse_box_stat_number(rush_attempts)
    if pass_attempts_num is not None and rush_attempts_num is not None:
        return str(pass_attempts_num + rush_attempts_num)
    total_yards_num = parse_box_stat_float(total_yards)
    yards_per_play_num = parse_box_stat_float(yards_per_play)
    if total_yards_num is not None and yards_per_play_num not in (None, 0):
        return str(int(round(total_yards_num / yards_per_play_num)))
    total_plays_text = normalize_box_stat(total_plays)
    return total_plays_text if total_plays_text else ""


def resolve_rate(primary: Any, numerator: Any, denominator: Any) -> str:
    numerator_num = parse_box_stat_float(numerator)
    denominator_num = parse_box_stat_float(denominator)
    if numerator_num is not None and denominator_num not in (None, 0):
        return format_box_rate(numerator_num / denominator_num)
    primary_text = normalize_box_stat(primary)
    return primary_text if primary_text else ""


def resolve_turnover_component(primary: Any, turnovers: Any, counterpart: Any) -> str:
    primary_num = parse_box_stat_number(primary)
    if primary_num is not None:
        return str(primary_num)
    turnovers_num = parse_box_stat_number(turnovers)
    counterpart_num = parse_box_stat_number(counterpart)
    if turnovers_num is None or counterpart_num is None:
        return ""
    derived = turnovers_num - counterpart_num
    if derived < 0:
        return ""
    return str(derived)


def resolve_attempts(primary: Any, yards: Any, yards_per_attempt: Any) -> str:
    primary_num = parse_box_stat_number(primary)
    if primary_num is not None:
        return str(primary_num)
    yards_num = parse_box_stat_float(yards)
    yards_per_attempt_num = parse_box_stat_float(yards_per_attempt)
    if yards_num is None or yards_per_attempt_num in (None, 0):
        return normalize_box_stat(primary)
    return str(int(round(yards_num / yards_per_attempt_num)))


def resolve_yards(primary: Any, attempts: Any, yards_per_attempt: Any) -> str:
    primary_num = parse_box_stat_number(primary)
    if primary_num is not None:
        return str(primary_num)
    attempts_num = parse_box_stat_float(attempts)
    yards_per_attempt_num = parse_box_stat_float(yards_per_attempt)
    if attempts_num is None or yards_per_attempt_num is None:
        return normalize_box_stat(primary)
    return str(int(round(attempts_num * yards_per_attempt_num)))


def apply_side_derived_stats(game: dict[str, Any], prefix: str = "") -> None:
    key = lambda field: f"{prefix}{field[0].upper()}{field[1:]}" if prefix else field
    game[key("passingYards")] = normalize_box_count(game.get(key("passingYards"))) or clean(game.get(key("passingYards")))
    game[key("rushingYards")] = normalize_box_count(game.get(key("rushingYards"))) or clean(game.get(key("rushingYards")))
    game[key("turnovers")] = normalize_box_count(game.get(key("turnovers"))) or clean(game.get(key("turnovers")))
    game[key("firstDowns")] = normalize_box_count(game.get(key("firstDowns"))) or clean(game.get(key("firstDowns")))
    game[key("passAttempts")] = normalize_box_count(game.get(key("passAttempts"))) or clean(game.get(key("passAttempts")))
    game[key("rushAttempts")] = normalize_box_count(game.get(key("rushAttempts"))) or clean(game.get(key("rushAttempts")))
    game[key("punts")] = normalize_box_count(game.get(key("punts"))) or clean(game.get(key("punts")))
    game[key("penalties")] = normalize_box_count(game.get(key("penalties"))) or clean(game.get(key("penalties")))
    game[key("sacks")] = normalize_box_count(game.get(key("sacks"))) or clean(game.get(key("sacks")))
    game[key("fumblesLost")] = resolve_turnover_component(
        game.get(key("fumblesLost")),
        game.get(key("turnovers")),
        game.get(key("interceptionsThrown")),
    )
    game[key("interceptionsThrown")] = resolve_turnover_component(
        game.get(key("interceptionsThrown")),
        game.get(key("turnovers")),
        game.get(key("fumblesLost")),
    )
    game[key("passAttempts")] = resolve_attempts(game.get(key("passAttempts")), game.get(key("passingYards")), game.get(key("yardsPerPass")))
    game[key("rushAttempts")] = resolve_attempts(game.get(key("rushAttempts")), game.get(key("rushingYards")), game.get(key("yardsPerRush")))
    game[key("passingYards")] = resolve_yards(game.get(key("passingYards")), game.get(key("passAttempts")), game.get(key("yardsPerPass")))
    game[key("rushingYards")] = resolve_yards(game.get(key("rushingYards")), game.get(key("rushAttempts")), game.get(key("yardsPerRush")))
    game[key("totalYards")] = resolve_total_yards(game.get(key("totalYards")), game.get(key("passingYards")), game.get(key("rushingYards")))
    game[key("totalPlays")] = resolve_total_plays(
        game.get(key("totalPlays")),
        game.get(key("passAttempts")),
        game.get(key("rushAttempts")),
        game.get(key("totalYards")),
        game.get(key("yardsPerPlay")),
    )
    game[key("yardsPerPlay")] = resolve_rate(game.get(key("yardsPerPlay")), game.get(key("totalYards")), game.get(key("totalPlays")))
    game[key("yardsPerPass")] = resolve_rate(game.get(key("yardsPerPass")), game.get(key("passingYards")), game.get(key("passAttempts")))
    game[key("yardsPerRush")] = resolve_rate(game.get(key("yardsPerRush")), game.get(key("rushingYards")), game.get(key("rushAttempts")))


def apply_derived_game_stats(game: dict[str, Any]) -> None:
    apply_side_derived_stats(game)
    apply_side_derived_stats(game, "opponent")


GAME_STAT_COMPARE_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("Total Yds", "totalYards", "opponentTotalYards"),
    ("Pass Yds", "passingYards", "opponentPassingYards"),
    ("Rush Yds", "rushingYards", "opponentRushingYards"),
    ("Total Plays", "totalPlays", "opponentTotalPlays"),
    ("Yards Per Play", "yardsPerPlay", "opponentYardsPerPlay"),
    ("Yards Per Pass", "yardsPerPass", "opponentYardsPerPass"),
    ("Yards Per Rush", "yardsPerRush", "opponentYardsPerRush"),
    ("Possession", "possession", "opponentPossession"),
    ("1st Downs", "firstDowns", "opponentFirstDowns"),
    ("Punts", "punts", "opponentPunts"),
    ("Turnovers", "turnovers", "opponentTurnovers"),
    ("Interceptions Thrown", "interceptionsThrown", "opponentInterceptionsThrown"),
    ("Fumbles Lost", "fumblesLost", "opponentFumblesLost"),
    ("Penalties", "penalties", "opponentPenalties"),
    ("Sacks", "sacks", "opponentSacks"),
)


HISTORICAL_STAT_TRACKING_CUTOFFS: dict[str, int] = {
    "Possession": 1984,
    "Punts": 1980,
    "Penalties": 1980,
    "Total Plays": 1980,
    "Yards Per Play": 1980,
    "Yards Per Rush": 1980,
}


def display_stat_value(value: Any, stat: str, year: int | None) -> str:
    text = clean(value)
    if text:
        return text
    cutoff_year = HISTORICAL_STAT_TRACKING_CUTOFFS.get(stat)
    if cutoff_year is not None and year is not None and year < cutoff_year:
        return "Not tracked"
    return "Unavailable"


def merge_game_stat_fields(target: dict[str, Any], source: dict[str, Any]) -> None:
    for field in (
        "totalYards",
        "opponentTotalYards",
        "passingYards",
        "rushingYards",
        "totalPlays",
        "yardsPerPlay",
        "yardsPerPass",
        "yardsPerRush",
        "turnovers",
        "firstDowns",
        "possession",
        "punts",
        "interceptionsThrown",
        "fumblesLost",
        "penalties",
        "sacks",
        "passAttempts",
        "rushAttempts",
        "opponentPassingYards",
        "opponentRushingYards",
        "opponentTotalPlays",
        "opponentYardsPerPlay",
        "opponentYardsPerPass",
        "opponentYardsPerRush",
        "opponentTurnovers",
        "opponentFirstDowns",
        "opponentPossession",
        "opponentPunts",
        "opponentInterceptionsThrown",
        "opponentFumblesLost",
        "opponentPenalties",
        "opponentSacks",
    ):
        value = clean(source.get(field))
        if value:
            target[field] = value
    apply_derived_game_stats(target)


def refresh_playoff_game_stats(slug: str, bundle: dict[str, Any]) -> None:
    meta = team_meta(slug)
    playoff_games = [game for game in bundle["ALL_GAMES"] if game.get("isPlayoff")]
    if not playoff_games:
        return
    lookup: dict[tuple[str, str, int, int], list[dict[str, Any]]] = {}
    for game in playoff_games:
        key = (
            clean(game.get("date")),
            resolve_game_opponent_slug(game.get("opponent", ""), int(game.get("year", 0)) if int(game.get("year", 0)) else None) or clean(game.get("opponent")),
            int(game.get("ravensScore", 0)),
            int(game.get("oppScore", 0)),
        )
        lookup.setdefault(key, []).append(game)
    playoff_years = sorted({int(game["year"]) for game in playoff_games})
    for year in playoff_years:
        rows = parse_game_log_rows(
            f"{meta['team_name']} playoff game log {year} including passing yards rushing yards turnovers first downs time of possession",
            year,
        )
        for row in rows:
            key = (
                clean(row.get("date")),
                resolve_game_opponent_slug(row.get("opponent", ""), int(row.get("year", 0)) if int(row.get("year", 0)) else year) or clean(row.get("opponent")),
                int(row.get("ravensScore", 0)),
                int(row.get("oppScore", 0)),
            )
            for game in lookup.get(key, []):
                merge_game_stat_fields(game, row)


def refresh_bundle_game_stats(slug: str, bundle: dict[str, Any]) -> None:
    meta = team_meta(slug)
    all_games = bundle["ALL_GAMES"]
    if not all_games:
        return
    lookup: dict[tuple[str, str, int, int], list[dict[str, Any]]] = {}
    for game in all_games:
        key = (
            clean(game.get("date")),
            resolve_game_opponent_slug(game.get("opponent", ""), int(game.get("year", 0)) if int(game.get("year", 0)) else None) or clean(game.get("opponent")),
            int(game.get("ravensScore", 0)),
            int(game.get("oppScore", 0)),
        )
        lookup.setdefault(key, []).append(game)
    years = sorted({int(game["year"]) for game in all_games if int(game.get("year", 0))})
    for year in years:
        queries = (
            f"{meta['team_name']} game log {year} including passing yards rushing yards turnovers first downs time of possession",
            f"{meta['team_name']} playoff game log {year} including passing yards rushing yards turnovers first downs time of possession",
        )
        for query in queries:
            for row in parse_game_log_rows(query, year):
                key = (
                    clean(row.get("date")),
                    resolve_game_opponent_slug(row.get("opponent", ""), int(row.get("year", 0)) if int(row.get("year", 0)) else year) or clean(row.get("opponent")),
                    int(row.get("ravensScore", 0)),
                    int(row.get("oppScore", 0)),
                )
                for game in lookup.get(key, []):
                    merge_game_stat_fields(game, row)


def matchup_lookup_key(slug: str, game: dict[str, Any], opponent_slug: str | None = None) -> tuple[str, str, str | None, int, int]:
    season_year = int(game.get("year", 0)) if int(game.get("year", 0)) else None
    return (
        slug,
        clean(game.get("date")),
        opponent_slug or resolve_game_opponent_slug(game.get("opponent", ""), season_year),
        int(game.get("ravensScore", 0)),
        int(game.get("oppScore", 0)),
    )


def build_league_game_index(bundles: dict[str, dict[str, Any]]) -> dict[tuple[str, str, str | None, int, int], list[dict[str, Any]]]:
    index: dict[tuple[str, str, str | None, int, int], list[dict[str, Any]]] = {}
    for slug, bundle in bundles.items():
        for game in bundle["ALL_GAMES"]:
            key = matchup_lookup_key(slug, game)
            index.setdefault(key, []).append(game)
    return index


def find_counterpart_game(slug: str, game: dict[str, Any], league_index: dict[tuple[str, str, str | None, int, int], list[dict[str, Any]]]) -> dict[str, Any] | None:
    season_year = int(game.get("year", 0)) if int(game.get("year", 0)) else None
    opponent_slug = resolve_game_opponent_slug(game.get("opponent", ""), season_year)
    if not opponent_slug:
        return None
    matches = league_index.get((opponent_slug, clean(game.get("date")), slug, int(game.get("oppScore", 0)), int(game.get("ravensScore", 0))), [])
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]
    for candidate in matches:
        if candidate.get("location") != game.get("location"):
            return candidate
    return matches[0]


def build_team_stat_detail(team_abbr: str, game: dict[str, Any], counterpart: dict[str, Any] | None) -> dict[str, Any]:
    season_year = int(game.get("year", 0)) if int(game.get("year", 0)) else None
    right_team = stat_team_abbreviation(game.get("opponent", ""), season_year, game.get("opponentCode", ""))
    if counterpart:
        apply_derived_game_stats(counterpart)
        for source_field, target_field in (("passAttempts", "opponentPassAttempts"), ("rushAttempts", "opponentRushAttempts")):
            counterpart_value = counterpart.get(source_field)
            if clean(counterpart_value):
                game[target_field] = counterpart_value
        for _, field, opponent_field in GAME_STAT_COMPARE_FIELDS:
            counterpart_value = counterpart.get(field)
            if clean(counterpart_value):
                game[opponent_field] = counterpart_value
    apply_derived_game_stats(game)
    game["opponentTotalYards"] = resolve_total_yards(game.get("opponentTotalYards"), game.get("opponentPassingYards"), game.get("opponentRushingYards"))
    game["opponentTotalPlays"] = resolve_total_plays(game.get("opponentTotalPlays"), game.get("opponentPassAttempts"), game.get("opponentRushAttempts"))
    game["opponentYardsPerPlay"] = resolve_rate(game.get("opponentYardsPerPlay"), game.get("opponentTotalYards"), game.get("opponentTotalPlays"))
    game["opponentYardsPerPass"] = resolve_rate(game.get("opponentYardsPerPass"), game.get("opponentPassingYards"), game.get("opponentPassAttempts"))
    game["opponentYardsPerRush"] = resolve_rate(game.get("opponentYardsPerRush"), game.get("opponentRushingYards"), game.get("opponentRushAttempts"))
    rows: list[dict[str, str]] = []
    for stat, field, opponent_field in GAME_STAT_COMPARE_FIELDS:
        rows.append(
            {
                "stat": stat,
                "left": display_stat_value(game.get(field), stat, season_year),
                "right": display_stat_value(game.get(opponent_field), stat, season_year),
            }
        )
    return {"leftTeam": team_abbr, "rightTeam": right_team, "teamStats": rows}


def enrich_bundles_for_matchups(bundles: dict[str, dict[str, Any]]) -> None:
    league_index = build_league_game_index(bundles)
    for slug, bundle in bundles.items():
        team_abbr = team_meta(slug)["espn_slug"].upper()
        rebuilt_match_details: dict[str, Any] = {}
        for game in bundle["ALL_GAMES"]:
            game["youtubeSummaryUrl"] = build_youtube_summary_url(bundle["TEAM_CONFIG"]["teamName"], game)
            game["youtubeSummaryLabel"] = "Watch on YouTube"
            counterpart = find_counterpart_game(slug, game, league_index)
            rebuilt_match_details[build_match_key(game)] = build_team_stat_detail(team_abbr, game, counterpart)
        bundle["MATCH_DETAILS"] = rebuilt_match_details


def optional_source_status(url: str) -> dict[str, Any]:
    return {"url": url, "status": "deferred"}


def unavailable_season_entry(meta: dict[str, Any], year: int, reason: str) -> dict[str, Any]:
    return {
        "team_name": meta["team_name"],
        "record": "Source unavailable",
        "wins": 0,
        "losses": 0,
        "ties": 0,
        "division": meta["division"],
        "division_rank": None,
        "division_finish": None,
        "playoff_result": "Unknown",
        "notable_season": year in meta["featured_seasons"],
        "stats": {},
        "standings": [],
        "leaders": [],
        "inactive": False,
        "source_unavailable": True,
        "sources": {
            "statmuseTeamQuery": ask_url(f"{meta['team_name']} season in {year}"),
            "espnSchedule": optional_source_status(f"https://www.espn.com/nfl/team/schedule/_/name/{meta['espn_slug']}/season/{year}"),
            "pfrTeam": optional_source_status(f"https://www.pro-football-reference.com/teams/{meta['pfr_code']}/{year}.htm"),
            "error": reason,
        },
    }


def scrape_team_dataset(slug: str) -> dict[str, Any]:
    meta = team_meta(slug)
    season_extra: dict[str, Any] = {}
    all_games: list[dict[str, Any]] = []
    match_details: dict[str, Any] = {}
    player_features_by_season: dict[str, Any] = {}

    for year in range(meta["season_start_year"], 2026):
        if year in meta.get("inactive_years", []):
            season_extra[str(year)] = {
                "team_name": meta["team_name"],
                "record": "Inactive",
                "wins": 0,
                "losses": 0,
                "ties": 0,
                "division": meta["division"],
                "division_rank": None,
                "division_finish": None,
                "playoff_result": "Inactive",
                "notable_season": False,
                "stats": {},
                "standings": [],
                "leaders": [],
                "inactive": True,
                "sources": {},
            }
            player_features_by_season[str(year)] = build_player_features([], str(year), meta["iconic_players"])
            continue

        used_fallback = False
        raw_html = ""
        team_url = ""
        try:
            team_url, season_name = find_team_season_link(meta["team_name"], year)
            soup, raw_html = fetch_team_page(team_url)
            standings_table = table_after_heading(soup, f"{year} Division Standings")
            standings = parse_standings_table(standings_table)
            stats = parse_stats_table(table_after_heading(soup, f"{year} Stats"))
            leaders = parse_team_leaders(soup)
            division_name = clean(extract_division_name(raw_html, f"{year} Division Standings") or "")
            game_log_rows = parse_game_log_rows(f"{meta['team_name']} game log {year} including passing yards rushing yards turnovers first downs time of possession", year)
            playoff_rows = parse_game_log_rows(f"{meta['team_name']} playoff game log {year} including passing yards rushing yards turnovers first downs time of possession", year)
        except Exception as exc:
            try:
                season_name, snapshot, division_name, division_rank_from_heading = fallback_season_snapshot(meta, year)
                stats = snapshot["stats"]
                leaders = fallback_team_leaders(meta["team_name"], year)
                standings = []
                game_log_rows = parse_game_log_rows(f"{meta['team_name']} game log {year} including passing yards rushing yards turnovers first downs time of possession", year)
                playoff_rows = parse_game_log_rows(f"{meta['team_name']} playoff game log {year} including passing yards rushing yards turnovers first downs time of possession", year)
                used_fallback = True
                fallback_error = str(exc)
            except Exception as fallback_exc:
                season_extra[str(year)] = unavailable_season_entry(meta, year, f"{exc}; fallback={fallback_exc}")
                player_features_by_season[str(year)] = build_player_features([], f"{meta['team_name']} {year}", meta["iconic_players"])
                continue

        stats_division_name: str | None = None
        stats_division_rank: int | None = None
        try:
            _, snapshot_probe, stats_division_name, stats_division_rank = fallback_season_snapshot(meta, year)
            if used_fallback and not stats:
                stats = snapshot_probe["stats"]
        except Exception:
            stats_division_name = None
            stats_division_rank = None

        detail_by_date = {row["date"]: row for row in game_log_rows}
        playoff_by_date = {row["date"]: row for row in playoff_rows}
        season_games = list(game_log_rows)
        for playoff_row in playoff_rows:
            if playoff_row["date"] not in detail_by_date:
                season_games.append(playoff_row)
                detail_by_date[playoff_row["date"]] = playoff_row
        season_games.sort(key=lambda row: row["date"])
        regular_gp = int(stats.get("GP", 0) or len(game_log_rows))

        for idx, game in enumerate(season_games):
            detail = detail_by_date.get(game["date"], {})
            merged = dict(game)
            merged["year"] = year
            merged["isPlayoff"] = idx >= regular_gp
            merged["round"] = f"Week {idx + 1}" if idx < regular_gp else clean(playoff_by_date.get(game["date"], {}).get("round")) or f"Playoff Game {idx - regular_gp + 1}"
            merged["teamScore"] = merged["ravensScore"]
            merged["totalYards"] = detail.get("totalYards") or ""
            merged["opponentTotalYards"] = detail.get("opponentTotalYards") or ""
            merged["passingYards"] = detail.get("passingYards") or ""
            merged["rushingYards"] = detail.get("rushingYards") or ""
            merged["totalPlays"] = detail.get("totalPlays") or ""
            merged["yardsPerPlay"] = detail.get("yardsPerPlay") or ""
            merged["yardsPerPass"] = detail.get("yardsPerPass") or ""
            merged["yardsPerRush"] = detail.get("yardsPerRush") or ""
            merged["turnovers"] = detail.get("turnovers") or ""
            merged["firstDowns"] = detail.get("firstDowns") or ""
            merged["possession"] = detail.get("possession") or ""
            merged["punts"] = detail.get("punts") or ""
            merged["interceptionsThrown"] = detail.get("interceptionsThrown") or ""
            merged["fumblesLost"] = detail.get("fumblesLost") or ""
            merged["penalties"] = detail.get("penalties") or ""
            merged["sacks"] = detail.get("sacks") or ""
            merged["passAttempts"] = detail.get("passAttempts") or ""
            merged["rushAttempts"] = detail.get("rushAttempts") or ""
            apply_derived_game_stats(merged)
            all_games.append(merged)

            rows = []
            for stat, left, right in (
                ("Total Yards", merged["totalYards"], merged["opponentTotalYards"] or "--"),
                ("Passing Yards", merged["passingYards"], "--"),
                ("Rushing Yards", merged["rushingYards"], "--"),
                ("Turnovers", merged["turnovers"], "--"),
                ("First Downs", merged["firstDowns"], "--"),
                ("Possession", merged["possession"], "--"),
            ):
                if left:
                    rows.append({"stat": stat, "left": str(left), "right": str(right)})
            match_details[build_match_key(merged)] = {"leftTeam": meta["short_name"], "rightTeam": merged["opponent"], "teamStats": rows}

        if used_fallback:
            record_w = int(snapshot["wins"])
            record_l = int(snapshot["losses"])
            record_t = int(snapshot["ties"])
        else:
            record_w = sum(1 for game in season_games[:regular_gp] if game["result"] == "W")
            record_l = sum(1 for game in season_games[:regular_gp] if game["result"] == "L")
            record_t = sum(1 for game in season_games[:regular_gp] if game["result"] == "T")
        playoff_games = [game for game in all_games if game["year"] == year and game["isPlayoff"]]
        division_name = normalize_division_label(division_name)
        stats_division_name = normalize_division_label(stats_division_name)
        historic_division = infer_historic_division(slug, year)
        division_name_inferred = False
        division_rank = division_rank_from_heading if used_fallback else None
        if not division_name:
            division_name = stats_division_name or meta["division"]
        if historic_division and historic_division != division_name:
            division_name = historic_division
            division_name_inferred = True
        if not division_rank:
            division_rank = stats_division_rank
        if not division_rank and division_name and can_derive_division_rank(division_name, division_name_inferred):
            for idx, row in enumerate(standings, start=1):
                row_name = row["team"].lower()
                if meta["short_name"].lower() in row_name or season_name.lower() in row_name:
                    division_rank = idx
                    break
        division_finish = f"{division_rank} of {len(standings)}" if division_rank and standings else None
        if division_rank and not division_finish:
            division_finish = ordinal(division_rank)
        season_extra[str(year)] = {
            "team_name": season_name,
            "record": f"{record_w}-{record_l}" + (f"-{record_t}" if record_t else ""),
            "wins": record_w,
            "losses": record_l,
            "ties": record_t,
            "division": clean(division_name or meta["division"]),
            "division_rank": division_rank,
            "division_finish": division_finish,
            "playoff_result": derive_playoff_result(playoff_games),
            "notable_season": year in meta["featured_seasons"],
            "stats": stats,
            "standings": standings,
            "leaders": leaders,
            "inactive": False,
            "source_unavailable": False,
            "sources": {
                "statmuseTeam": team_url,
                "statmuseGameLog": ask_url(f"{meta['team_name']} game log {year} including passing yards rushing yards turnovers first downs time of possession"),
                "statmusePlayoffs": ask_url(f"{meta['team_name']} playoff game log {year}"),
                "statmuseStatsAsk": ask_url(f"{meta['team_name']} stats {year}") if used_fallback else "",
                "espnSchedule": optional_source_status(f"https://www.espn.com/nfl/team/schedule/_/name/{meta['espn_slug']}/season/{year}"),
                "pfrTeam": optional_source_status(f"https://www.pro-football-reference.com/teams/{meta['pfr_code']}/{year}.htm"),
            },
        }
        if used_fallback:
            season_extra[str(year)]["sources"]["fallbackReason"] = fallback_error
        player_features_by_season[str(year)] = build_player_features(leaders, season_name, meta["iconic_players"])
        time.sleep(0.05)

    all_games.sort(key=lambda game: (game["year"], game["date"], game["round"]))
    featured_games = build_featured_games(all_games, meta["featured_seasons"])
    bundle = {
        "TEAM_CONFIG": build_team_config(slug, max(int(year) for year in season_extra)),
        "ALL_GAMES": all_games,
        "SEASON_EXTRA_DATA": season_extra,
        "MATCH_DETAILS": match_details,
        "RIVALRY_DATA": build_rivalry_data(all_games, meta["rivalries"]),
        "PLAYER_FEATURES_BY_SEASON": player_features_by_season,
        "FEATURED_GAMES": featured_games,
        "TIMELINE_COPY": build_timeline_copy(meta["team_name"], season_extra, featured_games, meta["identity_note"]),
        "TEAM_LOGO_MAP": build_team_logo_map(),
    }
    return bundle


def write_data_bundle(slug: str, bundle: dict[str, Any]) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data_path = DATA_DIR / f"{slug}.js"
    data_path.write_text(
        "\n".join(
            [
                "export const TEAM_CONFIG = " + compact(bundle["TEAM_CONFIG"]) + ";",
                "export const ALL_GAMES = " + compact(bundle["ALL_GAMES"]) + ";",
                "export const SEASON_EXTRA_DATA = " + compact(bundle["SEASON_EXTRA_DATA"]) + ";",
                "export const MATCH_DETAILS = " + compact(bundle["MATCH_DETAILS"]) + ";",
                "export const RIVALRY_DATA = " + compact(bundle["RIVALRY_DATA"]) + ";",
                "export const PLAYER_FEATURES_BY_SEASON = " + compact(bundle["PLAYER_FEATURES_BY_SEASON"]) + ";",
                "export const FEATURED_GAMES = " + compact(bundle["FEATURED_GAMES"]) + ";",
                "export const TIMELINE_COPY = " + compact(bundle["TIMELINE_COPY"]) + ";",
                "export const TEAM_LOGO_MAP = " + compact(bundle["TEAM_LOGO_MAP"]) + ";",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return data_path


def write_team_html(slug: str, bundle: dict[str, Any]) -> Path:
    TEAMS_DIR.mkdir(parents=True, exist_ok=True)
    html_path = TEAMS_DIR / f"{slug}.html"
    html = render_team_page(slug, bundle)
    html_path.write_text(html, encoding="utf-8")
    legacy_html_path = TEAMS_DIR / f"{slug}database.html"
    if legacy_html_path.exists():
        legacy_html_path.write_text(html, encoding="utf-8")
    return html_path


def write_bundle(slug: str, bundle: dict[str, Any]) -> tuple[Path, Path]:
    data_path = write_data_bundle(slug, bundle)
    html_path = write_team_html(slug, bundle)
    return data_path, html_path


def load_bundle_from_data_file(slug: str) -> dict[str, Any]:
    data_path = DATA_DIR / f"{slug}.js"
    if not data_path.exists():
        raise FileNotFoundError(f"Missing existing data bundle for {slug}: {data_path}")
    bundle: dict[str, Any] = {}
    for line in data_path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.match(r"export const (\w+) = (.*);$", line.strip())
        if not match:
            continue
        bundle[match.group(1)] = json.loads(match.group(2))
    required = {
        "TEAM_CONFIG",
        "ALL_GAMES",
        "SEASON_EXTRA_DATA",
        "MATCH_DETAILS",
        "RIVALRY_DATA",
        "PLAYER_FEATURES_BY_SEASON",
        "FEATURED_GAMES",
        "TIMELINE_COPY",
        "TEAM_LOGO_MAP",
    }
    missing = sorted(required - bundle.keys())
    if missing:
        raise ValueError(f"Existing data bundle for {slug} is missing exports: {', '.join(missing)}")
    season_years = [int(str(year)) for year in bundle["SEASON_EXTRA_DATA"].keys() if str(year).isdigit()]
    game_years = [int(game.get("year", 0)) for game in bundle["ALL_GAMES"] if int(game.get("year", 0))]
    current_end_year = max(season_years + game_years) if (season_years or game_years) else team_meta(slug)["season_start_year"]
    for game in bundle["ALL_GAMES"]:
        season_year = int(game.get("year", 0)) if int(game.get("year", 0)) else None
        if season_year:
            normalized_opponent = normalize_opponent(game.get("opponentCode") or game.get("opponent"), season_year)
            if normalized_opponent:
                game["opponent"] = normalized_opponent
        apply_derived_game_stats(game)
    meta = team_meta(slug)
    bundle["TEAM_CONFIG"] = build_team_config(slug, current_end_year)
    bundle["TEAM_LOGO_MAP"] = build_team_logo_map()
    bundle["RIVALRY_DATA"] = build_rivalry_data(bundle["ALL_GAMES"], meta["rivalries"])
    bundle["FEATURED_GAMES"] = build_featured_games(bundle["ALL_GAMES"], meta["featured_seasons"])
    bundle["TIMELINE_COPY"] = build_timeline_copy(meta["team_name"], bundle["SEASON_EXTRA_DATA"], bundle["FEATURED_GAMES"], meta["identity_note"])
    return bundle


def load_existing_render_bundles(exclude_slugs: set[str] | None = None) -> dict[str, dict[str, Any]]:
    bundles: dict[str, dict[str, Any]] = {}
    excluded = exclude_slugs or set()
    for slug in TARGET_TEAM_SLUGS:
        if slug in excluded:
            continue
        data_path = DATA_DIR / f"{slug}.js"
        if data_path.exists():
            bundles[slug] = load_bundle_from_data_file(slug)
    return bundles


def load_support_enrichment_bundles(exclude_slugs: set[str] | None = None, refresh_playoff_stats: bool = False) -> dict[str, dict[str, Any]]:
    bundles: dict[str, dict[str, Any]] = {}
    excluded = exclude_slugs or set()
    for slug in sorted(EXCLUDED_RENDER_SLUGS):
        if slug in excluded:
            continue
        data_path = DATA_DIR / f"{slug}.js"
        bundle = load_bundle_from_data_file(slug) if data_path.exists() else scrape_team_dataset(slug)
        if refresh_playoff_stats:
            refresh_bundle_game_stats(slug, bundle)
        bundles[slug] = bundle
    return bundles


def rerender_team_from_existing_data(slug: str, support_scrape: bool = False, refresh_playoff_stats: bool = False) -> tuple[Path, Path]:
    bundles = load_existing_render_bundles({slug})
    if support_scrape:
        bundles.update(load_support_enrichment_bundles({slug}, refresh_playoff_stats=refresh_playoff_stats))
    bundles[slug] = load_bundle_from_data_file(slug)
    if refresh_playoff_stats:
        refresh_bundle_game_stats(slug, bundles[slug])
    enrich_bundles_for_matchups(bundles)
    return write_bundle(slug, bundles[slug])


def generate_team(slug: str, support_scrape: bool = False, refresh_playoff_stats: bool = False) -> tuple[Path, Path]:
    bundles = load_existing_render_bundles({slug})
    if support_scrape:
        bundles.update(load_support_enrichment_bundles({slug}, refresh_playoff_stats=refresh_playoff_stats))
    bundles[slug] = scrape_team_dataset(slug)
    if refresh_playoff_stats:
        refresh_bundle_game_stats(slug, bundles[slug])
    enrich_bundles_for_matchups(bundles)
    return write_bundle(slug, bundles[slug])


def generate_all_teams(target_slugs: list[str] | None = None, skip_existing: bool = False, support_scrape: bool = False, refresh_playoff_stats: bool = False) -> list[tuple[str, Path, Path]]:
    bundles: dict[str, dict[str, Any]] = {}
    active_slugs: list[str] = []
    for slug in target_slugs or TARGET_TEAM_SLUGS:
        if skip_existing and (DATA_DIR / f"{slug}.js").exists() and (TEAMS_DIR / f"{slug}.html").exists():
            continue
        bundles[slug] = scrape_team_dataset(slug)
        if refresh_playoff_stats:
            refresh_bundle_game_stats(slug, bundles[slug])
        active_slugs.append(slug)
    if not bundles:
        return []
    enrichment_bundles = {**load_existing_render_bundles(set(active_slugs)), **bundles}
    if support_scrape:
        enrichment_bundles.update(load_support_enrichment_bundles(set(active_slugs), refresh_playoff_stats=refresh_playoff_stats))
    enrich_bundles_for_matchups(enrichment_bundles)
    results: list[tuple[str, Path, Path]] = []
    for slug in active_slugs:
        data_path, html_path = write_bundle(slug, bundles[slug])
        results.append((slug, data_path, html_path))
    return results


def rerender_all_teams(target_slugs: list[str] | None = None, skip_existing: bool = False, support_scrape: bool = False, refresh_playoff_stats: bool = False) -> list[tuple[str, Path, Path]]:
    bundles: dict[str, dict[str, Any]] = {}
    active_slugs: list[str] = []
    for slug in target_slugs or TARGET_TEAM_SLUGS:
        if skip_existing and (TEAMS_DIR / f"{slug}.html").exists():
            continue
        bundles[slug] = load_bundle_from_data_file(slug)
        if refresh_playoff_stats:
            refresh_bundle_game_stats(slug, bundles[slug])
        active_slugs.append(slug)
    if not bundles:
        return []
    enrichment_bundles = dict(bundles)
    if support_scrape:
        enrichment_bundles.update(load_support_enrichment_bundles(set(active_slugs), refresh_playoff_stats=refresh_playoff_stats))
    enrich_bundles_for_matchups(enrichment_bundles)
    results: list[tuple[str, Path, Path]] = []
    for slug in active_slugs:
        data_path, html_path = write_bundle(slug, bundles[slug])
        results.append((slug, data_path, html_path))
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate all-time NFL team archives from the Ravens master template.")
    parser.add_argument("--team", choices=sorted(TEAM_CATALOG), help="Generate a single team instead of the default 28-team batch.")
    parser.add_argument("--include-excluded", action="store_true", help="Allow generating Ravens, Eagles, Patriots, or Rams explicitly.")
    parser.add_argument("--start-from", choices=TARGET_TEAM_SLUGS, help="Start a batch from this team slug, inclusive.")
    parser.add_argument("--limit", type=int, help="Only generate this many teams in batch mode.")
    parser.add_argument("--render-only", action="store_true", help="Regenerate HTML pages from existing data bundles without scraping.")
    parser.add_argument("--support-scrape", action="store_true", help="Also scrape Ravens, Eagles, Patriots, and Rams as support-only sources for matchup enrichment.")
    parser.add_argument("--refresh-playoff-stats", action="store_true", help="Refresh per-game stat fields from richer StatMuse regular-season and playoff log queries before rendering.")
    parser.add_argument("--skip-existing", action="store_true", help="Skip teams that already have both a data bundle and an HTML page.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.team:
        if args.team in EXCLUDED_RENDER_SLUGS and not args.include_excluded:
            raise SystemExit(f"{args.team} is intentionally excluded from render output. Pass --include-excluded to override.")
        data_path, html_path = (
            rerender_team_from_existing_data(args.team, support_scrape=args.support_scrape, refresh_playoff_stats=args.refresh_playoff_stats)
            if args.render_only
            else generate_team(args.team, support_scrape=args.support_scrape, refresh_playoff_stats=args.refresh_playoff_stats)
        )
        print(f"generated {args.team}: {data_path} | {html_path}")
        return 0
    batch_slugs = list(TARGET_TEAM_SLUGS)
    if args.start_from:
        batch_slugs = batch_slugs[batch_slugs.index(args.start_from):]
    if args.limit is not None:
        batch_slugs = batch_slugs[: max(args.limit, 0)]
    generator = rerender_all_teams if args.render_only else generate_all_teams
    for slug, data_path, html_path in generator(batch_slugs, skip_existing=args.skip_existing, support_scrape=args.support_scrape, refresh_playoff_stats=args.refresh_playoff_stats):
        print(f"generated {slug}: {data_path} | {html_path}")
    return 0
