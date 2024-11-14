document.addEventListener('DOMContentLoaded', function() {
    fetch('https://nori.fish/api/uptime')
        .then(response => response.json())
        .then(data => {
            const servers = data.servers;
            const serverDataArray = [];

            for (let server in servers) {
                const serverData = servers[server];
                const initialTime = serverData.initial;
                const now = Math.floor(Date.now() / 1000);
                const uptimeSeconds = now - initialTime;
                const playersCount = serverData.players.length;

                const soulPoint = 1200 - (uptimeSeconds % 1200);

                serverDataArray.push({server, playersCount, initialTime, uptimeSeconds, soulPoint});
            }

            // type shit
            serverDataArray.sort((a, b) => a.uptimeSeconds - b.uptimeSeconds);
            renderTable(serverDataArray);

            const uptimeHeader = document.querySelector('th[onclick="sortTable(\'uptime\')"]');
            uptimeHeader.setAttribute('data-sort', 'asc');
            uptimeHeader.innerHTML = `${uptimeHeader.textContent.trim()} &#9650;`;

            window.sortTable = function (criteria) {
                const th = document.querySelector(`th[onclick="sortTable('${criteria}')"]`);
                const currentSortOrder = th.getAttribute('data-sort');
                const newSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';

                let sortedData;

                if (criteria === 'uptime') {
                    sortedData = serverDataArray.sort((a, b) => {
                        return newSortOrder === 'asc' ? a.uptimeSeconds - b.uptimeSeconds : b.uptimeSeconds - a.uptimeSeconds;
                    });
                } else if (criteria === 'soulTimer') {
                    sortedData = serverDataArray.sort((a, b) => {
                        return newSortOrder === 'asc' ? a.soulPoint - b.soulPoint : b.soulPoint - a.soulPoint;
                    });
                } else if (criteria === 'playersCount') {
                    sortedData = serverDataArray.sort((a, b) => {
                        return newSortOrder === 'asc' ? a.playersCount - b.playersCount : b.playersCount - a.playersCount;
                    });
                } else if (criteria === 'server') {
                    sortedData = serverDataArray.sort((a, b) => {
                        return newSortOrder === 'asc' ? a.server.localeCompare(b.server) : b.server.localeCompare(a.server);
                    });
                }

                document.querySelectorAll('th').forEach(header => {
                    header.innerHTML = header.innerHTML.replace(/ ▲| ▼/g, '');
                });

                th.setAttribute('data-sort', newSortOrder);
                th.innerHTML = `${th.textContent.trim()} ${newSortOrder === 'asc' ? '&#9650;' : '&#9660;'}`;

                renderTable(sortedData);
            }

            // Update timers every second
            setInterval(() => {
                serverDataArray.forEach(server => {
                    server.uptimeSeconds++;
                    server.soulPoint = 1200 - (server.uptimeSeconds % 1200);
                });
                renderTable(serverDataArray);
            }, 1000);
        })
        .catch(error => console.error('Error fetching data:', error));
});

function renderTable(dataArray) {
    const tableBody = document.querySelector('#uptimeTable tbody');
    tableBody.innerHTML = '';
    dataArray.forEach(data => {
        const uptime = new Date(data.uptimeSeconds * 1000).toISOString().substr(11, 8);
        const minutes = Math.floor(data.soulPoint / 60);
        const seconds = data.soulPoint % 60;
        const soulTimer = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${data.server}</td>
            <td>${data.playersCount}</td>
            <td>${uptime}</td>
            <td>${soulTimer}</td>
        `;
        tableBody.appendChild(row);
    });
}

