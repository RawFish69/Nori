window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['uuid-gen'] = {
  init: function(container) {
    function uuidv4() {
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
    }
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">🆔 UUID Generator</h1>' +
      '<div class="utils-output"><span id="uuid-display">-</span>' +
      '<button class="utils-btn" data-copy-uuid>Copy</button>' +
      '<span class="utils-copied" id="uuid-copied"></span></div>' +
      '<button class="utils-btn" data-gen-1>Generate</button>' +
      '<button class="utils-btn secondary" data-gen-5>Generate 5</button>' +
      '<button class="utils-btn secondary" data-gen-10>Generate 10</button>' +
      '<div class="utils-list" id="uuid-list"></div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var display = container.querySelector('#uuid-display');
    var list = container.querySelector('#uuid-list');
    function generate(n) {
      var uuids = [];
      for (var i = 0; i < n; i++) uuids.push(uuidv4());
      if (n === 1) {
        display.textContent = uuids[0];
        list.innerHTML = '';
      } else {
        display.textContent = '-';
        list.innerHTML = uuids.map(function(u) {
          return '<div><span class="uuid-val">' + u + '</span><button class="uuid-copy">Copy</button></div>';
        }).join('');
        list.querySelectorAll('.uuid-copy').forEach(function(btn) {
          btn.onclick = function() {
            var u = btn.previousElementSibling.textContent;
            navigator.clipboard.writeText(u);
          };
        });
      }
    }
    container.querySelector('[data-gen-1]').onclick = function() { generate(1); };
    container.querySelector('[data-gen-5]').onclick = function() { generate(5); };
    container.querySelector('[data-gen-10]').onclick = function() { generate(10); };
    container.querySelector('[data-copy-uuid]').onclick = function() {
      var u = display.textContent;
      if (u && u !== '-') {
        navigator.clipboard.writeText(u).then(function() {
          container.querySelector('#uuid-copied').textContent = 'Copied!';
          setTimeout(function() { container.querySelector('#uuid-copied').textContent = ''; }, 1500);
        });
      }
    };
    generate(1);
  },
  destroy: function() {}
};
