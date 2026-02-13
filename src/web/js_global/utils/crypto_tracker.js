/**
 * Crypto Tracker - Top cryptocurrencies via CoinGecko /coins/markets
 * Tracks most major cryptos with price, 24h change, market cap.
 * CoinGecko free tier: ~30 requests/minute — we use a 30s refresh cooldown.
 */
window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['crypto-tracker'] = {
  API_BASE: 'https://api.coingecko.com/api/v3/coins/markets',
  PER_PAGE: 100,
  COOLDOWN_SEC: 10,
  _interval: null,
  _cooldownTimer: null,
  init: function(container) {
    var self = this;
    container.innerHTML =
      '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">🪙 Crypto Tracker</h1>' +
      '<p class="utils-subtitle" style="color:var(--utils-text-dim);font-size:0.85rem;margin-bottom:1rem">Top cryptocurrencies by market cap. Data from CoinGecko. Refresh limited to once every 10s (API ~30/min).</p>' +
      '<div class="utils-row" style="margin-bottom:1rem;flex-wrap:wrap;align-items:center;gap:0.5rem">' +
        '<button class="utils-btn" id="crypto-refresh">Refresh</button>' +
        '<span class="utils-meta" id="crypto-cooldown"></span>' +
        '<select id="crypto-currency" class="utils-select" style="width:auto;margin:0">' +
          '<option value="usd" selected>USD</option><option value="eur">EUR</option>' +
        '</select>' +
        '<span class="utils-meta" id="crypto-meta"></span>' +
      '</div>' +
      '<div class="utils-status" id="crypto-status"></div>' +
      '<div id="crypto-table-wrap" style="overflow-x:auto;max-height:70vh;overflow-y:auto;margin-top:1rem">' +
        '<table class="utils-table" id="crypto-table" style="width:100%;border-collapse:collapse">' +
          '<thead><tr id="crypto-thead-row">' +
            '<th class="crypto-th" data-sort="rank" style="text-align:left;padding:0.5rem;border-bottom:1px solid var(--utils-border);cursor:pointer;user-select:none"># <span class="crypto-th-arrow"></span></th>' +
            '<th class="crypto-th" data-sort="name" style="text-align:left;padding:0.5rem;border-bottom:1px solid var(--utils-border);cursor:pointer;user-select:none">Coin <span class="crypto-th-arrow"></span></th>' +
            '<th class="crypto-th" data-sort="price" style="text-align:right;padding:0.5rem;border-bottom:1px solid var(--utils-border);cursor:pointer;user-select:none">Price <span class="crypto-th-arrow"></span></th>' +
            '<th class="crypto-th" data-sort="change" style="text-align:right;padding:0.5rem;border-bottom:1px solid var(--utils-border);cursor:pointer;user-select:none">24h % <span class="crypto-th-arrow"></span></th>' +
            '<th class="crypto-th" data-sort="cap" style="text-align:right;padding:0.5rem;border-bottom:1px solid var(--utils-border);cursor:pointer;user-select:none">Market Cap <span class="crypto-th-arrow"></span></th>' +
          '</tr></thead><tbody id="crypto-tbody"></tbody>' +
        '</table>' +
      '</div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var currencySelect = container.querySelector('#crypto-currency');
    var refreshBtn = container.querySelector('#crypto-refresh');
    var cooldownEl = container.querySelector('#crypto-cooldown');
    var cachedCoins = [];
    var sortBy = 'rank';
    var sortAsc = false;

    function sortCoins(coins) {
      var arr = coins.slice();
      arr.sort(function(a, b) {
        var va, vb;
        switch (sortBy) {
          case 'rank': va = a.market_cap_rank || 9999; vb = b.market_cap_rank || 9999; break;
          case 'name': va = (a.name || a.symbol || '').toLowerCase(); vb = (b.name || b.symbol || '').toLowerCase(); break;
          case 'price': va = a.current_price || 0; vb = b.current_price || 0; break;
          case 'change': va = a.price_change_percentage_24h ?? -Infinity; vb = b.price_change_percentage_24h ?? -Infinity; break;
          case 'cap': va = a.market_cap || 0; vb = b.market_cap || 0; break;
          default: return 0;
        }
        if (typeof va === 'string') return sortAsc ? (va < vb ? -1 : va > vb ? 1 : 0) : (va > vb ? -1 : va < vb ? 1 : 0);
        return sortAsc ? (va - vb) : (vb - va);
      });
      return arr;
    }

    function updateSortHeaders() {
      container.querySelectorAll('.crypto-th').forEach(function(th) {
        var key = th.getAttribute('data-sort');
        var arrow = th.querySelector('.crypto-th-arrow');
        arrow.textContent = key === sortBy ? (sortAsc ? ' ▲' : ' ▼') : ' ↕';
      });
    }

    function applySortAndRender() {
      if (cachedCoins.length) renderTable(sortCoins(cachedCoins), currencySelect.value);
      updateSortHeaders();
    }

    container.querySelectorAll('.crypto-th').forEach(function(th) {
      th.onclick = function() {
        var key = th.getAttribute('data-sort');
        if (sortBy === key) sortAsc = !sortAsc; else { sortBy = key; sortAsc = key === 'name'; }
        applySortAndRender();
      };
    });

    var lastRefreshTime = 0;
    function canRefresh() { return (Date.now() - lastRefreshTime) / 1000 >= self.COOLDOWN_SEC; }
    function setCooldownUI(secondsLeft) {
      if (secondsLeft > 0) {
        refreshBtn.disabled = true;
        cooldownEl.textContent = 'Refresh in ' + secondsLeft + 's';
        cooldownEl.style.color = 'var(--utils-text-dim)';
      } else {
        refreshBtn.disabled = false;
        cooldownEl.textContent = 'You can refresh now.';
        cooldownEl.style.color = 'var(--utils-success)';
      }
    }
    function startCooldown() {
      if (self._cooldownTimer) clearInterval(self._cooldownTimer);
      lastRefreshTime = Date.now();
      setCooldownUI(self.COOLDOWN_SEC);
      var left = self.COOLDOWN_SEC;
      self._cooldownTimer = setInterval(function() {
        left--;
        setCooldownUI(left);
        if (left <= 0) clearInterval(self._cooldownTimer);
      }, 1000);
    }

    function fetchData() {
      if (!canRefresh()) return;
      startCooldown();
      var currency = currencySelect.value;
      var status = container.querySelector('#crypto-status');
      status.textContent = 'Loading prices from CoinGecko...';
      status.className = 'utils-status loading';
      var url = self.API_BASE + '?vs_currency=' + currency + '&order=market_cap_desc&per_page=' + self.PER_PAGE + '&page=1&sparkline=false&price_change_percentage=24h';
      fetch(url)
        .then(function(r) { return r.json(); })
        .then(function(data) {
          if (!Array.isArray(data) || data.length === 0) throw new Error('No data');
          cachedCoins = data;
          renderTable(sortCoins(data), currency);
          container.querySelector('#crypto-meta').textContent = 'Updated ' + new Date().toLocaleTimeString() + ' · ' + data.length + ' coins';
          status.textContent = '';
          status.className = 'utils-status';
        })
        .catch(function(err) {
          status.textContent = 'Error: ' + (err.message || 'Failed to fetch');
          status.className = 'utils-status err';
        });
    }

    function renderTable(coins, currency) {
      var tbody = container.querySelector('#crypto-tbody');
      var sym = currency === 'eur' ? '€' : '$';
      tbody.innerHTML = coins.map(function(c) {
        var price = c.current_price;
        var priceStr = price >= 1 ? sym + price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) :
          price >= 0.0001 ? sym + price.toFixed(6) : sym + price.toExponential(2);
        var ch = c.price_change_percentage_24h;
        var chStr = ch != null ? (ch >= 0 ? '+' : '') + ch.toFixed(2) + '%' : '--';
        var chClass = ch != null ? (ch >= 0 ? 'var(--utils-success)' : 'var(--utils-danger)') : '';
        var mc = c.market_cap;
        var mcPrefix = currency === 'eur' ? '€' : '$';
        var mcStr = mc != null ? mcPrefix + (mc >= 1e9 ? (mc / 1e9).toFixed(2) + 'B' : mc >= 1e6 ? (mc / 1e6).toFixed(2) + 'M' : mc >= 1e3 ? (mc / 1e3).toFixed(2) + 'K' : mc.toLocaleString()) : '--';
        return '<tr style="border-bottom:1px solid var(--utils-border)">' +
          '<td style="padding:0.5rem;color:var(--utils-text-dim)">' + (c.market_cap_rank || '') + '</td>' +
          '<td style="padding:0.5rem"><img src="' + (c.image || '') + '" alt="" style="width:24px;height:24px;vertical-align:middle;margin-right:8px;border-radius:50%">' +
          '<strong>' + (c.name || c.id) + '</strong> <span style="color:var(--utils-text-dim);font-size:0.85em">' + (c.symbol || '').toUpperCase() + '</span></td>' +
          '<td style="padding:0.5rem;text-align:right;font-family:JetBrains Mono,monospace">' + priceStr + '</td>' +
          '<td style="padding:0.5rem;text-align:right;font-family:JetBrains Mono,monospace;color:' + chClass + '">' + chStr + '</td>' +
          '<td style="padding:0.5rem;text-align:right;font-family:JetBrains Mono,monospace;color:var(--utils-text-dim)">' + mcStr + '</td>' +
          '</tr>';
      }).join('');
      updateSortHeaders();
    }

    currencySelect.onchange = function() { if (cachedCoins.length) renderTable(sortCoins(cachedCoins), currencySelect.value); };
    refreshBtn.onclick = fetchData;
    setCooldownUI(0);
    fetchData();
    this._interval = setInterval(function() { if (canRefresh()) fetchData(); }, 60000);
  },
  destroy: function() {
    if (this._interval) clearInterval(this._interval);
    if (this._cooldownTimer) clearInterval(this._cooldownTimer);
  }
};

// Backward compatibility: bitcoin-tracker redirects to crypto-tracker
window.UtilsTools['bitcoin-tracker'] = window.UtilsTools['crypto-tracker'];
