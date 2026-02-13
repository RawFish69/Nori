window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['url-encoder'] = {
  init: function(container) {
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">🔗 URL Encoder / Decoder</h1>' +
      '<textarea id="url-input" class="utils-textarea" placeholder="Enter text or URL..." style="min-height:100px"></textarea>' +
      '<button class="utils-btn" data-encode>Encode</button>' +
      '<button class="utils-btn" data-decode>Decode</button>' +
      '<textarea id="url-output" class="utils-textarea" placeholder="Result..." readonly style="margin-top:0.5rem;min-height:100px"></textarea>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var input = container.querySelector('#url-input');
    var output = container.querySelector('#url-output');
    container.querySelector('[data-encode]').onclick = function() {
      output.value = encodeURIComponent(input.value);
    };
    container.querySelector('[data-decode]').onclick = function() {
      try {
        output.value = decodeURIComponent(input.value);
      } catch (e) {
        output.value = 'Error: Invalid encoded string';
      }
    };
  },
  destroy: function() {}
};
