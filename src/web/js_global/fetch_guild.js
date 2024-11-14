let guildData = null;
let membersArray = [];
let sortAscending = true;
let currentSortKey = 'contributed'; 
let isMembersVisible = false;

document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const guildName = params.get('guild');
    if (guildName) {
        document.getElementById('guild-name').value = guildName;
        fetchGuildData(guildName);
    }
});

document.getElementById('guild-search-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const guildName = document.getElementById('guild-name').value;
    if (guildName.trim() === '') {
        alert('Please enter a guild name or prefix');
        return;
    }
    fetchGuildData(guildName);
});

async function fetchGuildData(guildName) {
    displayLoadingMessage("Loading guild stats...");
    try {
        const response = await fetch(`https://nori.fish/api/guild/${guildName}`);
        if (!response.ok) {
            throw new Error('Guild not found');
        }
        guildData = await response.json();
        membersArray = [];
        Object.keys(guildData.members).forEach(rank => {
            if (rank !== 'total') {
                Object.keys(guildData.members[rank]).forEach(memberName => {
                    const member = guildData.members[rank][memberName];
                    membersArray.push({
                        name: memberName,
                        uuid: member.uuid,
                        rank: rank,
                        contributed: member.contributed,
                        joined: new Date(member.joined),
                        online: member.online,
                        server: member.server
                    });
                });
            }
        });
        displayGuildData(guildData);
        updateURL(guildName);
    } catch (error) {
        displayErrorMessage(`Cannot fetch guild ${guildName}`);
    }
}

function updateURL(guildName) {
    const url = new URL(window.location);
    url.searchParams.set('guild', guildName);
    window.history.pushState({}, '', url);
}

const rankSymbols = {
    "owner": "★★★★★",
    "chief": "★★★★",
    "strategist": "★★★",
    "captain": "★★",
    "recruiter": "★",
    "recruit": ""
};

function displayGuildData(guildData) {
    const resultsContainer = document.getElementById('guild-results');
    const onlinePlayers = membersArray.filter(member => member.online);

    const onlinePlayersHTML = onlinePlayers.map(player => `
        <li>
            <span class="server-name">[${player.server}]</span>
            <img src="https://visage.surgeplay.com/face/256/${player.uuid}" alt="${player.name}" class="player-icon">
            <span class="player-info">
                <span class="player-name">${player.name}</span> ${rankSymbols[player.rank]}
            </span>
        </li>
    `).join('');

    resultsContainer.innerHTML = `
        <div class="guild-card">
            <div class="guild-info">
                <h3>${guildData.name} [${guildData.prefix}]</h3>
                <p>Owner: ${guildData.owner}</p>
                <p>Created on: ${new Date(guildData.created_date).toLocaleDateString()}</p>
                <p>Level: ${guildData.level} (${guildData.xp_percent}%)</p>
                <p>War count: ${guildData.wars}</p>
                <p>Territory count: ${guildData.territories}</p>
                <p>Members: ${guildData.total_members}</p>
                <p>Online Players: ${onlinePlayers.length}</p>
            </div>
            <div class="online-players">
                ${onlinePlayersHTML.length ? '<h4>Online Players:</h4><ul>' + onlinePlayersHTML + '</ul>' : '<p>No online players</p>'}
            </div>
            <div class="buttons-container">
                <button onclick="toggleMembers()">All Members</button>
                <button onclick="toggleSeasons()">Previous Season Ranks</button>
            </div>
        </div>
        <div id="members-container" class="hidden"></div>
        <div id="seasons-container" class="hidden"></div>
    `;
}

function displayErrorMessage(message) {
    const resultsContainer = document.getElementById('guild-results');
    resultsContainer.innerHTML = `<p class="centered-text error-message">${message}</p>`;
}

function displayLoadingMessage(message) {
    const resultsContainer = document.getElementById('guild-results');
    resultsContainer.innerHTML = `<p class="centered-text loading-message">${message}</p>`;
}

function toggleMembers() {
    const membersContainer = document.getElementById('members-container');
    isMembersVisible = !isMembersVisible;
    if (isMembersVisible) {
        if (membersArray.length > 0) {
            renderMembers();
            membersContainer.classList.remove('hidden');
        } else {
            membersContainer.innerHTML = '<p class="no-results">No members data available</p>';
        }
    } else {
        membersContainer.classList.add('hidden');
        membersContainer.innerHTML = '';
    }
}

function renderMembers() {
    const membersContainer = document.getElementById('members-container');
    let memberList = `
        <table class="members-table">
            <thead>
                <tr>
                    <th onclick="sortMembers('name')">Player ${getSortArrow('name')}</th>
                    <th>Rank</th>
                    <th onclick="sortMembers('contributed')">Contributed XP ${getSortArrow('contributed')}</th>
                    <th onclick="sortMembers('joined', true)">Joined Date ${getSortArrow('joined')}</th>
                </tr>
            </thead>
            <tbody>`;
    membersArray.forEach(member => {
        memberList += `
            <tr>
                <td data-label="Player"><img src="https://visage.surgeplay.com/face/256/${member.uuid}" alt="${member.name}" class="player-icon">${member.name}</td>
                <td data-label="Rank">${rankSymbols[member.rank]}</td>
                <td data-label="Contributed XP">${member.contributed}</td>
                <td data-label="Joined Date">${member.joined.toLocaleDateString()}</td>
            </tr>`;
    });
    memberList += `</tbody></table>`;
    membersContainer.innerHTML = `<div class="members-card">${memberList}</div>`;
}

function toggleSeasons() {
    const seasonsContainer = document.getElementById('seasons-container');
    if (seasonsContainer.classList.contains('hidden')) {
        if (guildData && guildData.seasonRanks) {
            const seasons = guildData.seasonRanks;
            let seasonList = `
                <table class="seasons-table">
                    <thead>
                        <tr>
                            <th>Season</th>
                            <th>SR</th>
                            <th>Final Territories</th>
                        </tr>
                    </thead>
                    <tbody>`;
            Object.keys(seasons).forEach(season => {
                const seasonData = seasons[season];
                seasonList += `
                    <tr>
                        <td>Season ${season}</td>
                        <td>${seasonData.rating}</td>
                        <td>${seasonData.finalTerritories}</td>
                    </tr>`;
            });
            seasonList += `</tbody></table>`;
            seasonsContainer.innerHTML = `<div class="seasons-card">${seasonList}</div>`;
            seasonsContainer.classList.remove('hidden');
        } else {
            seasonsContainer.innerHTML = '<p class="no-results">No season ranks data available</p>';
        }
    } else {
        seasonsContainer.classList.add('hidden');
        seasonsContainer.innerHTML = '';
    }
}

function sortMembers(key, isDate = false) {
    if (currentSortKey === key) {
        sortAscending = !sortAscending;
    } else {
        currentSortKey = key;
        sortAscending = true;
    }
    
    membersArray.sort((a, b) => {
        if (isDate) {
            return sortAscending ? a[key] - b[key] : b[key] - a[key];
        } else if (key === 'contributed') {
            return sortAscending ? a[key] - b[key] : b[key] - a[key];
        } else {
            return sortAscending ? a[key].localeCompare(b[key]) : b[key].localeCompare(a[key]);
        }
    });
    
    renderMembers();
}

function getSortArrow(key) {
    if (currentSortKey !== key) return '';
    return sortAscending ? '↑' : '↓';
}
