/**
 * Video Compressor - Re-encode video with reduced bitrate/resolution
 * Uses FFmpeg.wasm (lazy-loaded, single-threaded core). Works without SharedArrayBuffer.
 */
window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['video-compressor'] = {
  init: function(container) {
    container.innerHTML =
      '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">🎞️ Video Compressor</h1>' +
      '<p class="utils-subtitle" style="color:var(--utils-text-dim);font-size:0.85rem;margin-bottom:1rem">Reduce video file size. Uses FFmpeg in your browser (~25MB first load). Works in all modern browsers.</p>' +
      '<div class="utils-dropzone" id="vc-dropzone"><input type="file" id="vc-file" accept="video/*" class="utils-file-input">' +
      '<p>Drop video here or click to choose</p></div>' +
      '<div id="vc-options" style="display:none">' +
        '<div class="utils-options">' +
          '<label>Resolution</label>' +
          '<select id="vc-resolution" class="utils-select">' +
            '<option value="1080">1080p (Full HD)</option>' +
            '<option value="720" selected>720p (HD)</option>' +
            '<option value="480">480p</option>' +
            '<option value="360">360p</option>' +
          '</select>' +
          '<label>Quality (CRF, lower = better quality, larger file)</label>' +
          '<div style="display:flex;flex-wrap:wrap;align-items:center;gap:0.75rem;margin-bottom:1rem">' +
            '<input type="range" id="vc-crf" min="18" max="36" value="28" style="flex:1;min-width:120px">' +
            '<span id="vc-crf-val" style="min-width:2ch;font-family:JetBrains Mono,monospace">28</span>' +
          '</div>' +
          '<button class="utils-btn" id="vc-compress">Compress</button>' +
        '</div>' +
        '<video id="vc-preview" style="max-width:100%;margin-top:1rem" controls></video>' +
      '</div>' +
      '<div class="utils-status" id="vc-status"></div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var dropzone = container.querySelector('#vc-dropzone');
    var fileInput = container.querySelector('#vc-file');
    var options = container.querySelector('#vc-options');
    var status = container.querySelector('#vc-status');
    var currentFile = null;
    dropzone.onclick = function() { fileInput.click(); };
    dropzone.ondragover = function(e) { e.preventDefault(); dropzone.classList.add('dragover'); };
    dropzone.ondragleave = function() { dropzone.classList.remove('dragover'); };
    dropzone.ondrop = function(e) {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    };
    fileInput.onchange = function() {
      if (fileInput.files.length) handleFile(fileInput.files[0]);
    };
    container.querySelector('#vc-crf').oninput = function() {
      container.querySelector('#vc-crf-val').textContent = this.value;
    };
    function handleFile(file) {
      if (!file.type.startsWith('video/')) {
        status.textContent = 'Please select a video file';
        status.className = 'utils-status err';
        return;
      }
      currentFile = file;
      container.querySelector('#vc-preview').src = URL.createObjectURL(file);
      options.style.display = 'block';
      status.textContent = '';
    }
    container.querySelector('#vc-compress').onclick = function() {
      if (!currentFile) {
        status.textContent = 'Select a video first';
        status.className = 'utils-status err';
        return;
      }
      var btn = container.querySelector('#vc-compress');
      var res = container.querySelector('#vc-resolution').value;
      var crf = container.querySelector('#vc-crf').value;
      btn.disabled = true;
      function setProgress(msg) {
        status.textContent = msg;
        status.className = 'utils-status loading';
      }
      setProgress('Step 1/4: Loading FFmpeg (~25MB, first time only)...');
      loadFfmpeg(setProgress).then(function(ffmpeg) {
        setProgress('Step 2/4: Reading video file...');
        return runCompress(ffmpeg, currentFile, parseInt(res, 10), parseInt(crf, 10), setProgress);
      }).then(function(blob) {
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = (currentFile.name.replace(/\.[^/.]+$/, '') || 'output') + '_compressed.mp4';
        a.click();
        URL.revokeObjectURL(a.href);
        status.textContent = 'Done! Downloaded.';
        status.className = 'utils-status ok';
        btn.disabled = false;
      }).catch(function(err) {
        var msg = (err && err.message ? err.message : 'Compression failed.');
        if (typeof SharedArrayBuffer === 'undefined') {
          msg += ' This environment does not support the required APIs. Try Chrome/Edge with cross-origin isolation, or use an online compressor.';
        }
        status.textContent = 'Error: ' + msg;
        status.className = 'utils-status err';
        btn.disabled = false;
      });
    };
    function loadFfmpeg(setProgress) {
      if (window.__noriFfmpeg && window.__noriFfmpeg.loaded) {
        return Promise.resolve(window.__noriFfmpeg);
      }
      setProgress = setProgress || function() {};
      function doLoad() {
        var FFmpeg = (window.FFmpegWASM || window.ffmpeg) && (window.FFmpegWASM ? window.FFmpegWASM.FFmpeg : window.ffmpeg);
        if (!FFmpeg) return Promise.reject(new Error('FFmpeg.wasm script failed to load'));
        var ff = typeof FFmpeg === 'function' ? new FFmpeg() : FFmpeg;
        if (ff.on) {
          ff.on('progress', function(e) {
            var pct = (e && e.progress != null) ? Math.round(e.progress * 100) : 0;
            setProgress('Step 3/4: Compressing... ' + pct + '%');
          });
        }
        var base = 'https://unpkg.com/@ffmpeg/core@0.12.6/dist/umd';
        return (ff.load ? ff.load({ coreURL: base + '/ffmpeg-core.js', wasmURL: base + '/ffmpeg-core.wasm' }) : Promise.resolve()).then(function() {
          window.__noriFfmpeg = { exec: ff.exec.bind(ff), writeFile: ff.writeFile.bind(ff), readFile: ff.readFile.bind(ff), loaded: true };
          return window.__noriFfmpeg;
        });
      }
      if (window.FFmpegWASM || window.ffmpeg) return doLoad();
      return new Promise(function(resolve, reject) {
        var s = document.createElement('script');
        s.src = 'https://unpkg.com/@ffmpeg/ffmpeg@0.12.10/dist/umd/ffmpeg.min.js';
        s.onload = function() { doLoad().then(resolve).catch(reject); };
        s.onerror = function() { reject(new Error('Could not load FFmpeg.wasm. Check your connection or try an online compressor.')); };
        document.head.appendChild(s);
      });
    }
    function runCompress(ffmpeg, file, height, crf, setProgress) {
      setProgress = setProgress || function() {};
      var inputName = 'input' + (file.name.match(/\.\w+$/) ? file.name.match(/\.\w+$/)[0] : '.mp4');
      return file.arrayBuffer().then(function(buf) {
        setProgress('Step 2/4: Writing file to encoder...');
        return ffmpeg.writeFile(inputName, new Uint8Array(buf));
      }).then(function() {
        setProgress('Step 3/4: Compressing... 0%');
        return ffmpeg.exec(['-i', inputName, '-vf', 'scale=-2:' + height, '-crf', String(crf), '-c:a', 'aac', 'output.mp4']);
      }).then(function() {
        setProgress('Step 4/4: Finalizing...');
        return ffmpeg.readFile('output.mp4');
      }).then(function(data) {
        return new Blob([data.buffer], { type: 'video/mp4' });
      });
    }
  },
  destroy: function() {}
};
