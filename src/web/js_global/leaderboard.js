document.addEventListener("DOMContentLoaded", () => {
    const categoryDropdown = document.getElementById("categoryDropdown");
    const leaderboardTable = document.getElementById("leaderboardTable");
    const leaderboardTableHeadRow = leaderboardTable.querySelector("thead tr");
    const leaderboardTableBody = leaderboardTable.querySelector("tbody");
    const paginationContainer = document.getElementById("pagination");
    let statHeader = document.getElementById("statHeader");
    let levelHeader = document.getElementById("levelHeader");
    let xpHeader = document.getElementById("xpHeader");
    let memberHeader = document.getElementById("memberHeader");
    let createdAtHeader = document.getElementById("createdAtHeader");
    const noDataMessage = document.getElementById("noDataMessage");
    const loadingMessage = document.getElementById("loadingMessage");
    const leaderboardTitle = document.querySelector("#Leaderboard h2");

    let currentType = getQueryParameter('type') || '';
    let currentCategory = getQueryParameter('category') || '';
    let currentPage = getQueryParameter('page') ? parseInt(getQueryParameter('page')) : 1;
    let raidAllPayload = null;
    let raidAllSortKey = getQueryParameter('sort') || 'raid_damage_dealt';
    const leaderboardPayloadCache = new Map();
    const playersPerPage = 10;
    const maxPages = 10;

    const fmt = (value) => (typeof window.formatCompact === 'function'
        ? window.formatCompact(value)
        : Number(value || 0).toLocaleString());

    // Raid leaderboard categories — covers per-raid clears AND aggregate raid metrics.
    // The "all" category renders a wide combined table; everything else is a focused
    // single-stat view. Metric keys (raid_*) match the JSON the data builder writes
    // into `player_leaderboard.json["ranking"]`.
    const raidCategories = {
        'all': 'All Raids & Metrics',
        'raids_total': 'Total Clears',
        'tna': 'The Nameless Anomaly (TNA)',
        'tcc': 'The Canyon Colossus (TCC)',
        'nol': "Orphion's Nexus of Light (NoL)",
        'nog': 'Nest of the Grootslangs (NoG)',
        'twp': 'The Wartorn Palace (TWP)',
        'raid_damage_dealt': 'Damage Dealt',
        'raid_damage_taken': 'Damage Taken',
        'raid_heal':         'Healing',
        'raid_deaths':       'Deaths',
        'raid_buffs_taken':  'Buffs Taken',
        'raid_gambits_used': 'Gambits Used',
    };

    // Categories whose values should render via the compact (K/M/B/T) formatter.
    // Clears stay as integers because they're typically <100k and the human
    // intuition for "127 clears" doesn't transfer well to "0.13K".
    const COMPACT_RAID_CATEGORIES = new Set([
        'raid_damage_dealt',
        'raid_damage_taken',
        'raid_heal',
        'raid_deaths',
        'raid_buffs_taken',
        'raid_gambits_used',
    ]);

    const statCategories = {
        'chests': 'Chests Opened',
        'mobs': 'Mobs Killed',
        'wars': 'Wars Joined',
        'dungeons': 'Dungeon Completed',
        'playtime': 'Playtime',
        'pvp_kills': 'PvP Kills',
        'quests': 'Quests Completed',
        'levels': 'Total Levels',
        'world_events': 'World Events',
        'deaths': 'Deaths'
    };

    const professionCategories = {
        'mining': 'Mining',
        'fishing': 'Fishing',
        'woodcutting': 'Woodcutting',
        'farming': 'Farming',
        'woodworking': 'Woodworking',
        'weaponsmithing': 'Weaponsmithing',
        'tailoring': 'Tailoring',
        'alchemism': 'Alchemism',
        'cooking': 'Cooking',
        'jeweling': 'Jeweling',
        'scribing': 'Scribing',
        'armouring': 'Armouring',
        "professionsGlobal": "Total"
    };

    const guildCategories = {
        'raids_total': 'All Raids',
        'chests': 'Chests Opened',
        'mobs': 'Mobs Killed',
        'tna': 'TNA',
        'tcc': 'TCC',
        'nol': 'NOL',
        'nog': 'NOG',
        'twp': 'TWP',
        'dungeons': 'Dungeons',
        'playtime': 'Playtime',
        'quests': 'Quests Completed',
        'levels': 'Player Levels',
        "sr": "Season Rating",
        'guildTerritories': 'Territories',
        'guildWars': 'Wars',
        'guildLevel': 'Levels'
    };

    const statHeaders = {
        'raids_total': 'Clears',
        'chests': 'Chests',
        'mobs': 'Kills',
        'tna': 'Clears',
        'tcc': 'Clears',
        'nol': 'Clears',
        'nog': 'Clears',
        'twp': 'Clears',
        'dungeons': 'Runs',
        'playtime': 'Hours',
        'quests': 'Quests',
        'levels': 'Level',
        'world_events': 'Events',
        'deaths': 'Deaths',
        'guild_raids_total': 'Clears',
        'g_tna': 'Clears',
        'g_tcc': 'Clears',
        'g_nol': 'Clears',
        'g_nog': 'Clears',
        'g_twp': 'Clears',
        "sr": "SR",
        'guildTerritories': 'Territories',
        'guildWars': 'Wars',
        'guildLevel': 'Level',
        'raid_damage_dealt': 'Dmg Dealt',
        'raid_damage_taken': 'Dmg Taken',
        'raid_heal': 'Healing',
        'raid_deaths': 'Deaths',
        'raid_buffs_taken': 'Buffs',
        'raid_gambits_used': 'Gambits',
    };

    // Column order for the "All" combined raid table. Individual raid clears
    // stay available as focused categories (TNA/TCC/NoL/NoG/TWP); the combined
    // view only shows total clears plus aggregate raid metrics.
    const RAID_ALL_COLUMNS = [
        { key: 'raids_total',       label: 'Clears',    compact: false },
        { key: 'raid_damage_dealt', label: 'Dmg Dealt', compact: true  },
        { key: 'raid_damage_taken', label: 'Dmg Taken', compact: true  },
        { key: 'raid_heal',         label: 'Healing',   compact: true  },
        { key: 'raid_deaths',       label: 'Deaths',    compact: true  },
        { key: 'raid_buffs_taken',  label: 'Buffs',     compact: true  },
        { key: 'raid_gambits_used', label: 'Gambits',   compact: true  },
    ];
    if (!RAID_ALL_COLUMNS.some(col => col.key === raidAllSortKey)) {
        raidAllSortKey = 'raid_damage_dealt';
    }

    function isRaidAllView() {
        return currentType === 'raids' && currentCategory === 'all';
    }

    window.chooseType = function(type) {
        currentType = type;
        raidAllPayload = null;
        if (currentType === 'raids' && !raidCategories[currentCategory]) {
            currentCategory = 'all';
        }
        displayCategories();
        if (currentType === 'raids') {
            currentPage = 1;
            updateStatHeader();
            updateLeaderboardTitle();
            fetchLeaderboardData();
        }
        updateURL();
    };

    function displayCategories() {
        categoryDropdown.style.display = 'inline-block';
        categoryDropdown.innerHTML = '<option value="">Select Category</option>';

        let categories = {};
        if (currentType === 'raids') {
            categories = raidCategories;
        } else if (currentType === 'stats') {
            categories = statCategories;
        } else if (currentType === 'professions') {
            categories = professionCategories;
        } else if (currentType === 'guilds') {
            categories = guildCategories;
        }

        for (const key in categories) {
            const option = document.createElement("option");
            option.value = key;
            option.text = categories[key];
            categoryDropdown.appendChild(option);
        }
        categoryDropdown.value = currentCategory;
    }

    window.chooseCategory = function(category) {
        currentCategory = category;
        currentPage = 1;
        updateStatHeader();
        updateLeaderboardTitle();
        updateURL();
        fetchLeaderboardData();
    };

    function updateStatHeader() {
        renderDefaultHeaders();
        statHeader.style.display = 'none';
        levelHeader.style.display = 'none';
        xpHeader.style.display = 'none';
        memberHeader.style.display = 'none';
        createdAtHeader.style.display = 'none';

        if (isRaidAllView()) {
            renderRaidAllHeaders();
        } else if (currentType === 'raids') {
            statHeader.style.display = 'table-cell';
            statHeader.innerText = statHeaders[currentCategory] || 'Value';
        } else if (currentType === 'professions') {
            levelHeader.style.display = 'table-cell';
            xpHeader.style.display = 'table-cell';
            levelHeader.innerText = 'Level';
            xpHeader.innerText = 'XP';
        } else if (currentType === 'guilds') {
            statHeader.style.display = 'table-cell';
            statHeader.innerText = statHeaders[currentCategory];
            memberHeader.style.display = 'table-cell';
            createdAtHeader.style.display = 'table-cell';
        } else {
            statHeader.style.display = 'table-cell';
            statHeader.innerText = statHeaders[currentCategory] || 'Stat';
        }
    }

    function updateLeaderboardTitle() {
        let title = 'Leaderboard';
        if (currentType === 'raids') {
            title = raidCategories[currentCategory] || 'Raids Leaderboard';
        } else if (currentType === 'stats') {
            title = statCategories[currentCategory] || 'Stats Leaderboard';
        } else if (currentType === 'professions') {
            title = professionCategories[currentCategory] || 'Professions Leaderboard';
        } else if (currentType === 'guilds') {
            title = guildCategories[currentCategory] || 'Guilds Leaderboard';
            title = `Guild ${title}`;
        }
        leaderboardTitle.innerText = `${title} Leaderboard`;

        // Let CSS size each leaderboard by what it actually renders. Most
        // single-stat tables should stay compact; guild/profession/wide views
        // need their own column hints.
        leaderboardTable.classList.toggle('wide-mode', isRaidAllView());
        leaderboardTable.classList.toggle('guild-mode', currentType === 'guilds' && !isRaidAllView());
        leaderboardTable.classList.toggle('profession-mode', currentType === 'professions');
    }

    async function fetchLeaderboardData() {
        let endpoint;
        if (isRaidAllView()) {
            endpoint = 'raid_all';
        } else if (currentType === 'raids') {
            // Both per-raid clears (tna/tcc/.../raids_total) and metric ranks
            // (raid_*) are served by the same `/api/leaderboard/raid/{key}`
            // route — the backend reads them from the same `ranking` block.
            endpoint = `raid/${currentCategory}`;
        } else if (currentType === 'professions') {
            endpoint = `profession/${currentCategory}`;
        } else if (currentType === 'guilds') {
            if (['guildLevel', 'guildTerritories', 'guildWars'].includes(currentCategory)) {
                endpoint = `guild/${currentCategory}`;
            } else {
                endpoint = 'database/guild';
            }
        } else {
            endpoint = `stat/${currentCategory}`;
        }

        const url = endpoint.includes('database/guild')
            ? `https://nori.fish/api/${endpoint}`
            : `https://nori.fish/api/leaderboard/${endpoint}`;
        let data = leaderboardPayloadCache.get(endpoint);
        if (!data) {
            leaderboardTable.style.display = 'none';
            noDataMessage.style.display = 'none';
            loadingMessage.style.display = 'block';
        }

        try {
            if (!data) {
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`Leaderboard request failed: ${response.status}`);
                }
                data = await response.json();
                leaderboardPayloadCache.set(endpoint, data);
            }
            console.log("Fetched Data:", data);
            loadingMessage.style.display = 'none';
            if (isRaidAllView()) {
                raidAllPayload = data;
                displayRaidAllLeaderboard();
                displayPagination(getRaidAllRanking().length);
            } else if (currentType === 'guilds' && endpoint.includes('database/guild')) {
                const sortedData = sortData(data, currentCategory);
                displayGuildLeaderboard(sortedData.slice(0, 100));
                displayPagination(100);
            } else {
                displayLeaderboard(data.slice(0, 100));
                displayPagination(100);
            }
        } catch (error) {
            loadingMessage.style.display = 'none';
            noDataMessage.style.display = 'block';
            console.error("Error fetching leaderboard data:", error);
        }
    }

    function renderDefaultHeaders() {
        leaderboardTableHeadRow.innerHTML = `
            <th>Rank</th>
            <th>Name</th>
            <th id="statHeader">Stat</th>
            <th id="levelHeader" style="display:none;">Level</th>
            <th id="xpHeader" style="display:none;">XP</th>
            <th id="memberHeader" style="display:none;">Member</th>
            <th id="createdAtHeader" style="display:none;">Created At</th>
        `;
        statHeader = document.getElementById("statHeader");
        levelHeader = document.getElementById("levelHeader");
        xpHeader = document.getElementById("xpHeader");
        memberHeader = document.getElementById("memberHeader");
        createdAtHeader = document.getElementById("createdAtHeader");
    }

    function renderRaidAllHeaders() {
        const cols = RAID_ALL_COLUMNS.map(col => {
            const cls = col.key === raidAllSortKey ? ' class="bold sortable-column active-sort"' : ' class="sortable-column"';
            const indicator = col.key === raidAllSortKey ? ' ▼' : '';
            return `<th${cls} data-sort-key="${col.key}">${col.label}${indicator}</th>`;
        }).join('');
        leaderboardTableHeadRow.innerHTML = `
            <th>Rank</th>
            <th>Name</th>
            ${cols}
        `;
        leaderboardTableHeadRow.querySelectorAll('[data-sort-key]').forEach(header => {
            header.addEventListener('click', () => {
                raidAllSortKey = header.dataset.sortKey;
                currentPage = 1;
                updateStatHeader();
                updateURL();
                if (raidAllPayload) {
                    displayRaidAllLeaderboard();
                    displayPagination(getRaidAllRanking().length);
                } else {
                    fetchLeaderboardData();
                }
            });
        });
    }

    function sortData(data, category) {
        return Object.entries(data)
            .map(([key, value]) => ({ prefix: key, ...value }))
            .sort((a, b) => b[category] - a[category]);
    }

    function displayLeaderboard(data) {
        leaderboardTableBody.innerHTML = '';
        if (data.length === 0) {
            leaderboardTable.style.display = 'none';
            noDataMessage.style.display = 'block';
            return;
        } else {
            leaderboardTable.style.display = 'table';
            noDataMessage.style.display = 'none';
        }

        const startIndex = (currentPage - 1) * playersPerPage;
        const endIndex = Math.min(startIndex + playersPerPage, data.length);

        for (let i = startIndex; i < endIndex; i++) {
            const item = data[i];
            const row = document.createElement("tr");
            let placeClass = '';
            if (i === 0) placeClass = 'gold';
            else if (i === 1) placeClass = 'silver';
            else if (i === 2) placeClass = 'bronze';
            const valueClass = i < 3 ? 'bold' : '';

            if (currentType === 'professions') {
                const playerName = Object.keys(item)[0];
                const playerData = item[playerName];
                row.innerHTML = `
                    <td class="${placeClass}">${i + 1}</td>
                    <td class="${placeClass}"><img src="https://visage.surgeplay.com/face/256/${Object.keys(item)[0]}" alt="${Object.keys(item)[0]}" width="32" height="32" class="player-icon" onerror="this.src='https://visage.surgeplay.com/face/256/MHF_Steve';this.onerror=null;"> ${Object.keys(item)[0]}</td>
                    <td class="${valueClass}">${playerData.level}</td>
                    <td>${formatLeaderboardValue(playerData.xp, 'xp')}</td>
                `;
            } else if (currentType === 'guilds' && !['guildLevel', 'guildTerritories', 'guildWars'].includes(currentCategory)) {
                row.innerHTML = `
                    <td class="${placeClass}">${i + 1}</td>
                    <td class="${placeClass}"><b>[${item.prefix}]</b> ${item.name}</td>
                    <td class="${valueClass}">${formatLeaderboardValue(item[currentCategory], currentCategory)}</td>
                    <td>${item.members}</td>
                    <td>${item.created_at}</td>
                `;
            } else if (currentType === 'guilds') {
                const guildName = Object.keys(item)[0];
                const guildData = item[guildName];
                const value = currentCategory === 'guildLevel' ? guildData.level
                    : currentCategory === 'guildTerritories' ? guildData.territories
                    : guildData.wars;
                row.innerHTML = `
                    <td class="${placeClass}">${i + 1}</td>
                    <td class="${placeClass}"><b>[${guildData.prefix}]</b> ${guildName}</td>
                    <td class="${valueClass}">${value}</td>
                    <td>${guildData.members}</td>
                    <td>${guildData.created_at}</td>
                `;
            } else {
                const value = Object.values(item)[0];
                row.innerHTML = `
                    <td class="${placeClass}">${i + 1}</td>
                    <td class="${placeClass}"><img src="https://visage.surgeplay.com/face/256/${Object.keys(item)[0]}" alt="${Object.keys(item)[0]}" width="32" height="32" class="player-icon" onerror="this.src='https://visage.surgeplay.com/face/256/MHF_Steve';this.onerror=null;"> ${Object.keys(item)[0]}</td>
                    <td class="${valueClass}">${formatLeaderboardValue(value, currentCategory)}</td>
                `;
            }
            leaderboardTableBody.appendChild(row);
        }
    }

    function formatLeaderboardValue(value, category) {
        if (COMPACT_RAID_CATEGORIES.has(category)) {
            return fmt(value);
        }
        // Stats like playtime, chests, mobs, kills can also be huge — apply
        // compact formatting. Clear counts and small categorical numbers stay
        // as raw integers because their magnitude is meaningful at a glance.
        const STAT_COMPACT = new Set(['chests', 'mobs', 'playtime', 'pvp_kills', 'levels', 'sr']);
        if (STAT_COMPACT.has(category) || category === 'xp') {
            return fmt(value);
        }
        return Number(value || 0).toLocaleString();
    }

    function getRaidAllRanking() {
        if (!raidAllPayload || !Array.isArray(raidAllPayload.ranking)) return [];
        return [...raidAllPayload.ranking].sort((a, b) => {
            const aStats = Object.values(a || {})[0] || {};
            const bStats = Object.values(b || {})[0] || {};
            return Number(bStats[raidAllSortKey] || 0) - Number(aStats[raidAllSortKey] || 0);
        });
    }

    function displayRaidAllLeaderboard() {
        const data = getRaidAllRanking();
        leaderboardTableBody.innerHTML = '';
        if (data.length === 0) {
            leaderboardTable.style.display = 'none';
            noDataMessage.style.display = 'block';
            return;
        }
        leaderboardTable.style.display = 'table';
        noDataMessage.style.display = 'none';

        const startIndex = (currentPage - 1) * playersPerPage;
        const endIndex = Math.min(startIndex + playersPerPage, data.length);
        for (let i = startIndex; i < endIndex; i++) {
            const item = data[i];
            const playerName = Object.keys(item)[0];
            const stats = item[playerName] || {};
            const row = document.createElement("tr");
            let placeClass = '';
            if (i === 0) placeClass = 'gold';
            else if (i === 1) placeClass = 'silver';
            else if (i === 2) placeClass = 'bronze';
            const cells = RAID_ALL_COLUMNS.map(col => {
                const raw = stats[col.key];
                const cellClass = col.key === raidAllSortKey ? 'bold' : '';
                const value = col.compact ? fmt(raw || 0) : Number(raw || 0).toLocaleString();
                return `<td class="${cellClass}">${value}</td>`;
            }).join('');
            row.innerHTML = `
                <td class="${placeClass}">${i + 1}</td>
                <td class="${placeClass}"><img src="https://visage.surgeplay.com/face/256/${playerName}" alt="${playerName}" width="32" height="32" class="player-icon" onerror="this.src='https://visage.surgeplay.com/face/256/MHF_Steve';this.onerror=null;"> ${playerName}</td>
                ${cells}
            `;
            leaderboardTableBody.appendChild(row);
        }
    }

    function displayGuildLeaderboard(data) {
        leaderboardTableBody.innerHTML = '';
        if (data.length === 0) {
            leaderboardTable.style.display = 'none';
            noDataMessage.style.display = 'block';
            return;
        } else {
            leaderboardTable.style.display = 'table';
            noDataMessage.style.display = 'none';
        }

        const startIndex = (currentPage - 1) * playersPerPage;
        const endIndex = Math.min(startIndex + playersPerPage, data.length);

        for (let i = startIndex; i < endIndex; i++) {
            const guildData = data[i];
            const row = document.createElement("tr");
            let placeClass = '';
            if (i === 0) placeClass = 'gold';
            else if (i === 1) placeClass = 'silver';
            else if (i === 2) placeClass = 'bronze';
            const valueClass = i < 3 ? 'bold' : '';

            row.innerHTML = `
                <td>${i + 1}</td>
                <td class="${placeClass}"><b>[${guildData.prefix}]</b> ${guildData.name}</td>
                <td class="${valueClass}">${formatLeaderboardValue(guildData[currentCategory], currentCategory)}</td>
                <td>${guildData.members}</td>
                <td>${guildData.created_at}</td>
            `;
            leaderboardTableBody.appendChild(row);
        }
    }

    function displayPagination(totalPlayers) {
        paginationContainer.innerHTML = '';

        const totalPages = Math.ceil(totalPlayers / playersPerPage);
        const limitedPages = Math.min(totalPages, maxPages);
        if (limitedPages <= 1) return;

        const createButton = (text, page) => {
            const button = document.createElement('button');
            button.innerHTML = text;
            button.disabled = page === currentPage;
            button.addEventListener('click', () => {
                currentPage = page;
                updateURL();
                if (isRaidAllView() && raidAllPayload) {
                    displayRaidAllLeaderboard();
                    displayPagination(getRaidAllRanking().length);
                } else {
                    fetchLeaderboardData();
                }
            });
            return button;
        };

        if (currentPage > 1) {
            paginationContainer.appendChild(createButton('&#x21E4;', 1));
            paginationContainer.appendChild(createButton('&#x2190;', currentPage - 1));
        }

        for (let i = 1; i <= limitedPages; i++) {
            paginationContainer.appendChild(createButton(i, i));
        }

        if (currentPage < limitedPages) {
            paginationContainer.appendChild(createButton('&#x2192;', currentPage + 1));
            paginationContainer.appendChild(createButton('&#x21E5;', limitedPages));
        }
    }

    function getQueryParameter(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    }

    function updateURL() {
        const url = new URL(window.location);
        url.searchParams.set('type', currentType);
        url.searchParams.set('category', currentCategory);
        url.searchParams.set('page', currentPage);
        if (isRaidAllView()) {
            url.searchParams.set('sort', raidAllSortKey);
        } else {
            url.searchParams.delete('sort');
        }
        window.history.pushState({}, '', url);
    }

    // Migrate stale ?type=raid_stats links from the previous deploy.
    if (currentType === 'raid_stats') {
        currentType = 'raids';
        if (!raidCategories[currentCategory]) {
            currentCategory = 'all';
        }
    }
    if (currentType === 'raids' && !currentCategory) {
        currentCategory = 'all';
    }
    if (currentType) {
        displayCategories();
        if (currentCategory) {
            categoryDropdown.value = currentCategory;
            updateStatHeader();
            updateLeaderboardTitle();
            fetchLeaderboardData();
        }
    }

    document.getElementById('typeDropdown').value = currentType;
});
