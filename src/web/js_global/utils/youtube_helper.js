/**
 * YouTube Download Helper - Validates URL, fetches title via oEmbed, links to third-party converters
 */
window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['youtube-helper'] = {
  OEMBED: 'https://www.youtube.com/oembed?url=',
  CONVERTERS: [
    { name: 'yt1s.com', url: 'https://yt1s.com/en/youtube-to-mp3', param: 'url' },
    { name: 'y2mate.com', url: 'https://www.y2mate.com/youtube', param: 'url' },
    { name: 'savefrom.net', url: 'https://en.savefrom.net/1-youtube-video-downloader', param: 'url' }
  ],
  init: function(container) {
    container.innerHTML =
      '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">▶️ YouTube Download Helper</h1>' +
      '<p class="utils-subtitle" style="color:var(--utils-text-dim);font-size:0.85rem;margin-bottom:1rem">Paste a YouTube URL to get the title and open in external converters. Conversion is done by third-party services.</p>' +
      '<label>YouTube URL</label>' +
      '<input type="url" id="yt-url" class="utils-input" placeholder="https://www.youtube.com/watch?v=...">' +
      '<button class="utils-btn" id="yt-fetch" style="margin-top:0.5rem">Fetch & Open</button>' +
      '<div id="yt-result" style="display:none;margin-top:1.5rem">' +
        '<div class="utils-box">' +
          '<img id="yt-thumb" src="" alt="" style="max-width:320px;border-radius:8px;margin-bottom:0.75rem">' +
          '<h3 id="yt-title" style="margin:0 0 1rem 0;font-size:1rem"></h3>' +
          '<label>Open in converter</label>' +
          '<div class="utils-btns" id="yt-btns"></div>' +
        '</div>' +
      '</div>' +
      '<div class="utils-status" id="yt-status"></div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var input = container.querySelector('#yt-url');
    var result = container.querySelector('#yt-result');
    var status = container.querySelector('#yt-status');
    function validYoutubeUrl(url) {
      if (!url || typeof url !== 'string') return false;
      var m = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
      return m ? m[1] : null;
    }
    container.querySelector('#yt-fetch').onclick = function() {
      var url = input.value.trim();
      var vid = validYoutubeUrl(url);
      if (!vid) {
        status.textContent = 'Please enter a valid YouTube URL (youtube.com/watch?v=... or youtu.be/...)';
        status.className = 'utils-status err';
        result.style.display = 'none';
        return;
      }
      var fullUrl = url.indexOf('youtube.com') !== -1 ? url : 'https://www.youtube.com/watch?v=' + vid;
      status.textContent = 'Fetching video info...';
      status.className = 'utils-status loading';
      result.style.display = 'none';
      fetch(window.UtilsTools['youtube-helper'].OEMBED + encodeURIComponent(fullUrl))
        .then(function(r) { return r.json(); })
        .then(function(data) {
          var title = data.title || 'Unknown';
          var thumb = data.thumbnail_url || '';
          container.querySelector('#yt-title').textContent = title;
          var thumbEl = container.querySelector('#yt-thumb');
          thumbEl.src = thumb;
          thumbEl.alt = title;
          var btns = container.querySelector('#yt-btns');
          btns.innerHTML = '';
          window.UtilsTools['youtube-helper'].CONVERTERS.forEach(function(c) {
            var u = c.url + (c.url.indexOf('?') !== -1 ? '&' : '?') + c.param + '=' + encodeURIComponent(fullUrl);
            var a = document.createElement('a');
            a.href = u;
            a.target = '_blank';
            a.rel = 'noopener noreferrer';
            a.className = 'utils-btn secondary';
            a.textContent = c.name;
            btns.appendChild(a);
          });
          result.style.display = 'block';
          status.textContent = '';
          status.className = 'utils-status';
        })
        .catch(function() {
          status.textContent = 'Could not fetch video info. You can still open in converters below.';
          status.className = 'utils-status err';
          container.querySelector('#yt-title').textContent = 'Video ID: ' + vid;
          container.querySelector('#yt-thumb').src = 'https://img.youtube.com/vi/' + vid + '/mqdefault.jpg';
          container.querySelector('#yt-thumb').alt = vid;
          var btns = container.querySelector('#yt-btns');
          btns.innerHTML = '';
          var fullUrl = 'https://www.youtube.com/watch?v=' + vid;
          window.UtilsTools['youtube-helper'].CONVERTERS.forEach(function(c) {
            var u = c.url + (c.url.indexOf('?') !== -1 ? '&' : '?') + c.param + '=' + encodeURIComponent(fullUrl);
            var a = document.createElement('a');
            a.href = u;
            a.target = '_blank';
            a.rel = 'noopener noreferrer';
            a.className = 'utils-btn secondary';
            a.textContent = c.name;
            btns.appendChild(a);
          });
          result.style.display = 'block';
        });
    };
  },
  destroy: function() {}
};
