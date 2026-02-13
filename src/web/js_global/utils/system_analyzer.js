window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['system-analyzer'] = {
  _intervals: [],
  _raf: null,
  _frameCount: 0,
  _lastTime: 0,
  _memoryHistory: [],
  init: function(container) {
    var self = this;
    var $ = function(id) { return container.querySelector('#' + id); };
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<div class="utils-live-dashboard">' +
      '<div class="utils-live-card"><span class="utils-live-card-label">Time</span><span class="utils-live-card-value" id="sa-clock">--:--:--</span></div>' +
      '<div class="utils-live-card"><span class="utils-live-card-label">FPS</span><span class="utils-live-card-value utils-pulse" id="sa-fps">0</span><div class="utils-gauge-wrap"><div class="utils-gauge-fill" id="sa-fps-gauge" style="width:0%"></div></div></div>' +
      '<div class="utils-live-card"><span class="utils-live-card-label">Memory</span><span class="utils-live-card-value" id="sa-mem">—</span><div class="utils-gauge-wrap"><div class="utils-gauge-fill" id="sa-mem-gauge" style="width:0%"></div></div></div>' +
      '<div class="utils-live-card"><span class="utils-live-card-label">Connection</span><span class="utils-live-card-value" id="sa-conn"><span class="utils-status-dot utils-pulse" id="sa-conn-dot"></span><span id="sa-conn-text">Checking...</span></span></div>' +
      '<div class="utils-live-card"><span class="utils-live-card-label">Battery</span><span class="utils-live-card-value" id="sa-battery">—</span><div class="utils-gauge-wrap"><div class="utils-gauge-fill" id="sa-bat-gauge" style="width:0%"></div></div></div>' +
      '<div class="utils-live-card"><span class="utils-live-card-label">Window</span><span class="utils-live-card-value" id="sa-window">0×0</span></div></div>' +
      '<header style="text-align:center;margin-bottom:1.5rem"><h1 class="utils-tool-title">System & Network Analyzer</h1>' +
      '<p style="color:var(--utils-text-dim);font-size:0.85rem;margin-top:0.25rem">Live metrics · Interactive · Detailed analysis</p>' +
      '<button class="utils-scan-btn" id="sa-scan-btn"><span id="sa-scan-icon">⟳</span> Run Full Analysis</button></header>' +
      '<div class="utils-section open" data-section="system"><div class="utils-section-header" data-section-toggle><h2>System</h2><span class="utils-section-toggle">▾</span></div><div class="utils-section-content"><div class="utils-grid" id="sa-system-grid"></div></div></div>' +
      '<div class="utils-section open" data-section="browser"><div class="utils-section-header" data-section-toggle><h2>Browser & Display</h2><span class="utils-section-toggle">▾</span></div><div class="utils-section-content"><div class="utils-grid" id="sa-browser-grid"></div></div></div>' +
      '<div class="utils-section open" data-section="network"><div class="utils-section-header" data-section-toggle><h2>Network</h2><span class="utils-section-toggle">▾</span></div><div class="utils-section-content"><div id="sa-network-content"></div><button class="utils-btn-small" id="sa-latency-btn">Test Latency</button><div class="utils-latency-box" id="sa-latency-box" style="display:none">Ping: <span class="utils-latency-value" id="sa-latency-value">—</span> ms</div></div></div>' +
      '<div class="utils-section open" data-section="performance"><div class="utils-section-header" data-section-toggle><h2>Performance & Memory</h2><span class="utils-section-toggle">▾</span></div><div class="utils-section-content"><div class="utils-grid" id="sa-performance-grid"></div><div id="sa-memory-graph-section" style="display:none"><span class="utils-live-card-label">Memory Over Time</span><div class="utils-memory-graph" id="sa-memory-graph"></div></div></div></div>' +
      '<div class="utils-section" data-section="hardware"><div class="utils-section-header" data-section-toggle><h2>Hardware & Capabilities</h2><span class="utils-section-toggle">▾</span></div><div class="utils-section-content"><div class="utils-grid" id="sa-hardware-grid"></div></div></div>' +
      '<div class="utils-section" data-section="raw"><div class="utils-section-header" data-section-toggle><h2>Raw Data</h2><span class="utils-section-toggle">▾</span></div><div class="utils-section-content"><div class="utils-item" style="margin-bottom:0.5rem"><div class="utils-item-label">User-Agent</div><div class="utils-item-row"><span class="utils-item-value" id="sa-raw-ua"></span><button class="utils-copy-btn" data-copy-id="sa-raw-ua">⎘</button></div></div><button class="utils-btn-small" id="sa-raw-toggle">Show Full Raw Navigator Data</button><div class="utils-raw-block" id="sa-raw-data" style="display:none;margin-top:0.5rem"></div></div></div>' +
      '<footer class="utils-footer" style="margin-top:2rem"><span id="sa-timestamp">—</span></footer>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    container.querySelectorAll('[data-section-toggle]').forEach(function(h) {
      h.onclick = function() { h.closest('.utils-section').classList.toggle('open'); };
    });
    function addItem(p, l, v, c, copyable) {
      var d = document.createElement('div');
      d.className = 'utils-item';
      var id = 'sa-item-' + Math.random().toString(36).slice(2);
      d.innerHTML = '<div class="utils-item-label">' + l + '</div><div class="utils-item-row"><span class="utils-item-value ' + (c || '') + '" ' + (copyable ? 'id="' + id + '"' : '') + '>' + v + '</span>' + (copyable ? '<button class="utils-copy-btn" data-copy-id="' + id + '">⎘</button>' : '') + '</div>';
      p.appendChild(d);
      if (copyable) {
        d.querySelector('.utils-copy-btn').onclick = function() {
          var el = container.querySelector('#' + id);
          if (el) navigator.clipboard.writeText(el.textContent).then(function() {
            var b = d.querySelector('.utils-copy-btn');
            if (b) { b.textContent = '✓'; setTimeout(function() { b.textContent = '⎘'; }, 1000); }
          });
        };
      }
    }
    self._intervals.push(setInterval(function() {
      var el = $('sa-clock');
      if (el) el.textContent = new Date().toLocaleTimeString('en-US', { hour12: false });
    }, 1000));
    function measureFps() {
      self._frameCount++;
      var now = performance.now();
      if (now - self._lastTime >= 1000) {
        var fps = Math.round(self._frameCount * 1000 / (now - self._lastTime));
        self._frameCount = 0;
        self._lastTime = now;
        var fe = $('sa-fps'), ge = $('sa-fps-gauge');
        if (fe) fe.textContent = fps;
        if (ge) ge.style.width = Math.min(100, fps) + '%';
      }
      self._raf = requestAnimationFrame(measureFps);
    }
    self._lastTime = performance.now();
    measureFps();
    self._intervals.push(setInterval(function() {
      if (performance.memory) {
        var u = performance.memory.usedJSHeapSize / 1024 / 1024;
        var l = performance.memory.jsHeapSizeLimit / 1024 / 1024;
        var me = $('sa-mem'), mg = $('sa-mem-gauge');
        if (me) me.textContent = u.toFixed(1) + ' MB';
        if (mg) mg.style.width = Math.min(100, (u / l) * 100) + '%';
        self._memoryHistory.push(u);
        if (self._memoryHistory.length > 50) self._memoryHistory.shift();
        var g = $('sa-memory-graph'), s = $('sa-memory-graph-section');
        if (g && s) {
          s.style.display = 'block';
          var m = Math.max.apply(null, self._memoryHistory.concat([1]));
          g.innerHTML = self._memoryHistory.map(function(v) { return '<div class="utils-memory-bar" style="height:' + (v / m) * 100 + '%"></div>'; }).join('');
        }
      } else {
        var me = $('sa-mem');
        if (me) me.textContent = 'N/A';
      }
    }, 1000));
    self._intervals.push(setInterval(function() {
      var dot = $('sa-conn-dot'), txt = $('sa-conn-text');
      if (dot) dot.className = 'utils-status-dot ' + (navigator.onLine ? 'utils-pulse' : 'offline');
      if (txt) {
        txt.textContent = navigator.onLine ? 'Online' : 'Offline';
        txt.className = navigator.onLine ? 'utils-success' : 'utils-danger';
        if (navigator.connection) txt.textContent += ' · ' + (navigator.connection.effectiveType || '?');
      }
    }, 2000));
    if (navigator.getBattery) {
      navigator.getBattery().then(function(b) {
        var be = $('sa-battery'), bg = $('sa-bat-gauge');
        if (be) be.textContent = Math.round(b.level * 100) + '%' + (b.charging ? ' ⚡' : '');
        if (bg) bg.style.width = Math.round(b.level * 100) + '%';
        b.onlevelchange = b.onchargingchange = function() {
          if (be) be.textContent = Math.round(b.level * 100) + '%' + (b.charging ? ' ⚡' : '');
          if (bg) bg.style.width = Math.round(b.level * 100) + '%';
        };
      }).catch(function() { if ($('sa-battery')) $('sa-battery').textContent = 'N/A'; });
    } else { if ($('sa-battery')) $('sa-battery').textContent = 'N/A'; }
    function updateWindow() { var w = $('sa-window'); if (w) w.textContent = window.innerWidth + '×' + window.innerHeight; }
    window.addEventListener('resize', updateWindow);
    updateWindow();
    self._resizeHandler = updateWindow;
    function getLocalIP() {
      return new Promise(function(r) {
        var pc = new RTCPeerConnection({ iceServers: [] });
        pc.createDataChannel('');
        pc.createOffer().then(function(o) { return pc.setLocalDescription(o); });
        pc.onicecandidate = function(e) {
          if (!e.candidate) return;
          var m = /([0-9]{1,3}(\.[0-9]{1,3}){3})/.exec(e.candidate.candidate);
          if (m) { pc.close(); r(m[1]); }
        };
        setTimeout(function() { pc.close(); r('N/A'); }, 3000);
      });
    }
    function getPublicIP() {
      return fetch('https://api.ipify.org?format=json', { signal: AbortSignal.timeout(5000) })
        .then(function(r) { return r.json(); })
        .then(function(j) { return j.ip; })
        .catch(function() { return 'N/A'; });
    }
    function parseUA() {
      var ua = navigator.userAgent;
      var os = 'Unknown', browser = 'Unknown';
      if (ua.indexOf('Win') !== -1) os = 'Windows';
      else if (ua.indexOf('Mac') !== -1) os = ua.indexOf('iPhone') !== -1 ? 'iOS' : 'macOS';
      else if (ua.indexOf('Linux') !== -1) os = 'Linux';
      else if (ua.indexOf('Android') !== -1) os = 'Android';
      if (ua.indexOf('Edg') !== -1) browser = 'Edge';
      else if (ua.indexOf('OPR') !== -1) browser = 'Opera';
      else if (ua.indexOf('Chrome') !== -1) browser = 'Chrome';
      else if (ua.indexOf('Firefox') !== -1) browser = 'Firefox';
      else if (ua.indexOf('Safari') !== -1) browser = 'Safari';
      return { os: os, browser: browser };
    }
    function getWebGL() {
      try {
        var c = document.createElement('canvas');
        var gl = c.getContext('webgl2') || c.getContext('webgl');
        if (!gl) return { vendor: 'N/A', renderer: 'N/A' };
        var d = gl.getExtension('WEBGL_debug_renderer_info');
        return {
          vendor: d ? gl.getParameter(d.UNMASKED_VENDOR_WEBGL) : 'N/A',
          renderer: d ? gl.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'N/A'
        };
      } catch (e) { return { vendor: 'N/A', renderer: 'N/A' }; }
    }
    $('sa-latency-btn').onclick = function() {
      var btn = $('sa-latency-btn'), box = $('sa-latency-box'), val = $('sa-latency-value');
      btn.disabled = true;
      box.style.display = 'inline-flex';
      var s = performance.now();
      fetch('https://api.ipify.org?format=json', { signal: AbortSignal.timeout(5000) })
        .then(function() {
          var ms = Math.round(performance.now() - s);
          val.textContent = ms;
          val.className = 'utils-latency-value ' + (ms < 100 ? 'fast' : ms < 300 ? 'medium' : 'slow');
        })
        .catch(function() {
          val.textContent = 'Failed';
          val.className = 'utils-latency-value utils-danger';
        })
        .then(function() {
          btn.disabled = false;
          btn.textContent = 'Test Latency Again';
        });
    };
    $('sa-raw-toggle').onclick = function() {
      var el = $('sa-raw-data');
      el.style.display = el.style.display === 'none' ? 'block' : 'none';
      if (el.style.display === 'block') {
        var o = {};
        for (var k in navigator) { try { o[k] = navigator[k]; } catch (e) {} }
        el.textContent = JSON.stringify(o, null, 2);
      }
    };
    container.querySelector('[data-copy-id="sa-raw-ua"]').onclick = function() {
      var el = $('sa-raw-ua');
      if (el) navigator.clipboard.writeText(el.textContent);
    };
    function runAnalysis() {
      var btn = $('sa-scan-btn');
      btn.classList.add('running');
      btn.innerHTML = '<span style="animation:utilsPulse 0.8s linear infinite">⟳</span> Analyzing...';
      var ua = parseUA(), webgl = getWebGL();
      var sg = $('sa-system-grid');
      sg.innerHTML = '';
      addItem(sg, 'Platform', navigator.platform, 'highlight');
      addItem(sg, 'OS', ua.os);
      addItem(sg, 'CPU Cores', navigator.hardwareConcurrency || 'N/A');
      addItem(sg, 'Device Memory', navigator.deviceMemory ? navigator.deviceMemory + ' GB' : 'N/A');
      addItem(sg, 'Timezone', Intl.DateTimeFormat().resolvedOptions().timeZone);
      addItem(sg, 'Languages', (navigator.languages && navigator.languages.join) ? navigator.languages.join(', ') : navigator.language);
      addItem(sg, 'Vendor', navigator.vendor || 'N/A');
      var bg = $('sa-browser-grid');
      bg.innerHTML = '';
      addItem(bg, 'Browser', ua.browser, 'highlight');
      addItem(bg, 'Screen', screen.width + ' × ' + screen.height);
      addItem(bg, 'Avail Size', screen.availWidth + ' × ' + screen.availHeight);
      addItem(bg, 'Window', window.innerWidth + ' × ' + window.innerHeight, '', true);
      addItem(bg, 'Pixel Ratio', window.devicePixelRatio || 1);
      addItem(bg, 'Color Depth', screen.colorDepth + '-bit');
      addItem(bg, 'Touch Points', navigator.maxTouchPoints);
      addItem(bg, 'Cookies', navigator.cookieEnabled ? 'Enabled' : 'Disabled');
      addItem(bg, 'Do Not Track', navigator.doNotTrack || 'Unset');
      addItem(bg, 'PDF Viewer', navigator.pdfViewerEnabled !== false ? 'Yes' : 'No');
      $('sa-network-content').innerHTML = '<p class="utils-live-card-label">Detecting IPs...</p>';
      Promise.all([getLocalIP(), getPublicIP()]).then(function(arr) {
        var localIP = arr[0], publicIP = arr[1];
        var nc = $('sa-network-content');
        nc.innerHTML = '';
        var ng = document.createElement('div');
        ng.className = 'utils-grid';
        addItem(ng, 'Local IP', localIP, 'highlight', true);
        addItem(ng, 'Public IP', publicIP, 'highlight', true);
        if (navigator.connection) {
          var c = navigator.connection;
          addItem(ng, 'Effective Type', c.effectiveType || 'N/A');
          addItem(ng, 'Downlink', (c.downlink || '?') + ' Mbps');
          addItem(ng, 'RTT', (c.rtt || '?') + ' ms');
          addItem(ng, 'Save Data', c.saveData ? 'Yes' : 'No');
        }
        nc.appendChild(ng);
      });
      var pg = $('sa-performance-grid');
      pg.innerHTML = '';
      if (performance.timing) {
        var l = performance.timing.loadEventEnd - performance.timing.navigationStart;
        addItem(pg, 'Page Load', l > 0 ? l + ' ms' : 'N/A');
      }
      if (performance.memory) {
        addItem(pg, 'JS Heap Used', (performance.memory.usedJSHeapSize / 1024 / 1024).toFixed(1) + ' MB');
        addItem(pg, 'JS Heap Limit', (performance.memory.jsHeapSizeLimit / 1024 / 1024).toFixed(0) + ' MB');
      }
      addItem(pg, 'WebGL', (document.createElement('canvas').getContext('webgl2') || document.createElement('canvas').getContext('webgl')) ? 'Supported' : 'No', 'utils-success');
      var hg = $('sa-hardware-grid');
      hg.innerHTML = '';
      addItem(hg, 'GPU Vendor', webgl.vendor, '', true);
      addItem(hg, 'GPU Renderer', webgl.renderer, '', true);
      addItem(hg, 'WebGL2', document.createElement('canvas').getContext('webgl2') ? 'Yes' : 'No');
      if (navigator.storage && navigator.storage.estimate) {
        navigator.storage.estimate().then(function(e) {
          addItem(hg, 'Storage Used', (e.usage / 1024 / 1024).toFixed(1) + ' MB');
          addItem(hg, 'Storage Quota', e.quota ? (e.quota / 1024 / 1024 / 1024).toFixed(2) + ' GB' : 'N/A');
        }).catch(function() {});
      }
      addItem(hg, 'Concurrent Threads', navigator.hardwareConcurrency || 'N/A');
      $('sa-raw-ua').textContent = navigator.userAgent;
      $('sa-timestamp').textContent = 'Analyzed at ' + new Date().toLocaleString();
      btn.classList.remove('running');
      btn.innerHTML = '<span id="sa-scan-icon">⟳</span> Run Again';
    }
    $('sa-scan-btn').onclick = runAnalysis;
    setTimeout(runAnalysis, 200);
  },
  destroy: function() {
    this._intervals.forEach(function(id) { clearInterval(id); });
    if (this._raf) cancelAnimationFrame(this._raf);
    if (this._resizeHandler) window.removeEventListener('resize', this._resizeHandler);
  }
};
