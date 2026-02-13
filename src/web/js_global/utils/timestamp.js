window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['timestamp'] = {
  _interval: null,
  init: function(container) {
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">⏱️ Timestamp Converter</h1>' +
      '<div class="utils-box"><label>Unix Timestamp (seconds or ms)</label>' +
      '<input type="text" id="ts-unix" placeholder="1699900000 or 1699900000000">' +
      '<button class="utils-btn" data-unix-to-date>Convert to Date</button>' +
      '<div class="utils-result-text" id="ts-unix-result"></div></div>' +
      '<div class="utils-box"><label>Date / Time</label>' +
      '<input type="datetime-local" id="ts-date">' +
      '<button class="utils-btn" data-date-to-unix>Convert to Unix</button>' +
      '<div class="utils-result-text" id="ts-date-result"></div></div>' +
      '<div class="utils-box"><label>Now</label>' +
      '<div class="utils-result-text">Unix: <span id="ts-now-unix"></span></div>' +
      '<div class="utils-result-text">ISO: <span id="ts-now-iso"></span></div></div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    function tick() {
      var n = Date.now();
      container.querySelector('#ts-now-unix').textContent = n;
      container.querySelector('#ts-now-iso').textContent = new Date().toISOString();
    }
    this._interval = setInterval(tick, 1000);
    tick();
    function unixToDate() {
      var v = container.querySelector('#ts-unix').value.trim();
      if (!v) { container.querySelector('#ts-unix-result').textContent = ''; return; }
      var ts = parseInt(v, 10);
      if (ts < 1e12) ts *= 1000;
      try {
        container.querySelector('#ts-unix-result').textContent = new Date(ts).toLocaleString();
      } catch (e) {
        container.querySelector('#ts-unix-result').textContent = 'Invalid';
      }
    }
    function dateToUnix() {
      var v = container.querySelector('#ts-date').value;
      if (!v) { container.querySelector('#ts-date-result').textContent = ''; return; }
      var d = new Date(v);
      container.querySelector('#ts-date-result').textContent = 'Unix: ' + Math.floor(d.getTime() / 1000) + ' (ms: ' + d.getTime() + ')';
    }
    container.querySelector('[data-unix-to-date]').onclick = unixToDate;
    container.querySelector('[data-date-to-unix]').onclick = dateToUnix;
    container.querySelector('#ts-unix').oninput = unixToDate;
    container.querySelector('#ts-date').oninput = dateToUnix;
  },
  destroy: function() {
    if (this._interval) clearInterval(this._interval);
  }
};
