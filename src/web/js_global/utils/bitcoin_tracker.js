/**
 * Bitcoin Price Tracker - CoinGecko API, USD/EUR, 24h change, auto-refresh
 */
window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['bitcoin-tracker'] = {
  API: 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,eur&include_24hr_change=true',
  _interval: null,
  init: function(container) {
    var self = this;
    container.innerHTML =
      '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">₿ Bitcoin Price Tracker</h1>' +
      '<div class="utils-live-dashboard" style="margin-bottom:1rem">' +
        '<div class="utils-live-card"><span class="utils-live-card-label">USD</span><span class="utils-live-card-value" id="btc-usd">--</span></div>' +
        '<div class="utils-live-card"><span class="utils-live-card-label">EUR</span><span class="utils-live-card-value" id="btc-eur">--</span></div>' +
        '<div class="utils-live-card"><span class="utils-live-card-label">24h Change</span><span class="utils-live-card-value" id="btc-change">--</span></div>' +
      '</div>' +
      '<button class="utils-btn" id="btc-refresh">Refresh</button>' +
      '<span class="utils-meta" id="btc-meta" style="margin-left:1rem">Auto-refresh every 60s</span>' +
      '<div class="utils-status" id="btc-status"></div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    function fetchPrice() {
      var status = container.querySelector('#btc-status');
      status.textContent = 'Loading...';
      status.className = 'utils-status loading';
      fetch(self.API)
        .then(function(r) { return r.json(); })
        .then(function(data) {
          var btc = data.bitcoin;
          if (!btc) throw new Error('No data');
          var usd = btc.usd;
          var eur = btc.eur;
          var ch = btc.usd_24h_change;
          container.querySelector('#btc-usd').textContent = usd != null ? '$' + usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '--';
          container.querySelector('#btc-eur').textContent = eur != null ? '€' + eur.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '--';
          var changeEl = container.querySelector('#btc-change');
          if (ch != null) {
            changeEl.textContent = (ch >= 0 ? '+' : '') + ch.toFixed(2) + '%';
            changeEl.style.color = ch >= 0 ? 'var(--utils-success)' : 'var(--utils-danger)';
          } else {
            changeEl.textContent = '--';
            changeEl.style.color = '';
          }
          container.querySelector('#btc-meta').textContent = 'Updated ' + new Date().toLocaleTimeString();
          status.textContent = '';
          status.className = 'utils-status';
        })
        .catch(function(err) {
          status.textContent = 'Error: ' + (err.message || 'Failed to fetch');
          status.className = 'utils-status err';
        });
    }
    container.querySelector('#btc-refresh').onclick = fetchPrice;
    fetchPrice();
    this._interval = setInterval(fetchPrice, 60000);
  },
  destroy: function() {
    if (this._interval) clearInterval(this._interval);
  }
};
