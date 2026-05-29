const RAID_DISPLAY_ORDER = ["TNA", "TCC", "NOL", "NOG", "TWP"];

const RAID_FULL_NAMES = {
    "TNA": "The Nameless Anomaly",
    "TCC": "The Canyon Colossus",
    "NOL": "Orphion's Nexus of Light",
    "NOG": "Nest of the Grootslangs",
    "TWP": "The Wartorn Palace"
};
const ASPECT_TIERS = ["Mythic", "Fabled", "Legendary"];
const ITEM_TIERS = ["Mythic", "Fabled", "Legendary", "Rare", "Unique", "Misc"];
const SOURCE_MODES = ["all", "aspects", "items"];
let gambitRefreshCountdownTimer = null;

const ASPECT_GLYPH_MAP = {
    "\ue000": "[Air]",
    "\ue001": "[Earth]",
    "\ue002": "[Fire]",
    "\ue003": "[Thunder]",
    "\ue004": "[Water]",
    "\ue005": "[Damage]",
    "\ue01b": "[Total Damage]",
    "\ue01c": "[Range]",
    "\ue01d": "[Area]",
    "\ue01e": "[Stat]",
    "\ue01f": "[Duration]"
};

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
    "ingredient bag 1": "crafter_varied.png",
    "ingredient bag 2": "crafter_packed.png",
    "ingredient bag 3": "crafter_stuffed.png",
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

const MYTHIC_ASPECT_GIF_FALLBACK_BY_ICON = {
    "warrior_aspect.png": "aspect_warrior.gif",
    "mage_aspect.png": "aspect_mage.gif",
    "archer_aspect.png": "aspect_archer.gif",
    "assassin_aspect.png": "aspect_assassin.gif",
    "shaman_aspect.png": "aspect_shaman.gif",
    "static_warrior.png": "aspect_warrior.gif",
    "static_mage.png": "aspect_mage.gif",
    "static_archer.png": "aspect_archer.gif",
    "static_assassin.png": "aspect_assassin.gif",
    "static_shaman.png": "aspect_shaman.gif"
};

document.addEventListener("DOMContentLoaded", () => {
    const tierFilters = document.getElementById("lootpool-filters");
    const sourceFilters = document.getElementById("source-filters");
    if (tierFilters) tierFilters.style.display = "none";
    if (sourceFilters) sourceFilters.style.display = "none";

    const lastKnownTimestamp = Number(localStorage.getItem("raid_pool_last_timestamp") || 0);

    fetch("https://nori.fish/api/raids", {
        method: "GET",
        credentials: "omit"
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.json();
        })
        .then((data) => {
            const normalized = normalizeRaidPayload(data);
            const currentTimestamp = Math.floor(Date.now() / 1000);
            const nextUpdateTimestamp = normalized.timestamp + 604800;

            updateLootpoolTitle(normalized.timestamp);
            renderGlobalGambits(normalized);

            if (currentTimestamp > nextUpdateTimestamp && normalized.timestamp === lastKnownTimestamp) {
                displayUpdatingMessage();
            } else {
                displayRaidLootpool(normalized);
                if (currentTimestamp <= nextUpdateTimestamp) {
                    startCountdown(nextUpdateTimestamp - currentTimestamp);
                } else {
                    displayPastDueNotice(nextUpdateTimestamp);
                }
            }

            localStorage.setItem("raid_pool_last_timestamp", String(normalized.timestamp));
            if (tierFilters) tierFilters.style.display = "flex";
            if (sourceFilters) sourceFilters.style.display = "flex";
            setupTierFilters();
            setupSourceFilters();
            filterLootpool();
        })
        .catch((error) => {
            console.error("Error fetching raid pool:", error);
            const title = document.getElementById("lootpool-title");
            if (title) title.textContent = "Failed to load raid lootpool data.";
        });
});

function normalizeRaidPayload(data) {
    const source = data && typeof data === "object" ? data : {};
    const nowTs = Math.floor(Date.now() / 1000);

    const aspectsRaw = source.Aspects && typeof source.Aspects === "object" ? source.Aspects : {};
    const itemsRaw = source.Items && typeof source.Items === "object" ? source.Items : {};
    const gambitsRaw = source.Gambits && typeof source.Gambits === "object" && !Array.isArray(source.Gambits)
        ? source.Gambits
        : {};

    const aspectsLootRaw = aspectsRaw.Loot && typeof aspectsRaw.Loot === "object" ? aspectsRaw.Loot : aspectsRaw;
    const itemLootRaw = itemsRaw.Loot && typeof itemsRaw.Loot === "object" ? itemsRaw.Loot : itemsRaw;
    const aspectsLoot = aspectsLootRaw && typeof aspectsLootRaw === "object" ? aspectsLootRaw : {};
    const itemLoot = itemLootRaw && typeof itemLootRaw === "object" ? itemLootRaw : {};

    let rawGambitEntries = [];
    if (Array.isArray(source.Gambits)) {
        rawGambitEntries = source.Gambits;
    } else if (Array.isArray(gambitsRaw.Entries)) {
        rawGambitEntries = gambitsRaw.Entries;
    } else {
        rawGambitEntries = gambitsRaw.Loot;
    }
    const gambitLoot = normalizeGambitLoot(rawGambitEntries);

    const rawGambitRotation = source.GambitRotation && typeof source.GambitRotation === "object"
        ? source.GambitRotation
        : gambitsRaw.Rotation;
    const gambitRotation = normalizeSharedGambitRotation(rawGambitRotation);

    const directIcons = source.Icons && typeof source.Icons === "object" ? source.Icons : {};
    const sharedIcons = source.Icon && typeof source.Icon === "object" ? source.Icon : {};
    const aspectIcons = aspectsRaw.Icon && typeof aspectsRaw.Icon === "object" ? aspectsRaw.Icon : {};
    const itemIcons = itemsRaw.Icon && typeof itemsRaw.Icon === "object" ? itemsRaw.Icon : {};
    const icons = { ...sharedIcons, ...itemIcons, ...aspectIcons, ...directIcons };

    const descriptions = source.AspectDescriptions && typeof source.AspectDescriptions === "object"
        ? source.AspectDescriptions
        : (
            aspectsRaw.Descriptions && typeof aspectsRaw.Descriptions === "object"
                ? aspectsRaw.Descriptions
                : {}
        );

    const timestamp = Number.isInteger(source.Timestamp) ? source.Timestamp : nowTs;
    const rotationStart = Number.isInteger(source.GambitRotationStart)
        ? source.GambitRotationStart
        : Number.isInteger(gambitsRaw.RotationStart)
            ? gambitsRaw.RotationStart
        : gambitRotation.rotation_start;
    const rotationEnd = Number.isInteger(source.GambitRotationEnd)
        ? source.GambitRotationEnd
        : Number.isInteger(gambitsRaw.RotationEnd)
            ? gambitsRaw.RotationEnd
        : gambitRotation.rotation_end;
    const refreshedAt = Number.isInteger(source.GambitRefreshedAt)
        ? source.GambitRefreshedAt
        : (Number.isInteger(gambitsRaw.RefreshedAt) ? gambitsRaw.RefreshedAt : null);

    return {
        aspectsLoot,
        itemLoot,
        gambitLoot,
        gambitRotation,
        gambitRotationStart: rotationStart,
        gambitRotationEnd: rotationEnd,
        gambitRefreshedAt: refreshedAt,
        icons,
        descriptions,
        timestamp
    };
}

function normalizeGambitEntries(entries) {
    if (!Array.isArray(entries)) return [];
    const out = [];
    entries.forEach((entry) => {
        if (!entry || typeof entry !== "object") return;
        const name = typeof entry.name === "string" ? entry.name.trim() : "";
        if (!name) return;
        const description = typeof entry.description === "string" ? entry.description.trim() : "";
        const confidence = Number.isFinite(entry.confidence) ? entry.confidence : null;
        out.push({ name, description, confidence });
    });
    return out;
}

function normalizeGambitLoot(rawLoot) {
    // New shape: shared gambit entries list.
    const shared = normalizeGambitEntries(rawLoot);
    if (shared.length) return shared;

    // Backward compatibility: old shape was {raid: [entries]}.
    if (rawLoot && typeof rawLoot === "object") {
        for (const raid of RAID_DISPLAY_ORDER) {
            const entries = normalizeGambitEntries(rawLoot[raid]);
            if (entries.length) return entries;
        }
        for (const value of Object.values(rawLoot)) {
            const entries = normalizeGambitEntries(value);
            if (entries.length) return entries;
        }
    }
    return [];
}

function normalizeSharedGambitRotation(rawRotation) {
    const fallback = { rotation_start: null, rotation_end: null };
    if (!rawRotation || typeof rawRotation !== "object") return fallback;
    if (Number.isInteger(rawRotation.rotation_start) || Number.isInteger(rawRotation.rotation_end)) {
        return {
            rotation_start: Number.isInteger(rawRotation.rotation_start) ? rawRotation.rotation_start : null,
            rotation_end: Number.isInteger(rawRotation.rotation_end) ? rawRotation.rotation_end : null
        };
    }
    // Backward compatibility: old shape was {raid: {rotation_start, rotation_end}}.
    for (const raid of RAID_DISPLAY_ORDER) {
        const regionRotation = rawRotation[raid];
        if (!regionRotation || typeof regionRotation !== "object") continue;
        return {
            rotation_start: Number.isInteger(regionRotation.rotation_start) ? regionRotation.rotation_start : null,
            rotation_end: Number.isInteger(regionRotation.rotation_end) ? regionRotation.rotation_end : null
        };
    }
    return fallback;
}

function updateLootpoolTitle(timestamp) {
    const date = new Date(timestamp * 1000);
    const formattedDate = date.toISOString().split("T")[0];
    const title = document.getElementById("lootpool-title");
    if (!title) return;
    title.textContent = "";

    const gifImage = document.createElement("img");
    gifImage.src = "../../resources/aspect.gif";
    gifImage.alt = "Aspect GIF";
    gifImage.classList.add("title-icon");

    const textNode = document.createTextNode(`Raid Lootpool Starting ${formattedDate}`);
    title.appendChild(gifImage);
    title.appendChild(textNode);
}

function displayUpdatingMessage() {
    const title = document.getElementById("lootpool-title");
    if (!title) return;
    const msg = document.createElement("div");
    msg.style.textAlign = "center";
    msg.style.fontSize = "1.1em";
    msg.style.marginTop = "0.4rem";
    msg.innerHTML = "We are updating this week's new raid pool. Join <a href=\"https://discord.gg/eDssA6Jbwd\" target=\"_blank\">support server</a> for live updates.";
    title.appendChild(msg);
}

function displayPastDueNotice(nextUpdateTimestamp) {
    const container = document.getElementById("countdown-container");
    if (!container) return;
    container.innerHTML = `<div id="countdown-label">Update overdue since ${new Date(nextUpdateTimestamp * 1000).toISOString().split("T")[0]}</div>`;
}

function stopGambitRefreshCountdown() {
    if (gambitRefreshCountdownTimer) {
        clearInterval(gambitRefreshCountdownTimer);
        gambitRefreshCountdownTimer = null;
    }
}

function formatCountdownLabel(totalSeconds) {
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    const parts = [];
    if (days > 0) parts.push(`${days}d`);
    parts.push(`${hours}h`);
    parts.push(`${minutes}m`);
    parts.push(`${seconds}s`);
    return parts.join(" ");
}

function startGambitRefreshCountdown(endTs, targetEl) {
    stopGambitRefreshCountdown();
    if (!targetEl || !Number.isInteger(endTs)) {
        return;
    }
    const update = () => {
        const nowTs = Math.floor(Date.now() / 1000);
        const remaining = endTs - nowTs;
        if (remaining <= 0) {
            targetEl.textContent = "refreshing now";
            return;
        }
        targetEl.textContent = formatCountdownLabel(remaining);
    };
    update();
    gambitRefreshCountdownTimer = setInterval(update, 1000);
}

function renderGlobalGambits(payload) {
    const container = document.getElementById("gambit-overview");
    if (!container) return;
    stopGambitRefreshCountdown();
    container.innerHTML = "";

    const card = document.createElement("div");
    card.classList.add("gambit-overview-card");

    const title = document.createElement("div");
    title.classList.add("gambit-overview-title");
    title.textContent = "Daily gambits (all raids)";
    card.appendChild(title);

    const meta = document.createElement("p");
    meta.classList.add("gambit-meta", "gambit-refresh-meta");
    if (Number.isInteger(payload.gambitRotationEnd)) {
        const label = document.createElement("span");
        label.classList.add("gambit-refresh-label");
        label.textContent = "Refresh in ";
        const timer = document.createElement("span");
        timer.classList.add("gambit-refresh-timer");
        meta.appendChild(label);
        meta.appendChild(timer);
        card.appendChild(meta);
        startGambitRefreshCountdown(payload.gambitRotationEnd, timer);
    } else {
        meta.textContent = "Refresh timer unavailable.";
        card.appendChild(meta);
    }

    const entries = Array.isArray(payload.gambitLoot) ? payload.gambitLoot : [];
    if (!entries.length) {
        const empty = document.createElement("p");
        empty.classList.add("empty-raid-text");
        empty.textContent = "No gambits published yet.";
        card.appendChild(empty);
        container.appendChild(card);
        return;
    }

    const list = document.createElement("ul");
    list.classList.add("gambit-list", "gambit-overview-list");
    entries.forEach((entry) => {
        if (!entry || typeof entry !== "object") return;
        const name = typeof entry.name === "string" ? entry.name.trim() : "";
        if (!name) return;
        const description = typeof entry.description === "string" ? entry.description.trim() : "";
        const li = document.createElement("li");
        li.classList.add("gambit-entry");

        const nameLine = document.createElement("div");
        nameLine.classList.add("gambit-name");
        nameLine.textContent = name;
        li.appendChild(nameLine);

        if (description) {
            const descLine = document.createElement("div");
            descLine.classList.add("gambit-description");
            descLine.textContent = description;
            li.appendChild(descLine);
        }
        list.appendChild(li);
    });
    card.appendChild(list);
    container.appendChild(card);
}

function displayRaidLootpool(payload) {
    const container = document.getElementById("lootpool");
    if (!container) return;
    container.innerHTML = "";

    const raidSet = new Set([
        ...Object.keys(payload.aspectsLoot || {}),
        ...Object.keys(payload.itemLoot || {})
    ]);
    const raids = [
        ...RAID_DISPLAY_ORDER.filter((raid) => raidSet.has(raid)),
        ...Array.from(raidSet).filter((raid) => !RAID_DISPLAY_ORDER.includes(raid))
    ];

    raids.forEach((raid) => {
        const card = document.createElement("div");
        card.classList.add("lootpool-card", "active");

        const title = document.createElement("div");
        title.classList.add("region-title");
        title.textContent = `${RAID_FULL_NAMES[raid] || raid} Raid Pool`;
        title.addEventListener("click", () => card.classList.toggle("active"));
        card.appendChild(title);

        const content = document.createElement("div");
        content.classList.add("lootpool-card-content");

        const aspectsSection = buildSourceSection({
            sourceKey: "aspect",
            sectionTitle: "Aspect Lootpool",
            tiers: ASPECT_TIERS,
            raidData: payload.aspectsLoot[raid] || {},
            icons: payload.icons,
            descriptions: payload.descriptions,
            includeDescriptions: true
        });

        const itemSection = buildSourceSection({
            sourceKey: "item",
            sectionTitle: "Raid Item Lootpool",
            tiers: ITEM_TIERS,
            raidData: payload.itemLoot[raid] || {},
            icons: payload.icons,
            descriptions: {},
            includeDescriptions: false
        });

        content.appendChild(aspectsSection);
        content.appendChild(itemSection);
        card.appendChild(content);
        container.appendChild(card);
    });
}

function buildSourceSection(options) {
    const {
        sourceKey,
        sectionTitle,
        tiers,
        raidData,
        icons,
        descriptions,
        includeDescriptions
    } = options;

    const section = document.createElement("div");
    section.classList.add("raid-source-section", `${sourceKey}-section`);
    section.dataset.source = sourceKey;

    const title = document.createElement("div");
    title.classList.add("source-section-title");
    title.textContent = sectionTitle;
    section.appendChild(title);

    let hasEntries = false;

    tiers.forEach((tier) => {
        const entries = Array.isArray(raidData[tier]) ? raidData[tier] : [];
        if (!entries.length) return;
        hasEntries = true;

        const group = document.createElement("div");
        group.classList.add("rarity-group");
        group.dataset.source = sourceKey;
        group.dataset.rarity = tier.toLowerCase();

        const rarityTitle = document.createElement("div");
        rarityTitle.classList.add("rarity-title", `${tier.toLowerCase()}-color`);
        rarityTitle.textContent = tier;
        group.appendChild(rarityTitle);

        const list = document.createElement("ul");
        const renderedEntries = sourceKey === "item" ? compactDuplicateEntries(entries) : asSingleCountEntries(entries);
        renderedEntries.forEach((entry) => {
            const entryName = entry.name;
            const entryCount = entry.count;
            const li = document.createElement("li");
            li.classList.add(`${tier.toLowerCase()}-color`);

            const iconUrl = getItemIconUrl(entryName, icons[entryName], { sourceKey, tier });
            if (iconUrl) {
                const icon = document.createElement("img");
                icon.src = iconUrl;
                icon.classList.add("item-icon");
                li.appendChild(icon);
            }

            const nameSpan = document.createElement("span");
            nameSpan.classList.add("item-name");
            nameSpan.textContent = entryName;
            if (sourceKey === "item" && isEmeraldLikeItem(entryName)) {
                nameSpan.classList.add("emerald-highlight");
            }
            li.appendChild(nameSpan);

            if (sourceKey === "item" && entryCount > 1) {
                const countSpan = document.createElement("span");
                countSpan.classList.add("item-count");
                if (isEmeraldLikeItem(entryName)) {
                    countSpan.classList.add("emerald-highlight");
                }
                countSpan.textContent = `x${entryCount}`;
                li.appendChild(countSpan);
            }

            if (includeDescriptions) {
                const desc = descriptions[entryName];
                if (desc) {
                    li.classList.add("has-description");
                    nameSpan.title = "Hover to view tier descriptions";
                    const descBlock = createAspectDescription(desc);
                    if (descBlock) li.appendChild(descBlock);
                }
            }

            list.appendChild(li);
        });

        group.appendChild(list);
        section.appendChild(group);
    });

    if (!hasEntries) {
        const empty = document.createElement("p");
        empty.classList.add("empty-raid-text");
        empty.dataset.source = sourceKey;
        empty.textContent = sourceKey === "aspect"
            ? "No listed aspects for this raid this week."
            : "No listed raid items for this raid this week.";
        section.appendChild(empty);
    }

    return section;
}

function createAspectDescription(descData) {
    const descBlock = document.createElement("div");
    descBlock.classList.add("aspect-desc");
    let hasAnyTier = false;

    ["1", "2", "3"].forEach((tier, idx) => {
        if (!descData[tier]) return;
        hasAnyTier = true;

        const tierDiv = document.createElement("div");
        tierDiv.classList.add("aspect-tier");

        const label = document.createElement("span");
        label.classList.add("tier-label");
        label.textContent = `Tier ${"III".slice(0, idx + 1)} (>=${descData[tier].threshold} XP): `;
        tierDiv.appendChild(label);

        const text = document.createElement("span");
        const normalizedLines = (descData[tier].description || [])
            .map(normalizeAspectDescriptionLine)
            .filter(Boolean);
        text.innerHTML = normalizedLines.map(escapeHtml).join("<br>");
        tierDiv.appendChild(text);

        descBlock.appendChild(tierDiv);
    });

    return hasAnyTier ? descBlock : null;
}

function setupTierFilters() {
    document.querySelectorAll("#lootpool-filters .filter-pill").forEach((button) => {
        button.addEventListener("click", function () {
            this.classList.toggle("active");
            filterLootpool();
        });
    });
}

function setupSourceFilters() {
    document.querySelectorAll("#source-filters .source-pill").forEach((button) => {
        button.addEventListener("click", function () {
            const source = this.dataset.source;
            if (!SOURCE_MODES.includes(source)) return;
            document.querySelectorAll("#source-filters .source-pill").forEach((pill) => pill.classList.remove("active"));
            this.classList.add("active");
            filterLootpool();
        });
    });
}

function filterLootpool() {
    const sourceMode = getActiveSourceMode();
    const tierFilters = {
        mythic: isTierEnabled("toggle-mythic"),
        fabled: isTierEnabled("toggle-fabled"),
        legendary: isTierEnabled("toggle-legendary"),
        rare: isTierEnabled("toggle-rare"),
        unique: isTierEnabled("toggle-unique"),
        misc: isTierEnabled("toggle-misc")
    };

    document.querySelectorAll(".lootpool-card").forEach((card) => {
        const aspectSection = card.querySelector(".aspect-section");
        const itemSection = card.querySelector(".item-section");

        const showAspectSection = sourceMode === "all" || sourceMode === "aspects";
        const showItemSection = sourceMode === "all" || sourceMode === "items";
        if (aspectSection) aspectSection.style.display = showAspectSection ? "" : "none";
        if (itemSection) itemSection.style.display = showItemSection ? "" : "none";

        const sectionHasVisible = { aspect: false, item: false };
        card.querySelectorAll(".rarity-group").forEach((group) => {
            const source = group.dataset.source;
            const rarity = group.dataset.rarity;
            const sourceAllowed = (source === "aspect" && showAspectSection) || (source === "item" && showItemSection);
            const tierAllowed = !!tierFilters[rarity];
            const visible = sourceAllowed && tierAllowed;
            group.style.display = visible ? "" : "none";
            if (visible) sectionHasVisible[source] = true;
        });

        let aspectEmptyVisible = false;
        let itemEmptyVisible = false;

        if (aspectSection) {
            const empty = aspectSection.querySelector(".empty-raid-text");
            aspectEmptyVisible = showAspectSection && !sectionHasVisible.aspect;
            if (empty) empty.style.display = aspectEmptyVisible ? "block" : "none";
        }
        if (itemSection) {
            const empty = itemSection.querySelector(".empty-raid-text");
            itemEmptyVisible = showItemSection && !sectionHasVisible.item;
            if (empty) empty.style.display = itemEmptyVisible ? "block" : "none";
        }

        const hasVisibleContent = (showAspectSection && (sectionHasVisible.aspect || aspectEmptyVisible))
            || (showItemSection && (sectionHasVisible.item || itemEmptyVisible));
        card.style.display = hasVisibleContent ? "block" : "none";
    });
}

function isTierEnabled(id) {
    const el = document.getElementById(id);
    return !!(el && el.classList.contains("active"));
}

function getActiveSourceMode() {
    const active = document.querySelector("#source-filters .source-pill.active");
    if (!active) return "all";
    const source = active.dataset.source;
    return SOURCE_MODES.includes(source) ? source : "all";
}

function startCountdown(seconds) {
    const countdownContainer = document.getElementById("countdown-container");
    if (!countdownContainer) return;
    countdownContainer.innerHTML = "";

    const countdownLabel = document.createElement("div");
    countdownLabel.id = "countdown-label";
    countdownLabel.textContent = "Next Update:";

    const countdownElement = document.createElement("div");
    countdownElement.id = "countdown";
    countdownElement.classList.add("countdown-container");

    countdownContainer.appendChild(countdownLabel);
    countdownContainer.appendChild(countdownElement);

    function updateCountdown() {
        const days = Math.floor(seconds / (3600 * 24));
        const hours = Math.floor((seconds % (3600 * 24)) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = seconds % 60;

        countdownElement.innerHTML = `
            <div class="countdown-segment"><div>${days}</div><span>Days</span></div>
            <div class="countdown-segment"><div>${hours}</div><span>Hours</span></div>
            <div class="countdown-segment"><div>${minutes}</div><span>Minutes</span></div>
            <div class="countdown-segment"><div>${remainingSeconds}</div><span>Seconds</span></div>
        `;

        if (seconds > 0) {
            seconds -= 1;
            setTimeout(updateCountdown, 1000);
        } else {
            location.reload();
        }
    }

    updateCountdown();
}

function getItemIconUrl(itemName, iconValue, context = {}) {
    const sourceKey = context && typeof context === "object" ? context.sourceKey : null;
    const tier = context && typeof context === "object" ? context.tier : null;
    let resolved = iconValue;
    if ((!resolved || typeof resolved !== "string") && typeof itemName === "string") {
        resolved = resolveSpecialItemIcon(itemName);
    }
    if (!resolved || typeof resolved !== "string") return null;
    if (sourceKey === "aspect" && tier === "Mythic") {
        resolved = resolveMythicAspectGifIcon(resolved);
    }
    const lowered = resolved.toLowerCase();
    const armorTypes = ["helmet", "chestplate", "leggings", "boots"];
    for (const type of armorTypes) {
        if (lowered.includes(type)) {
            return `../../resources/${type}.png`;
        }
    }
    if (!resolved.startsWith("http") && /\.(png|gif|webp|jpe?g|svg)$/i.test(resolved)) {
        return `../../resources/${resolved}`;
    }
    if (resolved.startsWith("http")) return resolved;
    return null;
}

function resolveMythicAspectGifIcon(iconValue) {
    if (typeof iconValue !== "string") return iconValue;
    const normalized = iconValue.trim().toLowerCase();
    return MYTHIC_ASPECT_GIF_FALLBACK_BY_ICON[normalized] || iconValue;
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
    if (lowered === "ability shard") return "scroll.png";
    const powderParts = lowered.split(" powder ");
    if (powderParts.length === 2 && ["earth", "thunder", "water", "fire", "air"].includes(powderParts[0])) {
        return "powder.png";
    }
    return null;
}

function compactDuplicateEntries(entries) {
    const counts = new Map();
    (Array.isArray(entries) ? entries : []).forEach((entry) => {
        if (typeof entry !== "string") return;
        const name = entry.trim();
        if (!name) return;
        counts.set(name, (counts.get(name) || 0) + 1);
    });
    return Array.from(counts.entries()).map(([name, count]) => ({ name, count }));
}

function asSingleCountEntries(entries) {
    return (Array.isArray(entries) ? entries : [])
        .filter((entry) => typeof entry === "string" && entry.trim())
        .map((entry) => ({ name: entry.trim(), count: 1 }));
}

function isEmeraldLikeItem(name) {
    if (typeof name !== "string") return false;
    return name.toLowerCase().includes("emerald");
}

function escapeHtml(text) {
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function normalizeAspectGlyphs(text) {
    return String(text).replace(/[\ue000-\uf8ff]/g, (glyph) => ASPECT_GLYPH_MAP[glyph] || "[Stat]");
}

function normalizeAspectDescriptionLine(rawLine) {
    if (!rawLine) return "";
    const normalizedHtml = String(rawLine)
        .replace(/<\/br\s*>/gi, "<br>")
        .replace(/<br\s*\/?>/gi, "\n");
    const parser = new DOMParser();
    const doc = parser.parseFromString(`<div>${normalizedHtml}</div>`, "text/html");
    const text = doc.body.textContent || "";
    return normalizeAspectGlyphs(text)
        .replace(/\r/g, "")
        .replace(/[ \t]+\n/g, "\n")
        .replace(/\n[ \t]+/g, "\n")
        .replace(/[ \t]{2,}/g, " ")
        .trim();
}
