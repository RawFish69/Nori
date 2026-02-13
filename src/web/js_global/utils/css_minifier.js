window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['css-minifier'] = {
  init: function(container) {
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">⬇️ CSS Minifier</h1>' +
      '<textarea id="css-input" class="utils-textarea" placeholder="Paste CSS here..."></textarea>' +
      '<button class="utils-btn" data-minify>Minify</button>' +
      '<button class="utils-btn" data-beautify>Beautify</button>' +
      '<div class="utils-status" id="css-status"></div>' +
      '<textarea id="css-output" class="utils-textarea" placeholder="Result..." readonly style="margin-top:1rem"></textarea>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var input = container.querySelector('#css-input');
    var output = container.querySelector('#css-output');
    var status = container.querySelector('#css-status');
    container.querySelector('[data-minify]').onclick = function() {
      var c = input.value.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\s+/g, ' ').replace(/\s*([{}:;,>+~])\s*/g, '$1').trim();
      output.value = c;
      var inLen = input.value.length;
      status.textContent = 'Minified: ' + inLen + ' → ' + c.length + ' chars (' + Math.round((1 - c.length / inLen) * 100) + '% smaller)';
      status.className = 'utils-status ok';
    };
    container.querySelector('[data-beautify]').onclick = function() {
      var c = input.value.replace(/\s*{\s*/g, ' {\n  ').replace(/\s*}\s*/g, '\n}\n').replace(/\s*;\s*/g, ';\n  ').replace(/\n\s*\n/g, '\n');
      output.value = c.trim();
      status.textContent = 'Beautified';
      status.className = 'utils-status ok';
    };
  },
  destroy: function() {}
};
