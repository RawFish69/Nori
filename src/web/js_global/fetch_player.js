const rankMap = {
    "vip": "VIP",
    "vipplus": "VIP+",
    "hero": "Hero",
    "champion": "Champion",
};

const rankColorMap = {
    "VIP": "green",
    "VIP+": "cyan",
    "Hero": "purple",
    "Champion": "gold",
    "Mod": "orange",
    "Admin": "maroon"
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
    const firstJoined = new Date(playerData.firstJoin).toLocaleString();
    const lastJoined = new Date(playerData.lastJoin).toLocaleString();
    const guildInfo = playerData.guild ? `Guild: [${playerData.guild.prefix}] ${playerData.guild.name} | ${playerData.guild.rank}` : 'Guild: N/A';

    const raidList = playerData.globalData.raids.list;
    const dungeonTotal = playerData.globalData.dungeons.total;
    const raidTotal = playerData.globalData.raids.total;

    const raidTable = createRaidTable(raidList, dungeonTotal, raidTotal);

    const playerCardHTML = `
        <div class="player-card">
            <div class="player-info">
                <h3>${playerData.username}</h3>
                <p class="${onlineClass}"><span style="color: ${rankColor};">[${gameRank}]</span> ${playerData.username} is ${onlineStatus}</p>
                <p>${guildInfo}</p>
                <p>First Joined: ${firstJoined}</p>
                <p>Last Seen: ${lastJoined}</p>
                <p>Mobs Killed: <span class="stat-positive">${playerData.globalData.mobsKilled}</span></p>
                <p>Chests Opened: <span class="stat-positive">${playerData.globalData.chestsFound}</span></p>
                <p>Playtime: <span class="stat-neutral">${playerData.playtime} hours</span></p>
                <p>War Count: <span class="stat-positive">${playerData.globalData.wars}</span></p>
                <p>PvP: <span class="stat-positive">${playerData.globalData.pvp.kills}</span> K / <span class="stat-negative">${playerData.globalData.pvp.deaths}</span> D [<span class="stat-neutral">${calculateKD(playerData.globalData.pvp.kills, playerData.globalData.pvp.deaths)}</span>]</p>
                <p>Quests Total: <span class="stat-positive">${playerData.globalData.completedQuests}</span></p>
                <p>Total Level: <span class="stat-positive">${playerData.globalData.totalLevel}</span></p>
                ${raidTable}
            </div>
            <div class="player-icon">
                <img src="https://visage.surgeplay.com/player/512/${playerData.uuid}" alt="${playerData.username}">
            </div>
        </div>
        <div class="buttons-container">
            ${Object.entries(playerData.characters).map(([id, character]) => {
                const charName = character.nickname ? `Lv. ${character.level} ${character.nickname}` : `Lv. ${character.level} ${character.type}`;
                const buttonClass = character.nickname ? 'character-button-cyan' : 'character-button-green';
                return `<button class="character-button ${buttonClass}" data-character-id="${id}">${charName}</button>`;
            }).join('')}
        </div>
        <button class="back-button" onclick="resetToGlobalView()">All classes</button>
        <div id="character-cards-container"></div>
    `;
    resultsContainer.innerHTML = playerCardHTML;
    window.globalPlayerData = playerData;
    document.querySelectorAll('.character-button').forEach(button => {
        button.addEventListener('click', () => {
            const id = button.getAttribute('data-character-id');
            displayCharacterData(playerData.characters[id], playerData.uuid, playerData.username);
        });
    });
}

function displayCharacterData(characterData, playerUuid, playerName) {
    const playerCard = document.querySelector('.player-card');
    const raidTable = createRaidTable(characterData.raids ? characterData.raids.list : {}, characterData.dungeons ? characterData.dungeons.total : 0, characterData.raids ? characterData.raids.total : 0);

    playerCard.innerHTML = `
        <div class="player-info">
            <p>Class: ${characterData.type}</p>
            <p>Total Level: <span class="stat-positive">${characterData.totalLevel}</span></p>
            <p>Wars: <span class="stat-positive">${characterData.wars}</span></p>
            <p>Playtime: <span class="stat-neutral">${characterData.playtime} hours</span></p>
            <p>Mobs Killed: <span class="stat-positive">${characterData.mobsKilled}</span></p>
            <p>Chests Found: <span class="stat-positive">${characterData.chestsFound}</span></p>
            <p>Blocks Walked: <span class="stat-neutral">${characterData.blocksWalked}</span></p>
            <p>Logins: <span class="stat-positive">${characterData.logins}</span></p>
            <p>Deaths: <span class="stat-negative">${characterData.deaths}</span></p>
            <p>Discoveries: <span class="stat-positive">${characterData.discoveries}</span></p>
            <p>PvP: <span class="stat-positive">${characterData.pvp.kills}</span> K / <span class="stat-negative">${characterData.pvp.deaths}</span> D</p>
            ${raidTable}
        </div>
        <div class="player-icon">
            <img src="https://visage.surgeplay.com/player/512/${playerUuid}" alt="${playerName}">
        </div>
    `;
}

function displayErrorMessage(message) {
    const resultsContainer = document.getElementById('player-results');
    resultsContainer.innerHTML = `<p class="centered-text error-message">${message}</p>`;
}

function displayLoadingMessage(message) {
    const resultsContainer = document.getElementById('player-results');
    resultsContainer.innerHTML = `<p class="centered-text loading-message">${message}</p>`;
}

function createRaidTable(raidList, dungeonTotal, raidTotal) {
    return `
        <div class="table-container content-table">
            <table>
                <thead>
                    <tr>
                        <th>Content</th>
                        <th>Clears</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.entries(raidList).map(([raidName, clears]) => `
                        <tr>
                            <td>${raidName}</td>
                            <td><span class="stat-bold">${clears}</span></td>
                        </tr>
                    `).join('')}
                    <tr>
                        <td>Dungeons</td>
                        <td><span class="stat-bold">${dungeonTotal}</span></td>
                    </tr>
                    <tr>
                        <td>All Raids</td>
                        <td><span class="stat-bold">${raidTotal}</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
}

function calculateKD(kills, deaths) {
    if (kills === 0 || deaths === 0) {
        return 0;
    }
    return (kills / deaths).toFixed(2);
}

function updateURL(playerName) {
    const url = new URL(window.location);
    url.searchParams.set('player', playerName);
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

    const initialPlayerName = getQueryParameter('player');
    if (initialPlayerName) {
        document.getElementById("player-name").value = initialPlayerName;
        displayLoadingMessage("Loading player stats...");
        fetchPlayerData(initialPlayerName);
    }
});
