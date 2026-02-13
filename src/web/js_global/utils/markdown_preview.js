window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['markdown-preview'] = {
  init: function(container) {
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">📄 Markdown Preview</h1>' +
      '<div class="utils-btns" style="margin-bottom:1rem;">' +
      '<button class="utils-btn" id="md-download-html">Download as HTML</button>' +
      '<button class="utils-btn secondary" id="md-download-md">Download as Markdown</button>' +
      '</div>' +
      '<div class="utils-split">' +
      '<div><label>Markdown</label>' +
      '<textarea id="md-input" class="utils-textarea"># Hello\n\n**Bold** and *italic* text.\n\n- List item 1\n- List item 2\n\n[Link](https://example.com)</textarea></div>' +
      '<div><label>Preview</label><div class="utils-preview-box" id="md-preview"></div></div></div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var md = container.querySelector('#md-input');
    var preview = container.querySelector('#md-preview');
    function escape(s) {
      return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
    function parse(t) {
      var s = t
        .replace(/^### (.*)$/gm, '<h3>$1</h3>')
        .replace(/^## (.*)$/gm, '<h2>$1</h2>')
        .replace(/^# (.*)$/gm, '<h1>$1</h1>')
        .replace(/^> (.*)$/gm, '<blockquote>$1</blockquote>')
        .replace(/^- (.*)$/gm, '<li>$1</li>')
        .replace(/(<li>.*?<\/li>\n?)+/gs, function(m) { return '<ul>' + m + '</ul>'; })
        .replace(/^```[\s\S]*?^```/gm, function(m) {
          return '<pre><code>' + escape(m.replace(/^```\w*\n?|^```$/gm, '').trim()) + '</code></pre>';
        });
      s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\*(.+?)\*/g, '<em>$1</em>').replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
      return s.split(/\n\n+/).map(function(p) {
        var t = p.trim();
        if (!t) return '';
        return /^<(h\d|ul|ol|blockquote|pre)/.test(t) ? t : '<p>' + t.replace(/\n/g, '<br>') + '</p>';
      }).join('');
    }
    function render() { preview.innerHTML = parse(md.value); }
    md.oninput = render;
    render();

    function download(filename, content, mime) {
      var blob = new Blob([content], { type: mime });
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      URL.revokeObjectURL(a.href);
    }
    container.querySelector('#md-download-html').onclick = function() {
      var html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Document</title></head><body>' +
        parse(md.value) + '</body></html>';
      download('document.html', html, 'text/html');
    };
    container.querySelector('#md-download-md').onclick = function() {
      download('document.md', md.value, 'text/markdown');
    };
  },
  destroy: function() {}
};
