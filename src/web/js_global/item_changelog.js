document.addEventListener('DOMContentLoaded', async function() {
    await fetchChangelogDates();
    await displayLatestChangelog('item');
    await displayLatestChangelog('ingredient');
});

async function fetchChangelogDates() {
    const response = await fetch('https://nori.fish/api/changelog/all');
    const data = await response.json();

    const itemDates = data.item.sort((a, b) => new Date(b) - new Date(a));
    const ingredientDates = data.ingredient.sort((a, b) => new Date(b) - new Date(a));

    const itemChangelogContainer = document.getElementById('historical-item-changelogs');
    const ingredientChangelogContainer = document.getElementById('historical-ingredient-changelogs');

    itemDates.forEach(date => {
        const button = document.createElement('button');
        button.id = `item-changelog-${date}-button`;
        button.className = 'changelog-button';
        button.textContent = `View changelog ${date}`;
        button.onclick = () => toggleHistoricalChangelog(`item-changelog-${date}`, button.id, `item/${date}`);
        itemChangelogContainer.appendChild(button);

        const div = document.createElement('div');
        div.id = `item-changelog-${date}`;
        div.className = 'changelog';
        div.innerHTML = `<zero-md src=""></zero-md>`;
        itemChangelogContainer.appendChild(div);
    });

    ingredientDates.forEach(date => {
        const button = document.createElement('button');
        button.id = `ingredient-changelog-${date}-button`;
        button.className = 'changelog-button';
        button.textContent = `View changelog ${date}`;
        button.onclick = () => toggleHistoricalChangelog(`ingredient-changelog-${date}`, button.id, `ingredient/${date}`);
        ingredientChangelogContainer.appendChild(button);

        const div = document.createElement('div');
        div.id = `ingredient-changelog-${date}`;
        div.className = 'changelog';
        div.innerHTML = `<zero-md src=""></zero-md>`;
        ingredientChangelogContainer.appendChild(div);
    });
}

function setChangelogButtonText(buttonId, text) {
    var button = document.getElementById(buttonId);
    if (button) {
        button.textContent = text;
    }
}

function toggleChangelog(changelogId, buttonId) {
    var changelog = document.getElementById(changelogId);
    var button = document.getElementById(buttonId);
    var showText = 'View changelog';
    var hideText = 'Hide changelog';

    if (changelog.style.display === 'none' || changelog.style.display === '') {
        changelog.style.display = 'block';
        button.textContent = hideText;
    } else {
        changelog.style.display = 'none';
        button.textContent = button.dataset.originalText || showText;
    }
}

function toggleHistoricalChangelog(changelogId, buttonId, apiPath) {
    var changelog = document.getElementById(changelogId);
    var button = document.getElementById(buttonId);
    
    if (!button.dataset.originalText) {
        button.dataset.originalText = button.textContent;
    }

    toggleChangelog(changelogId, buttonId);

    if (changelog.style.display === 'block' && changelog.querySelector('zero-md').getAttribute('src') === '') {
        changelog.querySelector('zero-md').setAttribute('src', `https://nori.fish/api/changelog/${apiPath}`);
    }
}

async function displayLatestChangelog(type) {
    const response = await fetch('https://nori.fish/api/changelog/all');
    const data = await response.json();

    const latestDate = data[type].sort((a, b) => new Date(b) - new Date(a))[0];

    const latestChangelogDiv = document.getElementById(`${type}-changelog`);
    latestChangelogDiv.querySelector('zero-md').setAttribute('src', `https://nori.fish/api/changelog/${type}/${latestDate}`);
}
