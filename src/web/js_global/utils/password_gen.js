window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['password-gen'] = {
  init: function(container) {
    var words = ['alpha','bravo','cobra','delta','echo','foxtrot','golf','hotel','india','juliet','kilo','lima','mike','november','oscar','papa','quebec','romeo','sierra','tango','uniform','victor','whiskey','xray','yankee','zulu','atom','byte','code','data','edge','flux','grid','hash','icon','java','key','loop','mode','node','port','query','root','sync','type','unit','void','zone'];
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">🔐 Password Generator</h1>' +
      '<div class="utils-output"><input type="text" id="pass-output" readonly value="Click Generate">' +
      '<button class="utils-btn" data-copy>Copy</button><span class="utils-copied" id="pass-copied"></span></div>' +
      '<div class="utils-options"><label><input type="number" id="pass-len" value="16" min="4" max="128"> Length</label>' +
      '<label><input type="checkbox" id="pass-upper" checked> Uppercase (A-Z)</label>' +
      '<label><input type="checkbox" id="pass-lower" checked> Lowercase (a-z)</label>' +
      '<label><input type="checkbox" id="pass-numbers" checked> Numbers (0-9)</label>' +
      '<label><input type="checkbox" id="pass-symbols" checked> Symbols (!@#$%^&*)</label>' +
      '<label><input type="checkbox" id="pass-ambig"> Exclude ambiguous (0O1lI)</label>' +
      '<div class="utils-row"><button class="utils-btn" data-generate>Generate</button>' +
      '<button class="utils-btn secondary" data-passphrase>Passphrase</button></div></div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var output = container.querySelector('#pass-output');
    var copied = container.querySelector('#pass-copied');
    function gen() {
      var chars = '';
      if (container.querySelector('#pass-upper').checked) chars += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
      if (container.querySelector('#pass-lower').checked) chars += 'abcdefghijklmnopqrstuvwxyz';
      if (container.querySelector('#pass-numbers').checked) chars += container.querySelector('#pass-ambig').checked ? '23456789' : '0123456789';
      if (container.querySelector('#pass-symbols').checked) chars += '!@#$%^&*()_+-=[]{}|;:,.<>?';
      if (!chars) { output.value = 'Select at least one option'; return; }
      var len = parseInt(container.querySelector('#pass-len').value) || 16;
      var pass = '';
      var arr = new Uint32Array(len);
      crypto.getRandomValues(arr);
      for (var i = 0; i < len; i++) pass += chars[arr[i] % chars.length];
      output.value = pass;
    }
    function passphrase() {
      var len = Math.min(parseInt(container.querySelector('#pass-len').value) || 5, 10);
      var p = [];
      var arr = new Uint32Array(len);
      crypto.getRandomValues(arr);
      for (var i = 0; i < len; i++) p.push(words[arr[i] % words.length]);
      output.value = p.join('-');
    }
    container.querySelector('[data-generate]').onclick = gen;
    container.querySelector('[data-passphrase]').onclick = passphrase;
    container.querySelector('[data-copy]').onclick = function() {
      var v = output.value;
      if (v && v !== 'Click Generate') {
        navigator.clipboard.writeText(v).then(function() {
          copied.textContent = 'Copied!';
          setTimeout(function() { copied.textContent = ''; }, 1500);
        });
      }
    };
    gen();
  },
  destroy: function() {}
};
