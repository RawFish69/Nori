let guildData = null;
let membersArray = [];
let sortAscending = true;
let currentSortKey = 'contributed';
let isMembersVisible = false;

const rankSymbols = {
    owner: '★★★★★',
    chief: '★★★★',
    strategist: '★★★',
    captain: '★★',
    recruiter: '★',
    recruit: '',
};

document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const guildName = params.get('guild');
    const form = document.getElementById('guild-search-form');

    if (guildName) {
        document.getElementById('guild-name').value = guildName;
        fetchGuildData(guildName);
    }

    if (form) {
        form.addEventListener('submit', (event) => {
            event.preventDefault();
            const input = document.getElementById('guild-name');
            const searchedGuild = input ? input.value.trim() : '';
            if (!searchedGuild) {
                displayErrorMessage('Please enter a guild name or prefix');
                return;
            }
            fetchGuildData(searchedGuild);
        });
    }
});

async function fetchGuildData(guildName) {
    displayLoadingMessage('Loading guild stats...');
    try {
        const response = await fetch(`https://nori.fish/api/guild/${encodeURIComponent(guildName)}`);
        if (!response.ok) {
            throw new Error('Guild not found');
        }
        guildData = await response.json();
        membersArray = buildMembersArray(guildData.members || {});
        isMembersVisible = false;
        displayGuildData(guildData);
        updateURL(guildName);
    } catch (error) {
        console.error('Error fetching guild:', error);
        displayErrorMessage(`Cannot fetch guild ${guildName}`);
    }
}

function buildMembersArray(members) {
    const normalized = [];
    Object.keys(members).forEach(rank => {
        if (rank === 'total') return;
        Object.keys(members[rank] || {}).forEach(memberName => {
            const member = members[rank][memberName];
            normalized.push({
                name: memberName,
                uuid: member.uuid,
                rank,
                contributed: Number(member.contributed || 0),
                joined: new Date(member.joined),
                online: Boolean(member.online),
                server: member.server || '',
            });
        });
    });
    return normalized;
}

function updateURL(guildName) {
    const url = new URL(window.location);
    url.searchParams.set('guild', guildName);
    window.history.pushState({}, '', url);
}

function displayGuildData(data) {
    const resultsContainer = document.getElementById('guild-results');
    const onlinePlayers = membersArray.filter(member => member.online);

    resultsContainer.innerHTML = `
        <div class="guild-card">
            ${renderGuildHero(data, onlinePlayers)}
            ${renderGuildStatsGrid(data, onlinePlayers)}
            <div class="panel-row">
                ${renderOnlinePlayersPanel(onlinePlayers)}
                ${renderGuildActions()}
            </div>
            <div id="members-container" class="hidden"></div>
            <div id="seasons-container" class="hidden"></div>
        </div>
    `;
}

function renderGuildHero(data, onlinePlayers) {
    const xpPercent = clampPercent(data.xp_percent);
    return `
        <section class="guild-hero">
            <div class="guild-crest" aria-hidden="true">
                <div class="guild-prefix">[${escapeHtml(data.prefix || '?')}]</div>
                <div class="guild-crest-label">Guild</div>
            </div>
            <div class="guild-identity">
                <h3 class="guild-name">${escapeHtml(data.name || 'Unknown Guild')}</h3>
                <div class="guild-meta">
                    <div class="guild-meta-row">
                        <span>Owner: <strong>${escapeHtml(data.owner || 'Unknown')}</strong></span>
                        <span>Created: <strong>${escapeHtml(formatDate(data.created_date))}</strong></span>
                    </div>
                    <div class="guild-meta-row">
                        <span>Members online: <strong>${formatNumber(onlinePlayers.length)} / ${formatNumber(data.total_members || membersArray.length)}</strong></span>
                        <span>Guild age: <strong>${escapeHtml(formatGuildAge(data.created_date))}</strong></span>
                    </div>
                </div>
            </div>
            <div class="guild-level-card">
                <div class="guild-level-label">Guild Level</div>
                <div class="guild-level-value">${formatNumber(data.level || 0)} <span class="stat-tile-sub">${xpPercent}% XP</span></div>
                <div class="level-progress" aria-label="Guild XP progress">
                    <div class="level-progress-bar" style="width: ${xpPercent}%;"></div>
                </div>
            </div>
        </section>
    `;
}

function renderGuildStatsGrid(data, onlinePlayers) {
    const tiles = [
        { label: 'Level', value: formatNumber(data.level || 0), sub: `${clampPercent(data.xp_percent)}% XP` },
        { label: 'Wars', value: formatCompactSafe(data.wars || 0) },
        { label: 'Territories', value: formatNumber(data.territories || 0) },
        { label: 'Members', value: formatNumber(data.total_members || membersArray.length) },
        { label: 'Online', value: formatNumber(onlinePlayers.length), sub: onlinePlayers.length ? 'active now' : 'none online' },
        { label: 'Created', value: formatDate(data.created_date), sub: formatGuildAge(data.created_date) },
    ];

    return `
        <section class="stats-grid">
            ${tiles.map(tile => `
                <div class="stat-tile">
                    <div class="stat-tile-label">${escapeHtml(tile.label)}</div>
                    <div class="stat-tile-value">${escapeHtml(String(tile.value))}</div>
                    ${tile.sub ? `<div class="stat-tile-sub">${escapeHtml(tile.sub)}</div>` : ''}
                </div>
            `).join('')}
        </section>
    `;
}

function renderOnlinePlayersPanel(onlinePlayers) {
    const body = onlinePlayers.length
        ? `<ul class="online-players-list">${onlinePlayers.map(renderOnlinePlayerRow).join('')}</ul>`
        : '<p class="no-results">No guild members are online right now.</p>';

    return `
        <section class="panel-card">
            <div class="panel-card-header">Online Members</div>
            <div class="panel-card-body">${body}</div>
        </section>
    `;
}

function renderOnlinePlayerRow(player) {
    return `
        <li class="online-player-row">
            <div class="online-player-main">
                <img src="https://visage.surgeplay.com/face/256/${encodeURIComponent(player.uuid)}" alt="${escapeHtml(player.name)}" class="player-icon">
                <span class="player-name">${escapeHtml(player.name)}</span>
                <span class="rank-symbol">${escapeHtml(rankSymbols[player.rank] || '')}</span>
            </div>
            <span class="server-name">[${escapeHtml(player.server || '?')}]</span>
        </li>
    `;
}

function renderGuildActions() {
    return `
        <section class="panel-card">
            <div class="panel-card-header">Guild Tables</div>
            <div class="panel-card-body">
                <div class="guild-actions">
                    <button id="toggle-members-button" type="button" class="guild-action-button" onclick="toggleMembers()">All Members</button>
                    <button id="toggle-seasons-button" type="button" class="guild-action-button" onclick="toggleSeasons()">Previous Season Ranks</button>
                </div>
            </div>
        </section>
    `;
}

function toggleMembers() {
    const membersContainer = document.getElementById('members-container');
    const button = document.getElementById('toggle-members-button');
    isMembersVisible = !isMembersVisible;

    if (isMembersVisible) {
        if (membersArray.length > 0) {
            renderMembersTable();
            membersContainer.classList.remove('hidden');
        } else {
            membersContainer.innerHTML = '<p class="no-results">No members data available</p>';
        }
    } else {
        membersContainer.classList.add('hidden');
        membersContainer.innerHTML = '';
    }

    if (button) {
        button.textContent = isMembersVisible ? 'Hide Members' : 'All Members';
    }
}

function renderMembersTable() {
    const membersContainer = document.getElementById('members-container');
    if (!membersContainer) return;

    const rows = membersArray.map(member => `
        <tr>
            <td data-label="Player">
                <div class="member-name-cell">
                    <img src="https://visage.surgeplay.com/face/256/${encodeURIComponent(member.uuid)}" alt="${escapeHtml(member.name)}" class="player-icon">
                    <span>${escapeHtml(member.name)}</span>
                </div>
            </td>
            <td data-label="Rank">${escapeHtml(formatRank(member.rank))}</td>
            <td data-label="Contributed XP">${escapeHtml(formatCompactSafe(member.contributed))}</td>
            <td data-label="Joined Date">${escapeHtml(formatDate(member.joined))}</td>
        </tr>
    `).join('');

    membersContainer.innerHTML = `
        <section class="members-card">
            <table class="members-table">
                <thead>
                    <tr>
                        <th class="${getSortClass('name')}" onclick="sortMembers('name')">Player</th>
                        <th>Rank</th>
                        <th class="${getSortClass('contributed')}" onclick="sortMembers('contributed')">Contributed XP</th>
                        <th class="${getSortClass('joined')}" onclick="sortMembers('joined', true)">Joined Date</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </section>
    `;
}

function renderMembers() {
    renderMembersTable();
}

function toggleSeasons() {
    const seasonsContainer = document.getElementById('seasons-container');
    const button = document.getElementById('toggle-seasons-button');
    if (!seasonsContainer) return;

    if (seasonsContainer.classList.contains('hidden')) {
        seasonsContainer.innerHTML = renderSeasonRanksPanel(guildData && guildData.seasonRanks);
        seasonsContainer.classList.remove('hidden');
        if (button) button.textContent = 'Hide Season Ranks';
    } else {
        seasonsContainer.classList.add('hidden');
        seasonsContainer.innerHTML = '';
        if (button) button.textContent = 'Previous Season Ranks';
    }
}

function renderSeasonRanksPanel(seasons) {
    if (!seasons || !Object.keys(seasons).length) {
        return '<p class="no-results">No season ranks data available</p>';
    }

    const rows = Object.keys(seasons)
        .sort((a, b) => Number(b) - Number(a))
        .map(season => {
            const seasonData = seasons[season];
            return `
                <tr>
                    <td data-label="Season">Season ${escapeHtml(season)}</td>
                    <td data-label="SR">${escapeHtml(formatNumber(seasonData.rating || 0))}</td>
                    <td data-label="Final Territories">${escapeHtml(formatNumber(seasonData.finalTerritories || 0))}</td>
                </tr>
            `;
        })
        .join('');

    return `
        <section class="seasons-card">
            <table class="seasons-table">
                <thead>
                    <tr>
                        <th>Season</th>
                        <th>SR</th>
                        <th>Final Territories</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </section>
    `;
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
        }
        if (key === 'contributed') {
            return sortAscending ? a[key] - b[key] : b[key] - a[key];
        }
        return sortAscending ? a[key].localeCompare(b[key]) : b[key].localeCompare(a[key]);
    });

    renderMembersTable();
}

function getSortClass(key) {
    if (currentSortKey !== key) return '';
    return sortAscending ? 'asc' : 'desc';
}

function formatRank(rank) {
    const label = rank ? rank.charAt(0).toUpperCase() + rank.slice(1) : 'Unknown';
    const stars = rankSymbols[rank] ? ` ${rankSymbols[rank]}` : '';
    return `${label}${stars}`;
}

function formatDate(value) {
    if (!value) return 'Unknown';
    const date = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(date.getTime())) return 'Unknown';
    return date.toLocaleDateString();
}

function formatGuildAge(value) {
    if (!value) return 'Unknown';
    const created = new Date(value);
    if (Number.isNaN(created.getTime())) return 'Unknown';
    const now = new Date();
    const months = Math.max(0, (now.getFullYear() - created.getFullYear()) * 12 + now.getMonth() - created.getMonth());
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;
    if (years && remainingMonths) return `${years}y ${remainingMonths}m`;
    if (years) return `${years}y`;
    return `${remainingMonths}m`;
}

function formatNumber(value) {
    return Number(value || 0).toLocaleString();
}

function formatCompactSafe(value) {
    if (window.formatCompact) {
        return window.formatCompact(value);
    }
    return formatNumber(value);
}

function clampPercent(value) {
    const numeric = Number(value || 0);
    if (Number.isNaN(numeric)) return 0;
    return Math.max(0, Math.min(100, Math.round(numeric)));
}

function displayErrorMessage(message) {
    const resultsContainer = document.getElementById('guild-results');
    resultsContainer.innerHTML = `<p class="error-message">${escapeHtml(message)}</p>`;
}

function displayLoadingMessage(message) {
    const resultsContainer = document.getElementById('guild-results');
    resultsContainer.innerHTML = `<p class="loading-message">${escapeHtml(message)}</p>`;
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
