window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['regex-tester'] = {
  init: function(container) {
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">🔍 Regex Tester</h1>' +
      '<label>Regular Expression</label>' +
      '<input type="text" id="regex-input" class="utils-input" placeholder="e.g. \\w+@\\w+\\.\\w+" value="\\w+@\\w+\\.\\w+">' +
      '<div class="utils-options flags"><label><input type="checkbox" id="regex-g"> Global (g)</label>' +
      '<label><input type="checkbox" id="regex-i"> Ignore case (i)</label>' +
      '<label><input type="checkbox" id="regex-m"> Multiline (m)</label></div>' +
      '<label>Test String</label>' +
      '<textarea id="regex-text" class="utils-textarea" placeholder="Text to test against...">test@example.com and admin@site.org</textarea>' +
      '<div class="utils-result" id="regex-result"></div>' +
      '<div class="utils-meta" id="regex-meta"></div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var regexIn = container.querySelector('#regex-input');
    var textIn = container.querySelector('#regex-text');
    var result = container.querySelector('#regex-result');
    var meta = container.querySelector('#regex-meta');
    function test() {
      var flags = [container.querySelector('#regex-g').checked ? 'g' : '',
        container.querySelector('#regex-i').checked ? 'i' : '',
        container.querySelector('#regex-m').checked ? 'm' : ''].join('');
      try {
        var re = new RegExp(regexIn.value, flags);
        var t = textIn.value;
        var matches = Array.from(t.matchAll(re));
        if (matches.length === 0) {
          result.innerHTML = 'No matches';
          result.className = 'utils-result';
          meta.textContent = '';
          return;
        }
        var sorted = matches.map(function(m) { return { i: m.index, l: m[0].length }; });
        var highlighted = t;
        for (var i = sorted.length - 1; i >= 0; i--) {
          var s = sorted[i];
          highlighted = highlighted.slice(0, s.i) + '<span class="utils-match">' + highlighted.slice(s.i, s.i + s.l) + '</span>' + highlighted.slice(s.i + s.l);
        }
        result.innerHTML = highlighted.replace(/\n/g, '<br>');
        result.className = 'utils-result';
        meta.textContent = matches.length + ' match(es)';
      } catch (e) {
        result.innerHTML = '<span class="utils-error">Invalid regex: ' + e.message + '</span>';
        result.className = 'utils-result';
        meta.textContent = '';
      }
    }
    regexIn.oninput = textIn.oninput = test;
    container.querySelectorAll('.flags input').forEach(function(c) { c.onchange = test; });
    test();
  },
  destroy: function() {}
};
