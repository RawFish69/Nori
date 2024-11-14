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
    "elementalDefense": "Elemental Defence %",
    "damageFromMobs": "Damage From Mobs %",
    "maxMana": "Max Mana"
};

const tierColors = {
    "mythic": "#AA00AA",
    "fabled": "#FF5555",
    "legendary": "#55FFFF",
    "rare": "#FF55FF",
    "unique": "#c1c11f",
    "common": "#FFFFFF"
};

let items = [];

document.addEventListener('DOMContentLoaded', async function() {
    await fetchItems();
});

async function fetchItems() {
    try {
        const response = await fetch('https://nori.fish/api/item/list');
        if (!response.ok) {
            throw new Error('Failed to fetch item list');
        }
        const data = await response.json();
        items = data.items;
    } catch (error) {
        console.error(error);
        alert('Failed to fetch item list');
    }
}

function showSuggestions(value) {
    const suggestionsContainer = document.getElementById('suggestions-container');
    suggestionsContainer.innerHTML = '';

    if (value.length === 0) {
        return;
    }

    const filteredItems = items.filter(item => item.toLowerCase().includes(value.toLowerCase()));

    filteredItems.forEach(item => {
        const suggestionElement = document.createElement('div');
        suggestionElement.textContent = item;
        suggestionElement.onclick = () => selectSuggestion(item);
        suggestionsContainer.appendChild(suggestionElement);
    });
}

function selectSuggestion(value) {
    document.getElementById('item-name').value = value;
    document.getElementById('suggestions-container').innerHTML = '';
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

function displayResults(result) {
    const resultsContainer = document.getElementById("analysis-results");
    resultsContainer.innerHTML = "";

    if (!result) {
        resultsContainer.innerHTML = "<p class='no-results'>No analysis result found</p>";
        return;
    }

    const itemName = Object.keys(result)[0];
    const itemData = result[itemName];
    const rateData = result.rate || {};
    const shiny = result.shiny;
    const icon = result.icon || `${result.item_type}.png`;
    const tier = result.item_tier || "common";
    const tierColor = tierColors[tier];

    const overallRating = rateData ? getOverallRating(rateData) : "N/A";

    const itemCardContainer = document.createElement("div");
    itemCardContainer.classList.add("item-card-container");

    const itemElement = document.createElement("div");
    itemElement.classList.add("item-card");
    itemElement.innerHTML = `
        <img src="${icon}" alt="${itemName}" class="item-icon">
        <h3 style="color: ${tierColor};">${itemName} <span style="color:${getRateColor(overallRating)}">[${overallRating}%]</span></h3>
    `;

    if (shiny) {
        const shinyElement = document.createElement("p");
        shinyElement.classList.add("shiny-value");
        shinyElement.innerHTML = `<img src="../../../resources/shiny.png" class="shiny-icon" alt="Shiny"> ${shiny}`;
        itemElement.appendChild(shinyElement);
    }

    const statsContainer = document.createElement("div");
    statsContainer.classList.add("stats-container");

    for (const stat in itemData) {
        if (stat !== "icon" && stat !== "item_type" && stat !== "scales" && stat !== "shiny" && stat !== "item_tier" && itemData[stat] !== null) {
            const statElement = document.createElement("div");
            statElement.classList.add("stat-row");

            if (rateData[stat] !== undefined) {
                statElement.innerHTML = `
                    <span class="stat-value">${itemData[stat]}</span>
                    <span class="stat-name">${mapping[stat]}</span>
                    <span class="stat-rate" style="color:${getRateColor(rateData[stat])}">[${rateData[stat]}%]</span>
                `;
            } else {
                statElement.innerHTML = `
                    <span class="stat-value">${itemData[stat]}</span>
                    <span class="stat-name">${mapping[stat]}</span>
                `;
            }

            statsContainer.appendChild(statElement);
        }
    }

    itemElement.appendChild(statsContainer);
    itemCardContainer.appendChild(itemElement);

    resultsContainer.appendChild(itemCardContainer);
}