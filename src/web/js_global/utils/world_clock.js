/**
 * World Clock - Multiple timezones, localStorage favorites, 12h/24h toggle
 */
window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['world-clock'] = {
  STORAGE_KEY: 'nori-world-clock-favorites',
  FORMAT_KEY: 'nori-world-clock-12h',
  init: function(container) {
    var self = this;
    var zones = this._loadFavorites();
    var use12h = this._loadFormat();
    var tzList = [
      'America/New_York', 'America/Los_Angeles', 'America/Chicago', 'America/Denver',
      'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Moscow',
      'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Hong_Kong', 'Asia/Singapore', 'Asia/Dubai',
      'Australia/Sydney', 'Pacific/Auckland', 'UTC'
    ];
    container.innerHTML =
      '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title wc-title">🌍 World Clock</h1>' +
      '<p class="utils-subtitle wc-subtitle">Track multiple timezones. Favorites are saved.</p>' +
      '<div class="wc-controls">' +
        '<div class="wc-control-group">' +
          '<label>Add timezone</label>' +
          '<div class="utils-row">' +
            '<select id="wc-tz-select" class="utils-select wc-select">' +
              tzList.map(function(tz) { return '<option value="' + tz + '">' + tz.replace(/_/g, ' ') + '</option>'; }).join('') +
            '</select>' +
            '<button class="utils-btn" id="wc-add">Add</button>' +
          '</div>' +
        '</div>' +
        '<div class="wc-control-group wc-format-toggle">' +
          '<label>Time format</label>' +
          '<div class="wc-toggle-group">' +
            '<button type="button" class="wc-toggle-btn' + (use12h ? '' : ' active') + '" data-format="24">24-hour</button>' +
            '<button type="button" class="wc-toggle-btn' + (use12h ? ' active' : '') + '" data-format="12">12-hour AM/PM</button>' +
          '</div>' +
        '</div>' +
      '</div>' +
      '<div class="wc-clocks-grid" id="wc-clocks"></div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var clocksEl = container.querySelector('#wc-clocks');
    var select = container.querySelector('#wc-tz-select');
    function getUtcOffset(tz) {
      try {
        var formatter = new Intl.DateTimeFormat('en-US', { timeZone: tz, timeZoneName: 'shortOffset' });
        var parts = formatter.formatToParts(new Date());
        var part = parts.find(function(p) { return p.type === 'timeZoneName'; });
        return part ? part.value : '';
      } catch (_) { return ''; }
    }
    function renderClocks() {
      if (zones.length === 0) {
        clocksEl.innerHTML = '<div class="wc-empty">Add timezones above. Your favorites are saved locally.</div>';
        return;
      }
      clocksEl.innerHTML = zones.map(function(tz) {
        var label = tz.replace(/\//g, ' · ').replace(/_/g, ' ');
        var offset = getUtcOffset(tz);
        return '<div class="wc-card" data-tz="' + tz + '">' +
          '<div class="wc-card-header">' +
            '<span class="wc-card-label">' + label + '</span>' +
            (offset ? '<span class="wc-card-offset">' + offset + '</span>' : '') +
          '</div>' +
          '<div class="wc-time" data-tz="' + tz + '">--:--:--</div>' +
          '<div class="wc-date" data-tz="' + tz + '">--</div>' +
          '<button type="button" class="wc-remove" data-tz="' + tz + '" aria-label="Remove ' + label + '">×</button>' +
          '</div>';
      }).join('');
      clocksEl.querySelectorAll('.wc-remove').forEach(function(btn) {
        btn.onclick = function() {
          var t = btn.getAttribute('data-tz');
          zones = zones.filter(function(z) { return z !== t; });
          self._saveFavorites(zones);
          renderClocks();
          tick();
        };
      });
      tick();
    }
    function tick() {
      var now = new Date();
      clocksEl.querySelectorAll('.wc-time').forEach(function(el) {
        var tz = el.getAttribute('data-tz');
        try {
          el.textContent = now.toLocaleTimeString('en-US', { timeZone: tz, hour12: use12h, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        } catch (_) { el.textContent = 'Invalid'; }
      });
      clocksEl.querySelectorAll('.wc-date').forEach(function(el) {
        var tz = el.getAttribute('data-tz');
        try {
          el.textContent = now.toLocaleDateString('en-US', { timeZone: tz, weekday: 'short', month: 'short', day: 'numeric' });
        } catch (_) { el.textContent = ''; }
      });
    }
    container.querySelectorAll('.wc-toggle-btn').forEach(function(btn) {
      btn.onclick = function() {
        container.querySelectorAll('.wc-toggle-btn').forEach(function(b) { b.classList.remove('active'); });
        btn.classList.add('active');
        use12h = btn.getAttribute('data-format') === '12';
        self._saveFormat(use12h);
        tick();
      };
    });
    container.querySelector('#wc-add').onclick = function() {
      var tz = select.value;
      if (zones.indexOf(tz) === -1) {
        zones.push(tz);
        self._saveFavorites(zones);
        renderClocks();
      }
    };
    function initZones() {
      if (zones.length === 0) {
        zones = ['America/New_York', 'Europe/London', 'Asia/Tokyo', 'UTC'];
        self._saveFavorites(zones);
      }
      renderClocks();
    }
    initZones();
    var interval = setInterval(tick, 1000);
    this._interval = interval;
  },
  _loadFavorites: function() {
    try {
      var s = localStorage.getItem(this.STORAGE_KEY);
      return s ? JSON.parse(s) : [];
    } catch (_) { return []; }
  },
  _saveFavorites: function(zones) {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(zones));
    } catch (_) {}
  },
  _loadFormat: function() {
    try {
      var s = localStorage.getItem(this.FORMAT_KEY);
      return s === 'true';
    } catch (_) { return false; }
  },
  _saveFormat: function(use12h) {
    try {
      localStorage.setItem(this.FORMAT_KEY, String(use12h));
    } catch (_) {}
  },
  destroy: function() {
    if (this._interval) clearInterval(this._interval);
  }
};
