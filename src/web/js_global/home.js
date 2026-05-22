// Global variables for time banner
let currentHue = Math.random() * 360;
let targetHue = Math.random() * 360;
let userTimezone = 'UTC';
let userLocation = '';
let isHovered = false;
let use24Hour = true;

// Section toggle function
function toggleSection(id, btn) {
    const section = document.getElementById(id);
    const hidden = (section.style.display === 'none');
    section.style.display = hidden ? 'block' : 'none';
    btn.classList.toggle('active', hidden);
}

// Time banner color transition
function smoothColorTransition() {
    if (isHovered) return; // Pause transitions on hover
    
    // Smoothly transition to target hue
    const diff = targetHue - currentHue;
    const shortestDiff = ((diff + 540) % 360) - 180;
    currentHue += shortestDiff * 0.01; // Faster transition
    currentHue = (currentHue + 360) % 360;

    // Pick new target occasionally
    if (Math.abs(shortestDiff) < 1) {
        targetHue = Math.random() * 360;
    }

    // Generate gradient colors with FULL freedom - can be bright or dark
    const saturation1 = 25 + Math.sin(Date.now() / 8000) * 45; // 0-70%
    const lightness1 = 25 + Math.sin(Date.now() / 12000) * 50; // 25-75% (avoid pure black/white)
    
    const hue2 = (currentHue + 60 + Math.sin(Date.now() / 6000) * 40) % 360;
    const saturation2 = 20 + Math.sin(Date.now() / 9000) * 40; // 0-60%
    const lightness2 = 20 + Math.sin(Date.now() / 11000) * 55; // 20-75% (avoid pure black/white)
    
    // Simple, smooth diagonal gradient - no direction changes
    const bgGradient = `linear-gradient(135deg, hsl(${currentHue}, ${saturation1}%, ${lightness1}%), hsl(${hue2}, ${saturation2}%, ${lightness2}%))`;
    
    // Ensure text contrast - use the darker of the two colors for contrast calculation
    const avgLightness = (lightness1 + lightness2) / 2;
    const textLightness = avgLightness < 50 ? 95 : 5;
    const textSaturation = Math.min(Math.max(saturation1, saturation2) * 0.2, 25);
    const textColor = `hsl(${currentHue}, ${textSaturation}%, ${textLightness}%)`;
    
    const banner = document.getElementById('timeBanner');
    if (banner) {
        banner.style.background = bgGradient;
        banner.style.color = textColor;
    }
}

// Update time display (in selected timezone)
function updateTime() {
    const now = new Date();
    const opts = {
        timeZone: userTimezone,
        weekday: 'long',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: !use24Hour
    };
    const formatter = new Intl.DateTimeFormat('en-CA', opts);
    const parts = formatter.formatToParts(now);
    const get = (type) => parts.find(p => p.type === type)?.value || '';
    const ampm = !use24Hour ? ` ${get('dayPeriod')}` : '';
    const timeString = `${get('weekday')}  ${get('year')}/${get('month')}/${get('day')} ${get('hour')}:${get('minute')}:${get('second')}${ampm}`;

    const timeDisplay = document.getElementById('timeDisplay');
    if (timeDisplay) {
        timeDisplay.textContent = timeString;
    }

    updateLunarDisplay();
}

let _lunarFormatter = null;
let _lunarFormatterTz = null;

function updateLunarDisplay() {
    const lunarDisplay = document.getElementById('lunarDisplay');
    if (!lunarDisplay) return;
    try {
        if (!_lunarFormatter || _lunarFormatterTz !== userTimezone) {
            _lunarFormatter = new Intl.DateTimeFormat('zh-u-ca-chinese', {
                timeZone: userTimezone,
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            _lunarFormatterTz = userTimezone;
        }
        lunarDisplay.textContent = '农历 ' + _lunarFormatter.format(new Date());
    } catch (e) {
        lunarDisplay.textContent = '';
    }
}

// Get timezone abbreviation
function getTimezoneAbbreviation(timezone) {
    const now = new Date();
    const options = {
        timeZone: timezone,
        timeZoneName: 'short'
    };
    
    try {
        const formatter = new Intl.DateTimeFormat('en-US', options);
        const parts = formatter.formatToParts(now);
        const timeZoneName = parts.find(part => part.type === 'timeZoneName');
        
        if (timeZoneName) {
            return timeZoneName.value; // e.g., "CST", "EST", "PST"
        }
    } catch (error) {
        console.log('Error getting timezone abbreviation');
    }
    
    return timezone.split('/').pop() || 'UTC'; // Fallback to last part of timezone
}

// Get location and time
function getLocationAndTime() {
    userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
    updateTimezoneDisplay();
    updateTime();
}

function updateTimezoneDisplay() {
    const timezoneDisplay = document.getElementById('timezoneDisplay');
    if (timezoneDisplay) {
        const abbrev = getTimezoneAbbreviation(userTimezone);
        let offset = 'UTC';
        try {
            const f = new Intl.DateTimeFormat('en-US', { timeZone: userTimezone, timeZoneName: 'shortOffset' });
            const parts = f.formatToParts(new Date());
            const p = parts.find(x => x.type === 'timeZoneName');
            if (p) offset = p.value.replace('GMT', 'UTC');
        } catch (_) {}
        timezoneDisplay.textContent = `${abbrev} / ${offset}`;
    }
}

// Toggle 12h/24h format
function toggleTimeFormat() {
    use24Hour = !use24Hour;
    const btn = document.getElementById('timeFormatBtn');
    if (btn) btn.textContent = use24Hour ? '24h' : '12h';
    updateTime();
}

// Major cities for timezone picker
const MAJOR_CITIES = [
    'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
    'America/Toronto', 'America/Vancouver', 'America/Sao_Paulo', 'America/Mexico_City',
    'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Moscow', 'Europe/Istanbul',
    'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Hong_Kong', 'Asia/Singapore', 'Asia/Dubai',
    'Asia/Kolkata', 'Asia/Seoul', 'Australia/Sydney', 'Australia/Melbourne',
    'Pacific/Auckland', 'Africa/Cairo', 'Africa/Johannesburg',
    'UTC'
];

function populateTimezonePicker() {
    const select = document.getElementById('timezoneSelect');
    if (!select) return;
    select.innerHTML = '';
    MAJOR_CITIES.forEach(tz => {
        const opt = document.createElement('option');
        opt.value = tz;
        opt.textContent = tz.replace(/_/g, ' ');
        if (tz === userTimezone) opt.selected = true;
        select.appendChild(opt);
    });
}

function initTimeControls() {
    const gearBtn = document.getElementById('timeGearBtn');
    const dropdown = document.getElementById('timeControlsDropdown');
    const formatBtn = document.getElementById('timeFormatBtn');
    const tzSelect = document.getElementById('timezoneSelect');

    function toggleDropdown() {
        if (!dropdown) return;
        const opening = !dropdown.classList.contains('open');
        dropdown.classList.toggle('open');
        if (opening) populateTimezonePicker();
    }

    function closeDropdown(e) {
        if (!dropdown || !dropdown.classList.contains('open')) return;
        if (gearBtn && gearBtn.contains(e.target)) return;
        if (dropdown.contains(e.target)) return;
        dropdown.classList.remove('open');
    }

    if (gearBtn && dropdown) {
        gearBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleDropdown();
        });
        document.addEventListener('click', closeDropdown);
    }

    if (formatBtn) {
        formatBtn.textContent = use24Hour ? '24h' : '12h';
        formatBtn.addEventListener('click', toggleTimeFormat);
    }

    if (tzSelect) {
        tzSelect.addEventListener('change', () => {
            userTimezone = tzSelect.value;
            _lunarFormatter = null;
            updateTimezoneDisplay();
            updateTime();
        });
    }
}

// Changelog toggle function
function toggleChangelog() {
    const changelog = document.getElementById('changelog');
    const button = document.getElementById('changelog-button');
    const showText = 'View Changelog';
    const hideText = 'Hide Changelog';

    if (changelog.style.display === 'none' || changelog.style.display === '') {
        changelog.style.display = 'block';
        button.textContent = hideText;
    } else {
        changelog.style.display = 'none';
        button.textContent = showText;
    }
}

// Output from my mind
const noriQuotes = [
    "Every weird behavior has a reason. It’s just usually annoying to find.",
    "If it only breaks sometimes, it’s just being polite.",
    "The system only understands exactly what you told it to do, not what you meant.",
    "Most clarity comes after things go wrong.",
    "Progress starts where comfort ends.",
    "I push systems until they reveal themselves.",
    "Every system tells a story if you listen.",
    "Controlled chaos is still control.",
    "State estimation is admitting you don’t actually know - It's pretty much disciplined guessing.",
    "Some ideas fail. That’s how you find the good ones.",
    "Iteration beats overthinking.",
    "Every system is a black box until you open it.",
    "I enjoy turning ideas into something tangible. Some work out, some don't, but I believe that even the wild ones deserve a shot to show what they can become.",
    "Half my breakthroughs start with \"I probably shouldn't do this,\" and honestly that's a system I'm proud of.",
    "My guiding philosophy: if it works, great. If it doesn't, it becomes a story. Both outcomes win.",
    "My creative process is like 30% planning, 70% \"oh, so that's what I meant.\"",
    "I trust my instincts even when they behave like they've never met me before.",
    "My sleep schedule has become more of a suggestion than a system.",
    "My toxic trait is thinking I can finish everything in one night.",
    "Healing is realizing you were never actually that serious.",
    "Consistently underestimating how long ‘real quick’ actually is.",
    "Making plans for a version of myself with dramatically more discipline.",
    "Either fully locked in or emotionally unavailable to productivity.",
    "Treating minor inconveniences like personal challenges from the universe.",
    "An attention span that’s either evolving or taking damage.",
    "Believing in balance while also believing in side quests.",
    "Half of adulthood is recovering from your own decisions.",
    "Sometimes the best self-care is pretending the email doesn’t exist for one more hour.",
    "Wanting inner peace but also wanting to see what happens if the button gets pressed.",
    "‘It is what it is’ because legally fighting the air isn’t an option.",
    "Accepting that being organized is more of a seasonal hobby.",
    "Every week unlocking a new and creative way to inconvenience myself.",
    "A brain that confuses pressure with motivation.",
    "Loving stability conceptually.",
    "Always one mildly good day away from reinventing my entire life.",
    "My favorite coping mechanism is acting like everything was intentional.",
    "Confidence is mostly just recovering quickly.",
    "Either responding immediately or after enough time has passed to fake my own death.",
    "Sometimes doing absolutely nothing is required before continuing to do too much.",
    "Everything will probably work out eventually because the alternative sounds exhausting.",
    "A personality built from accumulated unfinished side quests.",
    "Reached the stage of life where rest feels suspicious.",
    "Enjoying low-stress environments while recreationally creating high-stress situations.",
    "Healing is realizing not every part of existence needs optimization.",
    "I think the best solutions feel obvious only after they exist.",
    "Nothing strengthens problem-solving skills quite like refusing to quit.",
    "Every elegant solution started as something slightly embarrassing.",
    "Sometimes the best documentation is the scar tissue.",
    "Good systems survive bad decisions. Great systems survive me.",
    "Fun fact: I started this project for fun and accidentally developed responsibilities.",
];

// Quote rotation interval in milliseconds (30 seconds)
const QUOTE_ROTATION_INTERVAL = 30000;

let currentQuoteIndex = 0;

function rotateQuote() {
    const quoteElement = document.getElementById('nori-quote');
    if (!quoteElement) return;
    
    // Pick a random quote (excluding the current one to avoid immediate repeats)
    let newIndex;
    do {
        newIndex = Math.floor(Math.random() * noriQuotes.length);
    } while (newIndex === currentQuoteIndex && noriQuotes.length > 1);
    
    // Fade out, change quote, fade in
    quoteElement.style.opacity = '0';
    setTimeout(() => {
        currentQuoteIndex = newIndex;
        quoteElement.textContent = noriQuotes[currentQuoteIndex];
        quoteElement.style.opacity = '1';
    }, 250); // Half of transition duration (500ms / 2)
}

function initQuoteRefresh() {
    const btn = document.getElementById('quoteRefreshBtn');
    const fill = document.getElementById('quoteProgressFill');
    if (!btn || !fill) return;

    let holdTimer = null;
    let resetTimer = null;
    let fired = false;

    function clearResetTimer() {
        if (resetTimer) { clearTimeout(resetTimer); resetTimer = null; }
    }

    function resetBar() {
        fill.classList.remove('filling', 'complete');
        void fill.offsetWidth;
        btn.classList.remove('pressing');
        fired = false;
    }

    function startHold() {
        clearResetTimer();
        if (holdTimer) { clearTimeout(holdTimer); holdTimer = null; }
        fired = false;
        btn.classList.add('pressing');
        fill.classList.remove('filling', 'complete');
        void fill.offsetWidth;
        fill.classList.add('filling');

        holdTimer = setTimeout(() => {
            fired = true;
            fill.classList.remove('filling');
            fill.classList.add('complete');

            const quoteEl = document.getElementById('nori-quote');
            if (quoteEl) {
                quoteEl.style.transition = 'opacity 0.12s ease';
                quoteEl.style.opacity = '0';
                setTimeout(() => {
                    let newIndex;
                    do { newIndex = Math.floor(Math.random() * noriQuotes.length); }
                    while (newIndex === currentQuoteIndex && noriQuotes.length > 1);
                    currentQuoteIndex = newIndex;
                    quoteEl.textContent = noriQuotes[currentQuoteIndex];
                    quoteEl.style.opacity = '1';
                    setTimeout(() => { quoteEl.style.transition = ''; }, 200);
                }, 120);
            }

            resetTimer = setTimeout(resetBar, 500);
        }, 500);
    }

    function cancelHold() {
        if (holdTimer) { clearTimeout(holdTimer); holdTimer = null; }
        if (!fired) resetBar();
    }

    btn.addEventListener('mousedown', startHold);
    btn.addEventListener('touchstart', (e) => { e.preventDefault(); startHold(); }, { passive: false });
    btn.addEventListener('mouseup', cancelHold);
    btn.addEventListener('mouseleave', cancelHold);
    btn.addEventListener('touchend', cancelHold);
    btn.addEventListener('touchcancel', cancelHold);
}

function initializeQuoteRotation() {
    // Set initial random quote on page load
    currentQuoteIndex = Math.floor(Math.random() * noriQuotes.length);
    const quoteElement = document.getElementById('nori-quote');
    if (quoteElement) {
        quoteElement.textContent = noriQuotes[currentQuoteIndex];
        quoteElement.style.opacity = '1'; // Ensure initial quote is visible
    }
    
    // Rotate quote at the specified interval
    setInterval(rotateQuote, QUOTE_ROTATION_INTERVAL);
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set up time banner hover events
    const banner = document.getElementById('timeBanner');
    if (banner) {
        banner.addEventListener('mouseenter', () => isHovered = true);
        banner.addEventListener('mouseleave', () => isHovered = false);
    }

    // Initialize time and location
    getLocationAndTime();
    initTimeControls();
    setInterval(updateTime, 1000);
    setInterval(smoothColorTransition, 16); // ~60fps for smooth transitions

    // Initialize quote rotation
    initializeQuoteRotation();
    initQuoteRefresh();
});
