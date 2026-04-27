/**
 * Utility functions to apply configuration values to page elements
 */
document.addEventListener('DOMContentLoaded', function() {
    applyFooterText();
    replaceHardcodedURLs();
    applyStandardNavigation();
});

/**
 * Apply the footer text from configuration
 */
function applyFooterText() {
    if (!window.NoriConfig) return;
    
    const footers = document.querySelectorAll('footer p');
    if (footers.length > 0) {
        // Replace only the copyright text (usually the first or only paragraph)
        const copyrightText = footers[0];
        if (copyrightText && copyrightText.textContent.includes("©")) {
            copyrightText.textContent = NoriConfig.text.footerText;
        }
    }
}

/**
 * Replace hardcoded URLs with ones from configuration
 */
function replaceHardcodedURLs() {
    if (!window.NoriConfig) return;
    
    const domain = NoriConfig.domain.base;
    const wynndomain = NoriConfig.domain.wynn;
    document.querySelectorAll('a[href^="https://nori.fish"]').forEach(link => {
        const href = link.getAttribute('href');
        if (href.startsWith('https://nori.fish/wynn')) {
            link.setAttribute('href', href.replace('https://nori.fish/wynn', wynndomain));
        } else {
            link.setAttribute('href', href.replace('https://nori.fish', domain));
        }
    });
    document.querySelectorAll('a[href^="https://discord.gg/"]').forEach(link => {
        link.setAttribute('href', NoriConfig.links.discord);
    });
    
    document.querySelectorAll('a[href^="https://discord.com/application-directory/"]').forEach(link => {
        link.setAttribute('href', NoriConfig.links.discordBot);
    });
}

/**
 * Apply standard navigation from configuration
 */
function applyStandardNavigation() {
    if (!window.NoriConfig || !NoriConfig.navigation) return;
    const navElement = document.querySelector('header nav');
    if (!navElement) return;
    let navLinks;
    if (window.location.pathname.includes('/wynn')) {
        navLinks = NoriConfig.navigation.wynn;
    } else if (window.location.pathname.includes('/utils')) {
        navLinks = NoriConfig.navigation.utils;
    } else {
        navLinks = NoriConfig.navigation.default;
    }
    navElement.innerHTML = '';
    navLinks.forEach(link => {
        const a = document.createElement('a');
        a.textContent = link.text;
        
        if (link.url.startsWith('/')) {
            a.href = NoriConfig.domain.base + link.url;
        } else {
            a.href = link.url;
        }

        if (link.external) {
            a.setAttribute('target', '_blank');
        }

        if (link.special) {
            a.classList.add(link.special);
        }
        
        navElement.appendChild(a);
    });
}

/**
 * Add this function to any page that needs to set page title dynamically
 * @param {string} pageTitle - The specific page title
 */
function setPageTitle(pageTitle) {
    if (!window.NoriConfig) return;
    
    const baseTitle = document.querySelector('title');
    if (baseTitle) {
        if (pageTitle.includes('Wynn')) {
            baseTitle.textContent = pageTitle;
        } else {
            baseTitle.textContent = `${pageTitle} | ${NoriConfig.text.siteName}`;
        }
    }
}
