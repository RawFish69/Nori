window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['html-minifier'] = {
  init: function(container) {
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">⬇️ HTML Minifier</h1>' +
      '<textarea id="html-input" class="utils-textarea" placeholder="Paste HTML here..."></textarea>' +
      '<button class="utils-btn" data-minify>Minify</button>' +
      '<button class="utils-btn" data-beautify>Beautify</button>' +
      '<div class="utils-status" id="html-status"></div>' +
      '<textarea id="html-output" class="utils-textarea" placeholder="Result..." readonly style="margin-top:1rem"></textarea>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var input = container.querySelector('#html-input');
    var output = container.querySelector('#html-output');
    var status = container.querySelector('#html-status');
    container.querySelector('[data-minify]').onclick = function() {
      var h = input.value;
      h = h.replace(/<!--[\s\S]*?-->/g, '').replace(/>\s+</g, '><').replace(/\s+/g, ' ').trim();
      output.value = h;
      var inLen = input.value.length;
      status.textContent = 'Minified: ' + inLen + ' → ' + h.length + ' chars (' + Math.round((1 - h.length / inLen) * 100) + '% smaller)';
      status.className = 'utils-status ok';
    };
    container.querySelector('[data-beautify]').onclick = function() {
      var h = input.value.replace(/>\s+</g, '>\n<');
      var parts = h.split(/(<[^>]+>)/);
      var out = '', indent = 0;
      var inline = ['span','a','strong','em','b','i','code','small'];
      for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        if (p.match(/^<\//)) { indent = Math.max(0, indent - 1); out += '\n' + '  '.repeat(indent) + p; }
        else if (p.match(/^<\w/)) {
          out += '\n' + '  '.repeat(indent) + p;
          if (!p.match(/\/>|^<(br|hr|img|input|meta|link)/i)) {
            var tag = p.match(/<(\w+)/);
            if (tag && inline.indexOf(tag[1].toLowerCase()) === -1) indent++;
          }
        } else if (p.trim()) out += p;
      }
      output.value = out.trim();
      status.textContent = 'Beautified';
      status.className = 'utils-status ok';
    };
  },
  destroy: function() {}
};
