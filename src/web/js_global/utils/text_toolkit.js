/**
 * Text Toolkit - Word/character analysis, case conversion, text transforms
 * Replaces text-case with expanded features
 */
window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['text-toolkit'] = {
  init: function(container) {
    container.innerHTML =
      '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">🔤 Text Toolkit</h1>' +
      '<div class="utils-box" id="text-stats-box">' +
        '<div class="utils-live-dashboard" id="text-stats">' +
          '<div class="utils-live-card"><span class="utils-live-card-label">Words</span><span class="utils-live-card-value" id="stat-words">0</span></div>' +
          '<div class="utils-live-card"><span class="utils-live-card-label">Characters</span><span class="utils-live-card-value" id="stat-chars">0</span></div>' +
          '<div class="utils-live-card"><span class="utils-live-card-label">No spaces</span><span class="utils-live-card-value" id="stat-chars-ns">0</span></div>' +
          '<div class="utils-live-card"><span class="utils-live-card-label">Lines</span><span class="utils-live-card-value" id="stat-lines">0</span></div>' +
          '<div class="utils-live-card"><span class="utils-live-card-label">Paragraphs</span><span class="utils-live-card-value" id="stat-paras">0</span></div>' +
          '<div class="utils-live-card"><span class="utils-live-card-label">Reading time</span><span class="utils-live-card-value" id="stat-reading">~0 min</span></div>' +
        '</div>' +
      '</div>' +
      '<textarea id="text-input" class="utils-textarea" placeholder="Type or paste text..."></textarea>' +
      '<label>Case conversion</label>' +
      '<div class="utils-btns">' +
        '<button class="utils-btn secondary" data-case="upper">UPPERCASE</button>' +
        '<button class="utils-btn secondary" data-case="lower">lowercase</button>' +
        '<button class="utils-btn secondary" data-case="title">Title Case</button>' +
        '<button class="utils-btn secondary" data-case="sentence">Sentence case</button>' +
        '<button class="utils-btn secondary" data-case="camel">camelCase</button>' +
        '<button class="utils-btn secondary" data-case="pascal">PascalCase</button>' +
        '<button class="utils-btn secondary" data-case="snake">snake_case</button>' +
        '<button class="utils-btn secondary" data-case="kebab">kebab-case</button>' +
      '</div>' +
      '<label>Text transforms</label>' +
      '<div class="utils-btns">' +
        '<button class="utils-btn secondary" data-action="reverse">Reverse text</button>' +
        '<button class="utils-btn secondary" data-action="remove-spaces">Remove extra spaces</button>' +
        '<button class="utils-btn secondary" data-action="remove-breaks">Remove line breaks</button>' +
      '</div>';

    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };

    var input = container.querySelector('#text-input');

    function updateStats() {
      var t = input.value;
      var words = t.trim() ? t.trim().split(/\s+/).length : 0;
      var chars = t.length;
      var charsNoSpace = t.replace(/\s/g, '').length;
      var lines = t ? (t.split(/\r?\n/).length) : 0;
      var paras = t.trim() ? t.trim().split(/\n\s*\n/).length : 0;
      var wpm = 200;
      var readingMin = Math.max(0, Math.ceil(words / wpm));
      var readingStr = readingMin < 1 ? '< 1 min' : '~' + readingMin + ' min';

      container.querySelector('#stat-words').textContent = words;
      container.querySelector('#stat-chars').textContent = chars;
      container.querySelector('#stat-chars-ns').textContent = charsNoSpace;
      container.querySelector('#stat-lines').textContent = lines;
      container.querySelector('#stat-paras').textContent = paras;
      container.querySelector('#stat-reading').textContent = readingStr;
    }

    input.addEventListener('input', updateStats);
    input.addEventListener('paste', function() { setTimeout(updateStats, 0); });
    updateStats();

    container.querySelectorAll('[data-case]').forEach(function(btn) {
      btn.onclick = function() {
        var type = btn.getAttribute('data-case');
        var t = input.value;
        switch (type) {
          case 'upper': t = t.toUpperCase(); break;
          case 'lower': t = t.toLowerCase(); break;
          case 'title': t = t.toLowerCase().replace(/\b\w/g, function(c) { return c.toUpperCase(); }); break;
          case 'sentence': t = t.toLowerCase().replace(/(^\w|\.\s+\w)/g, function(c) { return c.toUpperCase(); }); break;
          case 'pascal': t = t.toLowerCase().replace(/(?:^|[^a-z0-9])(.)/g, function(_, c) { return c.toUpperCase(); }); break;
          case 'camel': t = t.toLowerCase().replace(/[^a-z0-9]+(.)/g, function(_, c) { return c.toUpperCase(); }); t = t.charAt(0).toLowerCase() + t.slice(1); break;
          case 'snake': t = t.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, ''); break;
          case 'kebab': t = t.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''); break;
        }
        input.value = t;
        updateStats();
      };
    });

    container.querySelectorAll('[data-action]').forEach(function(btn) {
      btn.onclick = function() {
        var action = btn.getAttribute('data-action');
        var t = input.value;
        switch (action) {
          case 'reverse': t = t.split('').reverse().join(''); break;
          case 'remove-spaces': t = t.replace(/\s+/g, ' ').trim(); break;
          case 'remove-breaks': t = t.replace(/\r?\n/g, ' ').replace(/\s+/g, ' ').trim(); break;
        }
        input.value = t;
        updateStats();
      };
    });
  },
  destroy: function() {}
};

// Backward compatibility: text-case redirects to text-toolkit
window.UtilsTools['text-case'] = window.UtilsTools['text-toolkit'];
