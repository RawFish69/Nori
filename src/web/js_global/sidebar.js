// Sidebar functions
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const menuButton = document.getElementById('menu-button');
    const body = document.body;

    sidebar.classList.toggle('active');

    if (sidebar.classList.contains('active')) {
        menuButton.classList.add('sidebar-active');
        body.classList.add('sidebar-active');
    } else {
        menuButton.classList.remove('sidebar-active');
        body.classList.remove('sidebar-active');
    }
}

function toggleSubMenu(id) {
    var subMenu = document.getElementById(id);
    subMenu.classList.toggle('active');
}

function createSidebar() {
    const sidebar = document.getElementById('sidebar');

    if (!sidebar) {
        console.error("Sidebar element not found");
        return;
    }

    const baseUrl = 'https://nori.fish';
    const sidebarItems = [
        {
            title: 'Utils',
            id: 'utils-sub',
            subItems: [
                { name: 'System Analyzer', url: baseUrl + '/utils#system-analyzer' },
                { name: 'Crypto Tracker', url: baseUrl + '/utils#crypto-tracker' },
                { name: 'MP4 to GIF', url: baseUrl + '/utils#mp4-to-gif' },
                { name: 'Image Converter', url: baseUrl + '/utils#image-converter' },
                { name: 'World Clock', url: baseUrl + '/utils#world-clock' },
                { name: 'Timestamp', url: baseUrl + '/utils#timestamp' },
                { name: 'Hash & Encode', url: baseUrl + '/utils#hash-tool' },
                { name: 'Markdown Preview', url: baseUrl + '/utils#markdown-preview' },
                { name: 'Text Toolkit', url: baseUrl + '/utils#text-toolkit' },
                { name: 'JSON Formatter', url: baseUrl + '/utils#json-tool' },
                { name: 'Password Generator', url: baseUrl + '/utils#password-gen' },
                { name: 'YouTube Helper', url: baseUrl + '/utils#youtube-helper' },
                { name: 'Chat Assistant', url: baseUrl + '/utils#chat-assistant' },
                { name: 'More tools...', url: baseUrl + '/utils' },
            ],
        },
        { type: 'category', title: 'Wynncraft' },
        {
            title: 'Items',
            id: 'item-sub',
            subItems: [
                { name: 'Item Analysis', url: 'https://nori.fish/wynn/item/analysis' },
                { name: 'Item Lootpool', url: 'https://nori.fish/wynn/item/lootpool' },
                { name: 'Raid Lootpool', url: 'https://nori.fish/wynn/raids' },
                { name: 'Item Simulation', url: 'https://nori.fish/wynn/item/simulation' },
                { name: 'Item Changelog', url: 'https://nori.fish/wynn/item/changelog' },
                { name: 'Mythic Items', url: 'https://nori.fish/wynn/item/mythic' },
                { name: 'Item Menu', url: 'https://nori.fish/wynn/item' },
            ],
        },
        {
            title: 'Builds',
            id: 'build-sub',
            subItems: [
                { name: 'Class Build Search', url: 'https://nori.fish/wynn/build' },
                { name: 'Recipe Search', url: 'https://nori.fish/wynn/recipe' },
                { name: 'Build Showcase', url: 'https://nori.fish/wynn/showcase' },
            ],
        },
        {
            title: 'Leaderboards',
            id: 'leaderboard-sub',
            subItems: [
                { name: 'Menu', url: 'https://nori.fish/wynn/leaderboard' },
                { name: 'Guilds', url: 'https://nori.fish/wynn/leaderboard/?type=guilds&category=raids_total&page=1' },
                { name: 'Raids', url: 'https://nori.fish/wynn/leaderboard/?type=raids&category=all&page=1' },
                { name: 'Stats', url: 'https://nori.fish/wynn/leaderboard/?type=stats&category=chests&page=1' },
                { name: 'Professions', url: 'https://nori.fish/wynn/leaderboard/?type=professions&category=professionsGlobal&page=1' },
            ],
        },
        {
            title: 'Stats',
            id: 'stats-sub',
            subItems: [
                { name: 'Player', url: 'https://nori.fish/wynn/player' },
                { name: 'Guild', url: 'https://nori.fish/wynn/guild' },
                { name: 'Online Players', url: 'https://nori.fish/wynn/online' },
            ],
        },
        {
            title: 'Utility',
            id: 'utility-sub',
            subItems: [
                { name: 'Server Uptime', url: 'https://nori.fish/wynn/uptime' },
                { name: 'Guild Tower Stats', url: 'https://nori.fish/wynn/tower' },
                { name: 'Mount Material Calculator', url: 'https://nori.fish/wynn/mount' },
            ],
        },
    ];

    sidebarItems.forEach(item => {
        if (item.type === 'category') {
            const categoryEl = document.createElement('div');
            categoryEl.className = 'sidebar-category';
            categoryEl.textContent = item.title;
            sidebar.appendChild(categoryEl);
            return;
        }

        const mainLink = document.createElement('a');
        mainLink.href = '#';
        mainLink.onclick = (event) => {
            event.preventDefault(); 
            toggleSubMenu(item.id);
        };
        mainLink.textContent = item.title;
        sidebar.appendChild(mainLink);

        const subMenu = document.createElement('div');
        subMenu.id = item.id;
        subMenu.className = 'sub-menu'; 

        item.subItems.forEach(subItem => {
            const subLink = document.createElement('a');
            subLink.href = subItem.url;
            subLink.textContent = subItem.name;
            subMenu.appendChild(subLink);
        });

        sidebar.appendChild(subMenu);
    });
}

function setThemeButtonContent(btn, isDark) {
    const isMobile = window.innerWidth <= 768;
    btn.textContent = isMobile ? (isDark ? '☀️' : '🌙') : (isDark ? 'Light Theme' : 'Dark Theme');
    btn.dataset.theme = isDark ? 'dark' : 'light';
}

function toggleTheme() {
    const themeButton = document.getElementById("theme-switch");
    const darkThemeLink = document.getElementById("dark-theme-css");
    const sidebar = document.getElementById("sidebar");
    const menuButton = document.getElementById("menu-button");
    const htmlElement = document.documentElement;

    if (darkThemeLink.disabled) {
        darkThemeLink.disabled = false;
        setThemeButtonContent(themeButton, true);
        themeButton.classList.add("dark-mode");
        sidebar.classList.add("dark-mode");
        menuButton.classList.add("dark-mode");
        htmlElement.classList.add("site-dark");
        htmlElement.classList.remove("site-light");
        localStorage.setItem('theme', 'dark');
    } else {
        darkThemeLink.disabled = true;
        setThemeButtonContent(themeButton, false);
        themeButton.classList.remove("dark-mode");
        sidebar.classList.remove("dark-mode");
        menuButton.classList.remove("dark-mode");
        htmlElement.classList.remove("site-dark");
        htmlElement.classList.add("site-light");
        localStorage.setItem('theme', 'light');
    }
}

document.addEventListener("DOMContentLoaded", function() {
    const isDocsPage = window.location.pathname.includes('/docs');
    
    if (!isDocsPage) {
        const themeButton = document.createElement("button");
        themeButton.id = "theme-switch";
        themeButton.className = "theme-button";
        themeButton.style.position = "absolute";
        themeButton.style.top = "10px";
        themeButton.style.right = "10px";
        themeButton.onclick = toggleTheme;
        const header = document.querySelector("header");
        if (header) {
            if (getComputedStyle(header).position === 'static') {
                header.style.position = 'relative';
            }
            header.appendChild(themeButton);
        }
        const savedTheme = localStorage.getItem('theme');
        const isDarkInit = savedTheme === 'dark' || (!savedTheme && savedTheme !== 'light');
        if (isDarkInit) {
            document.getElementById("dark-theme-css").disabled = false;
            setThemeButtonContent(themeButton, true);
            themeButton.classList.add("dark-mode");
            if (document.getElementById("sidebar")) document.getElementById("sidebar").classList.add("dark-mode");
            if (document.getElementById("menu-button")) document.getElementById("menu-button").classList.add("dark-mode");
            document.documentElement.classList.add("site-dark");
            document.documentElement.classList.remove("site-light");
        } else {
            document.getElementById("dark-theme-css").disabled = true;
            setThemeButtonContent(themeButton, false);
            themeButton.classList.remove("dark-mode");
            if (document.getElementById("sidebar")) document.getElementById("sidebar").classList.remove("dark-mode");
            if (document.getElementById("menu-button")) document.getElementById("menu-button").classList.remove("dark-mode");
            document.documentElement.classList.remove("site-dark");
            document.documentElement.classList.add("site-light");
        }
        window.addEventListener('resize', () => {
            const btn = document.getElementById("theme-switch");
            if (btn) setThemeButtonContent(btn, btn.dataset.theme === 'dark');
        });
    } else {
        document.getElementById("dark-theme-css").disabled = false;
        document.documentElement.classList.add("site-dark");
    }
    
    createSidebar();
});
