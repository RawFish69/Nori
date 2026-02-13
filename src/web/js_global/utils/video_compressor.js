/**
 * Video Compressor - Re-encode video with reduced bitrate/resolution
 * Tries FFmpeg.wasm first; falls back to browser-native (MediaRecorder + canvas) if FFmpeg fails.
 */
window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['video-compressor'] = {
  init: function(container) {
    container.innerHTML =
      '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">🎞️ Video Compressor</h1>' +
      '<p class="utils-subtitle" style="color:var(--utils-text-dim);font-size:0.85rem;margin-bottom:1rem">Reduce video file size. Uses FFmpeg when available (~25MB first load); otherwise uses your browser\'s built-in encoder.</p>' +
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
      var res = parseInt(container.querySelector('#vc-resolution').value, 10);
      var crf = parseInt(container.querySelector('#vc-crf').value, 10);
      btn.disabled = true;
      function setProgress(msg) {
        status.textContent = msg;
        status.className = 'utils-status loading';
      }
      function done(blob, ext) {
        ext = ext || 'mp4';
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = (currentFile.name.replace(/\.[^/.]+$/, '') || 'output') + '_compressed.' + ext;
        a.click();
        URL.revokeObjectURL(a.href);
        status.textContent = 'Done! Downloaded.';
        status.className = 'utils-status ok';
        btn.disabled = false;
      }
      setProgress('Step 1/4: Loading encoder...');
      loadFfmpeg(setProgress).then(function(ffmpeg) {
        setProgress('Step 2/4: Reading video file...');
        return runCompress(ffmpeg, currentFile, res, crf, setProgress);
      }).then(function(blob) {
        done(blob, 'mp4');
      }).catch(function(err) {
        var msg = err && err.message ? err.message : '';
        if (/Could not load FFmpeg|FFmpeg core|FFmpeg\./.test(msg)) {
          setProgress('FFmpeg unavailable. Using browser encoder...');
          compressWithBrowser(currentFile, res, crf, setProgress).then(function(blob) {
            done(blob, 'webm');
          }).catch(function(e) {
            status.textContent = 'Error: ' + (e && e.message ? e.message : 'Compression failed.');
            status.className = 'utils-status err';
            btn.disabled = false;
          });
        } else {
          status.textContent = 'Error: ' + msg;
          status.className = 'utils-status err';
          btn.disabled = false;
        }
      });
    };
    function toBlobURL(url) {
      return fetch(url, { mode: 'cors' }).then(function(r) {
        if (!r.ok) throw new Error('Fetch failed');
        return r.blob();
      }).then(function(blob) {
        return URL.createObjectURL(blob);
      });
    }
    function getClassWorkerBlobURL() {
      var urls = [
        'https://cdn.jsdelivr.net/npm/@ffmpeg/ffmpeg@0.12.10/dist/umd/814.ffmpeg.js',
        'https://unpkg.com/@ffmpeg/ffmpeg@0.12.10/dist/umd/814.ffmpeg.js'
      ];
      function tryNext(i) {
        if (i >= urls.length) return Promise.reject(new Error('Could not load FFmpeg worker script.'));
        return toBlobURL(urls[i]).catch(function() { return tryNext(i + 1); });
      }
      return tryNext(0);
    }
    function loadFfmpeg(setProgress) {
      if (window.__noriFfmpeg && window.__noriFfmpeg.loaded) {
        return Promise.resolve(window.__noriFfmpeg);
      }
      setProgress = setProgress || function() {};
      function doLoad() {
        var FFmpeg = (window.FFmpegWASM && window.FFmpegWASM.FFmpeg) || (window.ffmpeg && window.ffmpeg.FFmpeg);
        if (!FFmpeg) return Promise.reject(new Error('FFmpeg script did not load'));
        var ff = new FFmpeg();
        if (ff.on) {
          ff.on('progress', function(e) {
            var pct = (e && e.progress != null) ? Math.round(e.progress * 100) : 0;
            setProgress('Step 3/4: Compressing... ' + pct + '%');
          });
        }
        setProgress('Step 1/4: Loading FFmpeg core (~25MB)...');
        var coreBases = [
          'https://cdn.jsdelivr.net/npm/@ffmpeg/core@0.12.10/dist/umd',
          'https://unpkg.com/@ffmpeg/core@0.12.10/dist/umd'
        ];
        return getClassWorkerBlobURL().then(function(classWorkerURL) {
          function tryLoad(j) {
            if (j >= coreBases.length) {
              var hint = (typeof location !== 'undefined' && location.protocol === 'file:')
                ? ' Try opening the site over HTTP (e.g. npx serve) so the core can load.'
                : '';
              return Promise.reject(new Error('Could not load FFmpeg core.' + hint));
            }
            var base = coreBases[j];
            var c = base + '/ffmpeg-core.js';
            var w = base + '/ffmpeg-core.wasm';
            return ff.load({ coreURL: c, wasmURL: w, classWorkerURL: classWorkerURL })
              .catch(function() {
                return Promise.all([toBlobURL(c), toBlobURL(w)]).then(function(blobUrls) {
                  return ff.load({ coreURL: blobUrls[0], wasmURL: blobUrls[1], classWorkerURL: classWorkerURL });
                });
              })
              .catch(function(err) {
                return tryLoad(j + 1);
              });
          }
          return tryLoad(0);
        }).then(function() {
          window.__noriFfmpeg = { exec: ff.exec.bind(ff), writeFile: ff.writeFile.bind(ff), readFile: ff.readFile.bind(ff), loaded: true };
          return window.__noriFfmpeg;
        });
      }
      if (window.FFmpegWASM || window.ffmpeg) return doLoad();
      var scriptUrls = [
        'https://cdn.jsdelivr.net/npm/@ffmpeg/ffmpeg@0.12.10/dist/umd/ffmpeg.js',
        'https://unpkg.com/@ffmpeg/ffmpeg@0.12.10/dist/umd/ffmpeg.js'
      ];
      function tryScript(i) {
        if (i >= scriptUrls.length) return Promise.reject(new Error('Could not load FFmpeg. Check your connection or try an online compressor.'));
        return new Promise(function(resolve, reject) {
          var s = document.createElement('script');
          s.src = scriptUrls[i];
          s.crossOrigin = 'anonymous';
          s.onload = function() { doLoad().then(resolve).catch(reject); };
          s.onerror = function() { tryScript(i + 1).then(resolve).catch(reject); };
          document.head.appendChild(s);
        });
      }
      return tryScript(0);
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
    function compressWithBrowser(file, targetHeight, crf, setProgress) {
      setProgress = setProgress || function() {};
      return new Promise(function(resolve, reject) {
        var video = document.createElement('video');
        video.muted = true;
        video.playsInline = true;
        video.preload = 'auto';
        var url = URL.createObjectURL(file);
        video.src = url;
        video.onerror = function() {
          URL.revokeObjectURL(url);
          reject(new Error('Could not load video.'));
        };
        video.onloadedmetadata = function() {
          var w = video.videoWidth;
          var h = video.videoHeight;
          if (!w || !h) {
            URL.revokeObjectURL(url);
            reject(new Error('Invalid video dimensions.'));
            return;
          }
          var scale = Math.min(1, targetHeight / h);
          var cw = Math.max(1, Math.round(w * scale));
          var ch = Math.max(1, Math.round(h * scale));
          var canvas = document.createElement('canvas');
          canvas.width = cw;
          canvas.height = ch;
          var ctx = canvas.getContext('2d');
          var duration = video.duration;
          var stream = canvas.captureStream(25);
          var mime = 'video/webm';
          if (MediaRecorder.isTypeSupported('video/webm;codecs=vp9')) mime = 'video/webm;codecs=vp9';
          else if (MediaRecorder.isTypeSupported('video/webm;codecs=vp8')) mime = 'video/webm;codecs=vp8';
          var bitrate = Math.max(200, Math.round(2500 - (crf - 18) * 120));
          var recorder = new MediaRecorder(stream, { videoBitsPerSecond: bitrate * 1000, mimeType: mime });
          var chunks = [];
          recorder.ondataavailable = function(e) { if (e.data.size) chunks.push(e.data); };
          recorder.onstop = function() {
            URL.revokeObjectURL(url);
            resolve(new Blob(chunks, { type: mime.split(';')[0] }));
          };
          recorder.onerror = function() {
            URL.revokeObjectURL(url);
            reject(new Error('Browser encoder failed.'));
          };
          setProgress('Compressing with browser... 0%');
          recorder.start(500);
          function tick() {
            if (video.ended) return;
            if (video.paused) {
              requestAnimationFrame(tick);
              return;
            }
            ctx.drawImage(video, 0, 0, cw, ch);
            var pct = duration > 0 ? Math.min(99, Math.round((video.currentTime / duration) * 100)) : 0;
            setProgress('Compressing with browser... ' + pct + '%');
            requestAnimationFrame(tick);
          }
          video.onended = function() {
            ctx.drawImage(video, 0, 0, cw, ch);
            setProgress('Compressing with browser... 100%');
            setTimeout(function() { recorder.stop(); }, 200);
          };
          video.onplay = function() { tick(); };
          video.play().catch(function(e) {
            URL.revokeObjectURL(url);
            reject(e);
          });
        };
        video.load();
      });
    }
  },
  destroy: function() {}
};
