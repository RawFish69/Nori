let mythicData = null;
let allTypeIconInterval = null;

const armorTypes = ['helmet', 'chestplate', 'leggings', 'boots'];
const allItemTypes = ['spear', 'bow', 'wand', 'dagger', 'relik', ...armorTypes];
const pageState = {
    selectedType: null,
    selectedTypes: [],
    viewMode: 'full'
};

document.addEventListener('DOMContentLoaded', async function() {
    await fetchMythicData();
    initAllTypeIconAnimation();
    updateViewModeButtons();
});

function initAllTypeIconAnimation() {
    const allTypeIcon = document.getElementById('all-type-icon');
    if (!allTypeIcon) {
        return;
    }

    const iconSequence = [
        { src: '../../../resources/simulator.png', alt: 'All Items' },
        { src: '../../../resources/spear.png', alt: 'All Items - Spear' },
        { src: '../../../resources/bow.png', alt: 'All Items - Bow' },
        { src: '../../../resources/wand.png', alt: 'All Items - Wand' },
        { src: '../../../resources/dagger.png', alt: 'All Items - Dagger' },
        { src: '../../../resources/relik.png', alt: 'All Items - Relik' },
        { src: '../../../resources/helmet.png', alt: 'All Items - Helmet' },
        { src: '../../../resources/chestplate.png', alt: 'All Items - Chestplate' },
        { src: '../../../resources/leggings.png', alt: 'All Items - Leggings' },
        { src: '../../../resources/boots.png', alt: 'All Items - Boots' }
    ];

    let iconIndex = 0;
    allTypeIcon.src = iconSequence[iconIndex].src;
    allTypeIcon.alt = iconSequence[iconIndex].alt;

    if (allTypeIconInterval) {
        clearInterval(allTypeIconInterval);
    }

    allTypeIconInterval = setInterval(() => {
        allTypeIcon.classList.add('is-transitioning');

        setTimeout(() => {
            iconIndex = (iconIndex + 1) % iconSequence.length;
            allTypeIcon.src = iconSequence[iconIndex].src;
            allTypeIcon.alt = iconSequence[iconIndex].alt;
            allTypeIcon.classList.remove('is-transitioning');
        }, 380);
    }, 2000);
}

async function fetchMythicData() {
    try {
        const response = await fetch('https://nori.fish/api/item/mythic');
        if (!response.ok) {
            throw new Error('Failed to fetch item data');
        }
        mythicData = await response.json();
    } catch (error) {
        console.error(error);
    }
}

function selectType(type) {
    if (!mythicData) {
        alert('Still loading data, please wait...');
        return;
    }

    pageState.selectedType = type;
    pageState.selectedTypes = getSelectedTypes(type);

    document.getElementById('type-selector').style.display = 'none';
    document.getElementById('items-view').style.display = '';

    const typeLabels = {
        all: 'All',
        spear: 'Spear', bow: 'Bow', wand: 'Wand',
        dagger: 'Dagger', relik: 'Relik', armor: 'Armor'
    };
    document.getElementById('items-view-title').textContent = `${typeLabels[type] || type} Mythics`;

    renderCurrentView();
}

function goBack() {
    pageState.selectedType = null;
    pageState.selectedTypes = [];

    document.getElementById('type-selector').style.display = '';
    document.getElementById('items-view').style.display = 'none';
    document.getElementById('item-cards-container').innerHTML = '';
}

function setViewMode(mode) {
    if (mode !== 'full' && mode !== 'scale-only') {
        return;
    }
    pageState.viewMode = mode;
    updateViewModeButtons();
    renderCurrentView();
}

function updateViewModeButtons() {
    const fullBtn = document.getElementById('view-mode-full');
    const scaleOnlyBtn = document.getElementById('view-mode-scale-only');
    if (!fullBtn || !scaleOnlyBtn) {
        return;
    }

    fullBtn.classList.toggle('active', pageState.viewMode === 'full');
    scaleOnlyBtn.classList.toggle('active', pageState.viewMode === 'scale-only');
}

function renderCurrentView() {
    if (!mythicData || !pageState.selectedTypes.length) {
        return;
    }
    renderItems(mythicData, pageState.selectedTypes, pageState.viewMode);
}

function getSelectedTypes(type) {
    if (type === 'all') {
        return allItemTypes;
    }
    if (type === 'armor') {
        return armorTypes;
    }
    return [type];
}

function renderItems(data, selectedTypes, viewMode) {
    const itemCardsContainer = document.getElementById('item-cards-container');
    itemCardsContainer.innerHTML = '';

    const rankedItems = data.ranked || {};
    const weights = data.weights || {};
    const mythicInfo = data.info || {};

    if (viewMode === 'scale-only') {
        renderScaleOnlyMode(itemCardsContainer, rankedItems, weights, mythicInfo, selectedTypes);
    } else {
        renderFullMode(itemCardsContainer, rankedItems, weights, mythicInfo, selectedTypes);
    }

    if (itemCardsContainer.children.length === 0) {
        itemCardsContainer.innerHTML = '<p style="color: #888; text-align: center;">No mythic items found for this type.</p>';
    }
}

function renderFullMode(itemCardsContainer, rankedItems, weights, mythicInfo, selectedTypes) {
    const renderedItems = new Set();

    for (const itemName of Object.keys(rankedItems)) {
        const scales = rankedItems[itemName];
        if (!scales || typeof scales !== 'object') {
            continue;
        }

        const fallbackInfo = mythicInfo[itemName] || {};

        for (const scaleName of Object.keys(scales)) {
            const entry = scales[scaleName];
            if (!entry || typeof entry !== 'object') {
                continue;
            }

            const itemStats = entry.stats && typeof entry.stats === 'object' ? entry.stats : null;
            const itemData = itemStats && typeof itemStats[itemName] === 'object' ? itemStats[itemName] : null;
            const rateData = itemStats && typeof itemStats.rate === 'object' ? itemStats.rate : null;
            const hasSnapshot = typeof entry.has_snapshot === 'boolean' ? entry.has_snapshot : !!itemData;
            const snapshotMissing = typeof entry.snapshot_missing === 'boolean' ? entry.snapshot_missing : !hasSnapshot;

            const itemTypeRaw = (
                (itemStats && itemStats.item_type) ||
                entry.item_type ||
                fallbackInfo.item_type ||
                null
            );
            const itemType = typeof itemTypeRaw === 'string' ? itemTypeRaw.toLowerCase() : null;
            if (!itemType || !selectedTypes.includes(itemType)) {
                continue;
            }

            const iconRaw = (
                (itemStats && itemStats.icon) ||
                entry.icon ||
                fallbackInfo.icon ||
                ''
            );
            const icon = getDisplayIcon(iconRaw, itemType);
            const tierRaw = (
                (itemStats && itemStats.item_tier) ||
                entry.item_tier ||
                fallbackInfo.item_tier ||
                'mythic'
            );
            const tier = normalizeTier(tierRaw);
            const tierColor = tierColors[tier] || tierColors.mythic;

            const owner = entry.owner || 'None';
            const ownerColor = owner === 'None' ? '#888' : 'gold';
            const weight = itemStats && typeof itemStats.weight === 'number' ? itemStats.weight : null;
            const shiny = itemStats ? itemStats.shiny : null;
            const overallRating = rateData ? getOverallRating(rateData) : 'N/A';
            const ratingHtml = overallRating !== 'N/A'
                ? ` <span style="color:${getRateColor(overallRating)}">[${overallRating}%]</span>`
                : '';
            const weightHtml = typeof weight === 'number'
                ? ` <span style="color:${getRateColor(weight)}">[${weight}%]</span>`
                : '';

            const cardKey = makeCardKey(itemName, scaleName, 'full');
            const scaleSection = renderScaleSection(itemName, weights[itemName], cardKey, false);
            const snapshotNote = snapshotMissing
                ? '<p class="snapshot-note">ID snapshot unavailable</p>'
                : '';
            const statsHtml = itemData ? `<div class="item-stats">${renderStats(itemData, rateData)}</div>` : '';
            const shinyHtml = shiny
                ? `<p class="shiny-value"><img src="../../../resources/shiny.png" class="shiny-icon" alt="Shiny"> ${shiny}</p>`
                : '';

            const itemCard = document.createElement('div');
            itemCard.classList.add('item-card');
            itemCard.innerHTML = `
                <img src="${icon}" alt="${itemName}" class="item-icon">
                <h3 style="color: ${tierColor};">${itemName}${ratingHtml}</h3>
                <p class="item-scale">Scale: <span style="color: #DDA0DD;">${scaleName}</span>${weightHtml}</p>
                <p class="item-owner">Owner: <span style="color: ${ownerColor};">${owner}</span></p>
                ${snapshotNote}
                ${shinyHtml}
                ${statsHtml}
                ${scaleSection}
            `;

            itemCardsContainer.appendChild(itemCard);
            renderedItems.add(itemName);
        }
    }

    for (const itemName of Object.keys(weights)) {
        if (renderedItems.has(itemName)) {
            continue;
        }

        const info = mythicInfo[itemName] || {};
        const itemType = typeof info.item_type === 'string' ? info.item_type.toLowerCase() : null;
        if (!itemType || !selectedTypes.includes(itemType)) {
            continue;
        }

        const icon = getDisplayIcon(info.icon || '', itemType);
        const tier = normalizeTier(info.item_tier || 'mythic');
        const tierColor = tierColors[tier] || tierColors.mythic;
        const cardKey = makeCardKey(itemName, 'unranked', 'full');

        const itemCard = document.createElement('div');
        itemCard.classList.add('item-card');
        itemCard.innerHTML = `
            <img src="${icon}" alt="${itemName}" class="item-icon">
            <h3 style="color: ${tierColor};">${itemName}</h3>
            <p class="item-owner">Owner: <span style="color: #888;">None</span></p>
            ${renderScaleSection(itemName, weights[itemName], cardKey, false)}
        `;
        itemCardsContainer.appendChild(itemCard);
    }
}

function renderScaleOnlyMode(itemCardsContainer, rankedItems, weights, mythicInfo, selectedTypes) {
    const orderedItems = [];
    const seen = new Set();

    for (const itemName of Object.keys(rankedItems)) {
        if (!seen.has(itemName)) {
            seen.add(itemName);
            orderedItems.push(itemName);
        }
    }
    for (const itemName of Object.keys(weights)) {
        if (!seen.has(itemName)) {
            seen.add(itemName);
            orderedItems.push(itemName);
        }
    }

    for (const itemName of orderedItems) {
        const info = mythicInfo[itemName] || {};
        const scales = weights[itemName] || null;

        let itemType = info.item_type || null;
        let tierRaw = info.item_tier || null;
        let iconRaw = info.icon || '';

        if (!itemType && rankedItems[itemName] && typeof rankedItems[itemName] === 'object') {
            for (const scaleName of Object.keys(rankedItems[itemName])) {
                const entry = rankedItems[itemName][scaleName];
                if (!entry || typeof entry !== 'object') {
                    continue;
                }
                const stats = entry.stats && typeof entry.stats === 'object' ? entry.stats : null;
                itemType = itemType || (stats && stats.item_type) || entry.item_type || null;
                tierRaw = tierRaw || (stats && stats.item_tier) || entry.item_tier || null;
                iconRaw = iconRaw || (stats && stats.icon) || entry.icon || '';
            }
        }

        itemType = typeof itemType === 'string' ? itemType.toLowerCase() : null;
        if (!itemType || !selectedTypes.includes(itemType)) {
            continue;
        }

        const icon = getDisplayIcon(iconRaw, itemType);
        const tier = normalizeTier(tierRaw || 'mythic');
        const tierColor = tierColors[tier] || tierColors.mythic;
        const cardKey = makeCardKey(itemName, 'scale-only', 'scale-only');

        const itemCard = document.createElement('div');
        itemCard.classList.add('item-card', 'scale-only-card');
        itemCard.innerHTML = `
            <img src="${icon}" alt="${itemName}" class="item-icon">
            <h3 style="color: ${tierColor};">${itemName}</h3>
            ${renderScaleSection(itemName, scales, cardKey, true)}
        `;

        itemCardsContainer.appendChild(itemCard);
    }
}

function renderScaleSection(itemName, scales, cardKey, expandedByDefault) {
    const scaleId = `scales-${cardKey}`;
    const buttonText = expandedByDefault ? 'Hide Scales' : 'Show Scales';
    const displayStyle = expandedByDefault ? 'block' : 'none';

    return `
        <button class="show-scales-btn" onclick="toggleScales(event, '${scaleId}')">${buttonText}</button>
        <div class="scale-details" id="${scaleId}" style="display:${displayStyle}">${renderScales(scales)}</div>
    `;
}

function makeCardKey(itemName, scaleName, mode) {
    return [itemName, scaleName, mode].map(part => String(part)
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '')
    ).join('-');
}

function normalizeTier(tier) {
    if (!tier || typeof tier !== 'string') {
        return 'mythic';
    }
    return tier.toLowerCase();
}

function getDisplayIcon(icon, itemType) {
    if (armorTypes.includes(itemType)) {
        return `../../../resources/${itemType}.png`;
    }
    return icon || '';
}

function renderStats(stats, rateData) {
    let statsHtml = '';
    if (!stats || typeof stats !== 'object') {
        return statsHtml;
    }

    for (const stat in stats) {
        if (stat !== 'icon' && stat !== 'item_type' && stat !== 'shiny' && stat !== 'item_tier' && stats[stat] !== null) {
            const rate = rateData && typeof rateData[stat] === 'number' ? rateData[stat] : null;
            statsHtml += `
                <div class="stat-row">
                    <span class="stat-value">${stats[stat]}</span>
                    <span class="stat-name">${mapping[stat] || stat}</span>
                    ${rate !== null ? `<span class="stat-rate" style="color:${getRateColor(rate)}">[${rate}%]</span>` : ''}
                </div>
            `;
        }
    }
    return statsHtml;
}

function renderScales(scales) {
    if (!scales || typeof scales !== 'object') {
        return '<p>No scale data available</p>';
    }

    const scaleKeys = Object.keys(scales);
    if (!scaleKeys.length) {
        return '<p>No scale data available</p>';
    }

    let scalesHtml = '';
    for (const scale of scaleKeys) {
        const scaleStats = scales[scale];
        scalesHtml += `<div class="scale-row"><strong>${scale} Scale:</strong></div>`;
        if (!scaleStats || typeof scaleStats !== 'object') {
            scalesHtml += '<div><span>No scale data available</span></div>';
            scalesHtml += '<div class="scale-spacing"></div>';
            continue;
        }

        for (const stat in scaleStats) {
            const value = scaleStats[stat];
            const color = getRateColor(value);
            const displayValue = typeof value === 'number' ? `${value}%` : value;
            scalesHtml += `<div><span>${mapping[stat] || stat}: <span style="color:${color}">${displayValue}</span></span></div>`;
        }
        scalesHtml += '<div class="scale-spacing"></div>';
    }
    return scalesHtml;
}

function getOverallRating(rateData) {
    const values = Object.values(rateData).filter(value => typeof value === 'number' && Number.isFinite(value));
    if (!values.length) {
        return 'N/A';
    }

    const total = values.reduce((sum, value) => sum + value, 0);
    return (total / values.length).toFixed(2);
}

function getRateColor(rate) {
    const numericRate = Number(rate);
    if (!Number.isFinite(numericRate)) {
        return '#cccccc';
    }

    const red = [255, 0, 0];
    const orange = [255, 165, 0];
    const yellow = [255, 255, 0];
    const green = [0, 255, 0];
    const cyan = [0, 255, 255];

    if (numericRate <= 50) {
        return interpolateColor(red, orange, numericRate / 50);
    } else if (numericRate <= 75) {
        return interpolateColor(orange, yellow, (numericRate - 50) / 25);
    } else if (numericRate <= 90) {
        return interpolateColor(yellow, green, (numericRate - 75) / 15);
    }
    return interpolateColor(green, cyan, (numericRate - 90) / 10);
}

function interpolateColor(color1, color2, factor) {
    const safeFactor = Math.max(0, Math.min(1, factor));
    const result = color1.slice();
    for (let i = 0; i < 3; i++) {
        result[i] = Math.round(result[i] + safeFactor * (color2[i] - result[i]));
    }
    return `rgb(${result[0]}, ${result[1]}, ${result[2]})`;
}

const mapping = {
    "healthRegen": "Health Regen %",
    "manaRegen": "Mana Regen",
    "spellDamage": "Spell Damage %",
    "elementalSpellDamage": "Elemental Spell Damage %",
    "neutralSpellDamage": "Neutral Spell Damage %",
    "fireSpellDamage": "Fire Spell Damage %",
    "waterSpellDamage": "Water Spell Damage %",
    "airSpellDamage": "Air Spell Damage %",
    "thunderSpellDamage": "Thunder Spell Damage %",
    "earthSpellDamage": "Earth Spell Damage %",
    "mainAttackDamage": "Main Attack Damage %",
    "elementalMainAttackDamage": "Elemental Main Attack Damage %",
    "neutralMainAttackDamage": "Neutral Main Attack Damage %",
    "fireMainAttackDamage": "Fire Main Attack Damage %",
    "waterMainAttackDamage": "Water Main Attack Damage %",
    "airMainAttackDamage": "Air Main Attack Damage %",
    "thunderMainAttackDamage": "Thunder Main Attack Damage %",
    "earthMainAttackDamage": "Earth Main Attack Damage %",
    "lifeSteal": "Life Steal",
    "manaSteal": "Mana Steal",
    "xpBonus": "XP Bonus %",
    "lootBonus": "Loot Bonus %",
    "leveledXpBonus": "Leveled XP Bonus %",
    "leveledLootBonus": "Leveled Loot Bonus %",
    "reflection": "Reflection",
    "rawStrength": "Strength",
    "rawDexterity": "Dexterity",
    "rawIntelligence": "Intelligence",
    "rawDefence": "Defence",
    "rawAgility": "Agility",
    "thorns": "Thorns %",
    "poison": "Poison",
    "exploding": "Exploding %",
    "walkSpeed": "Walk Speed %",
    "rawAttackSpeed": "Attack Speed",
    "rawHealth": "Health",
    "soulPointRegen": "Soul Point Regen %",
    "stealing": "Stealing %",
    "healthRegenRaw": "Health Regen",
    "rawSpellDamage": "Spell Damage",
    "rawElementalSpellDamage": "Elemental Spell Damage",
    "rawNeutralSpellDamage": "Neutral Spell Damage",
    "rawFireSpellDamage": "Fire Spell Damage",
    "rawWaterSpellDamage": "Water Spell Damage",
    "rawAirSpellDamage": "Air Spell Damage",
    "rawThunderSpellDamage": "Thunder Spell Damage",
    "rawEarthSpellDamage": "Earth Spell Damage",
    "rawMainAttackDamage": "Main Attack Damage",
    "rawElementalMainAttackDamage": "Elemental Main Attack Damage",
    "rawNeutralMainAttackDamage": "Neutral Main Attack Damage",
    "rawFireMainAttackDamage": "Fire Main Attack Damage",
    "rawWaterMainAttackDamage": "Water Main Attack Damage ",
    "rawAirMainAttackDamage": "Air Main Attack Damage",
    "rawThunderMainAttackDamage": "Thunder Main Attack Damage",
    "rawEarthMainAttackDamage": "Earth Main Attack Damage",
    "damage": "Damage %",
    "neutralDamage": "Damage",
    "fireDamage": "Fire Damage",
    "waterDamage": "Water Damage",
    "airDamage": "Air Damage",
    "thunderDamage": "Thunder Damage",
    "earthDamage": "Earth Damage",
    "elementalDamage": "Elemental Damage %",
    "rawDamage": "Damage",
    "rawNeutralDamage": "Neutral Damage",
    "rawFireDamage": "Fire Damage",
    "rawWaterDamage": "Water Damage",
    "rawAirDamage": "Air Damage",
    "rawThunderDamage": "Thunder Damage",
    "rawEarthDamage": "Earth Damage",
    "rawElementalDamage": "Elemental Damage",
    "fireDefence": "Fire Defence %",
    "waterDefence": "Water Defence %",
    "airDefence": "Air Defence %",
    "thunderDefence": "Thunder Defence %",
    "earthDefence": "Earth Defence %",
    "elementalDefence": "Elemental Defence %",
    "1stSpellCost": "1st Spell Cost %",
    "raw1stSpellCost": "1st Spell Cost",
    "2ndSpellCost": "2nd Spell Cost %",
    "raw2ndSpellCost": "2nd Spell Cost",
    "3rdSpellCost": "3rd Spell Cost %",
    "raw3rdSpellCost": "3rd Spell Cost",
    "4thSpellCost": "4th Spell Cost %",
    "raw4thSpellCost": "4th Spell Cost",
    "sprint": "Sprint %",
    "sprintRegen": "Sprint Regen %",
    "jumpHeight": "Jump Height",
    "lootQuality": "Loot Quality %",
    "gatherXpBonus": "Gather XP Bonus %",
    "gatherSpeed": "Gather Speed %",
    "healingEfficiency": "Healing Efficiency %",
    "knockback": "Knockback %",
    "weakenEnemy": "Weaken Enemy %",
    "slowEnemy": "Slow Enemy %",
    "damageFromMobs": "Damage From Mobs %",
    "maxMana": "Max Mana %",
    "rawMaxMana": "Max Mana",
    "mainAttackRange": "Main Attack Range",
    "criticalDamageBonus": "Critical Damage Bonus"
};

const tierColors = {
    mythic: '#AA00AA',
    fabled: '#FF5555',
    legendary: '#55FFFF',
    rare: '#FF55FF',
    unique: '#c1c11f',
    common: '#FFFFFF'
};

function toggleScales(event, scaleId) {
    const scaleDetails = document.getElementById(scaleId);
    if (!scaleDetails) {
        return;
    }

    const isVisible = scaleDetails.style.display === 'block';
    scaleDetails.style.display = isVisible ? 'none' : 'block';
    event.target.textContent = isVisible ? 'Show Scales' : 'Hide Scales';
}
