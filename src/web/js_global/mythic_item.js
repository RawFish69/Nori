document.addEventListener('DOMContentLoaded', async function() {
    const checkboxes = document.querySelectorAll('.item-filter');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', handleCheckboxChange);
    });
    await fetchAndRenderItems();
});

async function fetchAndRenderItems() {
    try {
        const response = await fetch('https://nori.fish/api/item/mythic');
        if (!response.ok) {
            throw new Error('Failed to fetch item data');
        }
        const data = await response.json();
        renderItems(data);
    } catch (error) {
        console.error(error);
        alert('Failed to fetch item data');
    }
}

function handleCheckboxChange() {
    const checkboxes = document.querySelectorAll('.item-filter');
    const checkedCheckboxes = Array.from(checkboxes).filter(cb => cb.checked);

    if (checkedCheckboxes.length === 0) {
        this.checked = true;
        alert('At least one item type must be selected.');
    } else {
        fetchAndRenderItems();
    }
}

function getSelectedTypes() {
    const checkboxes = document.querySelectorAll('.item-filter:checked');
    const selectedTypes = Array.from(checkboxes).map(cb => cb.value);
    if (selectedTypes.includes('armor')) {
        selectedTypes.push('helmet', 'chestplate', 'leggings', 'boots');
    }
    return selectedTypes.flat();
}

function renderItems(data) {
    const itemCardsContainer = document.getElementById('item-cards-container');
    itemCardsContainer.innerHTML = '';

    const selectedTypes = getSelectedTypes();

    const rankedItems = data.ranked;
    const weights = data.weights;

    for (const itemName in rankedItems) {
        const scales = rankedItems[itemName];
        for (const scale in scales) {
            const itemStats = scales[scale].stats;
            if (!itemStats || !itemStats[itemName]) continue; 
            const itemType = itemStats.item_type;
            if (selectedTypes.includes(itemType)) {
                const itemData = itemStats[itemName];
                const rateData = itemStats.rate;
                const owner = scales[scale].owner;
                const weight = itemStats.weight;
                const shiny = itemStats.shiny;
                const icon = itemStats.icon || `../../../resources/${itemStats.item_type}.png`;
                const tier = itemStats.item_tier || 'common';
                const tierColor = tierColors[tier];

                const overallRating = rateData ? getOverallRating(rateData) : 'N/A';

                const itemCard = document.createElement('div');
                itemCard.classList.add('item-card');

                itemCard.innerHTML = `
                    <img src="${icon}" alt="${itemName}" class="item-icon">
                    <h3 style="color: ${tierColor};">${itemName} <span style="color:${getRateColor(overallRating)}">[${overallRating}%]</span></h3>
                    <p class="item-scale">Scale: <span style="color: #DDA0DD;">${scale}</span> <span style="color:${getRateColor(weight)}">[${weight}%]</span></p>
                    <p class="item-owner">Owner: <span style="color: gold;">${owner}</span></p>
                    ${shiny ? `<p class="shiny-value"><img src="../../../resources/shiny.png" class="shiny-icon" alt="Shiny"> ${shiny}</p>` : ''}
                    <div class="item-stats">
                        ${renderStats(itemData, rateData)}
                    </div>
                    <button class="show-scales-btn" onclick="toggleScales(event, '${itemName}')">Show Scales</button>
                    <div class="scale-details" id="scales-${itemName}">${renderScales(weights[itemName])}</div>
                `;

                itemCardsContainer.appendChild(itemCard);
            }
        }
    }
}

function renderStats(stats, rateData) {
    let statsHtml = '';

    for (const stat in stats) {
        if (stat !== 'icon' && stat !== 'item_type' && stat !== 'shiny' && stat !== 'item_tier' && stats[stat] !== null) {
            statsHtml += `
                <div class="stat-row">
                    <span class="stat-value">${stats[stat]}</span>
                    <span class="stat-name">${mapping[stat]}</span>
                    ${rateData[stat] !== undefined ? `<span class="stat-rate" style="color:${getRateColor(rateData[stat])}">[${rateData[stat]}%]</span>` : ''}
                </div>
            `;
        }
    }

    return statsHtml;
}

function renderScales(scales) {
    let scalesHtml = '';

    for (const scale in scales) {
        scalesHtml += `<div class="scale-row"><strong>${scale} Scale:</strong></div>`;
        for (const stat in scales[scale]) {
            scalesHtml += `<div><span>${mapping[stat] || stat}: <span style="color:${getRateColor(scales[scale][stat])}">${scales[scale][stat]}%</span></span></div>`;
        }
        scalesHtml += `<div class="scale-spacing"></div>`;
    }

    return scalesHtml;
}

function getOverallRating(rateData) {
    const values = Object.values(rateData);
    const total = values.reduce((sum, value) => sum + value, 0);
    return (total / values.length).toFixed(2);
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
    "elementalDefence": "Elemental Defence %",
    "damageFromMobs": "Damage From Mobs %",
    "maxMana": "Max Mana %",
    "rawMaxMana": "Max Mana",
    "mainAttackRange": "Main Attack Range",
    "criticalDamageBonus": "Critical Damage Bonus"
 };
 

const tierColors = {
    "mythic": "#AA00AA",
    "fabled": "#FF5555",
    "legendary": "#55FFFF",
    "rare": "#FF55FF",
    "unique": "#c1c11f",
    "common": "#FFFFFF"
};

function toggleScales(event, itemName) {
    const scaleDetails = document.getElementById(`scales-${itemName}`);
    const isVisible = scaleDetails.style.display === 'block';

    const allScales = document.querySelectorAll('.scale-details');
    allScales.forEach(scale => scale.style.display = 'none');

    const allButtons = document.querySelectorAll('.show-scales-btn');
    allButtons.forEach(button => button.textContent = 'Show Scales');

    if (isVisible) {
        scaleDetails.style.display = 'none';
        event.target.textContent = 'Show Scales';
    } else {
        scaleDetails.style.display = 'block';
        event.target.textContent = 'Hide Scales';
    }
}
