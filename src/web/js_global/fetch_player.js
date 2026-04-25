const rankMap = {
    "vip": "VIP",
    "vipplus": "VIP+",
    "hero": "Hero",
    "champion": "Champion",
};

const rankColorMap = {
    "VIP": "#22c55e",
    "VIP+": "#22d3ee",
    "Hero": "#a855f7",
    "Champion": "#f59e0b",
    "Media": "#ec4899",
    "Mod": "#fb923c",
    "Admin": "#dc2626"
};

// Order of raids in the combined table — mirrors the in-game release order
// so newer raids slot in at the bottom predictably.
const RAID_DISPLAY_ORDER = [
    "Nest of the Grootslangs",
    "Orphion's Nexus of Light",
    "The Canyon Colossus",
    "The Nameless Anomaly",
    "The Wartorn Palace",
];

// "Unknown" is the v3.3-prod label for The Wartorn Palace (raid un-named server-side).
// Any wire-name not in this map renders as "New Raid" rather than leaking the raw API
// string to the UI — future raids stay visible even before we ship a code update.
const RAID_NAME_NORMALIZE = {
    "The Nameless Anomaly": "The Nameless Anomaly (TNA)",
    "The Canyon Colossus": "The Canyon Colossus (TCC)",
    "Orphion's Nexus of Light": "Orphion's Nexus of Light (NOL)",
    "Nest of the Grootslangs": "Nest of the Grootslangs (NOG)",
    "The Wartorn Palace": "The Wartorn Palace (TWP)",
    "Unknown": "The Wartorn Palace (TWP)",
};

const RAID_STATS_LABELS = {
    damageDealt: "Damage Dealt",
    damageTaken: "Damage Taken",
    healthHealed: "Healing",
    deaths: "Deaths",
    buffsTaken: "Buffs Taken",
    gambitsUsed: "Gambits Used",
};

const RAID_STATS_RANK_LABELS = {
    raid_damage_dealt: "Damage Dealt",
    raid_damage_taken: "Damage Taken",
    raid_heal: "Healing",
    raid_deaths: "Deaths",
    raid_buffs_taken: "Buffs Taken",
    raid_gambits_used: "Gambits Used",
};

function resetToGlobalView() {
    if (window.globalPlayerData) {
        displayPlayerData(window.globalPlayerData);
    } else {
        console.error("Global player data not found.");
    }
}

function displayPlayerData(playerData) {
    const resultsContainer = document.getElementById('player-results');
    const onlineStatus = playerData.online ? `online on ${playerData.server}` : 'offline';
    const onlineClass = playerData.online ? 'online' : 'offline';

    const gameRank = playerData.shortenedRank || rankMap[playerData.supportRank] || 'None';
    const rankColor = rankColorMap[gameRank] || 'inherit';
    const firstJoined = formatDate(playerData.firstJoin);
    const lastJoined = formatDate(playerData.lastJoin);
    const guildInfo = playerData.guild
        ? `<strong>[${escapeHtml(playerData.guild.prefix)}] ${escapeHtml(playerData.guild.name)}</strong> · ${escapeHtml(playerData.guild.rank)}`
        : '<span class="muted-dash">No Guild</span>';

    const gd = playerData.globalData || {};
    const raidList = (gd.raids && gd.raids.list) || {};
    const raidTotal = (gd.raids && gd.raids.total) || 0;
    const dungeonTotal = (gd.dungeons && gd.dungeons.total) || 0;
    const guildRaids = gd.guildRaids || {};
    const guildRaidList = guildRaids.list || {};
    const guildRaidTotal = guildRaids.total || 0;

    const pvpKills = (gd.pvp && gd.pvp.kills) || 0;
    const pvpDeaths = (gd.pvp && gd.pvp.deaths) || 0;

    const heroSection = renderHeroSection({
        username: playerData.username,
        uuid: playerData.uuid,
        gameRank,
        rankColor,
        onlineStatus,
        onlineClass,
        guildInfo,
        firstJoined,
        lastJoined,
        statsGridHTML: renderStatsGrid(gd, playerData.playtime, pvpKills, pvpDeaths, dungeonTotal),
    });
    const combinedRaidsCard = renderCombinedRaidsCard(raidList, raidTotal, guildRaidList, guildRaidTotal);
    const raidStatsCard = renderRaidStatsCard(gd.raidStats);
    const guildHistoryCard = renderGuildHistoryCard(playerData.guildHistory, playerData.restrictions);
    const classButtons = renderClassButtons(playerData.characters);

    resultsContainer.innerHTML = `
        <div class="player-card">
            ${heroSection}
            <div class="panel-row">
                ${combinedRaidsCard}
                ${raidStatsCard}
            </div>
            <div class="panel-row" id="raid-rank-row"></div>
            ${guildHistoryCard}
            ${classButtons}
            <div id="character-cards-container"></div>
        </div>
    `;

    window.globalPlayerData = playerData;
    if (gd.raidStats) {
        renderRaidRankPanel(playerData.username);
    }
    document.querySelectorAll('.character-button').forEach(button => {
        button.addEventListener('click', () => {
            const id = button.getAttribute('data-character-id');
            displayCharacterData(playerData.characters[id], playerData.uuid, playerData.username);
        });
    });
}

function renderHeroSection({ username, uuid, gameRank, rankColor, onlineStatus, onlineClass, guildInfo, firstJoined, lastJoined, statsGridHTML }) {
    return `
        <section class="player-hero">
            <div class="player-hero-avatar">
                <img src="https://visage.surgeplay.com/player/512/${encodeURIComponent(uuid)}" alt="${escapeHtml(username)}" onerror="this.src='https://visage.surgeplay.com/player/512/MHF_Steve';this.onerror=null;">
            </div>
            <div class="player-hero-identity">
                <h3 class="player-hero-name">
                    <span class="player-hero-rank" style="color: ${rankColor};">[${escapeHtml(gameRank)}]</span>
                    ${escapeHtml(username)}
                </h3>
                <div class="player-hero-status ${onlineClass}">${escapeHtml(onlineStatus)}</div>
                <div class="player-hero-meta">
                    <div class="player-hero-meta-row"><span>Guild:</span> ${guildInfo}</div>
                    <div class="player-hero-meta-row">
                        <span>First Joined: <strong>${escapeHtml(firstJoined)}</strong></span>
                        <span>Last Seen: <strong>${escapeHtml(lastJoined)}</strong></span>
                    </div>
                </div>
            </div>
            ${statsGridHTML || ""}
        </section>
    `;
}

function renderStatsGrid(gd, playtime, pvpKills, pvpDeaths, dungeonTotal) {
    // Tile values that routinely exceed a million (mobs, chests) get the compact
    // formatter; smaller categorical totals stay as locale-grouped integers so the
    // exact number is still visible.
    const tiles = [
        { label: "Total Level", value: formatNumber(gd.totalLevel || 0) },
        { label: "Playtime", value: `${formatNumber(playtime || 0)}`, sub: "hours" },
        { label: "Mobs Killed", value: formatCompactSafe(gd.mobsKilled || 0) },
        { label: "Chests Opened", value: formatCompactSafe(gd.chestsFound || 0) },
        { label: "Dungeons", value: formatNumber(dungeonTotal || 0) },
        { label: "Wars Joined", value: formatNumber(gd.wars || 0) },
        { label: "Quests", value: formatNumber(gd.completedQuests || 0) },
        { label: "World Events", value: formatNumber(gd.worldEvents || 0) },
        { label: "PvP K / D", value: `${formatNumber(pvpKills)} / ${formatNumber(pvpDeaths)}`, sub: `K/D ${calculateKD(pvpKills, pvpDeaths)}` },
    ];
    return `
        <section class="stats-grid">
            ${tiles.map(t => `
                <div class="stat-tile">
                    <div class="stat-tile-label">${escapeHtml(t.label)}</div>
                    <div class="stat-tile-value">${t.value}</div>
                    ${t.sub ? `<div class="stat-tile-sub">${escapeHtml(t.sub)}</div>` : ""}
                </div>
            `).join('')}
        </section>
    `;
}

function buildOrderedRaidNames(soloList, guildList) {
    const seen = new Set();
    const names = [];
    for (const name of RAID_DISPLAY_ORDER) {
        if (name in soloList || name in guildList) {
            names.push(name);
            seen.add(name);
        }
    }
    // Server-side aliases like "Unknown" — fold into TWP if present, otherwise append.
    for (const name of Object.keys({ ...soloList, ...guildList })) {
        if (seen.has(name)) continue;
        if (name === "Unknown") {
            // Already covered by The Wartorn Palace if present; fall back to appending.
            if (!names.includes("The Wartorn Palace")) {
                names.push(name);
            }
            seen.add(name);
            continue;
        }
        names.push(name);
        seen.add(name);
    }
    return names;
}

function renderCombinedRaidsCard(raidList, raidTotal, guildRaidList, guildRaidTotal) {
    const orderedNames = buildOrderedRaidNames(raidList, guildRaidList);
    const rows = orderedNames.map(name => {
        const solo = raidList[name];
        const guild = guildRaidList[name];
        const aliasGuild = name === "The Wartorn Palace" ? guildRaidList["Unknown"] : undefined;
        const aliasSolo = name === "The Wartorn Palace" ? raidList["Unknown"] : undefined;
        const soloVal = (solo !== undefined ? solo : aliasSolo) || 0;
        const guildVal = (guild !== undefined ? guild : aliasGuild) || 0;
        return `
            <tr>
                <td>${displayRaidName(name)}</td>
                <td class="numeric">${formatNumber(soloVal)}</td>
                <td class="numeric">${formatNumber(guildVal)}</td>
            </tr>
        `;
    }).join('');
    return `
        <section class="panel-card">
            <div class="panel-card-header">Raid Clears</div>
            <div class="panel-card-body">
                <table class="stat-table">
                    <thead>
                        <tr>
                            <th>Content</th>
                            <th class="numeric">Normal</th>
                            <th class="numeric">Guild</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows || `<tr><td colspan="3" class="muted-dash">No raid clears recorded yet.</td></tr>`}
                        <tr class="total-row">
                            <td>All Raids</td>
                            <td class="numeric">${formatNumber(raidTotal)}</td>
                            <td class="numeric">${formatNumber(guildRaidTotal)}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>
    `;
}

function renderRaidStatsCard(raidStats) {
    if (!raidStats) {
        return `
            <section class="panel-card">
                <div class="panel-card-header">Raid Stats</div>
                <div class="panel-card-body">
                    <div class="guild-history-empty">No raid stats recorded yet.</div>
                </div>
            </section>
        `;
    }
    // Raid metric values are global aggregates that frequently land in the
    // hundreds-of-millions / billions range — compact (K/M/B/T) keeps the row
    // legible without horizontal overflow on the panel card.
    const rows = Object.entries(RAID_STATS_LABELS).map(([key, label]) => `
        <tr>
            <td>${label}</td>
            <td class="numeric">${formatCompactSafe(raidStats[key] || 0)}</td>
        </tr>
    `).join('');
    return `
        <section class="panel-card">
            <div class="panel-card-header">Raid Stats</div>
            <div class="panel-card-body">
                <table class="stat-table">
                    <tbody>${rows}</tbody>
                </table>
            </div>
        </section>
    `;
}

function renderGuildHistoryCard(guildHistory, restrictions) {
    if (restrictions && restrictions.guildHistoryAccess === false) {
        return `
            <section class="panel-card full-width">
                <div class="panel-card-header">Guild History</div>
                <div class="panel-card-body">
                    <div class="guild-history-empty">Player has hidden their guild history.</div>
                </div>
            </section>
        `;
    }
    if (!guildHistory || guildHistory.length === 0) {
        return "";
    }
    return `
        <section class="panel-card full-width">
            <div class="panel-card-header">Guild History (${formatNumber(guildHistory.length)})</div>
            <div class="panel-card-body">
                <ul class="guild-history-list">
                    ${guildHistory.map(entry => `<li>${formatGuildHistoryEntry(entry)}</li>`).join('')}
                </ul>
            </div>
        </section>
    `;
}

function formatGuildHistoryEntry(entry) {
    if (typeof entry === "string") {
        return escapeHtml(entry);
    }
    if (!entry || typeof entry !== "object") {
        return escapeHtml(String(entry));
    }
    const guildName = entry.name || entry.guild || entry.guildName || entry.prefix || "Unknown Guild";
    const raidCount = entry.raids || entry.guildRaids || entry.completions || entry.completionCount;
    if (raidCount !== undefined && raidCount !== null) {
        return `<strong>${escapeHtml(String(guildName))}</strong> · ${formatNumber(raidCount)} raids`;
    }
    return escapeHtml(Object.entries(entry).map(([key, value]) => `${key}: ${value}`).join(', '));
}

function renderClassButtons(characters) {
    if (!characters || Object.keys(characters).length === 0) {
        return "";
    }
    return `
        <section class="class-buttons-section">
            <div class="buttons-container">
                ${Object.entries(characters).map(([id, character]) => {
                    const charName = character.nickname
                        ? `Lv. ${character.level} ${character.nickname}`
                        : `Lv. ${character.level} ${character.type}`;
                    const buttonClass = character.nickname ? 'character-button-cyan' : 'character-button-green';
                    return `<button class="character-button ${buttonClass}" data-character-id="${id}">${escapeHtml(charName)}</button>`;
                }).join('')}
            </div>
            <button class="back-button" onclick="resetToGlobalView()">All classes</button>
        </section>
    `;
}

async function renderRaidRankPanel(username) {
    // The legacy `/api/leaderboard/raid_stats` aggregate endpoint was retired
    // when we merged raid metrics into the unified raid leaderboard
    // (`/api/leaderboard/raid/{key}`). To keep this rank panel working we now
    // fan out 6 small fetches in parallel — each returns a top-100 array, and
    // a player's index in that array is their rank on that metric.
    const row = document.getElementById('raid-rank-row');
    if (!row) {
        return;
    }
    const lowerName = username.toLowerCase();
    try {
        const entries = Object.entries(RAID_STATS_RANK_LABELS);
        const responses = await Promise.all(entries.map(([category]) =>
            fetch(`https://nori.fish/api/leaderboard/raid/${category}`)
                .then(r => (r.ok ? r.json() : null))
                .catch(() => null)
        ));

        let hasRank = false;
        const rows = entries.map(([category, label], i) => {
            const ranking = Array.isArray(responses[i]) ? responses[i] : [];
            const index = ranking.findIndex(entry => Object.keys(entry)[0].toLowerCase() === lowerName);
            if (index === -1) {
                return `<tr><td>${label}</td><td class="numeric"><span class="muted-dash">Unranked</span></td></tr>`;
            }
            hasRank = true;
            return `<tr><td>${label}</td><td class="numeric">#${index + 1}</td></tr>`;
        }).join('');

        if (!hasRank) {
            row.innerHTML = '';
            return;
        }
        row.innerHTML = `
            <section class="panel-card">
                <div class="panel-card-header">Raid Stat Ranks</div>
                <div class="panel-card-body">
                    <table class="stat-table">
                        <tbody>${rows}</tbody>
                    </table>
                </div>
            </section>
        `;
    } catch (error) {
        row.innerHTML = '';
    }
}

function displayCharacterData(characterData, playerUuid, playerName) {
    const resultsContainer = document.getElementById('player-results');
    const charType = characterData.nickname
        ? `${escapeHtml(characterData.nickname)} (${escapeHtml(characterData.type)})`
        : escapeHtml(characterData.type);
    const charRaids = (characterData.raids && characterData.raids.list) || {};
    const charRaidTotal = (characterData.raids && characterData.raids.total) || 0;
    const charDungeons = (characterData.dungeons && characterData.dungeons.total) || 0;
    const charPvpKills = (characterData.pvp && characterData.pvp.kills) || 0;
    const charPvpDeaths = (characterData.pvp && characterData.pvp.deaths) || 0;

    const heroSection = `
        <section class="player-hero">
            <div class="player-hero-avatar">
                <img src="https://visage.surgeplay.com/player/512/${encodeURIComponent(playerUuid)}" alt="${escapeHtml(playerName)}" onerror="this.src='https://visage.surgeplay.com/player/512/MHF_Steve';this.onerror=null;">
            </div>
            <div class="player-hero-identity">
                <h3 class="player-hero-name">${charType}</h3>
                <div class="player-hero-status">Lv. ${escapeHtml(String(characterData.level))} · ${escapeHtml(playerName)}</div>
                <div class="player-hero-meta">
                    <div class="player-hero-meta-row">
                        <span>Total Level: <strong>${formatNumber(characterData.totalLevel || 0)}</strong></span>
                        <span>Playtime: <strong>${formatNumber(characterData.playtime || 0)} hr</strong></span>
                    </div>
                </div>
            </div>
        </section>
    `;

    const tiles = [
        { label: "Total Level", value: formatNumber(characterData.totalLevel || 0) },
        { label: "Playtime", value: formatNumber(characterData.playtime || 0), sub: "hours" },
        { label: "Mobs Killed", value: formatNumber(characterData.mobsKilled || 0) },
        { label: "Chests Found", value: formatNumber(characterData.chestsFound || 0) },
        { label: "Wars", value: formatNumber(characterData.wars || 0) },
        { label: "Logins", value: formatNumber(characterData.logins || 0) },
        { label: "Deaths", value: formatNumber(characterData.deaths || 0) },
        { label: "Discoveries", value: formatNumber(characterData.discoveries || 0) },
        { label: "Blocks Walked", value: formatNumber(characterData.blocksWalked || 0) },
        { label: "PvP K / D", value: `${formatNumber(charPvpKills)} / ${formatNumber(charPvpDeaths)}`, sub: `K/D ${calculateKD(charPvpKills, charPvpDeaths)}` },
    ];
    const statsGrid = `
        <section class="stats-grid">
            ${tiles.map(t => `
                <div class="stat-tile">
                    <div class="stat-tile-label">${escapeHtml(t.label)}</div>
                    <div class="stat-tile-value">${t.value}</div>
                    ${t.sub ? `<div class="stat-tile-sub">${escapeHtml(t.sub)}</div>` : ""}
                </div>
            `).join('')}
        </section>
    `;

    const charRaidRows = Object.entries(charRaids).map(([raidName, clears]) => `
        <tr>
            <td>${displayRaidName(raidName)}</td>
            <td class="numeric">${formatNumber(clears)}</td>
        </tr>
    `).join('');
    const charRaidsCard = `
        <section class="panel-card">
            <div class="panel-card-header">Class Raid Clears</div>
            <div class="panel-card-body">
                <table class="stat-table">
                    <thead><tr><th>Content</th><th class="numeric">Clears</th></tr></thead>
                    <tbody>
                        ${charRaidRows || `<tr><td colspan="2" class="muted-dash">No raid clears for this class yet.</td></tr>`}
                        <tr class="total-row">
                            <td>All Raids</td>
                            <td class="numeric">${formatNumber(charRaidTotal)}</td>
                        </tr>
                        <tr>
                            <td>Dungeons</td>
                            <td class="numeric">${formatNumber(charDungeons)}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>
    `;

    resultsContainer.innerHTML = `
        <div class="player-card">
            ${heroSection}
            ${statsGrid}
            <div class="panel-row">
                ${charRaidsCard}
            </div>
            <section class="class-buttons-section">
                <button class="back-button" onclick="resetToGlobalView()">All classes</button>
            </section>
        </div>
    `;
}

function displayErrorMessage(message) {
    const resultsContainer = document.getElementById('player-results');
    resultsContainer.innerHTML = `<p class="error-message">${escapeHtml(message)}</p>`;
}

function displayLoadingMessage(message) {
    const resultsContainer = document.getElementById('player-results');
    resultsContainer.innerHTML = `<p class="loading-message">${escapeHtml(message)}</p>`;
}

function displayRaidName(rawName) {
    return RAID_NAME_NORMALIZE[rawName] || `New Raid (${escapeHtml(rawName)})`;
}

function calculateKD(kills, deaths) {
    if (!kills || !deaths) {
        return "0";
    }
    return (kills / deaths).toFixed(2);
}

function formatNumber(value) {
    return Number(value || 0).toLocaleString();
}

// Compact (K/M/B/T) formatter wrapper — uses the shared `window.formatCompact`
// from `number_format.js` when available, falls back to locale-grouped digits
// if that script failed to load (e.g. cache or CSP edge case).
function formatCompactSafe(value) {
    if (typeof window.formatCompact === 'function') {
        return window.formatCompact(value);
    }
    return Number(value || 0).toLocaleString();
}

function formatDate(value) {
    if (!value) return "—";
    const d = new Date(value);
    if (isNaN(d.getTime())) return String(value);
    return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, char => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
    }[char]));
}

function updateURL(playerName) {
    const url = new URL(window.location);
    url.searchParams.set('name', playerName);
    window.history.pushState({}, '', url);
}

function getQueryParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById('player-search-form');
    const resultsContainer = document.getElementById('player-results');

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const playerName = document.getElementById('player-name').value;
        if (playerName.trim() === '') {
            alert('Please enter a player name');
            return;
        }
        updateURL(playerName);
        displayLoadingMessage("Loading player stats...");
        await fetchPlayerData(playerName);
    });

    async function fetchPlayerData(playerName) {
        try {
            const response = await fetch(`https://nori.fish/api/player/${playerName}`);
            if (!response.ok) {
                throw new Error('Player not found');
            }
            const playerData = await response.json();
            displayPlayerData(playerData);
        } catch (error) {
            displayErrorMessage(`Cannot fetch player ${playerName}`);
        }
    }

    const initialPlayerName = getQueryParameter('name');
    if (initialPlayerName) {
        document.getElementById("player-name").value = initialPlayerName;
        displayLoadingMessage("Loading player stats...");
        fetchPlayerData(initialPlayerName);
    }
});
