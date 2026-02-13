window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['text-case'] = {
  init: function(container) {
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">🔤 Text Case Converter</h1>' +
      '<textarea id="text-input" class="utils-textarea" placeholder="Type or paste text..."></textarea>' +
      '<div class="utils-btns">' +
      '<button class="utils-btn secondary" data-case="upper">UPPERCASE</button>' +
      '<button class="utils-btn secondary" data-case="lower">lowercase</button>' +
      '<button class="utils-btn secondary" data-case="title">Title Case</button>' +
      '<button class="utils-btn secondary" data-case="sentence">Sentence case</button>' +
      '<button class="utils-btn secondary" data-case="camel">camelCase</button>' +
      '<button class="utils-btn secondary" data-case="pascal">PascalCase</button>' +
      '<button class="utils-btn secondary" data-case="snake">snake_case</button>' +
      '<button class="utils-btn secondary" data-case="kebab">kebab-case</button>' +
      '</div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var input = container.querySelector('#text-input');
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
      };
    });
  },
  destroy: function() {}
};
