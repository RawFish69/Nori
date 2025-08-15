document.addEventListener('DOMContentLoaded', () => {
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    function setTokens() {
        return fetch('https://nori.fish/api/tokens', {
            method: 'GET',
            credentials: 'include'
        });
    }

    setTokens().then(() => {
        const csrfToken = getCookie('csrf_token');
        console.log("Session token generated.")
        document.getElementById('lootpool-filters').style.display = 'none';
        fetch('https://nori.fish/api/lootpool', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            credentials: 'include' 
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
                document.getElementById('lootpool-filters').style.display = 'flex';
            } else {
                console.error('Invalid data structure:', data);
                alert('Failed to fetch lootpool data.');
            }
        })
        .catch(error => console.error('Error fetching the JSON:', error));
    }).catch(error => console.error('Error setting tokens:', error));
    setupTierFilters();
});


function formatIconUrl(iconUrl) {
    if (iconUrl === null || iconUrl === undefined) {
        return null;
    }
    const armorTypes = ["helmet", "chestplate", "leggings", "boots"];
    for (const type of armorTypes) {
        if (iconUrl.toLowerCase().includes(type)) {
            return `../../../resources/${type}.png`;
        }
    }
    if (!iconUrl.startsWith("http") && iconUrl.endsWith(".png")) {
        return `../../../resources/${iconUrl}`;
    }
    return iconUrl;
}


function updateLootpoolTitle(timestamp) {
    const date = new Date(timestamp * 1000);
    const formattedDate = date.toISOString().split('T')[0];
    const lootpoolTitle = document.getElementById('lootpool-title');
    lootpoolTitle.textContent = `Item Lootpool Starting ${formattedDate}`;
    lootpoolTitle.style.textAlign = 'center'; 
}

function displayLootpool(loot, icons) {
    const lootpoolContainer = document.getElementById('lootpool');
    lootpoolContainer.innerHTML = '';

    for (const region in loot) {
        if (loot.hasOwnProperty(region)) {
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

                const shinyItemIconUrl = formatIconUrl(icons[regionData.Shiny.Item]);
                if (shinyItemIconUrl) {
                    const shinyItemIcon = document.createElement('img');
                    shinyItemIcon.src = shinyItemIconUrl;
                    shinyItemIcon.classList.add('item-icon');
                    shinyItemElement.appendChild(shinyItemIcon);
                }

                const shinyItemName = document.createElement('span');
                shinyItemName.classList.add('label', 'item-name');
                shinyItemName.textContent = regionData.Shiny.Item; 
                shinyItemElement.appendChild(shinyItemName);

                const shinyItemTracker = document.createElement('span');
                shinyItemTracker.classList.add('label', 'tracker');
                shinyItemTracker.innerHTML = `<br>Tracker: ${regionData.Shiny.Tracker}`;
                shinyItemElement.appendChild(shinyItemTracker);

                shinyList.appendChild(shinyItemElement);
                regionContent.appendChild(shinyList);
            }

            if (regionData.hasOwnProperty('Mythic')) {
                const mythicTitle = document.createElement('div');
                mythicTitle.classList.add('rarity-title', 'mythic-color');
                mythicTitle.textContent = 'Mythic';
                regionContent.appendChild(mythicTitle);

                const mythicList = document.createElement('ul');

                if (regionData.hasOwnProperty('Shiny')) {
                    const shinyItemElement = document.createElement('li');
                    shinyItemElement.classList.add('shiny-item');

                    const shinyIcon = document.createElement('img');
                    shinyIcon.src = '../../../resources/shiny.png';
                    shinyIcon.classList.add('shiny-icon');
                    shinyItemElement.appendChild(shinyIcon);


                    const shinyItemIconUrl = formatIconUrl(icons[regionData.Shiny.Item]);
                    if (shinyItemIconUrl) {
                        const shinyItemIcon = document.createElement('img');
                        shinyItemIcon.src = shinyItemIconUrl;
                        shinyItemIcon.classList.add('item-icon');
                        shinyItemElement.appendChild(shinyItemIcon);
                    }

                    const shinyItemName = document.createElement('span');
                    shinyItemName.classList.add('label', 'item-name');
                    shinyItemName.textContent = regionData.Shiny.Item; 
                    shinyItemElement.appendChild(shinyItemName);

                    const shinyItemTracker = document.createElement('span');
                    shinyItemTracker.classList.add('label', 'tracker');
                    shinyItemTracker.innerHTML = `<br>Tracker: ${regionData.Shiny.Tracker}`;
                    shinyItemElement.appendChild(shinyItemTracker);

                    mythicList.appendChild(shinyItemElement);
                }

                regionData.Mythic.forEach(item => {
                    const itemElement = document.createElement('li');
                    itemElement.classList.add('mythic-color');

                    const itemIconUrl = formatIconUrl(icons[item]);
                    if (itemIconUrl) {
                        const itemIcon = document.createElement('img');
                        itemIcon.src = itemIconUrl;
                        itemIcon.classList.add('item-icon');
                        itemElement.appendChild(itemIcon);
                    }

                    const itemName = document.createElement('span');
                    itemName.textContent = item;
                    itemElement.appendChild(itemName);

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
                    regionData[rarity].forEach(item => {
                        const itemElement = document.createElement('li');
                        itemElement.classList.add(`${rarity.toLowerCase()}-color`);

                        const itemIconUrl = formatIconUrl(icons[item]);
                        if (itemIconUrl) {
                            const itemIcon = document.createElement('img');
                            itemIcon.src = itemIconUrl;
                            itemIcon.classList.add('item-icon');
                            itemElement.appendChild(itemIcon);
                        }

                        const itemName = document.createElement('span');
                        itemName.textContent = item;
                        itemElement.appendChild(itemName);

                        itemList.appendChild(itemElement);
                    });
                    regionContent.appendChild(itemList);
                }
            }

            regionCard.appendChild(regionContent);
            lootpoolContainer.appendChild(regionCard);
        }
    }

    filterLootpool();
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
    const countdownContainer = document.createElement('div');
    countdownContainer.id = 'countdown-container';

    const countdownLabel = document.createElement('div');
    countdownLabel.id = 'countdown-label';
    countdownLabel.textContent = 'Next Update:';
    const countdownElement = document.createElement('div');
    countdownElement.id = 'countdown';
    countdownElement.classList.add('countdown-container');
    countdownContainer.appendChild(countdownLabel);
    countdownContainer.appendChild(countdownElement);
    document.getElementById('lootpool-title').appendChild(countdownContainer);

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
    const filters = document.querySelectorAll('#lootpool-filters input[type="checkbox"]');
    filters.forEach(filter => {
        filter.addEventListener('change', filterLootpool);
        const id = filter.id.split('-')[1];
        filter.classList.add(id);
    });
}

function filterLootpool() {
    const filters = {
        mythic: document.getElementById('toggle-mythic').checked,
        fabled: document.getElementById('toggle-fabled').checked,
        legendary: document.getElementById('toggle-legendary').checked,
        rare: document.getElementById('toggle-rare').checked,
        unique: document.getElementById('toggle-unique').checked,
    };

    document.querySelectorAll('.lootpool-card').forEach(card => {
        let showCard = false;
        card.querySelectorAll('.rarity-title').forEach(title => {
            const rarity = title.classList[1].split('-')[0];
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
