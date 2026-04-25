document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('lootpool-filters').style.display = 'none';
    fetch('https://nori.fish/api/aspects', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data && data.Timestamp) {
            const currentTimestamp = Math.floor(Date.now() / 1000);
            const nextUpdateTimestamp = data.Timestamp + 604800;
            if (currentTimestamp > nextUpdateTimestamp) {
                updateLootpoolTitle(nextUpdateTimestamp);
                displayUpdatingMessage();
            } else {
                updateLootpoolTitle(data.Timestamp);
                displayLootpool(data.Loot, data.Icon, data.Descriptions || {});
                startCountdown(nextUpdateTimestamp - currentTimestamp);
            }
            document.getElementById('lootpool-filters').style.display = 'flex';
        } else {
            console.error('Invalid data structure:', data);
            alert('Failed to fetch lootpool data.');
        }
    })
    .catch(error => console.error('Error fetching the JSON:', error));
    setupTierFilters();
});

const ASPECT_GLYPH_MAP = {
    '\ue000': '[Air]',
    '\ue001': '[Earth]',
    '\ue002': '[Fire]',
    '\ue003': '[Thunder]',
    '\ue004': '[Water]',
    '\ue005': '[Damage]',
    '\ue01b': '[Total Damage]',
    '\ue01c': '[Range]',
    '\ue01d': '[Area]',
    '\ue01e': '[Stat]',
    '\ue01f': '[Duration]'
};
const RAID_DISPLAY_ORDER = ['TNA', 'TCC', 'NOL', 'NOG', 'TWP'];
const WARD_ICON_BY_NAME = {
    'yellow ward': 'yellow_ward.png',
    'white ward': 'white_ward.png',
    'red ward': 'red_ward.png',
    'purple ward': 'purple_ward.png',
    'pink ward': 'pink_ward.png',
    'orange ward': 'orange_ward.png',
    'green ward': 'green_ward.png',
    'cyan ward': 'cyan_ward.png',
    'blue ward': 'blue_ward.png',
    'black ward': 'black_ward.png'
};

function escapeHtml(text) {
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function normalizeAspectGlyphs(text) {
    return String(text).replace(/[\ue000-\uf8ff]/g, (glyph) => ASPECT_GLYPH_MAP[glyph] || '[Stat]');
}

function normalizeAspectDescriptionLine(rawLine) {
    if (!rawLine) return '';

    const normalizedHtml = String(rawLine)
        .replace(/<\/br\s*>/gi, '<br>')
        .replace(/<br\s*\/?>/gi, '\n');

    const parser = new DOMParser();
    const doc = parser.parseFromString(`<div>${normalizedHtml}</div>`, 'text/html');
    const text = doc.body.textContent || '';

    return normalizeAspectGlyphs(text)
        .replace(/\r/g, '')
        .replace(/[ \t]+\n/g, '\n')
        .replace(/\n[ \t]+/g, '\n')
        .replace(/[ \t]{2,}/g, ' ')
        .trim();
}

function getAspectIconUrl(itemName, iconValue) {
    let resolvedIcon = iconValue;

    if ((resolvedIcon === null || resolvedIcon === undefined || resolvedIcon === '') && typeof itemName === 'string') {
        resolvedIcon = WARD_ICON_BY_NAME[itemName.trim().toLowerCase()] || null;
    }

    if (!resolvedIcon || typeof resolvedIcon !== 'string') {
        return null;
    }

    if (!resolvedIcon.startsWith('http')) {
        return `../../resources/${resolvedIcon}`;
    }

    return resolvedIcon;
}

function updateLootpoolTitle(timestamp) {
    const date = new Date(timestamp * 1000);
    const formattedDate = date.toISOString().split('T')[0];
    const lootpoolTitle = document.getElementById('lootpool-title');
    lootpoolTitle.textContent = ''; 
    const gifImage = document.createElement('img');
    gifImage.src = "../../resources/aspect.gif"; 
    gifImage.alt = "Aspect GIF";
    gifImage.style.width = "80px";
    gifImage.style.height = "80px";
    gifImage.style.verticalAlign = "middle";
    gifImage.style.marginRight = "10px"; 
    gifImage.style.marginTop = "-10px"; 
    const textNode = document.createTextNode(`Aspect Lootpool Starting ${formattedDate}`);
    lootpoolTitle.appendChild(gifImage);
    lootpoolTitle.appendChild(textNode);
    lootpoolTitle.style.textAlign = 'center'; 
}

function displayLootpool(loot, icons, descriptions = {}) {
    const lootpoolContainer = document.getElementById('lootpool');
    lootpoolContainer.innerHTML = '';

    const regions = [
        ...RAID_DISPLAY_ORDER.filter((region) => Object.prototype.hasOwnProperty.call(loot, region)),
        ...Object.keys(loot).filter((region) => !RAID_DISPLAY_ORDER.includes(region))
    ];

    regions.forEach((region) => {
        const regionData = loot[region] || {};
        const regionCard = document.createElement('div');
        regionCard.classList.add('lootpool-card', 'active');

        const regionTitle = document.createElement('div');
        regionTitle.classList.add('region-title');
        regionTitle.textContent = `${region} Aspects`;
        regionTitle.addEventListener('click', () => {
            regionCard.classList.toggle('active');
        });
        regionCard.appendChild(regionTitle);

        const regionContent = document.createElement('div');
        regionContent.classList.add('lootpool-card-content');
        let hasAspects = false;

        ['Mythic', 'Fabled', 'Legendary'].forEach(rarity => {
            const rarityItems = Array.isArray(regionData[rarity]) ? regionData[rarity] : [];
            if (!rarityItems.length) {
                return;
            }

            hasAspects = true;
            const rarityTitle = document.createElement('div');
            rarityTitle.classList.add('rarity-title', `${rarity.toLowerCase()}-color`);
            rarityTitle.textContent = rarity;
            regionContent.appendChild(rarityTitle);

            const itemList = document.createElement('ul');
            rarityItems.forEach(item => {
                const itemElement = document.createElement('li');
                itemElement.classList.add(`${rarity.toLowerCase()}-color`);

                const itemIconUrl = getAspectIconUrl(item, icons[item]);
                if (itemIconUrl) {
                    const itemIcon = document.createElement('img');
                    itemIcon.src = itemIconUrl;
                    itemIcon.classList.add('item-icon');
                    itemElement.appendChild(itemIcon);
                }

                const itemName = document.createElement('span');
                itemName.classList.add('item-name');
                itemName.textContent = item;
                itemElement.appendChild(itemName);

                const itemDesc = descriptions[item];
                if (itemDesc) {
                    itemElement.classList.add('has-description');
                    itemName.title = 'Hover to view tier descriptions';
                    const descBlock = document.createElement('div');
                    descBlock.classList.add('aspect-desc');
                    ['1', '2', '3'].forEach((tier, idx) => {
                        if (!itemDesc[tier]) return;
                        const tierDiv = document.createElement('div');
                        tierDiv.classList.add('aspect-tier');
                        const tierLabel = document.createElement('span');
                        tierLabel.classList.add('tier-label');
                        tierLabel.textContent = `Tier ${'III'.slice(0, idx + 1)} (>=${itemDesc[tier].threshold} XP): `;
                        tierDiv.appendChild(tierLabel);
                        const tierText = document.createElement('span');
                        const normalizedLines = (itemDesc[tier].description || [])
                            .map(normalizeAspectDescriptionLine)
                            .filter(Boolean);
                        tierText.innerHTML = normalizedLines.map(escapeHtml).join('<br>');
                        tierDiv.appendChild(tierText);
                        descBlock.appendChild(tierDiv);
                    });
                    itemElement.appendChild(descBlock);
                }

                itemList.appendChild(itemElement);
            });
            regionContent.appendChild(itemList);
        });

        if (!hasAspects) {
            const emptyState = document.createElement('p');
            emptyState.classList.add('empty-raid-text');
            emptyState.textContent = 'No listed aspects for this raid this week.';
            regionContent.appendChild(emptyState);
        }

        regionCard.appendChild(regionContent);
        lootpoolContainer.appendChild(regionCard);
    });

    filterLootpool();
}

function startCountdown(seconds) {
    const countdownContainer = document.getElementById('countdown-container');
    countdownContainer.innerHTML = '';

    const countdownLabel = document.createElement('div');
    countdownLabel.id = 'countdown-label';
    countdownLabel.textContent = 'Next Update:';
    const countdownElement = document.createElement('div');
    countdownElement.id = 'countdown';
    countdownElement.classList.add('countdown-container');
    countdownContainer.appendChild(countdownLabel);
    countdownContainer.appendChild(countdownElement);

    function updateCountdown() {
        const days = Math.floor(seconds / (3600 * 24));
        const hours = Math.floor((seconds % (3600 * 24)) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = seconds % 60;
        const segments = [
            { value: days, label: 'Days', element: null, thresholds: { high: 4, medium: 2 } },
            { value: hours, label: 'Hours', element: null },
            { value: minutes, label: 'Minutes', element: null },
            { value: remainingSeconds, label: 'Seconds', element: null }
        ];
        countdownElement.innerHTML = segments.map(segment => `
            <div class="countdown-segment" id="countdown-${segment.label.toLowerCase()}">
                <div>${segment.value}</div>
                <span>${segment.label}</span>
            </div>
        `).join('');
        segments.forEach(segment => {
            segment.element = document.getElementById(`countdown-${segment.label.toLowerCase()}`);
        });
        let color = 'gray'; 
        const daySegment = segments.find(segment => segment.label === 'Days');
        if (daySegment.value > daySegment.thresholds.high) {
            color = 'green';
        } else if (daySegment.value >= daySegment.thresholds.medium) {
            color = 'gold';
        } else {
            color = 'red';
        }
        segments.forEach(segment => {
            if (segment.value === 0) {
                segment.element.style.backgroundColor = '#708090';
            } else {
                segment.element.style.backgroundColor = color;
            }
        });
        if (seconds > 0) {
            seconds--;
            setTimeout(updateCountdown, 1000);
        } else {
            location.reload();
        }
    }
    updateCountdown();
}

function setupTierFilters() {
    const filters = document.querySelectorAll('.filter-pill');
    filters.forEach(filter => {
        filter.addEventListener('click', function() {
            this.classList.toggle('active');
            filterLootpool();
        });
    });
}

function filterLootpool() {
    const filters = {
        mythic: document.getElementById('toggle-mythic').classList.contains('active'),
        fabled: document.getElementById('toggle-fabled').classList.contains('active'),
        legendary: document.getElementById('toggle-legendary').classList.contains('active'),
    };

    document.querySelectorAll('.lootpool-card').forEach(card => {
        const rarityTitles = card.querySelectorAll('.rarity-title');
        if (rarityTitles.length === 0) {
            card.style.display = 'block';
            return;
        }

        let showCard = false;
        rarityTitles.forEach(title => {
            const rarity = title.classList[1].split('-')[0];
            if (filters[rarity]) {
                title.style.display = 'flex';
                title.nextElementSibling.style.display = 'block';
                showCard = true;
            } else {
                title.style.display = 'none';
                title.nextElementSibling.style.display = 'none';
            }
        });
        card.style.display = showCard ? 'block' : 'none';
    });
}
