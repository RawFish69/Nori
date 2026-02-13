window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['json-tool'] = {
  init: function(container) {
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">{} JSON Formatter</h1>' +
      '<textarea id="json-input" class="utils-textarea" placeholder="Paste JSON here..." style="min-height:200px">{"name":"example","count":42}</textarea>' +
      '<div class="utils-btns">' +
      '<button class="utils-btn" data-format>Pretty Print</button>' +
      '<button class="utils-btn secondary" data-minify>Minify</button>' +
      '<button class="utils-btn secondary" data-validate>Validate</button>' +
      '<button class="utils-btn secondary" data-download>Download as .json</button></div>' +
      '<div class="utils-status" id="json-status"></div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var input = container.querySelector('#json-input');
    var status = container.querySelector('#json-status');
    function setStatus(msg, ok) { status.textContent = msg; status.className = 'utils-status ' + (ok ? 'ok' : 'err'); }
    container.querySelector('[data-format]').onclick = function() {
      try {
        var j = JSON.parse(input.value);
        input.value = JSON.stringify(j, null, 2);
        setStatus('✓ Formatted', true);
      } catch (e) { setStatus('Error: ' + e.message, false); }
    };
    container.querySelector('[data-minify]').onclick = function() {
      try {
        var j = JSON.parse(input.value);
        input.value = JSON.stringify(j);
        setStatus('✓ Minified', true);
      } catch (e) { setStatus('Error: ' + e.message, false); }
    };
    container.querySelector('[data-validate]').onclick = function() {
      try {
        JSON.parse(input.value);
        setStatus('✓ Valid JSON', true);
      } catch (e) { setStatus('Invalid: ' + e.message, false); }
    };
    container.querySelector('[data-download]').onclick = function() {
      try {
        var j = JSON.parse(input.value);
        var content = JSON.stringify(j, null, 2);
        var blob = new Blob([content], { type: 'application/json' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'output.json';
        a.click();
        URL.revokeObjectURL(a.href);
        setStatus('✓ Downloaded', true);
      } catch (e) { setStatus('Error: ' + e.message, false); }
    };
  },
  destroy: function() {}
};
