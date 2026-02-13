/**
 * MP4 to GIF - Canvas-based frame extraction + GIF encoding
 * Uses gifenc (ESM from unpkg) - runs on main thread and completes reliably.
 */
window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['mp4-to-gif'] = {
  init: function(container) {
    var self = this;
    container.innerHTML =
      '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">🎬 MP4 to GIF</h1>' +
      '<p class="utils-subtitle" style="color:var(--utils-text-dim);font-size:0.85rem;margin-bottom:1rem">Convert video clips to animated GIF. Runs in your browser.</p>' +
      '<div class="utils-dropzone" id="gif-dropzone"><input type="file" id="gif-file" accept="video/mp4,video/webm" class="utils-file-input">' +
      '<p>Drop MP4/WebM here or click to choose</p></div>' +
      '<div id="gif-options" style="display:none">' +
        '<div class="utils-options">' +
          '<label>Start (seconds)</label><input type="number" id="gif-start" class="utils-input" value="0" min="0" step="0.1">' +
          '<label>Duration (seconds)</label><input type="number" id="gif-duration" class="utils-input" value="3" min="0.5" max="15" step="0.5">' +
          '<label>FPS</label><input type="number" id="gif-fps" class="utils-input" value="10" min="5" max="15">' +
          '<label>Width (px, keep aspect)</label><input type="number" id="gif-width" class="utils-input" value="400" min="100" max="800">' +
          '<button class="utils-btn" id="gif-convert">Convert to GIF</button>' +
        '</div>' +
        '<video id="gif-video" style="max-width:100%;margin-top:1rem" controls></video>' +
      '</div>' +
      '<div class="utils-status" id="gif-status"></div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var dropzone = container.querySelector('#gif-dropzone');
    var fileInput = container.querySelector('#gif-file');
    var options = container.querySelector('#gif-options');
    var status = container.querySelector('#gif-status');
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
    function handleFile(file) {
      if (!file.type.startsWith('video/')) {
        status.textContent = 'Please select a video file (MP4, WebM)';
        status.className = 'utils-status err';
        return;
      }
      currentFile = file;
      var video = container.querySelector('#gif-video');
      video.src = URL.createObjectURL(file);
      options.style.display = 'block';
      status.textContent = '';
    }
    container.querySelector('#gif-convert').onclick = function() {
      if (!currentFile) {
        status.textContent = 'Select a video first';
        status.className = 'utils-status err';
        return;
      }
      var video = container.querySelector('#gif-video');
      var start = parseFloat(container.querySelector('#gif-start').value) || 0;
      var duration = parseFloat(container.querySelector('#gif-duration').value) || 3;
      var fps = parseInt(container.querySelector('#gif-fps').value, 10) || 10;
      var width = parseInt(container.querySelector('#gif-width').value, 10) || 400;
      var btn = container.querySelector('#gif-convert');
      btn.disabled = true;
      status.textContent = 'Step 1/3: Loading GIF encoder...';
      status.className = 'utils-status loading';
      loadGifenc().then(function() {
        var numFrames = Math.floor(duration * fps);
        status.textContent = 'Step 2/3: Extracting frames (0/' + numFrames + ')...';
        runConversion(video, start, duration, fps, width, function(blob) {
          var a = document.createElement('a');
          a.href = URL.createObjectURL(blob);
          a.download = (currentFile.name.replace(/\.[^/.]+$/, '') || 'output') + '.gif';
          a.click();
          URL.revokeObjectURL(a.href);
          status.textContent = 'Done! Downloaded.';
          status.className = 'utils-status ok';
          btn.disabled = false;
        }, function(err) {
          status.textContent = 'Error: ' + (err && err.message ? err.message : 'Conversion failed');
          status.className = 'utils-status err';
          btn.disabled = false;
        }, function(msg) {
          status.textContent = msg;
          status.className = 'utils-status loading';
        });
      }).catch(function(err) {
        status.textContent = 'Could not load GIF encoder. Try again or use an online converter.';
        status.className = 'utils-status err';
        btn.disabled = false;
      });
    };
    function loadGifenc() {
      if (window.__gifenc) return Promise.resolve(window.__gifenc);
      return import('https://unpkg.com/gifenc@1.0.3').then(function(m) {
        window.__gifenc = m;
        return m;
      });
    }
    function runConversion(video, startSec, durationSec, fps, maxWidth, onDone, onErr, onProgress) {
      onProgress = onProgress || function() {};
      var delayMs = Math.round(1000 / fps);
      var numFrames = Math.floor(durationSec * fps);
      var canvas = document.createElement('canvas');
      var ctx = canvas.getContext('2d', { willReadFrequently: true });
      var frameBuffers = [];
      var frameIdx = 0;
      var w = 0, h = 0;

      function captureNextFrame() {
        if (frameIdx >= numFrames) {
          video.onseeked = null;
          encodeGif();
          return;
        }
        var t = startSec + (frameIdx / fps);
        if (t >= video.duration) {
          video.onseeked = null;
          encodeGif();
          return;
        }
        video.currentTime = t;
      }

      video.onseeked = function() {
        var vw = video.videoWidth;
        var vh = video.videoHeight;
        if (vw > maxWidth) {
          vh = Math.round(vh * maxWidth / vw);
          vw = maxWidth;
        }
        if (!w) { w = vw; h = vh; }
        canvas.width = w;
        canvas.height = h;
        ctx.drawImage(video, 0, 0, w, h);
        var imgData = ctx.getImageData(0, 0, w, h);
        frameBuffers.push(new Uint8Array(imgData.data));
        frameIdx++;
        onProgress('Step 2/3: Extracting frames (' + frameIdx + '/' + numFrames + ')...');
        captureNextFrame();
      };

      function encodeGif() {
        var total = frameBuffers.length;
        if (total === 0) {
          onErr(new Error('No frames captured'));
          return;
        }
        onProgress('Step 3/3: Encoding GIF...');
        try {
          var gifenc = window.__gifenc;
          var quantize = gifenc.quantize;
          var applyPalette = gifenc.applyPalette;
          var GIFEncoder = gifenc.GIFEncoder;
          var firstFrame = frameBuffers[0];
          var palette = quantize(firstFrame, 256);
          var gif = GIFEncoder();
          for (var i = 0; i < total; i++) {
            onProgress('Step 3/3: Encoding GIF... frame ' + (i + 1) + '/' + total);
            var index = applyPalette(frameBuffers[i], palette);
            gif.writeFrame(index, w, h, { palette: palette, delay: delayMs });
          }
          gif.finish();
          var bytes = gif.bytes();
          var blob = new Blob([bytes], { type: 'image/gif' });
          onDone(blob);
        } catch (e) {
          onErr(e);
        }
      }

      video.currentTime = startSec;
    }
  },
  destroy: function() {}
};
