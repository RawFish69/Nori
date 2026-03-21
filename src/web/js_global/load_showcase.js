let showcaseData = [];
let activeIndex = 0;

async function fetchShowcaseData() {
    try {
        const response = await fetch('https://nori.fish/api/showcase');
        const data = await response.json();
        showcaseData = data;
        buildShowcase(data);
    } catch (error) {
        console.error('Error fetching showcase data:', error);
    }
}

function getYoutubeThumbnail(videoUrl) {
    // Extract video ID from embed URL like https://www.youtube.com/embed/XXXXX
    const match = videoUrl.match(/embed\/([a-zA-Z0-9_-]+)/);
    if (match) {
        return `https://img.youtube.com/vi/${match[1]}/mqdefault.jpg`;
    }
    return '';
}

function buildShowcase(data) {
    const playlist = document.getElementById('playlist');
    const countEl = document.getElementById('playlist-count');
    if (!playlist) return;

    playlist.innerHTML = '';

    if (!data || data.length === 0) return;

    if (countEl) countEl.textContent = `${data.length} videos`;

    data.forEach((item, index) => {
        const el = document.createElement('div');
        el.classList.add('playlist-item');
        if (index === 0) el.classList.add('active');

        const indexSpan = document.createElement('span');
        indexSpan.classList.add('playlist-item-index');
        indexSpan.textContent = index + 1;

        const thumb = document.createElement('img');
        thumb.classList.add('playlist-item-thumb');
        thumb.src = getYoutubeThumbnail(item.video_url);
        thumb.alt = item.title;
        thumb.loading = 'lazy';

        const info = document.createElement('div');
        info.classList.add('playlist-item-info');

        const title = document.createElement('span');
        title.classList.add('playlist-item-title');
        title.textContent = item.title;

        info.appendChild(title);
        el.appendChild(indexSpan);
        el.appendChild(thumb);
        el.appendChild(info);

        el.addEventListener('click', () => selectVideo(index));
        playlist.appendChild(el);
    });

    // Load first video
    selectVideo(0);
}

function selectVideo(index) {
    if (!showcaseData[index]) return;
    activeIndex = index;

    const item = showcaseData[index];
    const player = document.getElementById('main-player');
    const titleEl = document.getElementById('now-playing-link');
    const buildEl = document.getElementById('now-playing-build');

    if (player) player.src = item.video_url;
    if (titleEl) {
        titleEl.textContent = item.title;
        titleEl.href = item.url;
    }

    // Update active state in playlist
    const items = document.querySelectorAll('.playlist-item');
    items.forEach((el, i) => {
        el.classList.toggle('active', i === index);
    });

    // Scroll active item into view
    const activeItem = items[index];
    if (activeItem) {
        activeItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

document.addEventListener('DOMContentLoaded', fetchShowcaseData);
