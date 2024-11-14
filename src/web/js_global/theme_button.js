document.addEventListener('DOMContentLoaded', function() {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const sidebar = document.getElementById('sidebar');
    const menuButton = document.getElementById('menu-button');
    const storedTheme = localStorage.getItem('theme') || 'light';

    // Apply stored theme on page load
    if (storedTheme === 'dark') {
        applyDarkTheme();
    } else {
        applyLightTheme();
    }

    // Toggle theme on button click
    themeToggleBtn.addEventListener('click', function() {
        if (document.body.classList.contains('dark-mode')) {
            applyLightTheme();
        } else {
            applyDarkTheme();
        }
    });

    function applyDarkTheme() {
        document.body.classList.add('dark-mode');
        themeToggleBtn.textContent = 'Switch to Light Mode';
        localStorage.setItem('theme', 'dark');

        // Sidebar Dark Mode
        sidebar.style.backgroundColor = '#2c2c2c';
        menuButton.style.backgroundColor = '#2c2c2c';
        sidebar.querySelectorAll('a').forEach(link => link.style.color = '#e8e8e8');
    }

    function applyLightTheme() {
        document.body.classList.remove('dark-mode');
        themeToggleBtn.textContent = 'Switch to Dark Mode';
        localStorage.setItem('theme', 'light');

        // Sidebar Light Mode
        sidebar.style.backgroundColor = '#708090';
        menuButton.style.backgroundColor = '#708090';
        sidebar.querySelectorAll('a').forEach(link => link.style.color = '#fff');
    }
});
