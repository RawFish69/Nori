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
                displayLootpool(data.Loot, data.Icon);
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

function displayLootpool(loot, icons) {
    const lootpoolContainer = document.getElementById('lootpool');
    lootpoolContainer.innerHTML = '';

    for (const region in loot) {
        if (loot.hasOwnProperty(region)) {
            const regionData = loot[region];
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

            ['Mythic', 'Fabled', 'Legendary'].forEach(rarity => {
                if (regionData[rarity]) {
                    const rarityTitle = document.createElement('div');
                    rarityTitle.classList.add('rarity-title', `${rarity.toLowerCase()}-color`);
                    rarityTitle.textContent = rarity;
                    regionContent.appendChild(rarityTitle);

                    const itemList = document.createElement('ul');
                    regionData[rarity].forEach(item => {
                        const itemElement = document.createElement('li');
                        itemElement.classList.add(`${rarity.toLowerCase()}-color`);

                        const itemIconUrl = icons[item];
                        if (itemIconUrl) {
                            const itemIcon = document.createElement('img');
                            itemIcon.src = `../../resources/${itemIconUrl}`;
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
            });

            regionCard.appendChild(regionContent);
            lootpoolContainer.appendChild(regionCard);
        }
    }
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
        let showCard = false;
        card.querySelectorAll('.rarity-title').forEach(title => {
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
