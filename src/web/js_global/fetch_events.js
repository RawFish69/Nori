(function () {
    const WORLD_BOSS_NAMES = new Set(["Prelude to Annihilation"]);
    const API_URL = "https://nori.fish/api/world-events";

    let allEvents = [];
    // Map<eventName, {card: HTMLElement, countdownEl: HTMLElement, ts: number|null}>
    const cardMap = new Map();
    let lastFetch = 0;

    function parseSchedule(s) {
        if (s === null || s === undefined) return null;
        if (typeof s === "number") return Math.floor(s);
        if (typeof s === "string" && s) {
            try {
                const normalized = s.endsWith("Z") ? s.slice(0, -1) + "+00:00" : s;
                const ms = new Date(normalized).getTime();
                return isNaN(ms) ? null : Math.floor(ms / 1000);
            } catch (e) {
                return null;
            }
        }
        return null;
    }

    function isWorldBoss(event) {
        return WORLD_BOSS_NAMES.has(event && event.name);
    }

    function formatCountdown(ts) {
        const diff = ts - Math.floor(Date.now() / 1000);
        if (diff <= 0) return "starting now";
        const m = Math.floor(diff / 60);
        const s = diff % 60;
        return m > 0 ? `${m}m ${s}s` : `${s}s`;
    }

    function getLevelClass(level) {
        if (typeof level !== "number") return "level-green";
        if (level >= 100) return "level-red";
        if (level >= 60) return "level-yellow";
        return "level-green";
    }

    function getLevelRangeBucket(level) {
        if (typeof level !== "number") return 2;
        if (level >= 100) return 0;
        if (level >= 60) return 1;
        return 2;
    }

    function getDiffClass(diff) {
        if (!diff) return "";
        const d = diff.toUpperCase();
        if (d === "HARD" || d === "ELITE" || d === "LEGENDARY") return "diff-red";
        if (d === "MEDIUM" || d === "NORMAL") return "diff-yellow";
        return "diff-green";
    }

    function formatReqType(type) {
        if (!type) return "?";
        return String(type).replace(/_/g, " ").toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
    }

    function getFirstLocation(locations) {
        if (!Array.isArray(locations)) return null;
        for (const loc of locations) {
            if (!loc || typeof loc !== "object") continue;
            for (const key of ["event", "spawn", "reward"]) {
                const v = loc[key];
                if (v && typeof v === "object" && "x" in v) return v;
            }
            if ("x" in loc) return loc;
        }
        return null;
    }

    function flattenRewards(rewardPerLevel) {
        if (!rewardPerLevel || typeof rewardPerLevel !== "object" || Array.isArray(rewardPerLevel)) return [];
        const seen = new Set();
        const out = [];
        const keys = Object.keys(rewardPerLevel).sort((a, b) => {
            const ia = parseInt(a, 10), ib = parseInt(b, 10);
            return (!isNaN(ia) && !isNaN(ib)) ? ia - ib : String(a).localeCompare(String(b));
        });
        for (const key of keys) {
            const items = rewardPerLevel[key];
            if (!Array.isArray(items)) continue;
            for (const item of items) {
                if (typeof item === "string" && !seen.has(item)) {
                    seen.add(item);
                    out.push(item);
                }
            }
        }
        return out;
    }

    function applyControls() {
        const sortMode = (document.getElementById("sort-select") || {}).value || "time";
        const filterMode = (document.getElementById("filter-select") || {}).value || "all";
        const query = ((document.getElementById("search-input") || {}).value || "").trim().toLowerCase();

        let list = allEvents.slice();

        if (sortMode === "time") {
            list.sort((a, b) => {
                const ta = parseSchedule(a.schedule), tb = parseSchedule(b.schedule);
                if (ta !== null && tb !== null) return ta - tb;
                if (ta !== null) return -1;
                if (tb !== null) return 1;
                const la = typeof a.level === "number" ? a.level : 0;
                const lb = typeof b.level === "number" ? b.level : 0;
                return lb - la;
            });
        } else if (sortMode === "level") {
            const withTimer = list.filter(e => parseSchedule(e.schedule) !== null);
            const noTimer   = list.filter(e => parseSchedule(e.schedule) === null);
            withTimer.sort((a, b) => {
                const ra = getLevelRangeBucket(a.level), rb = getLevelRangeBucket(b.level);
                if (ra !== rb) return ra - rb;
                return parseSchedule(a.schedule) - parseSchedule(b.schedule);
            });
            noTimer.sort((a, b) => {
                const ra = getLevelRangeBucket(a.level), rb = getLevelRangeBucket(b.level);
                if (ra !== rb) return ra - rb;
                const la = typeof a.level === "number" ? a.level : 0;
                const lb = typeof b.level === "number" ? b.level : 0;
                return lb - la;
            });
            list = withTimer.concat(noTimer);
        } else if (sortMode === "name") {
            list.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
        }

        // Pin scheduled world bosses to front (regardless of sort mode)
        const pinned = list.filter(e => isWorldBoss(e) && parseSchedule(e.schedule) !== null);
        const rest = list.filter(e => !(isWorldBoss(e) && parseSchedule(e.schedule) !== null));
        list = pinned.concat(rest);

        if (filterMode === "scheduled") {
            list = list.filter(e => parseSchedule(e.schedule) !== null);
        } else if (filterMode === "lv80") {
            list = list.filter(e => typeof e.level === "number" && e.level >= 80);
        } else if (filterMode === "lv60") {
            list = list.filter(e => typeof e.level === "number" && e.level >= 60);
        }

        if (query) {
            list = list.filter(e => (e.name || "").toLowerCase().includes(query));
        }

        return list;
    }

    function buildCard(event, isHero) {
        const ts = parseSchedule(event.schedule);
        const boss = isWorldBoss(event);

        const card = document.createElement("div");
        const classes = ["event-card"];
        if (isHero) classes.push("event-card--hero");
        if (boss) classes.push("event-card--boss");
        classes.push(ts !== null ? "event-card--scheduled" : "event-card--unscheduled");
        card.className = classes.join(" ");
        card.dataset.name = event.name || "";

        // ── Header ──
        const header = document.createElement("div");
        header.className = "event-card-header";

        const nameRow = document.createElement("div");
        nameRow.className = "event-card-name-row";

        if (boss) {
            const bossChip = document.createElement("span");
            bossChip.className = "chip chip--boss";
            bossChip.textContent = "🌍 WORLD BOSS";
            nameRow.appendChild(bossChip);
        }

        const nameEl = document.createElement("h3");
        nameEl.className = "event-card-name";
        nameEl.textContent = event.name || "Unknown Event";
        nameRow.appendChild(nameEl);
        header.appendChild(nameRow);

        const metaRow = document.createElement("div");
        metaRow.className = "event-card-meta";

        if (typeof event.level === "number") {
            const levelChip = document.createElement("span");
            levelChip.className = `chip chip--level ${getLevelClass(event.level)}`;
            levelChip.textContent = `Lv ${event.level}`;
            metaRow.appendChild(levelChip);
        }
        if (event.difficulty) {
            const diffChip = document.createElement("span");
            diffChip.className = `chip chip--diff ${getDiffClass(event.difficulty)}`;
            diffChip.textContent = formatReqType(event.difficulty);
            metaRow.appendChild(diffChip);
        }
        if (event.length) {
            const lenChip = document.createElement("span");
            lenChip.className = "chip chip--len";
            lenChip.textContent = event.length;
            metaRow.appendChild(lenChip);
        }
        header.appendChild(metaRow);

        const cdRow = document.createElement("div");
        cdRow.className = "event-card-countdown" + (isHero ? " event-card-countdown--hero" : "");
        const cdEl = document.createElement("span");
        if (ts !== null) {
            cdEl.className = "countdown-chip";
            cdEl.textContent = `⏱ ${formatCountdown(ts)}`;
        } else {
            cdEl.className = "countdown-chip countdown-chip--unknown";
            cdEl.textContent = "Next run unknown";
        }
        cdRow.appendChild(cdEl);
        header.appendChild(cdRow);
        card.appendChild(header);

        // ── Divider ──
        const hr = document.createElement("hr");
        hr.className = "event-card-divider";
        card.appendChild(hr);

        // ── Body ──
        const body = document.createElement("div");
        body.className = "event-card-body";

        const reqs = Array.isArray(event.requirements) ? event.requirements : [];
        if (reqs.length > 0) {
            const sec = document.createElement("div");
            sec.className = "event-section";
            const label = document.createElement("div");
            label.className = "event-section-label";
            label.textContent = "Requirements";
            sec.appendChild(label);
            const ul = document.createElement("ul");
            ul.className = "event-list";
            for (const req of reqs) {
                if (!req || typeof req !== "object") continue;
                const li = document.createElement("li");
                li.textContent = `${formatReqType(req.type)}: ${req.value !== undefined ? req.value : "?"}`;
                ul.appendChild(li);
            }
            sec.appendChild(ul);
            body.appendChild(sec);
        }

        const rewards = flattenRewards(event.rewardPerLevel);
        if (rewards.length > 0) {
            const sec = document.createElement("div");
            sec.className = "event-section";
            const label = document.createElement("div");
            label.className = "event-section-label";
            label.textContent = "Rewards";
            sec.appendChild(label);
            const ul = document.createElement("ul");
            ul.className = "event-list";
            for (const r of rewards) {
                const li = document.createElement("li");
                if (r === "Corrupted Cache" || r === "+Corrupted Cache") li.className = "event-reward-mythic";
                li.textContent = r;
                ul.appendChild(li);
            }
            sec.appendChild(ul);
            body.appendChild(sec);
        }

        const loc = getFirstLocation(event.location);
        if (loc) {
            const sec = document.createElement("div");
            sec.className = "event-section";
            const label = document.createElement("div");
            label.className = "event-section-label";
            label.textContent = "Location";
            sec.appendChild(label);
            const coordStr = `${loc.x}, ${loc.y}, ${loc.z}`;
            const locRow = document.createElement("div");
            locRow.className = "event-location-row";
            const locText = document.createElement("span");
            locText.className = "event-location";
            locText.textContent = coordStr;
            const copyBtn = document.createElement("button");
            copyBtn.className = "event-location-copy";
            copyBtn.textContent = "Copy";
            copyBtn.title = "Copy coordinates";
            copyBtn.addEventListener("click", () => {
                navigator.clipboard.writeText(coordStr).then(() => {
                    copyBtn.textContent = "Copied!";
                    copyBtn.classList.add("event-location-copy--done");
                    setTimeout(() => {
                        copyBtn.textContent = "Copy";
                        copyBtn.classList.remove("event-location-copy--done");
                    }, 1200);
                });
            });
            locRow.appendChild(locText);
            locRow.appendChild(copyBtn);
            sec.appendChild(locRow);
            body.appendChild(sec);
        }

        if (isHero && event.lore && typeof event.lore === "string") {
            const sec = document.createElement("div");
            sec.className = "event-section event-section--lore";
            const p = document.createElement("p");
            p.className = "event-lore";
            p.textContent = event.lore.length > 140 ? event.lore.slice(0, 140) + "…" : event.lore;
            sec.appendChild(p);
            body.appendChild(sec);
        }

        card.appendChild(body);
        return { card, countdownEl: cdEl, ts };
    }

    function renderCards(list) {
        const container = document.getElementById("events-grid");
        if (!container) return;

        const nameSet = new Set(list.map(e => e.name));

        // Remove stale cards
        for (const [name, entry] of cardMap.entries()) {
            if (!nameSet.has(name)) {
                entry.card.remove();
                cardMap.delete(name);
            }
        }

        const fragment = document.createDocumentFragment();
        for (const event of list) {
            const ts = parseSchedule(event.schedule);
            const isHero = isWorldBoss(event) && ts !== null;

            if (cardMap.has(event.name)) {
                const existing = cardMap.get(event.name);
                existing.ts = ts;
                const cdEl = existing.countdownEl;
                if (ts !== null) {
                    cdEl.className = "countdown-chip";
                    cdEl.textContent = `⏱ ${formatCountdown(ts)}`;
                } else {
                    cdEl.className = "countdown-chip countdown-chip--unknown";
                    cdEl.textContent = "Next run unknown";
                }
                existing.card.classList.toggle("event-card--scheduled", ts !== null);
                existing.card.classList.toggle("event-card--unscheduled", ts === null);
                existing.card.classList.toggle("event-card--hero", isHero);
                fragment.appendChild(existing.card);
            } else {
                const { card, countdownEl } = buildCard(event, isHero);
                cardMap.set(event.name, { card, countdownEl, ts });
                fragment.appendChild(card);
            }
        }

        container.innerHTML = "";
        container.appendChild(fragment);
    }

    function tickCountdowns() {
        for (const entry of cardMap.values()) {
            if (entry.ts === null) continue;
            entry.countdownEl.textContent = `⏱ ${formatCountdown(entry.ts)}`;
        }
    }

    function updateLastUpdated() {
        const el = document.getElementById("last-updated");
        if (!el || !lastFetch) return;
        const s = Math.floor((Date.now() - lastFetch) / 1000);
        el.textContent = `Updated ${s}s ago`;
    }

    function _showBetaBanner(show) {
        let banner = document.getElementById("events-beta-banner");
        if (show) {
            if (!banner) {
                banner = document.createElement("div");
                banner.id = "events-beta-banner";
                banner.className = "events-beta-banner";
                banner.textContent = "⚠ Showing data from the Wynncraft beta API — prod API had no scheduled events";
                const grid = document.getElementById("events-grid");
                if (grid && grid.parentNode) grid.parentNode.insertBefore(banner, grid);
            }
        } else if (banner) {
            banner.remove();
        }
    }

    async function fetchEvents() {
        try {
            const resp = await fetch(API_URL, { method: "GET", credentials: "omit" });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            allEvents = Array.isArray(data) ? data : [];
            lastFetch = Date.now();
            _showBetaBanner(resp.headers.get("X-Nori-Source") === "beta");
        } catch (e) {
            console.error("[world-events] fetch failed:", e);
        }
    }

    document.addEventListener("DOMContentLoaded", async () => {
        const loadingEl = document.getElementById("events-loading");
        const emptyEl = document.getElementById("events-empty");

        if (loadingEl) loadingEl.style.display = "";
        if (emptyEl) emptyEl.style.display = "none";

        await fetchEvents();

        if (loadingEl) loadingEl.style.display = "none";

        const list = applyControls();
        if (emptyEl) emptyEl.style.display = list.length === 0 ? "" : "none";
        renderCards(list);

        setInterval(tickCountdowns, 1000);
        setInterval(updateLastUpdated, 1000);
        updateLastUpdated();

        setInterval(async () => {
            await fetchEvents();
            const updated = applyControls();
            if (emptyEl) emptyEl.style.display = updated.length === 0 ? "" : "none";
            renderCards(updated);
        }, 60000);

        function onControlChange() {
            const updated = applyControls();
            if (emptyEl) emptyEl.style.display = updated.length === 0 ? "" : "none";
            renderCards(updated);
        }

        const sortSel = document.getElementById("sort-select");
        const filterSel = document.getElementById("filter-select");
        const searchIn = document.getElementById("search-input");
        const refreshBtn = document.getElementById("refresh-btn");

        if (sortSel) sortSel.addEventListener("change", onControlChange);
        if (filterSel) filterSel.addEventListener("change", onControlChange);
        if (searchIn) searchIn.addEventListener("input", onControlChange);

        if (refreshBtn) {
            refreshBtn.addEventListener("click", async () => {
                refreshBtn.disabled = true;
                refreshBtn.textContent = "Refreshing...";
                await fetchEvents();
                const updated = applyControls();
                if (emptyEl) emptyEl.style.display = updated.length === 0 ? "" : "none";
                renderCards(updated);
                updateLastUpdated();
                refreshBtn.disabled = false;
                refreshBtn.textContent = "Refresh";
            });
        }
    });
})();
