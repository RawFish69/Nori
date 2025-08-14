document.addEventListener('DOMContentLoaded', function() {
    populateAmplifierDropdown('amplifier-tier');
    document.getElementById('item-simulation-form').addEventListener('submit', async function(event) {
        event.preventDefault();
        const itemName = document.getElementById('item-name').value;
        const amplifierTier = document.getElementById('amplifier-tier').value || 0;

        try {
            const response = await fetch(`https://nori.fish/api/item/get/${itemName}`);
            if (!response.ok) {
                throw new Error('Invalid item data');
            }

            const itemData = await response.json();
            processItemData(itemData, amplifierTier);
        } catch (error) {
            console.error(error);
            alert('Failed to fetch item data. Please check the item name and try again.');
        }
    });
});

let currentItemName = '';
let rerollCount = 0; 

function populateAmplifierDropdown(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    for (let i = 0; i <= 20; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.text = i;
        dropdown.appendChild(option);
    }
}

function processItemData(itemData, amplifierTier) {
    const resultsContainer = document.getElementById('simulation-results');
    resultsContainer.innerHTML = ''; 
    const itemName = Object.keys(itemData)[0];
    const item = itemData[itemName];
    if (!item.identifications) {
        alert('Invalid item data. No identifications found.');
        return;
    }
    currentItemName = itemName; 
    rerollCount = 1; 

    let rerolledItem;
    if (item.identifications && Object.keys(item.identifications).length > 0) {
        rerolledItem = rerollItemStats(item, amplifierTier, itemName);
    } else {
        rerolledItem = item; 
    }

    displayItem(rerolledItem, amplifierTier, rerollCount, true);
}


function rerollItem(itemName, amplifierTier) {
    fetch(`https://nori.fish/api/item/get/${itemName}`)
        .then(response => response.json())
        .then(itemData => {
            const newItemName = Object.keys(itemData)[0];
            const item = itemData[newItemName];
            if (!item.identifications) {
                alert('Invalid item data. No identifications found.');
                return;
            }
            const rerolledItem = rerollItemStats(item, amplifierTier, newItemName);
            rerollCount++; 
            displayItem(rerolledItem, amplifierTier, rerollCount, currentItemName !== newItemName);
            currentItemName = newItemName; 
        })
        .catch(error => {
            console.error(error);
            alert('Failed to reroll item. Please try again.');
        });
}

function displayItem(item, amplifierTier, rerollCount, isInitialLoad) {
    const resultsContainer = document.getElementById('simulation-results');
    resultsContainer.innerHTML = '';

    const itemName = item.name;
    const itemData = item.identifications;
    const tier = capitalizeFirstLetter(item.rarity);
    const type = capitalizeFirstLetter(item.type);
    const tierColor = tierColors[tier.toLowerCase()];
    const overallRating = item.overall;

    const itemCardContainer = document.createElement("div");
    itemCardContainer.classList.add("item-card-container");

    const icon = ["helmet", "chestplate", "leggings", "boots"].includes(item.type.toLowerCase()) 
        ? `${item.type.toLowerCase()}.png` 
        : item.icon;
    const imageSrc = icon.startsWith('http') ? icon : `../../../resources/${item.type.toLowerCase()}.png`;

    const itemElement = document.createElement("div");
    itemElement.classList.add("item-card");
    itemElement.innerHTML = `
        <img src="${imageSrc}" alt="${itemName}" class="item-icon">
        <h3 style="color: ${tierColor};">${itemName} ${overallRating !== "N/A" ? `<span style="color:${getRateColor(overallRating)}">[${overallRating}%]</span>` : ''}</h3>
    `;

    const statsContainer = document.createElement("div");
    statsContainer.classList.add("stats-container");

    for (const [stat, value] of Object.entries(itemData)) {
        let statValue = value.raw !== undefined ? value.raw : value;
        let percentage = value.percentage !== undefined ? `[${value.percentage}%]` : '';
        let star = value.star !== undefined ? `<span class="stat-star">${value.star}</span>` : '';

        const statElement = document.createElement("div");
        statElement.classList.add("stat-row");
        statElement.innerHTML = `
            <span class="stat-value">${statValue}${star}</span>
            <span class="stat-name">${mapping[stat]}</span>
            <span class="stat-rate" style="color:${getRateColor(parseFloat(value.percentage))}">${percentage}</span>
        `;
        statsContainer.appendChild(statElement);
    }

    itemElement.appendChild(statsContainer);

    const footer = document.createElement("div");
    footer.innerHTML = `<p>${tier} ${type} ${rerollCount > 1 ? `[${rerollCount}]` : ''}</p>`;
    footer.style.color = tierColor;
    footer.style.marginTop = "10px";

    itemElement.appendChild(footer);

    const rerollContainer = document.createElement("div");
    rerollContainer.style.display = 'flex';
    rerollContainer.style.justifyContent = 'center';
    rerollContainer.style.alignItems = 'center';
    rerollContainer.style.marginTop = '10px';
    
    const amplifierLabel = document.createElement("label");
    amplifierLabel.textContent = "Amp Tier:";
    amplifierLabel.style.marginRight = "10px";

    const amplifierSelect = document.createElement("select");
    amplifierSelect.id = 'amplifier-tier-dropdown-reroll';
    for (let i = 0; i <= 20; i++) {
        const option = document.createElement("option");
        option.value = i;
        option.text = i;
        amplifierSelect.appendChild(option);
    }
    amplifierSelect.value = amplifierTier; 
    amplifierSelect.classList.add('amplifier-dropdown');

    const rerollButton = document.createElement("button");
    rerollButton.id = 'reroll-button';
    rerollButton.textContent = 'Reroll';
    rerollButton.style.fontSize = '1.1em';
    rerollButton.classList.add('reroll-button');

    rerollContainer.appendChild(amplifierLabel);
    rerollContainer.appendChild(amplifierSelect);
    rerollContainer.appendChild(rerollButton);

    itemElement.appendChild(rerollContainer);

    itemCardContainer.appendChild(itemElement);
    resultsContainer.appendChild(itemCardContainer);

    rerollButton.addEventListener('click', function() {
        rerollItem(currentItemName, amplifierSelect.value);
    });
}


function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1).toLowerCase();
}

function getRateColor(rate) {
    const red = [255, 0, 0];
    const orange = [255, 165, 0];
    const yellow = [255, 255, 0];
    const green = [0, 255, 0];
    const cyan = [0, 255, 255];

    if (rate <= 50) {
        return interpolateColor(red, orange, rate / 50);
    } else if (rate <= 75) {
        return interpolateColor(orange, yellow, (rate - 50) / 20);
    } else if (rate <= 90) {
        return interpolateColor(yellow, green, (rate - 75) / 15);
    } else {
        return interpolateColor(green, cyan, (rate - 90) / 10);
    }
}

function interpolateColor(color1, color2, factor) {
    const result = color1.slice();
    for (let i = 0; i < 3; i++) {
        result[i] = Math.round(result[i] + factor * (color2[i] - result[i]));
    }
    return `rgb(${result[0]}, ${result[1]}, ${result[2]})`;
}

function rerollItemStats(item, tier, itemName) {
    const amp = 0.05 * parseInt(tier);
    const IDs = item.identifications;
    let rerolledItem = { ...item };
    let result = {};
    let overall = 0;
    let statCount = 0;

    for (const [stat, value] of Object.entries(IDs)) {
        if (typeof value === 'object' && 'raw' in value) {
            let id_rolled;
            let max_val, min_val, percentage, amp_roll;
            let positive_roll = parseFloat((Math.round((Math.random() * (1.3 - 0.3) + 0.3) * 100) / 100).toFixed(2));
            let negative_roll = parseFloat((Math.round((Math.random() * (1.3 - 0.7) + 0.7) * 100) / 100).toFixed(2));
            let star = '';
            amp_roll = parseFloat((positive_roll + (1.3 - positive_roll) * amp).toFixed(2));

            if (value.raw > 0) {
                max_val = Math.round(value.raw * 1.3);
                if (!stat.toLowerCase().includes('spellcost')) {
                    if (amp_roll >= 1.0 && amp_roll < 1.25) star = '*';
                    else if (amp_roll >= 1.25 && amp_roll < 1.3) star = '**';
                    else if (amp_roll === 1.3) star = '***';
                }

                if (stat.toLowerCase().includes('spellcost')) {
                    id_rolled = Math.round(value.raw * negative_roll);
                    
                    min_val = Math.round(value.raw * 0.7);
                    percentage = min_val !== max_val ? ((max_val - id_rolled) / (max_val - min_val)) * 100 : 100;
                } else {
                    id_rolled = Math.round(value.raw * amp_roll);
                
                    min_val = Math.round(value.raw * 0.3);
                    percentage = min_val !== max_val ? ((id_rolled - min_val) / (max_val - min_val)) * 100 : 100;
                }

                overall += percentage;
                statCount++;
                result[stat] = { raw: id_rolled, percentage: percentage.toFixed(1), star: star };
            } else {
                max_val = Math.round(value.raw * 1.3);

                if (stat.toLowerCase().includes('spellcost')) {
                    id_rolled = Math.round(value.raw * amp_roll);
                    min_val = Math.round(value.raw * 0.3);
                    percentage = min_val !== max_val ? ((id_rolled - min_val) / (max_val - min_val)) * 100 : 100;
                } else {
                    id_rolled = Math.round(value.raw * negative_roll);
                    min_val = Math.round(value.raw * 0.7);
                    percentage = min_val !== max_val ? ((max_val - id_rolled) / (max_val - min_val)) * 100 : 100;
                }

                overall += percentage;
                statCount++;
                result[stat] = { raw: id_rolled, percentage: percentage.toFixed(1), star: star };
            }
        } else {
            result[stat] = value;
        }
    }
    rerolledItem.identifications = result;
    rerolledItem.overall = (statCount > 0) ? (overall / statCount).toFixed(1) : "N/A";
    rerolledItem.name = itemName;
    
    return rerolledItem;
}