document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("item-analysis-form");
    const resultsContainer = document.getElementById("analysis-results");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const encodedItem = document.getElementById("encoded-item").value.trim();

        if (encodedItem === "") {
            resultsContainer.innerHTML = "<p class='search-warning'>Empty Input, enter an encoded item to get started.</p>";
            return;
        }

        try {
            const response = await fetch("https://nori.fish/api/item/analysis", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ encoded_item: encodedItem })
            });

            const data = await response.json();
            displayResults(data.Result);
        } catch (error) {
            console.error("Error analyzing item:", error);
            resultsContainer.innerHTML = "<p class='search-warning'>An error occurred. Please try again later.</p>";
        }
    });

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

    function displayResults(result) {
        const resultsContainer = document.getElementById("analysis-results");
        resultsContainer.innerHTML = "";
        if (!result) {
            resultsContainer.innerHTML = "<p class='no-results'>Error while analyzing item.</p>";
    
            return;
        }
    
        const itemName = Object.keys(result)[0];
        const itemData = result[itemName];
        const rateData = result.rate;
        const scales = result.scales || {};
        const weights = result.weights || {};
        const shiny = result.shiny;
        const icon = result.icon || `../../../resources/${result.item_type}.png`;
        const tier = result.item_tier || "common";
        const tierColor = tierColors[tier];
    
        const overallRating = getOverallRating(rateData);
    
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
                statElement.innerHTML = `
                    <span class="stat-value">${itemData[stat]}</span>
                    <span class="stat-name">${mapping[stat]}</span>
                    <span class="stat-rate" style="color:${getRateColor(rateData[stat])}">[${rateData[stat]}%]</span>
                `;
                statsContainer.appendChild(statElement);
            }
        }
    
        itemElement.appendChild(statsContainer);
        itemCardContainer.appendChild(itemElement);
    
        if (Object.keys(scales).length > 0 && Object.keys(weights).length > 0) {
            const scalesContainer = document.createElement("div");
            scalesContainer.classList.add("scales-container");
    
            const sortedScales = Object.entries(weights).sort((a, b) => b[1] - a[1]);
    
            for (const [scale, weight] of sortedScales) {
                const scaleItem = document.createElement("div");
                scaleItem.classList.add("scale-item");
                scaleItem.innerHTML = `<span style="font-weight: bold">${scale} Scale :</span> <span style="color:${getRateColor(weight)}">${weight}%</span>`;
                scaleItem.addEventListener("click", () => {
                    const content = document.getElementById(`scale-content-${scale}`);
                    content.classList.toggle("show");
                });
                scalesContainer.appendChild(scaleItem);
    
                const scaleContentElement = document.createElement("div");
                scaleContentElement.classList.add("scale-content");
                scaleContentElement.id = `scale-content-${scale}`;
                scaleContentElement.innerHTML = `<strong>${scale} Scale Weight Distribution</strong><br>`;
                for (const stat in scales[scale]) {
                    if (scales[scale][stat] !== null) {
                        const scaleStatElement = document.createElement("p");
                        scaleStatElement.innerHTML = `${mapping[stat]}: ${scales[scale][stat]}%`;
                        scaleContentElement.appendChild(scaleStatElement);
                    }
                }
                scalesContainer.appendChild(scaleContentElement);
            }
    
            itemCardContainer.appendChild(scalesContainer);
        }
    
        resultsContainer.appendChild(itemCardContainer);
    
        const noteElement = document.createElement("p");
        noteElement.classList.add("note");
        noteElement.innerHTML = "<i>The weight scale measures the effectiveness of an item, an item may have multiple scales.</i>";
        resultsContainer.appendChild(noteElement);
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
});
