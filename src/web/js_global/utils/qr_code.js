window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['qr-code'] = {
  _scriptLoaded: false,
  init: function(container) {
    var self = this;
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">📱 QR Code Generator</h1>' +
      '<textarea id="qr-input" class="utils-textarea" placeholder="Enter URL or text..." style="min-height:100px">https://example.com</textarea>' +
      '<div class="utils-presets">' +
      '<button data-preset="url">URL</button><button data-preset="wifi">WiFi</button>' +
      '<button data-preset="email">Email</button><button data-preset="phone">Phone</button></div>' +
      '<button class="utils-btn" data-qr-gen>Generate QR Code</button>' +
      '<div id="qr-output" style="display:flex;justify-content:center;align-items:center;min-height:200px"></div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var presets = { url: 'https://example.com', wifi: 'WIFI:T:WPA;S:MyNetwork;P:password123;;', email: 'mailto:you@example.com', phone: 'tel:+1234567890' };
    function loadAndGen() {
      if (typeof QRCode !== 'undefined') {
        self._scriptLoaded = true;
        generate();
      } else {
        var s = document.createElement('script');
        s.src = 'https://cdn.jsdelivr.net/npm/qrcode@1/build/qrcode.min.js';
        s.onload = function() { self._scriptLoaded = true; generate(); };
        document.head.appendChild(s);
      }
    }
    function generate() {
      var txt = (container.querySelector('#qr-input').value || ' ').trim();
      var el = container.querySelector('#qr-output');
      el.innerHTML = '';
      if (typeof QRCode !== 'undefined') {
        var canvas = document.createElement('canvas');
        QRCode.toCanvas(canvas, txt, { width: 200, margin: 2 }, function(err) {
          if (!err) { el.innerHTML = ''; el.appendChild(canvas); }
        });
      } else {
        el.innerHTML = '<p>QR library loading... try again</p>';
      }
    }
    container.querySelectorAll('[data-preset]').forEach(function(btn) {
      btn.onclick = function() {
        container.querySelector('#qr-input').value = presets[btn.getAttribute('data-preset')] || '';
        generate();
      };
    });
    container.querySelector('[data-qr-gen]').onclick = generate;
    container.querySelector('#qr-input').oninput = generate;
    loadAndGen();
  },
  destroy: function() {}
};
