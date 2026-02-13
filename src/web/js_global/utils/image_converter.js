window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['image-converter'] = {
  _currentUrl: null,
  init: function(container) {
    var self = this;
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">🖼️ Image Converter</h1>' +
      '<p class="utils-subtitle" style="color:var(--utils-text-dim);font-size:0.85rem;margin-bottom:1.5rem">Convert between PNG, JPEG, WebP, and SVG</p>' +
      '<div class="utils-dropzone" id="img-dropzone"><input type="file" id="img-file" accept="image/*" multiple class="utils-file-input">' +
      '<p>Drop image(s) here or click to choose</p><p style="font-size:0.8rem;color:var(--utils-text-dim);margin-top:0.5rem">PNG, JPEG, WebP, GIF, SVG — batch supported</p></div>' +
      '<div class="utils-preview" id="img-preview"></div>' +
      '<div class="utils-options" id="img-options" style="display:none">' +
      '<label>Convert to</label>' +
      '<select id="img-format" class="utils-select"><option value="png">PNG</option><option value="jpeg">JPEG</option><option value="webp">WebP</option><option value="svg">SVG (vectorize)</option></select>' +
      '<div id="img-quality-wrap" style="display:none"><label>Quality <span id="img-quality-val">0.92</span></label>' +
      '<input type="range" id="img-quality" min="0.1" max="1" step="0.01" value="0.92"></div>' +
      '<div id="img-svg-options" style="display:none;margin-top:1rem">' +
      '<label style="margin-bottom:0.5rem">SVG / CAD options</label>' +
      '<div style="display:flex;flex-wrap:wrap;gap:1rem">' +
      '<label style="display:flex;align-items:center;gap:0.5rem"><span>Path precision:</span><input type="number" id="img-roundcoords" min="0" max="5" value="2" style="width:50px"> (0=full, 5=clean for CAD)</label>' +
      '<label style="display:flex;align-items:center;gap:0.5rem"><span>Simplify:</span><input type="number" id="img-ltres" min="0.5" max="2" step="0.1" value="1" style="width:50px"> ltres</label>' +
      '<label style="display:flex;align-items:center;gap:0.5rem"><span>Detail:</span><input type="number" id="img-qtres" min="0.5" max="2" step="0.1" value="1" style="width:50px"> qtres</label>' +
      '</div></div>' +
      '<button class="utils-btn" id="img-convert-btn" data-convert>Convert</button></div>' +
      '<div class="utils-status" id="img-status"></div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var dropzone = container.querySelector('#img-dropzone');
    var fileInput = container.querySelector('#img-file');
    var preview = container.querySelector('#img-preview');
    var options = container.querySelector('#img-options');
    var formatSelect = container.querySelector('#img-format');
    var qualityWrap = container.querySelector('#img-quality-wrap');
    var qualityInput = container.querySelector('#img-quality');
    var qualityVal = container.querySelector('#img-quality-val');
    var svgOptions = container.querySelector('#img-svg-options');
    var currentFiles = [];
    var currentFile = null;
    dropzone.onclick = function() { fileInput.click(); };
    dropzone.ondragover = function(e) { e.preventDefault(); dropzone.classList.add('dragover'); };
    dropzone.ondragleave = function() { dropzone.classList.remove('dragover'); };
    dropzone.ondrop = function(e) {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files.length) handleFiles(Array.from(e.dataTransfer.files));
    };
    fileInput.onchange = function() {
      if (fileInput.files.length) handleFiles(Array.from(fileInput.files));
    };
    formatSelect.onchange = function() {
      qualityWrap.style.display = (formatSelect.value === 'jpeg' || formatSelect.value === 'webp') ? 'block' : 'none';
      svgOptions.style.display = formatSelect.value === 'svg' ? 'block' : 'none';
    };
    qualityInput.oninput = function() { qualityVal.textContent = qualityInput.value; };
    function handleFiles(files) {
      var valid = files.filter(function(f) { return f.type.startsWith('image/'); });
      if (valid.length === 0) {
        container.querySelector('#img-status').textContent = 'Please select image file(s)';
        container.querySelector('#img-status').className = 'utils-status err';
        return;
      }
      if (self._currentUrl) URL.revokeObjectURL(self._currentUrl);
      currentFiles = valid;
      currentFile = valid[0];
      self._currentUrl = URL.createObjectURL(valid[0]);
      preview.innerHTML = valid.length === 1 ? '<img src="' + self._currentUrl + '" alt="Preview">' :
        '<p style="font-size:0.9rem;color:var(--utils-text-dim)">' + valid.length + ' files selected. Batch convert all.</p>';
      options.style.display = 'block';
      container.querySelector('#img-status').textContent = valid.length > 1 ? valid.length + ' files ready' : '';
      container.querySelector('#img-status').className = 'utils-status';
      var hasSvg = valid.some(function(f) { return f.name.toLowerCase().endsWith('.svg'); });
      var hasRaster = valid.some(function(f) { return !f.name.toLowerCase().endsWith('.svg'); });
      formatSelect.innerHTML = '<option value="png">PNG</option><option value="jpeg">JPEG</option><option value="webp">WebP</option>';
      if (hasRaster) formatSelect.innerHTML += '<option value="svg">SVG (vectorize)</option>';
      svgOptions.style.display = formatSelect.value === 'svg' ? 'block' : 'none';
    }
    function download(blob, filename) {
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      URL.revokeObjectURL(a.href);
    }
    function getSvgOpts() {
      return {
        scale: 1,
        roundcoords: parseInt(container.querySelector('#img-roundcoords').value, 10) || 2,
        ltres: parseFloat(container.querySelector('#img-ltres').value) || 1,
        qtres: parseFloat(container.querySelector('#img-qtres').value) || 1
      };
    }
    function doSvgConversion(img, file, onDone) {
      var opts = getSvgOpts();
      function runTracer() {
        var c = document.createElement('canvas');
        var max = 800;
        var w = img.naturalWidth || img.width, h = img.naturalHeight || img.height;
        if (w > max || h > max) { var r = Math.min(max/w, max/h); w = Math.round(w*r); h = Math.round(h*r); }
        c.width = w; c.height = h;
        c.getContext('2d').drawImage(img, 0, 0, w, h);
        var imgData = c.getContext('2d').getImageData(0, 0, w, h);
        var svgstr = ImageTracer.imagedataToSVG(imgData, opts);
        var blob = new Blob([svgstr], { type: 'image/svg+xml' });
        var base = file.name.replace(/\.[^/.]+$/, '');
        download(blob, base + '.svg');
        onDone();
      }
      if (typeof ImageTracer === 'undefined') {
        var script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/imagetracerjs@1.2.6/imagetracer_v1.2.6.js';
        script.onload = runTracer;
        document.head.appendChild(script);
      } else {
        runTracer();
      }
    }
    function convertOne(file, idx, total, next) {
      var url = file.type === 'image/svg+xml' ? URL.createObjectURL(file) : (idx === 0 && self._currentUrl ? self._currentUrl : URL.createObjectURL(file));
      var img = new Image();
      img.onload = function() {
        if (file.type === 'image/svg+xml') {
          if (toFormat === 'svg') { if (url !== self._currentUrl) URL.revokeObjectURL(url); next(); return; }
          var canvas = document.createElement('canvas');
          canvas.width = img.naturalWidth || img.width;
          canvas.height = img.naturalHeight || img.height;
          canvas.getContext('2d').drawImage(img, 0, 0);
          var mime = toFormat === 'jpeg' ? 'image/jpeg' : toFormat === 'webp' ? 'image/webp' : 'image/png';
          var quality = (toFormat === 'jpeg' || toFormat === 'webp') ? parseFloat(qualityInput.value) : 1;
          canvas.toBlob(function(blob) {
            var base = file.name.replace(/\.[^/.]+$/, '');
            download(blob, base + '.' + (toFormat === 'jpeg' ? 'jpg' : toFormat));
            if (url !== self._currentUrl) URL.revokeObjectURL(url);
            next();
          }, mime, quality);
          return;
        }
        if (toFormat === 'svg') {
          doSvgConversion(img, file, function() {
            if (url !== self._currentUrl) URL.revokeObjectURL(url);
            next();
          });
        } else {
          var canvas = document.createElement('canvas');
          canvas.width = img.naturalWidth || img.width;
          canvas.height = img.naturalHeight || img.height;
          canvas.getContext('2d').drawImage(img, 0, 0);
          var mime = toFormat === 'jpeg' ? 'image/jpeg' : toFormat === 'webp' ? 'image/webp' : 'image/png';
          var quality = (toFormat === 'jpeg' || toFormat === 'webp') ? parseFloat(qualityInput.value) : 1;
          canvas.toBlob(function(blob) {
            var base = file.name.replace(/\.[^/.]+$/, '');
            download(blob, base + '.' + (toFormat === 'jpeg' ? 'jpg' : toFormat));
            if (url !== self._currentUrl) URL.revokeObjectURL(url);
            next();
          }, mime, quality);
        }
      };
      img.onerror = function() {
        if (url !== self._currentUrl) URL.revokeObjectURL(url);
        next();
      };
      img.src = url;
    }
    var toFormat;
    container.querySelector('[data-convert]').onclick = function convert() {
      if (!currentFiles.length) {
        container.querySelector('#img-status').textContent = 'No file selected';
        container.querySelector('#img-status').className = 'utils-status err';
        return;
      }
      toFormat = formatSelect.value;
      var status = container.querySelector('#img-status');
      var btn = container.querySelector('#img-convert-btn');
      btn.disabled = true;
      var files = currentFiles.slice();
      var i = 0;
      function next() {
        i++;
        status.textContent = 'Converting (' + i + '/' + files.length + '): ' + (files[i - 1] ? files[i - 1].name : '') + '...';
        if (i >= files.length) {
          status.textContent = 'Done! Downloaded ' + files.length + ' file(s).';
          status.className = 'utils-status ok';
          btn.disabled = false;
          return;
        }
        convertOne(files[i], i, files.length, next);
      }
      status.textContent = 'Converting (1/' + files.length + '): ' + (files[0] ? files[0].name : '') + '...';
      status.className = 'utils-status loading';
      convertOne(files[0], 0, files.length, next);
    };
  },
  destroy: function() {
    if (this._currentUrl) {
      URL.revokeObjectURL(this._currentUrl);
      this._currentUrl = null;
    }
  }
};
