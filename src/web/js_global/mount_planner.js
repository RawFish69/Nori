const MOUNT_STATS = [
    "Speed",
    "Acceleration",
    "Altitude",
    "Energy",
    "Handling",
    "Toughness",
    "Boost",
    "Training"
];

const MOUNT_MATERIAL_NAMES = {
    1: ["Copper Ingot", "Copper Gem", "Oak Plank", "Oak Paper", "Wheat String", "Wheat Grains", "Gudgeon Oil", "Gudgeon Meat"],
    10: ["Granite Ingot", "Granite Gem", "Birch Plank", "Birch Paper", "Barley String", "Barley Grains", "Trout Oil", "Trout Meat"],
    20: ["Gold Ingot", "Gold Gem", "Willow Plank", "Willow Paper", "Oat String", "Oat Grains", "Salmon Oil", "Salmon Meat"],
    30: ["Sandstone Ingot", "Sandstone Gem", "Acacia Plank", "Acacia Paper", "Malt String", "Malt Grains", "Carp Oil", "Carp Meat"],
    40: ["Iron Ingot", "Iron Gem", "Spruce Plank", "Spruce Paper", "Hops String", "Hops Grains", "Icefish Oil", "Icefish Meat"],
    50: ["Silver Ingot", "Silver Gem", "Jungle Plank", "Jungle Paper", "Rye String", "Rye Grains", "Piranha Oil", "Piranha Meat"],
    60: ["Cobalt Ingot", "Cobalt Gem", "Dark Plank", "Dark Paper", "Millet String", "Millet Grains", "Koi Oil", "Koi Meat"],
    70: ["Kanderstone Ingot", "Kanderstone Gem", "Light Plank", "Light Paper", "Decay String", "Decay Grains", "Gylia Oil", "Gylia Meat"],
    80: ["Diamond Ingot", "Diamond Gem", "Pine Plank", "Pine Paper", "Rice String", "Rice Grains", "Bass Oil", "Bass Meat"],
    90: ["Molten Ingot", "Molten Gem", "Avo Plank", "Avo Paper", "Sorghum String", "Sorghum Grains", "Molten Oil", "Molten Meat"],
    100: ["Voidstone Ingot", "Voidstone Gem", "Sky Plank", "Sky Paper", "Hemp String", "Hemp Grains", "Starfish Oil", "Starfish Meat"],
    105: ["Dernic Ingot", "Dernic Gem", "Dernic Plank", "Dernic Paper", "Dernic String", "Dernic Grains", "Dernic Oil", "Dernic Meat"],
    110: ["Titanium Ingot", "Titanium Gem", "Maple Plank", "Maple Paper", "Jute String", "Jute Grains", "Sturgeon Oil", "Sturgeon Meat"],
    115: ["Cinnabar Ingot", "Cinnabar Gem", "Redwood Plank", "Redwood Paper", "Heather String", "Heather Grains", "Mahseer Oil", "Mahseer Meat"]
};

const MOUNT_GAIN_TABLE = {
    1: [[0, 0, 0, 4, 0, 8, 0, 0], [4, 0, 0, 2, 0, 0, 0, 6], [2, 6, 0, 0, 0, 4, 0, 0], [0, 0, 8, 0, 0, 0, 4, 0], [0, 2, 0, 0, 4, 0, 6, 0], [8, 0, 4, 0, 0, 0, 0, 0], [0, 0, 2, 0, 6, 0, 0, 4], [0, 4, 0, 8, 0, 0, 0, 0]],
    10: [[0, 0, 0, 5, 0, 10, 0, 0], [5, 0, 0, 2, 0, 0, 0, 8], [2, 8, 0, 0, 0, 5, 0, 0], [0, 0, 10, 0, 0, 0, 5, 0], [0, 2, 0, 0, 5, 0, 8, 0], [10, 0, 5, 0, 0, 0, 0, 0], [0, 0, 2, 0, 8, 0, 0, 5], [0, 5, 0, 10, 0, 0, 0, 0]],
    20: [[0, 0, 0, 5, 0, 12, 0, 0], [6, 0, 0, 3, 0, 0, 0, 9], [3, 9, 0, 0, 0, 6, 0, 0], [0, 0, 12, 0, 0, 0, 5, 0], [0, 3, 0, 0, 6, 0, 9, 0], [12, 0, 5, 0, 0, 0, 0, 0], [0, 0, 3, 0, 9, 0, 0, 6], [0, 5, 0, 12, 0, 0, 0, 0]],
    30: [[0, 0, 0, 6, 0, 14, 0, 0], [6, 0, 0, 3, 0, 0, 0, 11], [3, 11, 0, 0, 0, 6, 0, 0], [0, 0, 14, 0, 0, 0, 6, 0], [0, 3, 0, 0, 6, 0, 11, 0], [14, 0, 6, 0, 0, 0, 0, 0], [0, 0, 3, 0, 11, 0, 0, 6], [0, 6, 0, 14, 0, 0, 0, 0]],
    40: [[0, 0, 0, 6, 0, 16, 0, 0], [7, 0, 0, 3, 0, 0, 0, 12], [3, 12, 0, 0, 0, 7, 0, 0], [0, 0, 16, 0, 0, 0, 6, 0], [0, 3, 0, 0, 7, 0, 12, 0], [16, 0, 6, 0, 0, 0, 0, 0], [0, 0, 3, 0, 12, 0, 0, 7], [0, 6, 0, 16, 0, 0, 0, 0]],
    50: [[0, 0, 0, 7, 0, 18, 0, 0], [8, 0, 0, 4, 0, 0, 0, 14], [4, 14, 0, 0, 0, 8, 0, 0], [0, 0, 18, 0, 0, 0, 7, 0], [0, 4, 0, 0, 8, 0, 14, 0], [18, 0, 7, 0, 0, 0, 0, 0], [0, 0, 4, 0, 14, 0, 0, 8], [0, 7, 0, 18, 0, 0, 0, 0]],
    60: [[0, 0, 0, 8, 0, 20, 0, 0], [9, 0, 0, 4, 0, 0, 0, 15], [4, 15, 0, 0, 0, 9, 0, 0], [0, 0, 20, 0, 0, 0, 8, 0], [0, 4, 0, 0, 9, 0, 15, 0], [20, 0, 8, 0, 0, 0, 0, 0], [0, 0, 4, 0, 15, 0, 0, 9], [0, 8, 0, 20, 0, 0, 0, 0]],
    70: [[0, 0, 0, 8, 0, 22, 0, 0], [10, 0, 0, 4, 0, 0, 0, 17], [4, 17, 0, 0, 0, 10, 0, 0], [0, 0, 22, 0, 0, 0, 8, 0], [0, 4, 0, 0, 10, 0, 17, 0], [22, 0, 8, 0, 0, 0, 0, 0], [0, 0, 4, 0, 17, 0, 0, 10], [0, 8, 0, 22, 0, 0, 0, 0]],
    80: [[0, 0, 0, 9, 0, 24, 0, 0], [10, 0, 0, 4, 0, 0, 0, 18], [4, 18, 0, 0, 0, 10, 0, 0], [0, 0, 24, 0, 0, 0, 9, 0], [0, 4, 0, 0, 10, 0, 18, 0], [24, 0, 9, 0, 0, 0, 0, 0], [0, 0, 4, 0, 18, 0, 0, 10], [0, 9, 0, 24, 0, 0, 0, 0]],
    90: [[0, 0, 0, 9, 0, 26, 0, 0], [11, 0, 0, 5, 0, 0, 0, 20], [5, 20, 0, 0, 0, 11, 0, 0], [0, 0, 26, 0, 0, 0, 9, 0], [0, 5, 0, 0, 11, 0, 20, 0], [26, 0, 9, 0, 0, 0, 0, 0], [0, 0, 5, 0, 20, 0, 0, 11], [0, 9, 0, 26, 0, 0, 0, 0]],
    100: [[0, 0, 0, 10, 0, 28, 0, 0], [12, 0, 0, 5, 0, 0, 0, 21], [5, 21, 0, 0, 0, 12, 0, 0], [0, 0, 28, 0, 0, 0, 10, 0], [0, 5, 0, 0, 12, 0, 21, 0], [28, 0, 10, 0, 0, 0, 0, 0], [0, 0, 5, 0, 21, 0, 0, 12], [0, 10, 0, 28, 0, 0, 0, 0]],
    105: [[0, 0, 0, 10, 0, 29, 0, 0], [12, 0, 0, 5, 0, 0, 0, 22], [5, 22, 0, 0, 0, 12, 0, 0], [0, 0, 29, 0, 0, 0, 10, 0], [0, 5, 0, 0, 12, 0, 22, 0], [29, 0, 10, 0, 0, 0, 0, 0], [0, 0, 5, 0, 22, 0, 0, 12], [0, 10, 0, 29, 0, 0, 0, 0]],
    110: [[0, 0, 0, 11, 0, 30, 0, 0], [13, 0, 0, 5, 0, 0, 0, 23], [5, 23, 0, 0, 0, 13, 0, 0], [0, 0, 30, 0, 0, 0, 11, 0], [0, 5, 0, 0, 13, 0, 23, 0], [30, 0, 11, 0, 0, 0, 0, 0], [0, 0, 5, 0, 23, 0, 0, 13], [0, 11, 0, 30, 0, 0, 0, 0]],
    115: [[0, 0, 0, 11, 0, 31, 0, 0], [13, 0, 0, 5, 0, 0, 0, 23], [5, 23, 0, 0, 0, 13, 0, 0], [0, 0, 31, 0, 0, 0, 11, 0], [0, 5, 0, 0, 13, 0, 23, 0], [31, 0, 11, 0, 0, 0, 0, 0], [0, 0, 5, 0, 23, 0, 0, 13], [0, 11, 0, 31, 0, 0, 0, 0]]
};

const MOUNT_TIERS = Object.keys(MOUNT_GAIN_TABLE).map(Number).sort((a, b) => a - b);
const DEFAULT_LIMIT = 10;
const DEFAULT_TARGET = 30;

function readInt(value, fallback) {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? Math.max(0, parsed) : fallback;
}

function blankMountRows() {
    return MOUNT_STATS.map(() => ({ level: 1, limit: DEFAULT_LIMIT, target: DEFAULT_TARGET }));
}

function feedingCostMinutes(averageLimit) {
    if (averageLimit >= 20) return 360;
    if (averageLimit >= 19) return 300;
    if (averageLimit >= 18) return 240;
    if (averageLimit >= 17) return 180;
    if (averageLimit >= 16) return 120;
    if (averageLimit >= 15) return 60;
    if (averageLimit >= 14) return 30;
    if (averageLimit >= 13) return 15;
    if (averageLimit >= 12) return 5;
    return 1;
}

function formatDuration(totalMinutes) {
    if (totalMinutes < 60) return `${totalMinutes} min`;
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    return minutes ? `${hours} hr ${minutes} min` : `${hours} hr`;
}

function usableTiersFromRows(rows) {
    const highestStatLevel = Math.max(...rows.map((row) => row.level));
    return MOUNT_TIERS.filter((tier) => tier <= highestStatLevel);
}

function selectedTierFromRows(rows) {
    const usable = usableTiersFromRows(rows);
    return usable.length ? usable[usable.length - 1] : null;
}

function inputRowsToNeeds(rows) {
    return rows.map((row) => Math.max(0, row.target - row.limit));
}

function vectorAdd(base, gains, count) {
    return base.map((value, idx) => value + gains[idx] * count);
}

function canStillReach(matrix, startIndex, current, needed, cap) {
    for (let stat = 0; stat < needed.length; stat++) {
        let possible = current[stat];
        for (let material = startIndex; material < matrix.length; material++) {
            possible += matrix[material][stat] * cap;
        }
        if (possible < needed[stat]) return false;
    }
    return true;
}

function isCovered(current, needed) {
    return current.every((value, idx) => value >= needed[idx]);
}

function overflowAmount(current, needed) {
    return current.reduce((sum, value, idx) => sum + Math.max(0, value - needed[idx]), 0);
}

function solveTier(tier, needed, cap) {
    const matrix = MOUNT_GAIN_TABLE[tier];
    let best = null;
    const counts = Array(matrix.length).fill(0);

    function search(materialIndex, used, gained) {
        if (best && used > best.total) return;
        if (isCovered(gained, needed)) {
            const waste = overflowAmount(gained, needed);
            if (!best || used < best.total || (used === best.total && waste < best.waste)) {
                best = { tier, total: used, counts: counts.slice(), gained: gained.slice(), waste };
            }
            return;
        }
        if (materialIndex >= matrix.length) return;
        if (!canStillReach(matrix, materialIndex, gained, needed, cap)) return;

        for (let amount = 0; amount <= cap; amount++) {
            counts[materialIndex] = amount;
            search(materialIndex + 1, used + amount, vectorAdd(gained, matrix[materialIndex], amount));
        }
        counts[materialIndex] = 0;
    }

    search(0, 0, Array(needed.length).fill(0));
    return best;
}

function chooseTierPlan(rows, cap) {
    return chooseTierPlanWithStrategy(rows, cap, "highest", null);
}

function chooseTierPlanWithStrategy(rows, cap, strategy, exactTier) {
    const needed = inputRowsToNeeds(rows);
    if (needed.every((value) => value === 0)) {
        return { tier: null, total: 0, counts: Array(8).fill(0), gained: Array(8).fill(0), waste: 0, alreadyDone: true };
    }

    const usable = usableTiersFromRows(rows);
    if (!usable.length) return null;

    let candidates;
    if (strategy === "exact") {
        if (!usable.includes(exactTier)) return null;
        candidates = [exactTier];
    } else if (strategy === "best") {
        candidates = usable.slice().reverse();
    } else {
        candidates = [usable[usable.length - 1]];
    }

    let best = null;
    candidates.forEach((tier) => {
        const plan = solveTier(tier, needed, cap);
        if (!plan) return;
        if (
            !best ||
            plan.total < best.total ||
            (plan.total === best.total && plan.waste < best.waste) ||
            (plan.total === best.total && plan.waste === best.waste && plan.tier > best.tier)
        ) {
            best = plan;
        }
    });
    return best;
}

function estimateFeedingTime(rows, plan) {
    if (!plan || plan.alreadyDone || plan.tier === null) return 0;
    const matrix = MOUNT_GAIN_TABLE[plan.tier];
    const gains = [];
    plan.counts.forEach((count, materialIndex) => {
        const gainTotal = matrix[materialIndex].reduce((sum, value) => sum + value, 0);
        for (let i = 0; i < count; i++) gains.push(gainTotal);
    });

    let currentTotal = rows.reduce((sum, row) => sum + row.limit, 0);
    let minutes = 0;
    gains.sort((a, b) => a - b).forEach((gain) => {
        minutes += feedingCostMinutes(Math.ceil(currentTotal / MOUNT_STATS.length));
        currentTotal += gain;
    });
    return minutes;
}

function encodeRows(rows) {
    return rows.map((row) => `${row.level}.${row.limit}.${row.target}`).join("_");
}

function decodeRows(value) {
    if (!value) return null;
    const parts = value.split("_");
    if (parts.length !== MOUNT_STATS.length) return null;
    return parts.map((part) => {
        const [level, limit, target] = part.split(".").map((piece) => readInt(piece, 0));
        return { level, limit, target: Math.max(limit, target) };
    });
}

function mountPlannerMain() {
    const grid = document.getElementById("mountStatsGrid");
    const tierStrategy = document.getElementById("tierStrategy");
    const exactTier = document.getElementById("exactTier");
    const materialCap = document.getElementById("materialCap");
    const tierHint = document.getElementById("tierHint");
    const calculatePlan = document.getElementById("calculatePlan");
    const resetPlanner = document.getElementById("resetPlanner");
    const copyPlannerLink = document.getElementById("copyPlannerLink");
    const plannerResult = document.getElementById("plannerResult");
    const resultMeta = document.getElementById("resultMeta");
    const totalMaterials = document.getElementById("totalMaterials");
    const chosenTier = document.getElementById("chosenTier");
    const estimatedTime = document.getElementById("estimatedTime");
    const shoppingList = document.getElementById("shoppingList");
    const finalStats = document.getElementById("finalStats");
    const inputs = [];

    MOUNT_TIERS.forEach((tier) => {
        const option = document.createElement("option");
        option.value = String(tier);
        option.textContent = `Level ${tier}`;
        exactTier.appendChild(option);
    });

    MOUNT_STATS.forEach((stat, idx) => {
        const row = document.createElement("div");
        row.className = "stat-row";
        row.innerHTML = `
            <div class="stat-name">${stat}</div>
            <input type="number" min="0" step="1" aria-label="${stat} level">
            <input type="number" min="0" step="1" aria-label="${stat} limit">
            <input type="number" min="0" step="1" aria-label="${stat} target">
        `;
        grid.appendChild(row);
        const [level, limit, target] = row.querySelectorAll("input");
        inputs[idx] = { level, limit, target };
    });

    function rowsFromInputs() {
        return inputs.map((input) => {
            const level = readInt(input.level.value, 1);
            const limit = readInt(input.limit.value, DEFAULT_LIMIT);
            const target = Math.max(limit, readInt(input.target.value, DEFAULT_TARGET));
            return { level, limit, target };
        });
    }

    function setRows(rows) {
        rows.forEach((row, idx) => {
            inputs[idx].level.value = row.level;
            inputs[idx].limit.value = row.limit;
            inputs[idx].target.value = row.target;
        });
        refreshTierHint();
    }

    function refreshTierHint() {
        const rows = rowsFromInputs();
        const defaultTier = selectedTierFromRows(rows);
        exactTier.disabled = tierStrategy.value !== "exact";
        tierHint.textContent = defaultTier === null
            ? "No tier available"
            : `Level ${defaultTier}`;
    }

    function validateRows(rows) {
        for (let i = 0; i < rows.length; i++) {
            if (rows[i].level > rows[i].limit || rows[i].limit > rows[i].target) {
                return `${MOUNT_STATS[i]} must satisfy Level <= Limit <= Target.`;
            }
        }
        return null;
    }

    function renderPlan(rows, plan, cap) {
        plannerResult.hidden = false;
        shoppingList.innerHTML = "";
        finalStats.innerHTML = "";

        if (!plan) {
            resultMeta.textContent = "No plan found for the selected material tier.";
            totalMaterials.textContent = "-";
            chosenTier.textContent = "-";
            estimatedTime.textContent = "-";
            shoppingList.innerHTML = "<tr><td>No matching set</td><td>-</td></tr>";
            finalStats.textContent = "Try increasing the max per material or checking the target gaps.";
            return;
        }

        if (plan.alreadyDone) {
            resultMeta.textContent = "Targets are already met.";
            totalMaterials.textContent = "0";
            chosenTier.textContent = "-";
            estimatedTime.textContent = "0 min";
        } else {
            const strategyLabel = tierStrategy.value === "best"
                ? "fewest-material strategy"
                : tierStrategy.value === "exact"
                    ? "exact-tier strategy"
                    : "highest-Level tier";
            resultMeta.textContent = `Using ${strategyLabel}, up to ${cap} of each material.`;
            totalMaterials.textContent = String(plan.total);
            chosenTier.textContent = `Level ${plan.tier}`;
            estimatedTime.textContent = formatDuration(estimateFeedingTime(rows, plan));
        }

        const materialNames = plan.tier ? MOUNT_MATERIAL_NAMES[plan.tier] : [];
        let printed = 0;
        plan.counts.forEach((count, idx) => {
            if (count <= 0) return;
            printed += 1;
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${materialNames[idx]}</td><td>${count}</td>`;
            shoppingList.appendChild(tr);
        });
        if (!printed) {
            shoppingList.innerHTML = "<tr><td>None</td><td>0</td></tr>";
        }

        rows.forEach((row, idx) => {
            const card = document.createElement("div");
            card.className = "final-stat";
            const rawFinal = row.limit + plan.gained[idx];
            const finalLimit = Math.min(row.target, rawFinal);
            const overflow = Math.max(0, rawFinal - row.target);
            card.innerHTML = `
                <span>${MOUNT_STATS[idx]}</span>
                <strong>${finalLimit} / ${row.target}</strong>
                ${overflow ? `<em class="overflow-note">${overflow} unused</em>` : ""}
            `;
            finalStats.appendChild(card);
        });
    }

    function runPlanner() {
        const rows = rowsFromInputs();
        const error = validateRows(rows);
        if (error) {
            alert(error);
            return;
        }

        const cap = Math.min(20, Math.max(1, readInt(materialCap.value, 5)));
        materialCap.value = cap;
        const plan = chooseTierPlanWithStrategy(rows, cap, tierStrategy.value, readInt(exactTier.value, MOUNT_TIERS[0]));
        renderPlan(rows, plan, cap);
    }

    function syncUrl() {
        const url = new URL(window.location.href);
        url.searchParams.set("stats", encodeRows(rowsFromInputs()));
        url.searchParams.set("cap", materialCap.value);
        url.searchParams.set("strategy", tierStrategy.value);
        url.searchParams.set("tier", exactTier.value);
        window.history.replaceState({}, "", url);
        return url.toString();
    }

    const params = new URLSearchParams(window.location.search);
    setRows(decodeRows(params.get("stats")) || blankMountRows());
    materialCap.value = params.get("cap") || "5";
    tierStrategy.value = params.get("strategy") || "highest";
    exactTier.value = params.get("tier") || "10";
    refreshTierHint();

    inputs.forEach((group) => {
        Object.values(group).forEach((input) => input.addEventListener("input", refreshTierHint));
    });
    tierStrategy.addEventListener("change", refreshTierHint);

    calculatePlan.addEventListener("click", () => {
        runPlanner();
        syncUrl();
    });

    resetPlanner.addEventListener("click", () => {
        setRows(blankMountRows());
        materialCap.value = "5";
        tierStrategy.value = "highest";
        exactTier.value = "10";
        plannerResult.hidden = true;
        syncUrl();
    });

    copyPlannerLink.addEventListener("click", async () => {
        const link = syncUrl();
        try {
            await navigator.clipboard.writeText(link);
            copyPlannerLink.textContent = "Copied";
            setTimeout(() => { copyPlannerLink.textContent = "Copy Link"; }, 1200);
        } catch (_) {
            window.prompt("Copy planner link", link);
        }
    });
}

document.addEventListener("DOMContentLoaded", mountPlannerMain);
