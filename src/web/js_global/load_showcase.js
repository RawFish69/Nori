async function fetchShowcaseData() {
    try {
        const response = await fetch('https://nori.fish/api/showcase');
        const data = await response.json();
        displayShowcaseData(data);
    } catch (error) {
        console.error('Error fetching showcase data:', error);
    }
}

function displayShowcaseData(data) {
    const showcaseContainer = document.querySelector('.panel-content');
    showcaseContainer.innerHTML = '';

    data.forEach(item => {
        const card = document.createElement('div');
        card.classList.add('card');

        const buildLink = document.createElement('a');
        buildLink.href = item.url;
        buildLink.textContent = item.title;
        buildLink.classList.add('build-link');

        const iframe = document.createElement('iframe');
        iframe.width = '100%';
        iframe.height = '315'; 
        iframe.src = item.video_url;
        iframe.frameBorder = '0';
        iframe.allowFullscreen = true;

        card.appendChild(buildLink);
        card.appendChild(iframe);

        showcaseContainer.appendChild(card);
    });
}


document.addEventListener('DOMContentLoaded', fetchShowcaseData);
