let allExpanded = false;
let latestPlayersData = [];
let latestPlayerIndex = new Map();

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('online-player-form');
    if (form) {
        form.addEventListener('submit', handleOnlinePlayerSearch);
    }

    loadOnlinePlayers();
});

async function loadOnlinePlayers() {
    setStatusMessage('Loading online worlds...');
    try {
        const response = await fetch('https://nori.fish/api/uptime');
        if (!response.ok) {
            throw new Error(`Uptime request failed with ${response.status}`);
        }

        const data = await response.json();
        latestPlayersData = normalizeServers(data.servers || {});
        latestPlayerIndex = buildPlayerIndex(latestPlayersData);
        renderSummary(latestPlayersData);
        renderPlayersGrid(latestPlayersData);
        setStatusMessage('');
        runLookupFromUrl();
    } catch (error) {
        console.error('Error fetching online players:', error);
        renderSummary([]);
        renderPlayersGrid([]);
        setStatusMessage('Could not load online players right now. Please try again in a bit.', true);
    }
}

function normalizeServers(servers) {
    return Object.entries(servers)
        .map(([server, serverData]) => ({
            server,
            players: Array.isArray(serverData.players) ? serverData.players.slice().sort((a, b) => a.localeCompare(b)) : [],
            uptime: calculateUptime(serverData.initial),
        }))
        .sort((a, b) => compareServerNames(a.server, b.server));
}

function compareServerNames(a, b) {
    const aNumber = Number((a.match(/\d+/) || [Number.MAX_SAFE_INTEGER])[0]);
    const bNumber = Number((b.match(/\d+/) || [Number.MAX_SAFE_INTEGER])[0]);
    if (aNumber !== bNumber) return aNumber - bNumber;
    return a.localeCompare(b);
}

function buildPlayerIndex(dataArray) {
    const index = new Map();
    dataArray.forEach(({ server, players }) => {
        players.forEach(player => {
            index.set(player.toLowerCase(), { name: player, server });
        });
    });
    return index;
}

function calculateUptime(initialTime) {
    if (!initialTime) return 'Unknown';
    const initialDate = new Date(initialTime * 1000);
    const now = new Date();
    const diffMs = Math.max(0, now - initialDate);
    const diffHrs = Math.floor(diffMs / 3600000);
    const diffMins = Math.floor((diffMs % 3600000) / 60000);
    return `${diffHrs}h ${diffMins}m`;
}

function renderSummary(dataArray) {
    const summary = document.getElementById('online-summary');
    if (!summary) return;

    const totalPlayers = dataArray.reduce((sum, data) => sum + data.players.length, 0);
    const busiest = dataArray.reduce((best, data) => {
        if (!best || data.players.length > best.players.length) return data;
        return best;
    }, null);

    const tiles = [
        { label: 'Online Players', value: totalPlayers.toLocaleString() },
        { label: 'Active Worlds', value: dataArray.length.toLocaleString() },
        { label: 'Busiest World', value: busiest ? `${busiest.server} (${busiest.players.length})` : 'None' },
    ];

    summary.innerHTML = '';
    tiles.forEach(tile => {
        const tileElement = document.createElement('div');
        tileElement.className = 'summary-tile';

        const label = document.createElement('div');
        label.className = 'summary-label';
        label.textContent = tile.label;

        const value = document.createElement('div');
        value.className = 'summary-value';
        value.textContent = tile.value;

        tileElement.appendChild(label);
        tileElement.appendChild(value);
        summary.appendChild(tileElement);
    });
}

function renderPlayersGrid(dataArray) {
    const playersListContainer = document.querySelector('#playersList');
    if (!playersListContainer) return;

    playersListContainer.innerHTML = '';
    dataArray.forEach(data => {
        const serverDiv = document.createElement('article');
        serverDiv.className = `server ${getLoadClass(data.players.length)}`;

        const serverHeader = document.createElement('button');
        serverHeader.type = 'button';
        serverHeader.className = 'server-header';
        serverHeader.setAttribute('aria-expanded', 'false');

        const title = document.createElement('span');
        title.className = 'server-title';

        const serverName = document.createElement('span');
        serverName.className = 'server-name';
        serverName.textContent = data.server;

        const uptime = document.createElement('span');
        uptime.className = 'server-uptime';
        uptime.textContent = `Uptime ${data.uptime}`;

        title.appendChild(serverName);
        title.appendChild(uptime);

        const count = document.createElement('span');
        count.className = 'server-count';
        count.textContent = `${data.players.length} players`;

        serverHeader.appendChild(title);
        serverHeader.appendChild(count);

        const serverBody = document.createElement('div');
        serverBody.className = 'server-body collapsed';

        if (data.players.length) {
            const playersList = document.createElement('ul');
            data.players.forEach(player => {
                const playerItem = document.createElement('li');
                playerItem.textContent = player;
                playersList.appendChild(playerItem);
            });
            serverBody.appendChild(playersList);
        } else {
            const empty = document.createElement('p');
            empty.className = 'empty-server';
            empty.textContent = 'No players listed for this world.';
            serverBody.appendChild(empty);
        }

        serverHeader.addEventListener('click', () => {
            const isCollapsed = serverBody.classList.toggle('collapsed');
            serverHeader.setAttribute('aria-expanded', String(!isCollapsed));
        });

        serverDiv.appendChild(serverHeader);
        serverDiv.appendChild(serverBody);
        playersListContainer.appendChild(serverDiv);
    });
}

function getLoadClass(playerCount) {
    if (playerCount < 10) return 'server-low';
    if (playerCount < 25) return 'server-medium';
    if (playerCount < 40) return 'server-high';
    return 'server-full';
}

function handleOnlinePlayerSearch(event) {
    event.preventDefault();
    const input = document.getElementById('online-player-name');
    const playerName = input ? input.value.trim() : '';
    updatePlayerQuery(playerName);
    renderLookup(playerName);
}

function runLookupFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const playerName = params.get('player');
    if (!playerName) return;

    const input = document.getElementById('online-player-name');
    if (input) {
        input.value = playerName;
    }
    renderLookup(playerName);
}

function renderLookup(playerName) {
    const result = document.getElementById('online-player-result');
    if (!result) return;

    result.innerHTML = '';
    if (!playerName) {
        result.appendChild(createLookupCard('Check a player', 'Enter a player name to see if they are currently listed online.', 'offline'));
        return;
    }

    const match = latestPlayerIndex.get(playerName.toLowerCase());
    if (match) {
        const detail = document.createElement('p');
        detail.className = 'lookup-detail';
        detail.append('Found on ', createStrong(match.server), '. ');

        const link = document.createElement('a');
        link.href = `/wynn/player/?name=${encodeURIComponent(match.name)}`;
        link.textContent = 'Open player stats';
        detail.appendChild(link);

        result.appendChild(createLookupCard(`${match.name} is online`, detail, 'online'));
        return;
    }

    result.appendChild(createLookupCard(`${playerName} is not currently online`, 'The uptime feed can lag slightly, so refresh if this changed in-game very recently.', 'offline'));
}

function createLookupCard(title, detail, state) {
    const card = document.createElement('div');
    card.className = `lookup-card ${state}`;

    const kicker = document.createElement('p');
    kicker.className = 'lookup-kicker';
    kicker.textContent = state === 'online' ? 'Online now' : 'Player lookup';

    const heading = document.createElement('h3');
    heading.className = 'lookup-title';
    heading.textContent = title;

    card.appendChild(kicker);
    card.appendChild(heading);

    if (typeof detail === 'string') {
        const detailElement = document.createElement('p');
        detailElement.className = 'lookup-detail';
        detailElement.textContent = detail;
        card.appendChild(detailElement);
    } else {
        card.appendChild(detail);
    }

    return card;
}

function createStrong(text) {
    const strong = document.createElement('strong');
    strong.textContent = text;
    return strong;
}

function updatePlayerQuery(playerName) {
    const url = new URL(window.location);
    if (playerName) {
        url.searchParams.set('player', playerName);
    } else {
        url.searchParams.delete('player');
    }
    window.history.replaceState({}, '', url);
}

function setStatusMessage(message, isError = false) {
    const status = document.getElementById('online-status-message');
    if (!status) return;

    status.textContent = message;
    status.classList.toggle('error', isError);
}

function toggleAllServers() {
    const serverBodies = document.querySelectorAll('.server-body');
    const serverHeaders = document.querySelectorAll('.server-header');
    const toggleAllButton = document.getElementById('toggleAllButton');

    serverBodies.forEach(serverBody => {
        serverBody.classList.toggle('collapsed', allExpanded);
    });
    serverHeaders.forEach(serverHeader => {
        serverHeader.setAttribute('aria-expanded', String(!allExpanded));
    });

    allExpanded = !allExpanded;
    if (toggleAllButton) {
        toggleAllButton.textContent = allExpanded ? 'Collapse All' : 'Expand All';
    }
}
