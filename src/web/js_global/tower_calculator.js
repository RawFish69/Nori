const towerValues = {
    damageMin: [1000, 1400, 1800, 2200, 2600, 3000, 3400, 3800, 4200, 4600, 5000, 5400],
    damageMax: [1500, 2100, 2700, 3300, 3900, 4500, 5100, 5700, 6300, 6900, 7500, 8100],
    attack: [0.5, 0.75, 1.0, 1.25, 1.6, 2.0, 2.5, 3.0, 3.6, 3.8, 4.2, 4.7],
    health: [300000, 450000, 600000, 750000, 960000, 1200000, 1500000, 1860000, 2220000, 2580000, 2940000, 3300000],
    defense: [0.1, 0.4, 0.55, 0.625, 0.7, 0.75, 0.79, 0.82, 0.84, 0.86, 0.88, 0.9]
};

const difficultyNames = ["Very Low", "Low", "Medium", "High", "Very High"];

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("towerCalculator");
    if (!form) return;

    const modeInputs = Array.from(document.querySelectorAll('input[name="towerMode"]'));
    const externalsField = document.getElementById("externalsField");
    const resultPanel = document.getElementById("towerResult");
    const copyButton = document.getElementById("copyTowerLink");
    const resetButton = document.getElementById("resetTower");

    modeInputs.forEach(input => {
        input.addEventListener("change", () => {
            syncModeVisibility();
            calculateAndRender();
        });
    });

    form.addEventListener("input", calculateAndRender);
    copyButton.addEventListener("click", copyShareLink);
    resetButton.addEventListener("click", () => {
        form.reset();
        syncModeVisibility();
        calculateAndRender();
    });

    hydrateFromUrl();
    syncModeVisibility();
    calculateAndRender();

    function getNumber(id) {
        const input = document.getElementById(id);
        const min = Number(input.min || 0);
        const max = Number(input.max || 999);
        const value = Number(input.value);
        return Math.min(max, Math.max(min, Number.isFinite(value) ? value : min));
    }

    function getMode() {
        return document.querySelector('input[name="towerMode"]:checked')?.value || "regular";
    }

    function syncModeVisibility() {
        const isHq = getMode() === "hq";
        externalsField.hidden = !isHq;
        document.getElementById("externals").disabled = !isHq;
    }

    function calculateAndRender() {
        const values = readValues();
        const stats = calculateTower(values);
        const tier = calculateTier(values);

        renderSummary(values, stats, tier);
        renderDetails(values, stats, tier);
        updateUrl(values);
        resultPanel.hidden = false;
    }

    function readValues() {
        return {
            mode: getMode(),
            links: getNumber("links"),
            externals: getNumber("externals"),
            damage: getNumber("damage"),
            attack: getNumber("attack"),
            health: getNumber("health"),
            defense: getNumber("defense"),
            aura: getNumber("aura"),
            volley: getNumber("volley")
        };
    }

    function calculateTower(values) {
        const linkMultiplier = 1 + 0.3 * values.links;
        const hqMultiplier = values.mode === "hq" ? 1.5 + 0.25 * values.externals : 1;
        const multiplier = linkMultiplier * hqMultiplier;
        const minDamage = towerValues.damageMin[values.damage] * multiplier;
        const maxDamage = towerValues.damageMax[values.damage] * multiplier;
        const averageDamage = (minDamage + maxDamage) / 2;
        const attackRate = towerValues.attack[values.attack];
        const health = towerValues.health[values.health] * multiplier;
        const defense = towerValues.defense[values.defense];
        const ehp = health / (1 - defense);

        return {
            minDamage,
            maxDamage,
            averageDamage,
            attackRate,
            dps: averageDamage * attackRate,
            health,
            defense,
            ehp,
            linkMultiplier,
            hqMultiplier
        };
    }

    function calculateTier(values) {
        const rating = values.damage + values.attack + values.health + values.defense
            + values.aura + values.volley
            + (values.aura > 0 ? 5 : 0)
            + (values.volley > 0 ? 3 : 0);
        const baseTier = 1
            + (rating > 5 ? 1 : 0)
            + (rating > 18 ? 1 : 0)
            + (rating > 30 ? 1 : 0)
            + (rating > 48 ? 1 : 0);
        const tier = Math.min(5, baseTier + (values.mode === "hq" ? 1 : 0));

        return {
            rating,
            tier,
            label: difficultyNames[tier - 1]
        };
    }

    function renderSummary(values, stats, tier) {
        setText("summaryDamage", `${formatNumber(stats.minDamage)} - ${formatNumber(stats.maxDamage)}`);
        setText("summaryDps", formatNumber(stats.dps, 2));
        setText("summaryHealth", formatNumber(stats.health));
        setText("summaryTier", `${tier.tier} / ${tier.label}`);
        setText("summaryMode", values.mode === "hq" ? "HQ Tower" : "Regular Tower");
        setText("summaryInputs", buildInputSummary(values));
    }

    function renderDetails(values, stats, tier) {
        const rows = [
            ["Average hit", formatNumber(stats.averageDamage, 2)],
            ["Attack rate", `${formatNumber(stats.attackRate, 2)}x per second`],
            ["Effective HP", `${formatNumber(stats.ehp)} (${formatNumber(stats.ehp / 1000000, 2)}M)`],
            ["Defense", `${formatNumber(stats.defense * 100, 1)}%`],
            ["Rating", `${tier.rating} points`],
            ["Multiplier", `${formatNumber(stats.linkMultiplier, 2)}x links${values.mode === "hq" ? `, ${formatNumber(stats.hqMultiplier, 2)}x HQ` : ""}`]
        ];

        document.getElementById("detailRows").innerHTML = rows.map(([label, value]) => `
            <div class="detail-row">
                <span>${label}</span>
                <strong>${value}</strong>
            </div>
        `).join("");
    }

    function buildInputSummary(values) {
        const base = `Links ${values.links}, upgrades ${values.damage}/${values.attack}/${values.health}/${values.defense}`;
        return values.mode === "hq" ? `${base}, externals ${values.externals}` : base;
    }

    function setText(id, text) {
        document.getElementById(id).textContent = text;
    }

    function formatNumber(value, decimals = 0) {
        return Number(value).toLocaleString(undefined, {
            maximumFractionDigits: decimals,
            minimumFractionDigits: decimals
        });
    }

    function updateUrl(values) {
        const params = new URLSearchParams({
            mode: values.mode,
            links: values.links,
            externals: values.externals,
            damage: values.damage,
            attack: values.attack,
            health: values.health,
            defense: values.defense,
            aura: values.aura,
            volley: values.volley
        });
        history.replaceState(null, "", `${location.pathname}?${params.toString()}`);
    }

    function hydrateFromUrl() {
        const params = new URLSearchParams(location.search);
        const mode = params.get("mode");
        if (mode === "hq" || mode === "regular") {
            document.querySelector(`input[name="towerMode"][value="${mode}"]`).checked = true;
        }

        ["links", "externals", "damage", "attack", "health", "defense", "aura", "volley"].forEach(id => {
            const input = document.getElementById(id);
            const value = params.get(id);
            if (value !== null) input.value = value;
        });
    }

    async function copyShareLink() {
        try {
            await navigator.clipboard.writeText(location.href);
            copyButton.textContent = "Copied";
        } catch (error) {
            copyButton.textContent = "Copy failed";
        }

        window.setTimeout(() => {
            copyButton.textContent = "Copy Link";
        }, 1400);
    }
});
