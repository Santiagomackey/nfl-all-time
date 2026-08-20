import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const ROOT = path.resolve('C:/Users/tomas/OneDrive/Documents/New project/nfl_all_time');
const DATA_DIR = path.join(ROOT, 'data');
const BROWSER_DATA_DIR = path.join(DATA_DIR, 'browser');

const SPECIAL_TEAM_ENRICHMENTS = {
  ravens: {
    franchiseSummary: {
      legacySummary:
        'The Ravens built their identity around violent defense, controlled games, and postseason resilience before evolving into a modern offense around Lamar Jackson.',
      notableEras: [
        {
          label: 'Founding Identity',
          years: '1996-1999',
          description: 'Baltimore established the franchise foundation through defense-first football and early roster pillars like Jonathan Ogden and Ray Lewis.'
        },
        {
          label: 'Championship Defense',
          years: '2000-2007',
          description: 'A historic defense delivered the first Super Bowl and set the tone for how Ravens football would be understood league-wide.'
        },
        {
          label: 'Harbaugh-Flacco Run',
          years: '2008-2017',
          description: 'Consistent playoff appearances, big road wins, and the 2012 Super Bowl title defined this era.'
        },
        {
          label: 'Lamar Era',
          years: '2018-present',
          description: 'Baltimore shifted into an explosive, quarterback-driven offense without losing its physical edge.'
        }
      ]
    },
    coaches: [
      { name: 'Ted Marchibroda', years: '1996-1998', summary: 'The franchise’s first head coach, responsible for the transition from Cleveland to Baltimore.' },
      { name: 'Brian Billick', years: '1999-2007', summary: 'Oversaw the 2000 championship team and one of the great defenses in NFL history.' },
      { name: 'John Harbaugh', years: '2008-present', summary: 'Delivered long-term stability, a second Super Bowl, and the Lamar Jackson era.' }
    ],
    stadiumHistory: [
      { name: 'Memorial Stadium', years: '1996-1997', location: 'Baltimore, Maryland', notes: 'Temporary home during the franchise launch period.' },
      { name: 'M&T Bank Stadium', years: '1998-present', location: 'Baltimore, Maryland', notes: 'Opened as Ravens Stadium, later renamed PSINet Stadium, M&T Bank Stadium, and now The Bank.' }
    ],
    honors: {
      retiredNumbers: [],
      hallOfFamers: ['Ray Lewis', 'Ed Reed', 'Jonathan Ogden']
    },
    overviewOverrides: {
      championships: 2,
      superBowls: 2,
      conferenceTitles: 2,
      playoffAppearances: null
    }
  },
  patriots: {
    franchiseSummary: {
      legacySummary:
        'The Patriots moved from AFL instability to one of the most dominant dynasties in North American sports, anchored by elite coaching, quarterback play, and situational excellence.',
      notableEras: [
        {
          label: 'AFL Origins',
          years: '1960-1975',
          description: 'Boston and early Foxborough seasons built the roots of the franchise before sustained NFL relevance arrived.'
        },
        {
          label: 'Parcells Revival',
          years: '1993-1996',
          description: 'Bill Parcells restored credibility and carried the Patriots back into contender status.'
        },
        {
          label: 'Brady-Belichick Dynasty',
          years: '2001-2019',
          description: 'Six Super Bowls, constant division control, and one of the greatest dynastic runs in sports history.'
        },
        {
          label: 'Post-Dynasty Reset',
          years: '2020-present',
          description: 'The modern Patriots are reshaping their identity after the Brady era while staying anchored in franchise history.'
        }
      ]
    },
    coaches: [
      { name: 'Chuck Fairbanks', years: '1973-1978', summary: 'Built one of the first Patriots teams with sustained modern relevance.' },
      { name: 'Raymond Berry', years: '1984-1989', summary: 'Led the franchise to its first Super Bowl appearance in the 1985 season.' },
      { name: 'Bill Parcells', years: '1993-1996', summary: 'Dragged the franchise back to contention and the Super Bowl.' },
      { name: 'Bill Belichick', years: '2000-2023', summary: 'Architect of the Brady-Belichick dynasty and the defining coach in franchise history.' },
      { name: 'Mike Vrabel', years: '2024-present', summary: 'Leads the latest Patriots rebuild with a franchise-icon perspective.' }
    ],
    stadiumHistory: [
      { name: 'Nickerson Field', years: '1960-1962', location: 'Boston, Massachusetts', notes: 'Original AFL-era home of the Boston Patriots.' },
      { name: 'Fenway Park', years: '1963-1968', location: 'Boston, Massachusetts', notes: 'Shared venue that helped keep the Patriots tied to the city during the early years.' },
      { name: 'Alumni Stadium', years: '1969', location: 'Chestnut Hill, Massachusetts', notes: 'Single-season stop before the permanent move to Foxborough.' },
      { name: 'Harvard Stadium', years: '1970', location: 'Boston, Massachusetts', notes: 'Short final Boston-area stop before the move to Foxborough.' },
      { name: 'Foxboro Stadium', years: '1971-2001', location: 'Foxborough, Massachusetts', notes: 'Also known as Schaefer and Sullivan Stadium during the franchise’s first long-term home era.' },
      { name: 'Gillette Stadium', years: '2002-present', location: 'Foxborough, Massachusetts', notes: 'Home of the modern dynasty and the current franchise era.' }
    ],
    honors: {
      retiredNumbers: ['20 - Gino Cappelletti', '40 - Mike Haynes', '57 - Steve Nelson', '73 - John Hannah'],
      hallOfFamers: ['John Hannah', 'Andre Tippett', 'Mike Haynes', 'Ty Law', 'Richard Seymour', 'Tom Brady']
    },
    overviewOverrides: {
      championships: 6,
      superBowls: 6,
      conferenceTitles: 11,
      playoffAppearances: null
    }
  }
};

function loadLegacyTeamFile(filePath) {
  let source = fs.readFileSync(filePath, 'utf8');
  source = source.replace(/export const /g, 'const ');
  source += '\nthis.__exports = { TEAM_CONFIG, ALL_GAMES, SEASON_EXTRA_DATA, MATCH_DETAILS, RIVALRY_DATA, PLAYER_FEATURES_BY_SEASON, FEATURED_GAMES, TIMELINE_COPY, TEAM_LOGO_MAP };';
  const context = {};
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.__exports;
}

function slugify(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function toNumber(value) {
  if (value === null || value === undefined || value === '') return null;
  const num = Number(String(value).replace(/,/g, ''));
  return Number.isFinite(num) ? num : null;
}

function computeOverviewStats(games, seasons) {
  const regularGames = games.filter((game) => !game.isPlayoff);
  const playoffGames = games.filter((game) => game.isPlayoff);
  const countResult = (items, result) => items.filter((game) => game.result === result).length;
  const divisionTitles = seasons.filter((season) => Number(season.divisionRank) === 1).length;
  const conferenceTitles = seasons.filter((season) => /Super Bowl/i.test(season.playoffResult || '')).length;
  const superBowlWins = seasons.filter((season) => /Super Bowl Champion/i.test(season.playoffResult || '')).length;
  const championships = superBowlWins;
  const playoffAppearances = playoffGames.length
    ? seasons.filter((season) => games.some((game) => game.season === season.year && game.isPlayoff)).length
    : null;

  return {
    games: games.length,
    wins: countResult(games, 'W'),
    losses: countResult(games, 'L'),
    ties: countResult(games, 'T'),
    winPct: games.length ? Number((countResult(games, 'W') / games.length).toFixed(3)) : 0,
    regularSeasonGames: regularGames.length,
    playoffGames: playoffGames.length,
    playoffWins: countResult(playoffGames, 'W'),
    playoffLosses: countResult(playoffGames, 'L'),
    playoffAppearances,
    championships,
    superBowls: superBowlWins,
    conferenceTitles,
    divisionTitles,
    pointsFor: games.reduce((sum, game) => sum + (toNumber(game.teamScore) ?? 0), 0),
    pointsAgainst: games.reduce((sum, game) => sum + (toNumber(game.opponentScore) ?? 0), 0)
  };
}

function buildSeasonRecords(allGames, seasonExtraData, currentCoach) {
  const seasons = Object.keys(seasonExtraData || {})
    .sort((a, b) => Number(a) - Number(b))
    .map((year) => {
      const extra = seasonExtraData[year] || {};
      const games = allGames.filter((game) => String(game.season) === String(year));
      const leaderMap = new Map((extra.leaders || []).map((leader) => [String(leader.metric), leader]));
      const passLeader = leaderMap.get('PASS YDS');
      return {
        year: Number(year),
        record: extra.record || null,
        wins: extra.wins ?? games.filter((game) => game.result === 'W').length,
        losses: extra.losses ?? games.filter((game) => game.result === 'L').length,
        ties: extra.ties ?? games.filter((game) => game.result === 'T').length,
        coach: extra.coach || (Number(year) === Math.max(...Object.keys(seasonExtraData).map(Number)) ? currentCoach : null),
        quarterback: extra.qb || passLeader?.name || null,
        finish: extra.division_finish || null,
        division: extra.division || null,
        divisionRank: extra.division_rank ?? null,
        playoffResult: extra.playoff_result || (games.some((game) => game.isPlayoff) ? 'Playoff team' : 'Missed playoffs'),
        notableSeason: Boolean(extra.notable_season),
        teamStats: extra.stats || {},
        leaders: extra.leaders || [],
        standings: extra.standings || [],
        sources: extra.sources || {}
      };
    });

  seasons.forEach((season) => {
    const yearGames = allGames.filter((game) => game.season === season.year);
    if (yearGames.some((game) => game.isPlayoff)) {
      const finalGame = yearGames.filter((game) => game.isPlayoff).slice(-1)[0];
      if (/Super Bowl/i.test(finalGame.round) && finalGame.result === 'W') {
        season.playoffResult = 'Super Bowl Champion';
      } else if (/Super Bowl/i.test(finalGame.round) && finalGame.result === 'L') {
        season.playoffResult = 'Super Bowl appearance';
      } else if (/Conference Championship/i.test(finalGame.round)) {
        season.playoffResult = 'Conference Championship';
      } else if (/Divisional/i.test(finalGame.round)) {
        season.playoffResult = 'Divisional Round';
      } else if (/Wild Card/i.test(finalGame.round)) {
        season.playoffResult = 'Wild Card Round';
      }
    }
  });

  return seasons;
}

function buildGames(allGames, matchDetails) {
  return allGames.map((game, index) => {
    const detailKey = [
      game.year,
      String(game.round || '').trim(),
      game.opponent,
      game.location,
      `${game.teamScore ?? game.ravensScore}-${game.oppScore}`
    ].join('|');
    const detail = matchDetails?.[detailKey] || null;
    return {
      id: `${game.year}-${index}-${slugify(game.opponent)}-${slugify(game.round)}`,
      season: Number(game.year),
      date: game.date || null,
      displayDate: game.displayDate || game.date || null,
      round: game.round || '',
      competition: game.isPlayoff ? 'Playoffs' : 'Regular Season',
      opponent: game.opponent,
      opponentSlug: slugify(game.opponent),
      homeAway: game.location === 'Home' ? 'home' : 'away',
      location: game.location,
      result: game.result,
      teamScore: toNumber(game.teamScore ?? game.ravensScore),
      opponentScore: toNumber(game.oppScore),
      overtime: /OT/i.test(String(game.round || '')) || Boolean(game.overtime),
      isPlayoff: Boolean(game.isPlayoff),
      stadium: game.stadium || null,
      stats: {
        totalYards: toNumber(game.totalYards),
        passingYards: toNumber(game.passingYards),
        rushingYards: toNumber(game.rushingYards),
        turnovers: toNumber(game.turnovers),
        firstDowns: toNumber(game.firstDowns),
        possession: game.possession || null,
        opponentTotalYards: toNumber(game.opponentTotalYards),
        opponentPassingYards: toNumber(game.opponentPassingYards),
        opponentRushingYards: toNumber(game.opponentRushingYards)
      },
      links: {
        youtubeSummary: game.youtubeSummaryUrl || null
      },
      detail: detail
        ? {
            leftTeam: detail.leftTeam || null,
            rightTeam: detail.rightTeam || null,
            teamStats: detail.teamStats || []
          }
        : null
    };
  });
}

function buildRivalries(rivalryData) {
  return Object.entries(rivalryData || {}).map(([team, rivalry]) => ({
    team,
    teamSlug: slugify(team),
    summary: `${team} is one of the core recurring opponents in this archive, with ${rivalry.games} tracked meetings.`,
    record: rivalry.record || null,
    games: rivalry.games || 0,
    firstMeeting: rivalry.firstMeeting || null,
    lastMeeting: rivalry.lastMeeting || null,
    recentMeetings: rivalry.recent || [],
    notableMeetings: [rivalry.firstMeeting, rivalry.lastMeeting].filter(Boolean)
  }));
}

function buildLegends(playerFeaturesBySeason) {
  const bucket = new Map();
  Object.entries(playerFeaturesBySeason || {}).forEach(([season, players]) => {
    (players || []).forEach((player) => {
      const key = `${player.name}|${player.role}`;
      if (!bucket.has(key)) {
        bucket.set(key, {
          name: player.name,
          position: player.role,
          years: new Set(),
          summary: player.mini || player.subtitle || '',
          tags: new Set(player.kpis || []),
          facts: new Set(player.facts || []),
          seasonsFeatured: []
        });
      }
      const entry = bucket.get(key);
      entry.years.add(season);
      entry.seasonsFeatured.push(Number(season));
      (player.kpis || []).forEach((tag) => entry.tags.add(tag));
      (player.facts || []).forEach((fact) => entry.facts.add(fact));
    });
  });

  return [...bucket.values()]
    .map((entry) => {
      const years = [...entry.years].sort((a, b) => Number(a) - Number(b));
      return {
        name: entry.name,
        position: entry.position,
        years: years.length ? `${years[0]}-${years[years.length - 1]}` : null,
        summary: entry.summary,
        tags: [...entry.tags].slice(0, 5),
        facts: [...entry.facts].slice(0, 4),
        seasonsFeatured: [...new Set(entry.seasonsFeatured)].sort((a, b) => a - b)
      };
    })
    .sort((a, b) => b.seasonsFeatured.length - a.seasonsFeatured.length)
    .slice(0, 14);
}

function buildTimeline(timelineCopy) {
  return (timelineCopy || []).map((item) => ({
    year: item.year || null,
    title: item.title || '',
    description: item.copy || item.description || ''
  }));
}

function buildAchievements(seasons, timeline) {
  const superBowls = seasons
    .filter((season) => /Super Bowl/i.test(season.playoffResult || ''))
    .map((season) => ({
      season: season.year,
      result: season.playoffResult
    }));
  const divisionTitles = seasons
    .filter((season) => Number(season.divisionRank) === 1)
    .map((season) => season.year);

  return {
    championships: superBowls.filter((item) => /Champion/i.test(item.result)),
    superBowls,
    conferenceTitles: seasons
      .filter((season) => /Conference Championship|Super Bowl/i.test(season.playoffResult || ''))
      .map((season) => ({
        season: season.year,
        result: season.playoffResult
      })),
    divisionTitles,
    milestones: timeline.slice(0, 8)
  };
}

function buildManifestEntry(teamJson) {
  return {
    slug: teamJson.slug,
    dataFile: `data/${teamJson.slug}.json`,
    teamName: teamJson.identity.teamName,
    shortName: teamJson.identity.shortName,
    city: teamJson.identity.city,
    conference: teamJson.identity.conference,
    division: teamJson.identity.division,
    foundedYear: teamJson.identity.foundedYear,
    colors: teamJson.identity.colors,
    logo: teamJson.identity.assets.logo,
    wordmark: teamJson.identity.assets.wordmark,
    overviewStats: {
      wins: teamJson.overviewStats.wins,
      losses: teamJson.overviewStats.losses,
      championships: teamJson.overviewStats.championships,
      playoffAppearances: teamJson.overviewStats.playoffAppearances
    },
    heroText: teamJson.identity.branding.heroText
  };
}

function transformTeam(slug, legacy) {
  const { TEAM_CONFIG, ALL_GAMES, SEASON_EXTRA_DATA, MATCH_DETAILS, RIVALRY_DATA, PLAYER_FEATURES_BY_SEASON, FEATURED_GAMES, TIMELINE_COPY, TEAM_LOGO_MAP } = legacy;
  const games = buildGames(ALL_GAMES, MATCH_DETAILS);
  const seasons = buildSeasonRecords(games, SEASON_EXTRA_DATA, TEAM_CONFIG.headCoach);
  const overviewStats = computeOverviewStats(games, seasons);
  const enrichment = SPECIAL_TEAM_ENRICHMENTS[slug] || {};
  Object.assign(overviewStats, enrichment.overviewOverrides || {});
  const city = TEAM_CONFIG.teamName.replace(` ${TEAM_CONFIG.shortName}`, '').trim();

  return {
    schemaVersion: '1.0.0',
    slug,
    identity: {
      teamName: TEAM_CONFIG.teamName,
      fullName: TEAM_CONFIG.teamName,
      shortName: TEAM_CONFIG.shortName,
      nickname: TEAM_CONFIG.mascotName || TEAM_CONFIG.shortName,
      city,
      conference: TEAM_CONFIG.conference,
      division: TEAM_CONFIG.division,
      foundedYear: TEAM_CONFIG.foundedYear,
      seasonStartYear: TEAM_CONFIG.seasonStartYear || TEAM_CONFIG.foundedYear,
      colors: {
        primary: TEAM_CONFIG.primaryColor,
        secondary: TEAM_CONFIG.secondaryColor,
        tertiary: TEAM_CONFIG.tertiaryColor || '#ffffff',
        darkBgStart: TEAM_CONFIG.darkBgStart,
        darkBgMid: TEAM_CONFIG.darkBgMid,
        darkBgEnd: TEAM_CONFIG.darkBgEnd
      },
      assets: {
        logo: TEAM_CONFIG.logoMain,
        wordmark: TEAM_CONFIG.logoWordmark,
        favicon: TEAM_CONFIG.favicon,
        helmet: TEAM_CONFIG.helmetImage || null
      },
      branding: {
        heroTitle: TEAM_CONFIG.heroTitle,
        heroKicker: TEAM_CONFIG.heroKicker,
        heroText: TEAM_CONFIG.heroText,
        badgeText: TEAM_CONFIG.badgeText
      }
    },
    franchiseSummary: {
      intro: TEAM_CONFIG.heroText,
      legacySummary:
        enrichment.franchiseSummary?.legacySummary ||
        `${TEAM_CONFIG.teamName} spans ${overviewStats.games} archived games and ${seasons.length} seasons in this database.`,
      notableEras:
        enrichment.franchiseSummary?.notableEras ||
        buildTimeline(TIMELINE_COPY).slice(0, 4).map((entry) => ({
          label: entry.title,
          years: String(entry.year || ''),
          description: entry.description
        }))
    },
    overviewStats,
    seasons,
    games,
    rivalries: buildRivalries(RIVALRY_DATA),
    legends: buildLegends(PLAYER_FEATURES_BY_SEASON),
    coaches: enrichment.coaches || (TEAM_CONFIG.headCoach ? [{ name: TEAM_CONFIG.headCoach, years: 'Current', summary: 'Current head coach listed in the team configuration.' }] : []),
    stadiumHistory: enrichment.stadiumHistory || [],
    timeline: buildTimeline(TIMELINE_COPY),
    achievements: buildAchievements(seasons, buildTimeline(TIMELINE_COPY)),
    honors: {
      retiredNumbers: enrichment.honors?.retiredNumbers || [],
      hallOfFamers: enrichment.honors?.hallOfFamers || []
    },
    featuredGames: FEATURED_GAMES || [],
    featuredPlayersBySeason: PLAYER_FEATURES_BY_SEASON || {},
    teamLogoMap: TEAM_LOGO_MAP || {},
    ui: {
      supportLink: TEAM_CONFIG.supportLink || null,
      supportLabel: TEAM_CONFIG.supportLabel || null,
      headCoach: TEAM_CONFIG.headCoach || null,
      externalLinks: TEAM_CONFIG.externalLinks || {}
    }
  };
}

const jsFiles = fs
  .readdirSync(DATA_DIR)
  .filter((file) => file.endsWith('.js'))
  .sort((a, b) => a.localeCompare(b));

fs.mkdirSync(BROWSER_DATA_DIR, { recursive: true });

const manifest = [];

for (const file of jsFiles) {
  const slug = path.basename(file, '.js');
  const legacy = loadLegacyTeamFile(path.join(DATA_DIR, file));
  const json = transformTeam(slug, legacy);
  fs.writeFileSync(path.join(DATA_DIR, `${slug}.json`), JSON.stringify(json, null, 2));
  fs.writeFileSync(path.join(BROWSER_DATA_DIR, `${slug}.mjs`), `export default ${JSON.stringify(json, null, 2)};\n`);
  fs.writeFileSync(
    path.join(BROWSER_DATA_DIR, `${slug}.js`),
    `window.__NFL_TEAM_DATA__ = window.__NFL_TEAM_DATA__ || {}; window.__NFL_TEAM_DATA__[${JSON.stringify(slug)}] = ${JSON.stringify(json, null, 2)};\n`
  );
  manifest.push(buildManifestEntry(json));
}

manifest.sort((a, b) => a.teamName.localeCompare(b.teamName));
fs.writeFileSync(path.join(DATA_DIR, 'teams-manifest.json'), JSON.stringify({ schemaVersion: '1.0.0', teams: manifest }, null, 2));
fs.writeFileSync(path.join(BROWSER_DATA_DIR, 'teams-manifest.mjs'), `export default ${JSON.stringify({ schemaVersion: '1.0.0', teams: manifest }, null, 2)};\n`);
fs.writeFileSync(
  path.join(BROWSER_DATA_DIR, 'teams-manifest.js'),
  `window.__NFL_TEAM_MANIFEST__ = ${JSON.stringify({ schemaVersion: '1.0.0', teams: manifest }, null, 2)};\n`
);

console.log(`Generated ${manifest.length} team JSON files + manifest.`);
