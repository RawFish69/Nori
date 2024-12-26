let allExpanded = false;

document.addEventListener('DOMContentLoaded', function() {
    fetch('https://nori.fish/api/uptime')
        .then(response => response.json())
        .then(data => {
            const servers = data.servers;
            const playersDataArray = [];
            let maxPlayers = 0;
            let minPlayers = Infinity;
            for (let server in servers) {
                const serverData = servers[server];
                const players = serverData.players;
                maxPlayers = Math.max(maxPlayers, players.length);
                minPlayers = Math.min(minPlayers, players.length);

                const uptime = calculateUptime(serverData.initial);
                playersDataArray.push({server, players, uptime});
            }
            renderPlayersGrid(playersDataArray, minPlayers, maxPlayers);
        })
        .catch(error => console.error('Error fetching data:', error));
});

function calculateUptime(initialTime) {
    const initialDate = new Date(initialTime * 1000);
    const now = new Date();
    const diffMs = now - initialDate;
    const diffHrs = Math.floor(diffMs / 3600000); 
    const diffMins = Math.floor((diffMs % 3600000) / 60000);
    return `${diffHrs}h ${diffMins}m`;
}

function renderPlayersGrid(dataArray, minPlayers, maxPlayers) {
    const playersListContainer = document.querySelector('#playersList');
    playersListContainer.innerHTML = '';

    dataArray.forEach(data => {
        const serverDiv = document.createElement('div');
        serverDiv.className = 'server';
        const serverHeader = document.createElement('div');
        serverHeader.className = 'server-header';
        serverHeader.textContent = `${data.server} (${data.players.length} players)`;
        const color = getColorGradient(data.players.length);
        serverHeader.style.background = color;
        serverHeader.addEventListener('mouseover', (e) => {
            showTooltip(e, `Uptime: ${data.uptime}`);
        });
        serverHeader.addEventListener('mouseout', hideTooltip);
        serverHeader.addEventListener('click', () => {
            serverBody.classList.toggle('collapsed');
        });
        const serverBody = document.createElement('div');
        serverBody.className = 'server-body collapsed';
        const playersList = document.createElement('ul');
        data.players.forEach(player => {
            const playerItem = document.createElement('li');
            playerItem.textContent = player;
            playersList.appendChild(playerItem);
        });
        serverBody.appendChild(playersList);
        serverDiv.appendChild(serverHeader);
        serverDiv.appendChild(serverBody);
        playersListContainer.appendChild(serverDiv);
    });
}

function getColorGradient(playerCount) {
    let r, g, b;
    if (playerCount < 10) {
        r = 0;
        g = 225;
        b = 0;
    } else if (playerCount < 20) {
        r = 0;
        g = 150;
        b = 0;
    } else if (playerCount < 30) {
        r = 200;
        g = 200;
        b = 0;
    } else if (playerCount < 40) {
        r = 255;
        g = 150;
        b = 0;
    } else if (playerCount < 45) {
        r = 255;
        g = 0;
        b = 0;
    } else {
        r = 139;
        g = 0;
        b = 0;
    }
    return `rgb(${r},${g},${b})`;
}


function showTooltip(event, text) {
    let tooltip = document.querySelector('.tooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        document.body.appendChild(tooltip);
    }
    tooltip.textContent = text;
    tooltip.style.left = `${event.pageX + 10}px`;
    tooltip.style.top = `${event.pageY + 10}px`;
    tooltip.style.display = 'block';
}

function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.style.display = 'none';
    }
}

function toggleAllServers() {
    const serverBodies = document.querySelectorAll('.server-body');
    const toggleAllButton = document.getElementById('toggleAllButton');

    serverBodies.forEach(serverBody => {
        if (allExpanded) {
            serverBody.classList.add('collapsed');
        } else {
            serverBody.classList.remove('collapsed');
        }
    });
    if (allExpanded) {
        toggleAllButton.textContent = 'Expand All';
    } else {
        toggleAllButton.textContent = 'Collapse All';
    }
    allExpanded = !allExpanded;
}