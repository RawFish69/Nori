window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['hash-tool'] = {
  init: function(container) {
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">#️⃣ Hash & Encode</h1>' +
      '<div class="utils-tabs"><button class="active" data-tab="hash">Hash</button>' +
      '<button data-tab="base64e">Base64 Encode</button><button data-tab="base64d">Base64 Decode</button>' +
      '<button data-tab="file">File Hash</button></div>' +
      '<div id="hash-panel" class="utils-panel active"><textarea id="hash-input" class="utils-textarea" placeholder="Enter text to hash..."></textarea>' +
      '<button class="utils-btn" data-hash-sha256>SHA-256</button>' +
      '<button class="utils-btn" data-hash-sha384>SHA-384</button>' +
      '<button class="utils-btn" data-hash-sha512>SHA-512</button>' +
      '<div class="utils-result" id="hash-result"></div></div>' +
      '<div id="base64e-panel" class="utils-panel"><textarea id="b64e-input" class="utils-textarea" placeholder="Enter text to encode..."></textarea>' +
      '<button class="utils-btn" data-b64-encode>Encode</button><div class="utils-result" id="b64e-result"></div></div>' +
      '<div id="base64d-panel" class="utils-panel"><textarea id="b64d-input" class="utils-textarea" placeholder="Enter Base64 to decode..."></textarea>' +
      '<button class="utils-btn" data-b64-decode>Decode</button><div class="utils-result" id="b64d-result"></div></div>' +
      '<div id="file-panel" class="utils-panel"><label class="utils-file-label"><input type="file" id="hash-file" class="utils-file-input"> Choose File</label>' +
      '<div class="utils-result" id="file-result" style="margin-top:1rem"></div></div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    function showTab(id) {
      container.querySelectorAll('.utils-panel').forEach(function(p) { p.classList.remove('active'); });
      container.querySelectorAll('.utils-tabs button').forEach(function(b) { b.classList.remove('active'); });
      container.querySelector('#' + id + '-panel').classList.add('active');
      container.querySelector('[data-tab="' + id + '"]').classList.add('active');
    }
    container.querySelectorAll('.utils-tabs button').forEach(function(btn) {
      btn.onclick = function() { showTab(btn.getAttribute('data-tab')); };
    });
    function hashText(algo) {
      var t = container.querySelector('#hash-input').value;
      if (!t) { container.querySelector('#hash-result').textContent = 'Enter text'; return; }
      var enc = new TextEncoder();
      crypto.subtle.digest(algo, enc.encode(t)).then(function(buf) {
        var arr = Array.from(new Uint8Array(buf));
        container.querySelector('#hash-result').textContent = arr.map(function(b) { return b.toString(16).padStart(2, '0'); }).join('');
      });
    }
    container.querySelector('[data-hash-sha256]').onclick = function() { hashText('SHA-256'); };
    container.querySelector('[data-hash-sha384]').onclick = function() { hashText('SHA-384'); };
    container.querySelector('[data-hash-sha512]').onclick = function() { hashText('SHA-512'); };
    container.querySelector('[data-b64-encode]').onclick = function() {
      var t = container.querySelector('#b64e-input').value;
      container.querySelector('#b64e-result').textContent = t ? btoa(unescape(encodeURIComponent(t))) : '';
    };
    container.querySelector('[data-b64-decode]').onclick = function() {
      try {
        var t = container.querySelector('#b64d-input').value;
        container.querySelector('#b64d-result').textContent = t ? decodeURIComponent(escape(atob(t))) : '';
      } catch (e) {
        container.querySelector('#b64d-result').textContent = 'Invalid Base64';
      }
    };
    container.querySelector('#hash-file').onchange = function() {
      var f = this.files[0];
      if (!f) return;
      var resultEl = container.querySelector('#file-result');
      resultEl.innerHTML = 'Reading file...';
      f.arrayBuffer().then(function(buf) {
        resultEl.innerHTML = 'Computing hash...';
        return crypto.subtle.digest('SHA-256', buf);
      }).then(function(hash) {
        var arr = Array.from(new Uint8Array(hash));
        resultEl.innerHTML = '<strong>' + f.name + '</strong><br>SHA-256: ' + arr.map(function(b) { return b.toString(16).padStart(2, '0'); }).join('');
      }).catch(function() {
        resultEl.innerHTML = 'Failed to hash file.';
      });
    };
    container.querySelector('#hash-input').oninput = function() {
      if (container.querySelector('#hash-input').value) hashText('SHA-256');
    };
  },
  destroy: function() {}
};
