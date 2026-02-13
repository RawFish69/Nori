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
    const timeString = `${get('year')}/${get('month')}/${get('day')} ${get('hour')}:${get('minute')}:${get('second')}${ampm}`;

    const timeDisplay = document.getElementById('timeDisplay');
    if (timeDisplay) {
        timeDisplay.textContent = timeString;
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
async function getLocationAndTime() {
    try {
        // Try to get timezone from IP
        const response = await fetch('https://ipapi.co/json/');
        const data = await response.json();
        
        if (data.timezone) {
            userTimezone = data.timezone;
        } else {
            userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
        }
    } catch (error) {
        console.log('Could not fetch location, using local timezone');
        userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
    }
    
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
    const tzBtn = document.getElementById('timezoneBtn');
    const tzPicker = document.getElementById('timezonePicker');
    const tzSelect = document.getElementById('timezoneSelect');

    function toggleDropdown() {
        if (dropdown) dropdown.classList.toggle('open');
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

    if (tzBtn && tzPicker && tzSelect) {
        tzBtn.addEventListener('click', () => {
            tzPicker.style.display = tzPicker.style.display === 'none' ? 'block' : 'none';
            if (tzPicker.style.display === 'block') populateTimezonePicker();
        });
        tzSelect.addEventListener('change', () => {
            userTimezone = tzSelect.value;
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
    "I enjoy turning ideas into something tangible. Some work out, some don't, but I believe that even the wild ones deserve a shot to show what they can become.",
    "Half my breakthroughs start with \"I probably shouldn't do this,\" and honestly that's a system I'm proud of.",
    "My guiding philosophy: if it works, great. If it doesn't, it becomes a story. Both outcomes win.",
    "My creative process is like 30% planning, 70% \"oh, so that's what I meant.\"",
    "I trust my instincts even when they behave like they've never met me before.",
    "If life hands you confusion, build something weird out of it.",
    "I like doing things I've never done before because technically that means I have no expectations to disappoint :)",
    "If you're wondering why I stopped doing that gaming stuff, that's just me attempting to be a responsible adult.",
    "I'm not always motivated, especially when I'm doing stuff I don't even like but somehow still ended up responsible for. I just rely on discipline and the fear of regret.",
    "I used to have zero patience. I worked on it for years, and now I’m still not patient - I just wait aggressively."
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
});
