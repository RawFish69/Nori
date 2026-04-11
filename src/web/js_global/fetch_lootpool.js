document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('lootpool-filters').style.display = 'none';
    const lastKnownTimestamp = Number(localStorage.getItem('item_lootpool_last_timestamp') || 0);

    fetch('https://nori.fish/api/lootpool', {
        method: 'GET',
        credentials: 'omit'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data && data.Timestamp) {
            const currentTimestamp = Math.floor(Date.now() / 1000);
            const nextUpdateTimestamp = data.Timestamp + 604800;
            if (currentTimestamp > nextUpdateTimestamp) {
                if (data.Timestamp === lastKnownTimestamp) {
                    updateLootpoolTitle(nextUpdateTimestamp);
                    displayUpdatingMessage();
                } else {
                    updateLootpoolTitle(data.Timestamp);
                    displayLootpool(data.Loot, data.Icon);
                }
            } else {
                updateLootpoolTitle(data.Timestamp);
                displayLootpool(data.Loot, data.Icon);
                startCountdown(nextUpdateTimestamp - currentTimestamp);
                console.log("Lootpool fetched successfully.");
            }
            localStorage.setItem('item_lootpool_last_timestamp', String(data.Timestamp));
            document.getElementById('lootpool-filters').style.display = 'flex';
        } else {
            console.error('Invalid data structure:', data);
            alert('Failed to fetch lootpool data.');
        }
    })
    .catch(error => console.error('Error fetching the JSON:', error));
    setupTierFilters();
});

const WARD_ICON_BY_NAME = {
    "yellow ward": "yellow_ward.png",
    "white ward": "white_ward.png",
    "red ward": "red_ward.png",
    "purple ward": "purple_ward.png",
    "pink ward": "pink_ward.png",
    "orange ward": "orange_ward.png",
    "green ward": "green_ward.png",
    "cyan ward": "cyan_ward.png",
    "blue ward": "blue_ward.png",
    "black ward": "black_ward.png"
};

const MISC_ICON_BY_NAME = {
    "liquid emerald": "liquid_emerald.png",
    "emerald block": "emerald_block.png",
    "emerald": "emerald.png",
    "packed crafter bag [1/1]": "crafter_packed.png",
    "stuffed crafter bag [1/1]": "crafter_stuffed.png",
    "varied crafter bag [1/1]": "crafter_varied.png",
    "corkian insulator": "insulator.png",
    "corkian simulator": "simulator.png",
    "tol rune": "tol.png",
    "uth rune": "uth.png",
    "nii rune": "nii.png",
    "az rune": "az.png",
    "ek rune": "ek.png"
};


function formatIconUrl(iconUrl, itemName = null) {
    let resolved = iconUrl;
    if ((resolved === null || resolved === undefined || resolved === "") && typeof itemName === "string") {
        resolved = resolveSpecialItemIcon(itemName);
    }
    if (resolved === null || resolved === undefined || typeof resolved !== "string") {
        return null;
    }
    const armorTypes = ["helmet", "chestplate", "leggings", "boots"];
    for (const type of armorTypes) {
        if (resolved.toLowerCase().includes(type)) {
            return `../../../resources/${type}.png`;
        }
    }
    if (!resolved.startsWith("http") && resolved.endsWith(".png")) {
        return `../../../resources/${resolved}`;
    }
    return resolved;
}

function resolveSpecialItemIcon(itemName) {
    if (typeof itemName !== "string") return null;
    const normalized = itemName.replace(/\u00a0/g, " ").replace(/\u00c0/g, " ").replace(/\s+/g, " ").trim();
    const lowered = normalized.toLowerCase();
    if (!lowered) return null;
    if (WARD_ICON_BY_NAME[lowered]) return WARD_ICON_BY_NAME[lowered];
    if (MISC_ICON_BY_NAME[lowered]) return MISC_ICON_BY_NAME[lowered];
    if (lowered.endsWith(" key")) return "dungeon_key.png";
    if (lowered.startsWith("corkian amplifier")) return "corkian_amplifier.png";
    if (lowered.includes("crafter bag")) {
        if (lowered.includes("packed")) return "crafter_packed.png";
        if (lowered.includes("stuffed")) return "crafter_stuffed.png";
        if (lowered.includes("varied")) return "crafter_varied.png";
    }
    const powderParts = lowered.split(" powder ");
    if (powderParts.length === 2 && ["earth", "thunder", "water", "fire", "air"].includes(powderParts[0])) {
        return "powder.png";
    }
    return null;
}


function updateLootpoolTitle(timestamp) {
    const date = new Date(timestamp * 1000);
    const formattedDate = date.toISOString().split('T')[0];
    const lootpoolTitle = document.getElementById('lootpool-title');
    lootpoolTitle.textContent = `Item Lootpool Starting ${formattedDate}`;
    lootpoolTitle.style.textAlign = 'center'; 
}

function lootpoolHasAnyWard(loot) {
    const wardPattern = /\bward\b/i;

    for (const regionData of Object.values(loot || {})) {
        if (!regionData || typeof regionData !== 'object') continue;

        if (regionData.Shiny && typeof regionData.Shiny.Item === 'string' && wardPattern.test(regionData.Shiny.Item)) {
            return true;
        }

        for (const tierItems of Object.values(regionData)) {
            if (!Array.isArray(tierItems)) continue;
            if (tierItems.some(item => typeof item === 'string' && wardPattern.test(item))) {
                return true;
            }
        }
    }

    return false;
}

function displayLootpool(loot, icons) {
    const lootpoolContainer = document.getElementById('lootpool');
    lootpoolContainer.innerHTML = '';
    const hasAnyWard = lootpoolHasAnyWard(loot);
    const shouldAddNoWard = !hasAnyWard;
    const normalizeRegionKey = value =>
        String(value || '')
            .toLowerCase()
            .replace(/[\s_-]+/g, '');
    const existingRegionKeys = new Set(Object.keys(loot || {}).map(normalizeRegionKey));
    const renderedRegionKeys = new Set();

    for (const region in loot) {
        if (loot.hasOwnProperty(region)) {
            const canonicalRegion = normalizeRegionKey(region);
            if (renderedRegionKeys.has(canonicalRegion)) {
                continue;
            }
            renderedRegionKeys.add(canonicalRegion);
            const regionData = loot[region];
            const regionCard = document.createElement('div');
            regionCard.classList.add('lootpool-card');
            regionCard.classList.add('active');

            const regionTitle = document.createElement('div');
            regionTitle.classList.add('region-title');
            regionTitle.textContent = `${region} Lootpool`;
            regionTitle.addEventListener('click', () => {
                regionCard.classList.toggle('active');
            });
            regionCard.appendChild(regionTitle);

            const regionContent = document.createElement('div');
            regionContent.classList.add('lootpool-card-content');

            if (regionData.hasOwnProperty('Shiny')) {
                const shinyTitle = document.createElement('div');
                shinyTitle.classList.add('rarity-title', 'shiny-color');
                shinyTitle.textContent = 'Shiny Mythic';
                regionContent.appendChild(shinyTitle);

                const shinyList = document.createElement('ul');
                const shinyItemElement = document.createElement('li');
                shinyItemElement.classList.add('shiny-item');

                const shinyIcon = document.createElement('img');
                shinyIcon.src = '../../../resources/shiny.png';
                shinyIcon.classList.add('shiny-icon');
                shinyItemElement.appendChild(shinyIcon);

                const shinyItemIconUrl = formatIconUrl(icons[regionData.Shiny.Item], regionData.Shiny.Item);
                if (shinyItemIconUrl) {
                    const shinyItemIcon = document.createElement('img');
                    shinyItemIcon.src = shinyItemIconUrl;
                    shinyItemIcon.classList.add('item-icon');
                    shinyItemElement.appendChild(shinyItemIcon);
                }

                const shinyMeta = document.createElement('div');
                shinyMeta.classList.add('shiny-meta');

                const shinyItemName = document.createElement('span');
                shinyItemName.classList.add('label', 'item-name');
                shinyItemName.textContent = regionData.Shiny.Item; 
                shinyMeta.appendChild(shinyItemName);

                const shinyItemTracker = document.createElement('span');
                shinyItemTracker.classList.add('label', 'tracker');
                shinyItemTracker.textContent = `Tracker: ${regionData.Shiny.Tracker}`;
                shinyMeta.appendChild(shinyItemTracker);

                shinyItemElement.appendChild(shinyMeta);

                shinyList.appendChild(shinyItemElement);
                regionContent.appendChild(shinyList);
            }

            const mythicItems = Array.isArray(regionData.Mythic) ? [...regionData.Mythic] : [];
            if (shouldAddNoWard && !mythicItems.some(item => typeof item === 'string' && item.toLowerCase() === 'no ward')) {
                mythicItems.push('No Ward');
            }

            if (mythicItems.length > 0) {
                const mythicTitle = document.createElement('div');
                mythicTitle.classList.add('rarity-title', 'mythic-color');
                mythicTitle.textContent = 'Mythic';
                regionContent.appendChild(mythicTitle);

                const mythicList = document.createElement('ul');
                const compactedMythic = compactDuplicateEntries(mythicItems);
                compactedMythic.forEach(({ name, count }) => {
                    const itemElement = document.createElement('li');
                    const isNoWard = name === 'No Ward';
                    itemElement.classList.add(isNoWard ? 'no-ward-item' : 'mythic-color');

                    const itemIconUrl = isNoWard
                        ? '../../../resources/white_ward.png'
                        : formatIconUrl(icons[name], name);
                    if (itemIconUrl) {
                        const itemIcon = document.createElement('img');
                        itemIcon.src = itemIconUrl;
                        itemIcon.classList.add('item-icon');
                        itemElement.appendChild(itemIcon);
                    }

                    const itemName = document.createElement('span');
                    itemName.classList.add('item-name');
                    itemName.textContent = name;
                    itemElement.appendChild(itemName);
                    if (count > 1) {
                        const countBadge = document.createElement('span');
                        countBadge.classList.add('item-count');
                        countBadge.textContent = `x${count}`;
                        itemElement.appendChild(countBadge);
                    }

                    mythicList.appendChild(itemElement);
                });
                regionContent.appendChild(mythicList);
            }

            for (const rarity in regionData) {
                if (regionData.hasOwnProperty(rarity) && Array.isArray(regionData[rarity]) && rarity !== 'Mythic') {
                    const rarityTitle = document.createElement('div');
                    rarityTitle.classList.add('rarity-title', `${rarity.toLowerCase()}-color`);
                    rarityTitle.textContent = rarity;
                    regionContent.appendChild(rarityTitle);

                    const itemList = document.createElement('ul');
                    const compactedEntries = compactDuplicateEntries(regionData[rarity]);
                    compactedEntries.forEach(({ name, count }) => {
                        const itemElement = document.createElement('li');
                        itemElement.classList.add(`${rarity.toLowerCase()}-color`);

                        const itemIconUrl = formatIconUrl(icons[name], name);
                        if (itemIconUrl) {
                            const itemIcon = document.createElement('img');
                            itemIcon.src = itemIconUrl;
                            itemIcon.classList.add('item-icon');
                            itemElement.appendChild(itemIcon);
                        }

                        const itemName = document.createElement('span');
                        itemName.classList.add('item-name');
                        itemName.textContent = name;
                        itemElement.appendChild(itemName);
                        if (count > 1) {
                            const countBadge = document.createElement('span');
                            countBadge.classList.add('item-count');
                            countBadge.textContent = `x${count}`;
                            itemElement.appendChild(countBadge);
                        }

                        itemList.appendChild(itemElement);
                    });
                    regionContent.appendChild(itemList);
                }
            }

            regionCard.appendChild(regionContent);
            lootpoolContainer.appendChild(regionCard);
        }
    }

    // Add Fruma placeholders as normal regions if not yet present
    const frumaRegions = [
        { key: 'Fruma West', label: 'Fruma West Lootpool' },
        { key: 'Fruma East', label: 'Fruma East Lootpool' }
    ];

    frumaRegions.forEach(({ key, label }) => {
        const exists = existingRegionKeys.has(normalizeRegionKey(key));
        if (!exists) {
            const regionCard = document.createElement('div');
            regionCard.classList.add('lootpool-card', 'active', 'coming-soon-card');

            const regionTitle = document.createElement('div');
            regionTitle.classList.add('region-title');
            regionTitle.textContent = label;
            regionTitle.addEventListener('click', () => {
                regionCard.classList.toggle('active');
            });
            regionCard.appendChild(regionTitle);

            const regionContent = document.createElement('div');
            regionContent.classList.add('lootpool-card-content');

            const labelEl = document.createElement('p');
            labelEl.classList.add('coming-soon-text');
            labelEl.textContent = 'COMING SOON';
            regionContent.appendChild(labelEl);

            const sub = document.createElement('p');
            sub.classList.add('coming-soon-subtext');
            sub.textContent = `Lootrun rewards for ${key} will be added in a future update.`;
            regionContent.appendChild(sub);

            regionCard.appendChild(regionContent);
            lootpoolContainer.appendChild(regionCard);
        }
    });

    filterLootpool();
}

function compactDuplicateEntries(entries) {
    const counts = new Map();
    (Array.isArray(entries) ? entries : []).forEach(item => {
        if (typeof item !== 'string') return;
        const name = item.trim();
        if (!name) return;
        counts.set(name, (counts.get(name) || 0) + 1);
    });
    return Array.from(counts.entries()).map(([name, count]) => ({ name, count }));
}

function displayUpdatingMessage() {
    const lootpoolTitle = document.getElementById('lootpool-title');
    const updatingMessage = document.createElement('div');
    updatingMessage.style.textAlign = 'center';
    updatingMessage.style.fontSize = '1.2em'; 
    updatingMessage.innerHTML = `
        <p>We are updating this week's new lootpool, <a href="https://discord.gg/eDssA6Jbwd">Join support server</a> to follow updates.</p>
    `;
    lootpoolTitle.appendChild(updatingMessage);
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
        rare: document.getElementById('toggle-rare').classList.contains('active'),
        unique: document.getElementById('toggle-unique').classList.contains('active'),
        misc: document.getElementById('toggle-misc').classList.contains('active'),
    };

    document.querySelectorAll('.lootpool-card').forEach(card => {
        // Always show placeholder / coming-soon cards
        if (card.classList.contains('coming-soon-card')) {
            card.style.display = 'block';
            return;
        }

        let showCard = false;
        card.querySelectorAll('.rarity-title').forEach(title => {
            let rarity = title.classList[1].split('-')[0];
            if (rarity === 'shiny') {
                rarity = 'mythic';
            }
            if (filters[rarity]) {
                title.style.display = 'block';
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
