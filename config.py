from __future__ import annotations

from typing import Any


SUPPORT_LINK = "https://cafecito.app/santimackey"
SUPPORT_LABEL = "Cafecito"
SUPPORT_COPYRIGHT_YEAR = 2026

EXCLUDED_RENDER_SLUGS = {"ravens", "eagles", "patriots", "rams"}

CURRENT_HEAD_COACHES = {
    "49ers": "Kyle Shanahan",
    "bears": "Ben Johnson",
    "bengals": "Zac Taylor",
    "bills": "Joe Brady",
    "broncos": "Sean Payton",
    "browns": "Todd Monken",
    "buccaneers": "Todd Bowles",
    "cardinals": "Mike LaFleur",
    "chargers": "Jim Harbaugh",
    "chiefs": "Andy Reid",
    "colts": "Shane Steichen",
    "commanders": "Dan Quinn",
    "cowboys": "Brian Schottenheimer",
    "dolphins": "Jeff Hafley",
    "eagles": "Nick Sirianni",
    "falcons": "Kevin Stefanski",
    "giants": "John Harbaugh",
    "jaguars": "Liam Coen",
    "jets": "Aaron Glenn",
    "lions": "Dan Campbell",
    "packers": "Matt LaFleur",
    "panthers": "Dave Canales",
    "patriots": "Mike Vrabel",
    "raiders": "Klint Kubiak",
    "rams": "Sean McVay",
    "ravens": "Jesse Minter",
    "saints": "Kellen Moore",
    "seahawks": "Mike Macdonald",
    "steelers": "Mike McCarthy",
    "texans": "DeMeco Ryans",
    "titans": "Robert Saleh",
    "vikings": "Kevin O'Connell",
}


def logo_url(espn_logo_id: int) -> str:
    return f"https://a.espncdn.com/i/teamlogos/nfl/500/{espn_logo_id}.png"


def tm(
    team_name: str,
    short_name: str,
    mascot_name: str,
    conference: str,
    division: str,
    founded_year: int,
    season_start_year: int,
    primary_color: str,
    secondary_color: str,
    tertiary_color: str,
    dark_bg_start: str,
    dark_bg_mid: str,
    dark_bg_end: str,
    light_theme_primary: str,
    light_theme_accent: str,
    text_on_dark: str,
    muted_on_dark: str,
    archive_kicker: str,
    identity_note: str,
    rivalries: list[str],
    featured_seasons: list[int],
    iconic_players: list[str],
    espn_logo_id: int,
    espn_slug: str,
    nfl_slug: str,
    pfr_code: str,
    inactive_years: list[int] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "team_name": team_name,
        "short_name": short_name,
        "mascot_name": mascot_name,
        "conference": conference,
        "division": division,
        "founded_year": founded_year,
        "season_start_year": season_start_year,
        "primary_color": primary_color,
        "secondary_color": secondary_color,
        "tertiary_color": tertiary_color,
        "dark_bg_start": dark_bg_start,
        "dark_bg_mid": dark_bg_mid,
        "dark_bg_end": dark_bg_end,
        "light_theme_primary": light_theme_primary,
        "light_theme_accent": light_theme_accent,
        "text_on_dark": text_on_dark,
        "muted_on_dark": muted_on_dark,
        "archive_kicker": archive_kicker,
        "identity_note": identity_note,
        "rivalries": rivalries,
        "featured_seasons": featured_seasons,
        "iconic_players": iconic_players,
        "espn_logo_id": espn_logo_id,
        "espn_slug": espn_slug,
        "nfl_slug": nfl_slug,
        "pfr_code": pfr_code,
    }
    if inactive_years:
        payload["inactive_years"] = inactive_years
    return payload


TEAM_CATALOG: dict[str, dict[str, Any]] = {
    "49ers": tm("San Francisco 49ers", "49ers", "49ers", "NFC", "NFC West", 1946, 1946, "#AA0000", "#B3995D", "#FFFFFF", "#160304", "#3A090C", "#070203", "#AA0000", "#B3995D", "#F7F3EE", "#D4C5B2", "49ers archive - West Coast dynasties and bay fog Sundays", "AAFC roots to Shanahan-era peaks in one long-running San Francisco archive.", ["Cowboys", "Rams", "Seahawks", "Packers"], [1957, 1981, 1984, 1994, 2019, 2023], ["Joe Montana", "Jerry Rice", "Steve Young"], 25, "sf", "san-francisco-49ers", "sfo"),
    "bears": tm("Chicago Bears", "Bears", "Bears", "NFC", "NFC North", 1920, 1920, "#0B162A", "#C83803", "#FFFFFF", "#060A11", "#0E1A30", "#030509", "#0B162A", "#C83803", "#F1F4F8", "#B8C2D1", "Bears archive - charter-league grit and lakefront history", "George Halas roots, 1985 force, and every cold-weather season in between.", ["Packers", "Vikings", "Lions", "Cardinals"], [1940, 1963, 1985, 2006, 2018], ["Walter Payton", "Dick Butkus", "Mike Singletary"], 3, "chi", "chicago-bears", "chi"),
    "bengals": tm("Cincinnati Bengals", "Bengals", "Bengals", "AFC", "AFC North", 1968, 1968, "#FB4F14", "#000000", "#FFFFFF", "#120705", "#341309", "#060202", "#FB4F14", "#111111", "#FFF4EF", "#E6B9A9", "Bengals archive - striped chaos, riverfront swings, and Burrow-era sparks", "Paul Brown roots, late-1980s peaks, and modern AFC title pushes stay connected here.", ["Steelers", "Browns", "Ravens", "Chiefs"], [1981, 1988, 2005, 2021, 2022], ["Anthony Munoz", "Ken Anderson", "Joe Burrow"], 4, "cin", "cincinnati-bengals", "cin"),
    "bills": tm("Buffalo Bills", "Bills", "Bills", "AFC", "AFC East", 1960, 1960, "#00338D", "#C60C30", "#FFFFFF", "#050C19", "#0C1C3B", "#02050A", "#00338D", "#C60C30", "#F0F5FF", "#B7C4E5", "Bills archive - AFL thunder, four straight Super Bowls, and Orchard Park snow", "Buffalo's AFL rise, Levy-era run, and Josh Allen resurgence in one file.", ["Dolphins", "Jets", "Patriots", "Chiefs"], [1964, 1965, 1990, 1993, 2020], ["Jim Kelly", "Bruce Smith", "Josh Allen"], 2, "buf", "buffalo-bills", "buf"),
    "broncos": tm("Denver Broncos", "Broncos", "Broncos", "AFC", "AFC West", 1960, 1960, "#FB4F14", "#002244", "#FFFFFF", "#140702", "#2B1205", "#05070C", "#002244", "#FB4F14", "#F5F3F0", "#D7B6A2", "Broncos archive - mile-high pivots, orange crush, and altitude Januarys", "AFL start, Orange Crush, Elway titles, Manning surge, and the latest Denver turns.", ["Raiders", "Chiefs", "Chargers", "Seahawks"], [1977, 1987, 1997, 1998, 2015], ["John Elway", "Terrell Davis", "Peyton Manning"], 7, "den", "denver-broncos", "den"),
    "browns": tm("Cleveland Browns", "Browns", "Browns", "AFC", "AFC North", 1946, 1946, "#311D00", "#FF3C00", "#FFFFFF", "#120A02", "#2B1605", "#040200", "#311D00", "#FF3C00", "#F7F1EA", "#D8C1A8", "Browns archive - AAFC force, municipal ghosts, and return-era resets", "Otto Graham dominance, Kardiac swings, and the expansion-return era all in one archive.", ["Steelers", "Bengals", "Ravens"], [1946, 1950, 1964, 1986, 2020], ["Jim Brown", "Otto Graham", "Joe Thomas"], 5, "cle", "cleveland-browns", "cle", inactive_years=[1996, 1997, 1998]),
    "buccaneers": tm("Tampa Bay Buccaneers", "Buccaneers", "Buccaneers", "NFC", "NFC South", 1976, 1976, "#D50A0A", "#FF7900", "#0A0A08", "#150405", "#33090B", "#070202", "#A71930", "#FF7900", "#FFF3EF", "#E2BCB2", "Buccaneers archive - creamsicle swings, Sapp-era bite, and modern title flashes", "Expansion hardship, 2002 defense, Brady-era peak, and every Tampa pivot between them.", ["Saints", "Falcons", "Panthers", "Packers"], [1979, 2002, 2020, 2021], ["Derrick Brooks", "Warren Sapp", "Mike Evans"], 27, "tb", "tampa-bay-buccaneers", "tam"),
    "cardinals": tm("Arizona Cardinals", "Cardinals", "Cardinals", "NFC", "NFC West", 1898, 1920, "#97233F", "#FFB612", "#000000", "#14070A", "#311019", "#050203", "#97233F", "#FFB612", "#F8F2F3", "#D7B7C0", "Cardinals archive - charter-franchise roots to desert Sundays", "Chicago, St. Louis, and Arizona eras stitched into one long Cardinals ledger.", ["Bears", "Rams", "Seahawks", "49ers"], [1925, 1947, 1974, 2008, 2015], ["Larry Fitzgerald", "Night Train Lane", "Aeneas Williams"], 22, "ari", "arizona-cardinals", "crd"),
    "chargers": tm("Los Angeles Chargers", "Chargers", "Chargers", "AFC", "AFC West", 1960, 1960, "#0080C6", "#FFC20E", "#FFFFFF", "#04131D", "#0A2434", "#02070B", "#0080C6", "#FFC20E", "#F4FBFF", "#BCD6E3", "Chargers archive - AFL fireworks, Air Coryell routes, and west-coast resets", "Los Angeles to San Diego and back again, with Fouts, LT, and modern quarterback eras intact.", ["Raiders", "Chiefs", "Broncos"], [1963, 1980, 1994, 2006, 2018], ["Dan Fouts", "LaDainian Tomlinson", "Junior Seau"], 24, "lac", "los-angeles-chargers", "sdg"),
    "chiefs": tm("Kansas City Chiefs", "Chiefs", "Chiefs", "AFC", "AFC West", 1960, 1960, "#E31837", "#FFB81C", "#FFFFFF", "#150407", "#370B13", "#050203", "#E31837", "#FFB81C", "#FFF4F5", "#E1BCC5", "Chiefs archive - Texans roots, Arrowhead winters, and modern title runs", "Dallas Texans origin to Mahomes-era championships without losing the franchise throughline.", ["Raiders", "Broncos", "Chargers", "Bills"], [1962, 1969, 1997, 2019, 2022, 2023], ["Len Dawson", "Derrick Thomas", "Patrick Mahomes"], 12, "kc", "kansas-city-chiefs", "kan"),
    "colts": tm("Indianapolis Colts", "Colts", "Colts", "AFC", "AFC South", 1953, 1953, "#013369", "#FFFFFF", "#A2AAAD", "#04101A", "#0B2035", "#02060A", "#013369", "#A2AAAD", "#F0F6FF", "#B7C7D8", "Colts archive - Baltimore thunder, midnight relocation, and Manning-era rhythm", "Unitas, the move, and the Peyton years all stay linked in one Colts history.", ["Patriots", "Titans", "Texans"], [1958, 1968, 1970, 2006, 2009], ["Johnny Unitas", "Peyton Manning", "Marvin Harrison"], 11, "ind", "indianapolis-colts", "clt"),
    "commanders": tm("Washington Commanders", "Commanders", "Commanders", "NFC", "NFC East", 1932, 1932, "#5A1414", "#FFB612", "#FFFFFF", "#130405", "#2D0A0C", "#050102", "#5A1414", "#FFB612", "#FAF3EA", "#D9C1A2", "Washington archive - capital-city branding changes and hard-running title teams", "Boston roots, Gibbs championships, and modern rebrand years without losing the franchise arc.", ["Cowboys", "Giants", "Eagles"], [1937, 1942, 1982, 1987, 1991], ["Sammy Baugh", "Art Monk", "Darrell Green"], 28, "wsh", "washington-commanders", "was"),
    "cowboys": tm("Dallas Cowboys", "Cowboys", "Cowboys", "NFC", "NFC East", 1960, 1960, "#041E42", "#869397", "#FFFFFF", "#050913", "#0D1E39", "#020409", "#041E42", "#869397", "#F3F7FB", "#BAC6CF", "Cowboys archive - star power, Landry structure, and January mythology", "Expansion years through Staubach, Aikman, and the modern Dallas spotlight in one file.", ["Commanders", "Giants", "Eagles", "49ers"], [1966, 1971, 1977, 1992, 1995], ["Roger Staubach", "Emmitt Smith", "Troy Aikman"], 6, "dal", "dallas-cowboys", "dal"),
    "dolphins": tm("Miami Dolphins", "Dolphins", "Dolphins", "AFC", "AFC East", 1966, 1966, "#008E97", "#FC4C02", "#FFFFFF", "#041314", "#0C2B2D", "#020707", "#008E97", "#FC4C02", "#F1FCFB", "#B8DDDA", "Dolphins archive - perfect-season precision and humid orange-blue flash", "AFL entry, 1972 perfection, Marino fireworks, and the latest Miami speed-era reset.", ["Jets", "Bills", "Patriots"], [1972, 1973, 1984, 1992, 2023], ["Dan Marino", "Larry Csonka", "Jason Taylor"], 15, "mia", "miami-dolphins", "mia"),
    "eagles": tm("Philadelphia Eagles", "Eagles", "Eagles", "NFC", "NFC East", 1933, 1933, "#004C54", "#A5ACAF", "#FFFFFF", "#031819", "#0A2A2D", "#020708", "#004C54", "#A5ACAF", "#EEF7F8", "#BFD2D4", "Eagles archive - broad-street edge, title eras, and midnight green layers", "The Eagles page already exists, but Philadelphia stays in the catalog for support scraping and rivalry context.", ["Cowboys", "Giants", "Commanders"], [1948, 1949, 1960, 2017, 2024], ["Reggie White", "Brian Dawkins", "Donovan McNabb"], 21, "phi", "philadelphia-eagles", "phi"),
    "falcons": tm("Atlanta Falcons", "Falcons", "Falcons", "NFC", "NFC South", 1966, 1966, "#A71930", "#000000", "#A5ACAF", "#120405", "#2B090D", "#030102", "#A71930", "#111111", "#FFF5F6", "#D9B8BF", "Falcons archive - dome speed, heartbreak valleys, and red-black resets", "Atlanta's first breakthrough, Vick years, 2016 offense, and every extreme in between.", ["Saints", "Panthers", "Buccaneers"], [1980, 1998, 2004, 2012, 2016], ["Matt Ryan", "Julio Jones", "Deion Sanders"], 1, "atl", "atlanta-falcons", "atl"),
    "giants": tm("New York Giants", "Giants", "Giants", "NFC", "NFC East", 1925, 1925, "#0B2265", "#A71930", "#FFFFFF", "#040914", "#0D1B3A", "#020307", "#0B2265", "#A71930", "#F4F6FB", "#BBC3D8", "Giants archive - polo grounds roots, Parcells steel, and New York title spikes", "One of the league's oldest franchises, from pre-war titles to the Manning Super Bowls.", ["Cowboys", "Eagles", "Commanders", "49ers"], [1927, 1956, 1986, 1990, 2007, 2011], ["Lawrence Taylor", "Phil Simms", "Eli Manning"], 19, "nyg", "new-york-giants", "nyg"),
    "jaguars": tm("Jacksonville Jaguars", "Jaguars", "Jaguars", "AFC", "AFC South", 1995, 1995, "#006778", "#D7A22A", "#101820", "#041214", "#0A252A", "#020607", "#006778", "#D7A22A", "#F1FBFC", "#BED7DA", "Jaguars archive - teal expansion energy, 1999 roar, and modern comeback nights", "Immediate expansion rise, late-1990s peaks, Sacksonville, and the latest reboot all stay connected.", ["Titans", "Colts", "Texans"], [1996, 1999, 2007, 2017, 2022], ["Fred Taylor", "Tony Boselli", "Mark Brunell"], 30, "jax", "jacksonville-jaguars", "jax"),
    "jets": tm("New York Jets", "Jets", "Jets", "AFC", "AFC East", 1960, 1960, "#125740", "#FFFFFF", "#000000", "#04110C", "#0A241A", "#010403", "#125740", "#D0D8D3", "#F1FAF5", "#B9D0C3", "Jets archive - Namath swagger, Meadowlands noise, and endless reset attempts", "Titans-to-Jets rename, Super Bowl III, Sack Exchange, and every modern restart.", ["Patriots", "Bills", "Dolphins"], [1968, 1982, 1998, 2009, 2010], ["Joe Namath", "Curtis Martin", "Darrelle Revis"], 20, "nyj", "new-york-jets", "nyj"),
    "lions": tm("Detroit Lions", "Lions", "Lions", "NFC", "NFC North", 1930, 1930, "#0076B6", "#B0B7BC", "#FFFFFF", "#031019", "#0A2231", "#02060A", "#0076B6", "#B0B7BC", "#F2FAFF", "#B9D0DB", "Lions archive - portsmouth roots, silver helmets, and modern Ford Field lift", "Portsmouth Spartans roots, 1950s titles, Barry years, and the latest Detroit climb.", ["Packers", "Bears", "Vikings"], [1935, 1952, 1957, 1991, 2023], ["Barry Sanders", "Calvin Johnson", "Bobby Layne"], 8, "det", "detroit-lions", "det"),
    "packers": tm("Green Bay Packers", "Packers", "Packers", "NFC", "NFC North", 1919, 1921, "#203731", "#FFB612", "#FFFFFF", "#08110F", "#152A24", "#030605", "#203731", "#FFB612", "#F7F7F0", "#D8D1A8", "Packers archive - town-owned permanence, Lombardi titles, and frozen-field gravity", "Early titles, Lombardi's peak, Favre, Rodgers, and every Green Bay winter still together.", ["Bears", "Vikings", "Lions", "Cowboys"], [1929, 1962, 1966, 1996, 2010], ["Brett Favre", "Bart Starr", "Aaron Rodgers"], 9, "gb", "green-bay-packers", "gnb"),
    "panthers": tm("Carolina Panthers", "Panthers", "Panthers", "NFC", "NFC South", 1995, 1995, "#0085CA", "#101820", "#BFC0BF", "#031118", "#0B2330", "#020607", "#0085CA", "#101820", "#F2FAFE", "#BFD2DA", "Panthers archive - expansion speed, keep-pounding peaks, and blue-black jolts", "Immediate rise, 2003 and 2015 Super Bowl trips, and every Carolina reset after.", ["Falcons", "Saints", "Buccaneers"], [1996, 2003, 2005, 2015], ["Cam Newton", "Luke Kuechly", "Steve Smith Sr."], 29, "car", "carolina-panthers", "car"),
    "patriots": tm("New England Patriots", "Patriots", "Patriots", "AFC", "AFC East", 1960, 1960, "#002244", "#C60C30", "#B0B7BC", "#04101D", "#0A2037", "#02050A", "#002244", "#C60C30", "#F2F6FB", "#B8C4D2", "Patriots archive - AFL roots, dynasty scale, and Foxborough winters", "Boston AFL origins, Parcells breakthroughs, Brady-Belichick dynasties, and every Foxborough era shift in one archive.", ["Jets", "Bills", "Dolphins", "Colts"], [1985, 2001, 2003, 2007, 2014, 2016], ["Tom Brady", "Rob Gronkowski", "Andre Tippett"], 17, "ne", "new-england-patriots", "nwe"),
    "raiders": tm("Las Vegas Raiders", "Raiders", "Raiders", "AFC", "AFC West", 1960, 1960, "#000000", "#A5ACAF", "#FFFFFF", "#040404", "#151515", "#000000", "#111111", "#A5ACAF", "#FAFAFA", "#CACACA", "Raiders archive - silver-and-black menace, relocation scars, and outlaw mythology", "Oakland, Los Angeles, back to Oakland, and Las Vegas all in one franchise archive.", ["Chiefs", "Broncos", "Chargers", "Steelers"], [1967, 1976, 1980, 1983, 2002], ["Ken Stabler", "Howie Long", "Marcus Allen"], 13, "lv", "las-vegas-raiders", "rai"),
    "rams": tm("Los Angeles Rams", "Rams", "Rams", "NFC", "NFC West", 1937, 1937, "#003594", "#FFD100", "#FFFFFF", "#061126", "#0D1A3A", "#020611", "#003594", "#FFD100", "#F3F8FF", "#B9CAE9", "Rams archive - Cleveland roots, Hollywood angles, and modern all-in titles", "Cleveland beginnings, Fearsome Foursome peaks, Greatest Show on Turf brilliance, and the modern all-in title run in one archive.", ["49ers", "Seahawks", "Cardinals"], [1945, 1951, 1999, 2001, 2018, 2021], ["Aaron Donald", "Kurt Warner", "Deacon Jones"], 14, "lar", "los-angeles-rams", "ram", inactive_years=[1943]),
    "ravens": tm("Baltimore Ravens", "Ravens", "Ravens", "AFC", "AFC North", 1996, 1996, "#24125F", "#D8B03E", "#FFFFFF", "#090012", "#180826", "#030006", "#24125F", "#D8B03E", "#F6F0FF", "#D6CFDE", "Ravens archive - original template source", "The Ravens page is the template source for this system and stays excluded from output generation.", ["Steelers", "Bengals", "Browns", "Titans"], [2000, 2006, 2012, 2019, 2023], ["Ray Lewis", "Ed Reed", "Lamar Jackson"], 33, "bal", "baltimore-ravens", "rav"),
    "saints": tm("New Orleans Saints", "Saints", "Saints", "NFC", "NFC South", 1967, 1967, "#D3BC8D", "#101820", "#FFFFFF", "#0B0B09", "#1F1C14", "#040403", "#101820", "#D3BC8D", "#FBF8F0", "#D7CDB4", "Saints archive - baghead lows, dome noise, and Brees-era precision", "New Orleans lows, 2009 title peak, and the Brees-Payton years all stay intact here.", ["Falcons", "Panthers", "Buccaneers", "Vikings"], [1987, 2000, 2006, 2009, 2018], ["Drew Brees", "Rickey Jackson", "Archie Manning"], 18, "no", "new-orleans-saints", "nor"),
    "seahawks": tm("Seattle Seahawks", "Seahawks", "Seahawks", "NFC", "NFC West", 1976, 1976, "#002244", "#69BE28", "#A5ACAF", "#031019", "#0A1C2C", "#02070B", "#002244", "#69BE28", "#F2F8FC", "#BCD0DA", "Seahawks archive - northwest rain, legion boom thunder, and neon green edges", "Expansion years, Holmgren steadiness, Legion of Boom height, and the modern Seattle cycles.", ["49ers", "Rams", "Cardinals", "Broncos"], [1983, 2005, 2013, 2014], ["Steve Largent", "Walter Jones", "Russell Wilson"], 26, "sea", "seattle-seahawks", "sea"),
    "steelers": tm("Pittsburgh Steelers", "Steelers", "Steelers", "AFC", "AFC North", 1933, 1933, "#101820", "#FFB612", "#FFFFFF", "#060606", "#151515", "#000000", "#101820", "#FFB612", "#FBFBF7", "#D6CEAA", "Steelers archive - smoke-stack roots, steel curtain force, and Rooney steadiness", "Pirates era through the Steel Curtain and Tomlin consistency in one Pittsburgh file.", ["Ravens", "Browns", "Bengals", "Raiders"], [1974, 1975, 1978, 2005, 2008], ["Mean Joe Greene", "Terry Bradshaw", "Ben Roethlisberger"], 23, "pit", "pittsburgh-steelers", "pit"),
    "texans": tm("Houston Texans", "Texans", "Texans", "AFC", "AFC South", 2002, 2002, "#03202F", "#C8102E", "#FFFFFF", "#041018", "#0A202B", "#020508", "#03202F", "#C8102E", "#F3F7FA", "#BED0DA", "Texans archive - newest-franchise build, deep-blue reset cycles, and recent lift", "Expansion build, Watt-Hopkins years, and the recent Houston rebound in one archive.", ["Colts", "Titans", "Jaguars"], [2011, 2012, 2019, 2023, 2024], ["J.J. Watt", "Andre Johnson", "Arian Foster"], 34, "hou", "houston-texans", "htx"),
    "titans": tm("Tennessee Titans", "Titans", "Titans", "AFC", "AFC South", 1960, 1960, "#4B92DB", "#0C2340", "#C8102E", "#04101A", "#0C2234", "#02060A", "#0C2340", "#4B92DB", "#F2F8FF", "#BFD0E5", "Titans archive - oilers powder-blue memory and nashville-era edge", "Houston Oilers and Tennessee Titans history remain one continuous file here.", ["Colts", "Jaguars", "Texans", "Ravens"], [1960, 1961, 1978, 1999, 2008, 2021], ["Earl Campbell", "Warren Moon", "Steve McNair"], 10, "ten", "tennessee-titans", "oti"),
    "vikings": tm("Minnesota Vikings", "Vikings", "Vikings", "NFC", "NFC North", 1961, 1961, "#4F2683", "#FFC62F", "#FFFFFF", "#090513", "#1A0D2B", "#030106", "#4F2683", "#FFC62F", "#F7F1FF", "#D4C2E8", "Vikings archive - four-super-bowl echoes, dome offense, and winter heartbreak", "Bud Grant roots, Moss-Carter fireworks, and every Minnesota near-miss or spike in one place.", ["Packers", "Bears", "Saints"], [1969, 1973, 1976, 1998, 2009, 2017], ["Fran Tarkenton", "Randy Moss", "Alan Page"], 16, "min", "minnesota-vikings", "min"),
}


TARGET_TEAM_SLUGS = sorted(slug for slug in TEAM_CATALOG if slug not in EXCLUDED_RENDER_SLUGS)


def team_meta(slug: str) -> dict[str, Any]:
    return TEAM_CATALOG[slug]


def build_team_config(slug: str, end_year: int) -> dict[str, Any]:
    meta = team_meta(slug)
    start_year = meta["season_start_year"]
    logo = f"https://a.espncdn.com/i/teamlogos/nfl/500/{meta['espn_slug']}.png"
    return {
        "teamName": meta["team_name"],
        "shortName": meta["short_name"],
        "mascotName": meta["mascot_name"],
        "conference": meta["conference"],
        "division": meta["division"],
        "foundedYear": meta["founded_year"],
        "seasonStartYear": start_year,
        "primaryColor": meta["primary_color"],
        "secondaryColor": meta["secondary_color"],
        "tertiaryColor": meta["tertiary_color"],
        "darkBgStart": meta["dark_bg_start"],
        "darkBgMid": meta["dark_bg_mid"],
        "darkBgEnd": meta["dark_bg_end"],
        "lightThemePrimary": meta["light_theme_primary"],
        "lightThemeAccent": meta["light_theme_accent"],
        "textOnDark": meta["text_on_dark"],
        "mutedOnDark": meta["muted_on_dark"],
        "logoMain": logo,
        "logoWordmark": logo,
        "favicon": logo,
        "heroTitle": f"{meta['team_name']}<br>All-Time Database",
        "heroKicker": meta["archive_kicker"],
        "heroText": (
            f"This site is a fan-built database documenting every {meta['team_name']} game from "
            f"{start_year} through {end_year}. {meta['identity_note']}"
        ),
        "badgeText": f"{meta['team_name']} - {start_year}-{end_year}",
        "copyrightLabel": f"{meta['short_name']} Game Archive",
        "headCoach": CURRENT_HEAD_COACHES.get(slug, ""),
        "supportLink": SUPPORT_LINK,
        "supportLabel": SUPPORT_LABEL,
        "disclaimerTeamName": meta["team_name"],
        "rivalryTeams": list(meta["rivalries"]),
        "featuredSeasons": list(meta["featured_seasons"]),
        "iconicPlayers": list(meta["iconic_players"]),
        "externalLinks": {
            "officialSite": f"https://www.nfl.com/teams/{meta['nfl_slug']}/",
            "statMuse": f"https://www.statmuse.com/nfl/team/{meta['nfl_slug']}",
            "proFootballReference": f"https://www.pro-football-reference.com/teams/{meta['pfr_code']}/",
            "espn": f"https://www.espn.com/nfl/team/schedule/_/name/{meta['espn_slug']}",
            "youtubeSearchBase": f"https://www.google.com/search?btnI=I&q={meta['team_name'].replace(' ', '+')}+NFL+highlights+site%3Ayoutube.com%2Fwatch",
        },
        "espnTeamId": meta["espn_logo_id"],
        "espnSlug": meta["espn_slug"],
        "nflSlug": meta["nfl_slug"],
    }
