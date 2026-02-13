/**
 * Nori Utils SPA - Hash-based router and tool loader
 */
(function() {
  'use strict';

  const TOOL_SLUGS = [
    'system-analyzer', 'json-tool', 'timestamp', 'html-minifier', 'css-minifier', 'regex-tester', 'world-clock',
    'password-gen', 'hash-tool', 'uuid-gen', 'url-encoder',
    'image-converter', 'qr-code', 'color-picker', 'mp4-to-gif', 'video-compressor',
    'notes', 'lorem', 'markdown-preview', 'text-toolkit', 'text-case',
    'crypto-tracker', 'bitcoin-tracker', 'youtube-helper', 'chat-assistant'
  ];

  const SLUG_TO_SCRIPT = {
    'system-analyzer': 'system_analyzer.js',
    'json-tool': 'json_tool.js',
    'timestamp': 'timestamp.js',
    'html-minifier': 'html_minifier.js',
    'css-minifier': 'css_minifier.js',
    'regex-tester': 'regex_tester.js',
    'world-clock': 'world_clock.js',
    'password-gen': 'password_gen.js',
    'hash-tool': 'hash_tool.js',
    'uuid-gen': 'uuid_gen.js',
    'url-encoder': 'url_encoder.js',
    'image-converter': 'image_converter.js',
    'qr-code': 'qr_code.js',
    'color-picker': 'color_picker.js',
    'mp4-to-gif': 'mp4_to_gif.js',
    'video-compressor': 'video_compressor.js',
    'notes': 'notes.js',
    'lorem': 'lorem.js',
    'markdown-preview': 'markdown_preview.js',
    'text-toolkit': 'text_toolkit.js',
    'text-case': 'text_toolkit.js',
    'crypto-tracker': 'crypto_tracker.js',
    'bitcoin-tracker': 'crypto_tracker.js',
    'youtube-helper': 'youtube_helper.js',
    'chat-assistant': 'chat_assistant.js'
  };

  window.UtilsTools = window.UtilsTools || {};
  let currentTool = null;
  let currentDestroy = null;

  const homeEl = document.getElementById('utils-home');
  const toolViewEl = document.getElementById('utils-tool-view');

  function getBasePath() {
    const script = document.currentScript || document.querySelector('script[src*="utils_app"]');
    if (script && script.src) {
      const src = script.src;
      return src.replace(/utils_app\.js.*$/, '');
    }
    return '../js_global/';
  }

  function loadScript(src) {
    return new Promise(function(resolve, reject) {
      if (document.querySelector('script[src="' + src + '"]')) {
        resolve();
        return;
      }
      const s = document.createElement('script');
      s.src = src;
      s.onload = resolve;
      s.onerror = reject;
      document.body.appendChild(s);
    });
  }

  function showHome() {
    if (homeEl) homeEl.style.display = 'block';
    if (toolViewEl) toolViewEl.style.display = 'none';
    if (currentDestroy) {
      try { currentDestroy(); } catch (e) { console.warn(e); }
      currentDestroy = null;
    }
    currentTool = null;
  }

  function trackPageView(slug) {
    if (typeof gtag === 'function') {
      gtag('event', 'page_view', { page_path: '/utils#' + (slug || ''), page_title: slug ? slug.replace(/-/g, ' ') + ' - Nori Utils' : 'Nori Utils' });
    }
  }

  function showTool(slug) {
    if (!TOOL_SLUGS.includes(slug)) {
      showHome();
      trackPageView('');
      return;
    }
    trackPageView(slug);
    if (homeEl) homeEl.style.display = 'none';
    if (toolViewEl) toolViewEl.style.display = 'block';

    if (currentDestroy) {
      try { currentDestroy(); } catch (e) { console.warn(e); }
      currentDestroy = null;
    }

    const scriptName = SLUG_TO_SCRIPT[slug];
    const basePath = getBasePath();
    const scriptPath = basePath + 'utils/' + scriptName;

    loadScript(scriptPath).then(function() {
      const tool = window.UtilsTools[slug];
      if (!tool || typeof tool.init !== 'function') {
        showHome();
        return;
      }
      toolViewEl.innerHTML = '';
      const container = document.createElement('div');
      container.className = 'utils-tool-view';
      toolViewEl.appendChild(container);
      try {
        tool.init(container);
        currentTool = slug;
        currentDestroy = tool.destroy || null;
      } catch (e) {
        console.error('Tool init error:', e);
        showHome();
      }
    }).catch(function(err) {
      console.error('Failed to load tool:', err);
      showHome();
    });
  }

  function route() {
    const hash = window.location.hash.slice(1);
    if (!hash) {
      trackPageView('');
      showHome();
      return;
    }
    showTool(hash);
  }

  function initClock() {
    const clock = document.getElementById('utils-clock');
    if (!clock) return;
    function tick() {
      clock.textContent = new Date().toLocaleTimeString('en-US', { hour12: false });
    }
    tick();
    setInterval(tick, 1000);
  }

  function init() {
    if (!homeEl || !toolViewEl) return;
    initClock();
    route();
    window.addEventListener('hashchange', route);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
