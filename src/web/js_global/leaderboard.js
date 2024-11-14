document.addEventListener("DOMContentLoaded", () => {
    const categoryDropdown = document.getElementById("categoryDropdown");
    const leaderboardTable = document.getElementById("leaderboardTable");
    const leaderboardTableBody = leaderboardTable.querySelector("tbody");
    const paginationContainer = document.getElementById("pagination");
    const statHeader = document.getElementById("statHeader");
    const levelHeader = document.getElementById("levelHeader");
    const xpHeader = document.getElementById("xpHeader");
    const memberHeader = document.getElementById("memberHeader");
    const createdAtHeader = document.getElementById("createdAtHeader");
    const noDataMessage = document.getElementById("noDataMessage");
    const leaderboardTitle = document.querySelector("#Leaderboard h2");

    let currentType = getQueryParameter('type') || '';
    let currentCategory = getQueryParameter('category') || '';
    let currentPage = getQueryParameter('page') ? parseInt(getQueryParameter('page')) : 1;
    const playersPerPage = 10;
    const maxPages = 10;

    const raidCategories = {
        'raids_total': 'All Raids',
        'tna': 'The Nameless Anomaly (TNA)',
        'tcc': 'The Canyon Colossus (TCC)',
        'nol': 'Nexus of Light (NOL)',
        'nog': 'Nest of Grootslangs (NOG)'
    };

    const statCategories = {
        'chests': 'Chests Opened',
        'mobs': 'Mobs Killed',
        'wars': 'Wars Joined',
        'dungeons': 'Dungeon Completed',
        'playtime': 'Playtime',
        'pvp_kills': 'PvP Kills',
        'quests': 'Quests Completed',
        'levels': 'Total Levels'
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
        'dungeons': 'Runs',
        'playtime': 'Hours',
        'quests': 'Quests',
        'levels': 'Level',
        "sr": "SR",
        'guildTerritories': 'Territories',
        'guildWars': 'Wars',
        'guildLevel': 'Level',
    };

    window.chooseType = function(type) {
        currentType = type;
        displayCategories();
        updateURL();
    };

    function displayCategories() {
        categoryDropdown.style.display = 'inline-block';
        categoryDropdown.innerHTML = '<option value="">Select Category</option>';

        let categories;
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
        statHeader.style.display = 'none';
        levelHeader.style.display = 'none';
        xpHeader.style.display = 'none';
        memberHeader.style.display = 'none';
        createdAtHeader.style.display = 'none';

        if (currentType === 'raids') {
            statHeader.style.display = 'table-cell';
            statHeader.innerText = 'Clears';
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
            title = `Guild ${title}`
        }
        leaderboardTitle.innerText = `${title} Leaderboard`;
    }

    async function fetchLeaderboardData() {
        let endpoint;
        if (currentType === 'raids') {
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

        try {
            const url = endpoint.includes('database/guild')
                ? `https://nori.fish/api/${endpoint}`
                : `https://nori.fish/api/leaderboard/${endpoint}`;
            const response = await fetch(url);
            const data = await response.json();
            console.log("Fetched Data:", data);
            if (currentType === 'guilds' && endpoint.includes('database/guild')) {
                const sortedData = sortData(data, currentCategory);
                displayGuildLeaderboard(sortedData.slice(0, 100));
                displayPagination(100);
            } else {
                displayLeaderboard(data.slice(0, 100)); 
                displayPagination(100); 
            }
        } catch (error) {
            console.error("Error fetching leaderboard data:", error);
        }
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
                    <td class="${placeClass}"><img src="https://visage.surgeplay.com/face/256/${Object.keys(item)[0]}" alt="${Object.keys(item)[0]}" class="player-icon"> ${Object.keys(item)[0]}</td>
                    <td class="${valueClass}">${playerData.level}</td>
                    <td>${playerData.xp}</td>
                `;
            } else if (currentType === 'guilds' && !['guildLevel', 'guildTerritories', 'guildWars'].includes(currentCategory)) {
                row.innerHTML = `
                    <td class="${placeClass}">${i + 1}</td>
                    <td class="${placeClass}"><b>[${item.prefix}]</b> ${item.name}</td>
                    <td class="${valueClass}">${item[currentCategory]}</td>
                    <td>${item.members}</td>
                    <td>${item.created_at}</td>
                `;
            } else if (currentType === 'guilds') {
                const guildName = Object.keys(item)[0];
                const guildData = item[guildName];
                row.innerHTML = `
                    <td class="${placeClass}">${i + 1}</td>
                    <td class="${placeClass}"><b>[${guildData.prefix}]</b> ${guildName}</td>
                    <td class="${valueClass}">${currentCategory === 'guildLevel' ? guildData.level : currentCategory === 'guildTerritories' ? guildData.territories : guildData.wars}</td>
                    <td>${guildData.members}</td>
                    <td>${guildData.created_at}</td>
                `;
            } else {
                row.innerHTML = `
                    <td class="${placeClass}">${i + 1}</td>
                    <td class="${placeClass}"><img src="https://visage.surgeplay.com/face/256/${Object.keys(item)[0]}" alt="${Object.keys(item)[0]}" class="player-icon"> ${Object.keys(item)[0]}</td>
                    <td class="${valueClass}">${Object.values(item)[0]}</td>
                `;
            }
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
                <td class="${valueClass}">${guildData[currentCategory]}</td>
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
                fetchLeaderboardData();
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
        window.history.pushState({}, '', url);
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
});
