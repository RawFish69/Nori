window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['model-viewer'] = {
  _objectUrl: null,
  _dropEvents: null,
  _threeHost: null,
  _threeCtx: null,
  _occtPromise: null,

  init: function(container) {
    var self = this;
    container.classList.add('utils-model-tool');

    container.innerHTML =
      '<a href="#" class="utils-back-link" data-utils-back><- Back to Utils</a>' +
      '<h1 class="utils-tool-title">3D Model Converter</h1>' +
      '<p class="utils-subtitle" style="color:var(--utils-text-dim);font-size:0.85rem;margin-bottom:1.25rem">Inspect .glb / .gltf / .obj / .stl / .step / .stp in your browser, then export to other mesh formats.</p>' +
      '<div class="utils-dropzone utils-model-dropzone" id="model-dropzone">' +
      '<input type="file" id="model-file" class="utils-file-input" accept=".glb,.gltf,.obj,.stl,.step,.stp,model/gltf-binary,model/gltf+json">' +
      '<p>Drop a 3D model here or click to choose</p>' +
      '<p style="font-size:0.8rem;color:var(--utils-text-dim);margin-top:0.45rem">Supported import: GLB, GLTF, OBJ, STL, STEP/STP.</p>' +
      '</div>' +
      '<div class="utils-model-layout">' +
      '<div class="utils-model-stage"><div id="model-three-host" style="width:100%;height:100%;"></div></div>' +
      '<div class="utils-model-controls">' +
      '<button class="utils-btn" id="model-reset">Reset Camera</button>' +
      '<button class="utils-btn secondary" id="model-autorotate">Enable Auto-Rotate</button>' +
      '<label for="model-sample-select">Sample Models</label>' +
      '<select id="model-sample-select" class="utils-select">' +
      '<option value="https://cdn.jsdelivr.net/gh/KhronosGroup/glTF-Sample-Models@master/2.0/Fox/glTF-Binary/Fox.glb">Fox</option>' +
      '<option value="https://cdn.jsdelivr.net/gh/KhronosGroup/glTF-Sample-Models@master/2.0/Duck/glTF-Binary/Duck.glb">Duck</option>' +
      '<option value="https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/BarramundiFish/glTF-Binary/BarramundiFish.glb">Fish (Barramundi)</option>' +
      '<option value="https://threejs.org/examples/models/gltf/Flamingo.glb">Flamingo</option>' +
      '<option value="https://threejs.org/examples/models/gltf/Parrot.glb">Parrot</option>' +
      '<option value="https://threejs.org/examples/models/gltf/Horse.glb">Horse</option>' +
      '<option value="https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Lantern/glTF-Binary/Lantern.glb">Lantern</option>' +
      '<option value="https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/WaterBottle/glTF-Binary/WaterBottle.glb">Water Bottle</option>' +
      '<option value="https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/2CylinderEngine/glTF-Binary/2CylinderEngine.glb">Engine</option>' +
      '<option value="https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/BoomBox/glTF-Binary/BoomBox.glb">Boombox</option>' +
      '<option value="https://threejs.org/examples/models/gltf/RobotExpressive/RobotExpressive.glb">Robot Expressive</option>' +
      '<option value="https://threejs.org/examples/models/gltf/Soldier.glb">Soldier</option>' +
      '<option value="https://threejs.org/examples/models/gltf/Xbot.glb">Xbot</option>' +
      '<option value="https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/CesiumMan/glTF-Binary/CesiumMan.glb">Cesium Man</option>' +
      '<option value="https://modelviewer.dev/shared-assets/models/Astronaut.glb">Astronaut</option>' +
      '</select>' +
      '<button class="utils-btn secondary" id="model-sample-load">Load Selected Sample</button>' +
      '<details class="utils-model-advanced">' +
      '<summary>Advanced Options</summary>' +
      '<div class="utils-model-advanced-body">' +
      '<div class="utils-model-toggle-row">' +
      '<input id="model-grid-toggle" type="checkbox">' +
      '<label for="model-grid-toggle">Show Ground Grid</label>' +
      '</div>' +
      '<div class="utils-model-exposure-row"><label for="model-exposure">Exposure</label><span id="model-exposure-value" class="utils-model-exposure-value">1.0</span></div>' +
      '<input id="model-exposure" class="utils-input" type="range" min="0.4" max="2.2" step="0.1" value="1">' +
      '<label for="model-bg">Stage Background</label>' +
      '<input id="model-bg" class="utils-input" type="color" value="#101827">' +
      '</div>' +
      '</details>' +
      '<label for="model-export-format">Export Format</label>' +
      '<select id="model-export-format" class="utils-select">' +
      '<option value="obj">OBJ</option>' +
      '<option value="stl">STL</option>' +
      '<option value="gltf">GLTF</option>' +
      '<option value="glb">GLB</option>' +
      '</select>' +
      '<button class="utils-btn" id="model-export">Download Converted File</button>' +
      '<div id="model-status" class="utils-status">Preparing viewer...</div>' +
      '</div>' +
      '</div>';

    var back = container.querySelector('[data-utils-back]');
    var dropzone = container.querySelector('#model-dropzone');
    var fileInput = container.querySelector('#model-file');
    var status = container.querySelector('#model-status');
    var resetBtn = container.querySelector('#model-reset');
    var autoRotateBtn = container.querySelector('#model-autorotate');
    var sampleSelect = container.querySelector('#model-sample-select');
    var sampleLoadBtn = container.querySelector('#model-sample-load');
    var gridToggle = container.querySelector('#model-grid-toggle');
    var exposureInput = container.querySelector('#model-exposure');
    var exposureValueEl = container.querySelector('#model-exposure-value');
    var bgInput = container.querySelector('#model-bg');
    var exportSelect = container.querySelector('#model-export-format');
    var exportBtn = container.querySelector('#model-export');
    var stageEl = container.querySelector('.utils-model-stage');
    var threeHost = container.querySelector('#model-three-host');

    self._threeHost = threeHost;

    function setStatus(message, cls) {
      status.textContent = message;
      status.className = 'utils-status' + (cls ? ' ' + cls : '');
    }

    function clearObjectUrl() {
      if (self._objectUrl) {
        URL.revokeObjectURL(self._objectUrl);
        self._objectUrl = null;
      }
    }

    function setAutoRotateButtonState(isOn) {
      if (isOn) {
        autoRotateBtn.textContent = 'Disable Auto-Rotate';
        autoRotateBtn.className = 'utils-btn';
      } else {
        autoRotateBtn.textContent = 'Enable Auto-Rotate';
        autoRotateBtn.className = 'utils-btn secondary';
      }
    }

    function onFileSelect() {
      if (fileInput.files && fileInput.files[0]) {
        loadModelFromFile(fileInput.files[0]);
      }
    }

    function onDragOver(e) {
      e.preventDefault();
      dropzone.classList.add('dragover');
    }

    function onDragLeave() {
      dropzone.classList.remove('dragover');
    }

    function onDrop(e) {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      var files = e.dataTransfer && e.dataTransfer.files;
      if (files && files.length) {
        loadModelFromFile(files[0]);
      }
    }

    function loadModelFromFile(file) {
      if (!file) return;
      var name = (file.name || '').toLowerCase();
      var ext = '';
      if (name.endsWith('.glb')) ext = 'glb';
      else if (name.endsWith('.gltf')) ext = 'gltf';
      else if (name.endsWith('.obj')) ext = 'obj';
      else if (name.endsWith('.stl')) ext = 'stl';
      else if (name.endsWith('.step') || name.endsWith('.stp')) ext = 'step';

      if (!ext) {
        setStatus('Unsupported file type. Use .glb, .gltf, .obj, .stl, .step, or .stp.', 'err');
        return;
      }

      clearObjectUrl();
      setStatus('Loading: ' + file.name, 'loading');
      self._loadObjectByType(file, ext).then(function(object3d) {
        self._setThreeObject(object3d);
        setAutoRotateButtonState(false);
        setStatus('Loaded ' + ext.toUpperCase() + ': ' + file.name, 'ok');
      }).catch(function(err) {
        console.error(err);
        setStatus('Failed to load file. Try another export variant.', 'err');
      });
    }

    back.onclick = function(e) {
      e.preventDefault();
      location.hash = '#';
    };

    dropzone.onclick = function() {
      fileInput.click();
    };

    fileInput.addEventListener('change', onFileSelect);
    dropzone.addEventListener('dragover', onDragOver);
    dropzone.addEventListener('dragleave', onDragLeave);
    dropzone.addEventListener('drop', onDrop);

    self._dropEvents = {
      fileInput: fileInput,
      dropzone: dropzone,
      onFileSelect: onFileSelect,
      onDragOver: onDragOver,
      onDragLeave: onDragLeave,
      onDrop: onDrop
    };

    resetBtn.onclick = function() {
      if (!self._threeCtx || !self._threeCtx.controls) return;
      self._threeCtx.controls.reset();
      self._frameThreeObject();
    };

    autoRotateBtn.onclick = function() {
      if (!self._threeCtx || !self._threeCtx.controls) return;
      self._threeCtx.controls.autoRotate = !self._threeCtx.controls.autoRotate;
      setAutoRotateButtonState(self._threeCtx.controls.autoRotate);
    };

    sampleLoadBtn.onclick = function() {
      clearObjectUrl();
      var sampleUrl = sampleSelect.value;
      var sampleName = sampleSelect.options[sampleSelect.selectedIndex] ? sampleSelect.options[sampleSelect.selectedIndex].text : 'Sample';
      setStatus('Loading sample: ' + sampleName + '...', 'loading');
      self._loadSampleGlb(sampleUrl).then(function(obj) {
        self._setThreeObject(obj);
        setAutoRotateButtonState(false);
        setStatus('Sample loaded: ' + sampleName, 'ok');
      }).catch(function(err) {
        console.error(err);
        setStatus('Could not load sample model: ' + sampleName + '.', 'err');
      });
    };

    exposureInput.oninput = function() {
      exposureValueEl.textContent = parseFloat(exposureInput.value).toFixed(1);
      if (self._threeCtx && self._threeCtx.renderer) {
        self._threeCtx.renderer.toneMappingExposure = parseFloat(exposureInput.value);
      }
    };

    bgInput.oninput = function() {
      stageEl.style.background = bgInput.value;
      if (self._threeCtx && self._threeCtx.renderer) {
        self._threeCtx.renderer.setClearColor(bgInput.value, 1);
      }
    };

    gridToggle.onchange = function() {
      self._setGridVisible(gridToggle.checked);
    };

    exportBtn.onclick = function() {
      var format = exportSelect.value;
      if (!self._threeCtx || !self._threeCtx.currentObject) {
        setStatus('Load a model before exporting.', 'err');
        return;
      }
      setStatus('Exporting to ' + format.toUpperCase() + '...', 'loading');
      self._exportCurrentObject(format).then(function(filename) {
        setStatus('Export complete: ' + filename, 'ok');
      }).catch(function(err) {
        console.error(err);
        setStatus('Export failed for ' + format.toUpperCase() + '.', 'err');
      });
    };

    stageEl.style.background = bgInput.value;
    exposureValueEl.textContent = parseFloat(exposureInput.value).toFixed(1);

    this._ensureThreeScene(exposureInput.value, bgInput.value)
      .then(function() {
        self._setGridVisible(false);
        setAutoRotateButtonState(false);
        setStatus('Ready. Load a model to begin.', '');
      })
      .catch(function() {
        setStatus('Could not load 3D libraries. Check network and refresh.', 'err');
      });
  },

  _loadScriptOnce: function(id, src) {
    return new Promise(function(resolve, reject) {
      var existing = document.querySelector('script[data-utils-lib="' + id + '"]');
      if (existing) {
        if (existing.getAttribute('data-loaded') === '1') {
          resolve();
          return;
        }
        existing.addEventListener('load', function() { resolve(); }, { once: true });
        existing.addEventListener('error', reject, { once: true });
        return;
      }
      var script = document.createElement('script');
      script.src = src;
      script.async = true;
      script.setAttribute('data-utils-lib', id);
      script.onload = function() {
        script.setAttribute('data-loaded', '1');
        resolve();
      };
      script.onerror = reject;
      document.head.appendChild(script);
    });
  },

  _ensureThreeLibs: function() {
    var self = this;
    if (window.THREE &&
        window.THREE.OrbitControls &&
        window.THREE.STLLoader &&
        window.THREE.OBJLoader &&
        window.THREE.GLTFLoader &&
        window.THREE.OBJExporter &&
        window.THREE.STLExporter &&
        window.THREE.GLTFExporter) {
      return Promise.resolve(window.THREE);
    }

    return self._loadScriptOnce('three-core', 'https://unpkg.com/three@0.124.0/build/three.min.js')
      .then(function() { return self._loadScriptOnce('three-orbit', 'https://unpkg.com/three@0.124.0/examples/js/controls/OrbitControls.js'); })
      .then(function() { return self._loadScriptOnce('three-stl', 'https://unpkg.com/three@0.124.0/examples/js/loaders/STLLoader.js'); })
      .then(function() { return self._loadScriptOnce('three-obj', 'https://unpkg.com/three@0.124.0/examples/js/loaders/OBJLoader.js'); })
      .then(function() { return self._loadScriptOnce('three-gltf', 'https://unpkg.com/three@0.124.0/examples/js/loaders/GLTFLoader.js'); })
      .then(function() { return self._loadScriptOnce('three-exp-obj', 'https://unpkg.com/three@0.124.0/examples/js/exporters/OBJExporter.js'); })
      .then(function() { return self._loadScriptOnce('three-exp-stl', 'https://unpkg.com/three@0.124.0/examples/js/exporters/STLExporter.js'); })
      .then(function() { return self._loadScriptOnce('three-exp-gltf', 'https://unpkg.com/three@0.124.0/examples/js/exporters/GLTFExporter.js'); })
      .then(function() { return window.THREE; });
  },

  _ensureOcct: function() {
    var self = this;
    if (self._occtPromise) return self._occtPromise;
    self._occtPromise = self._loadScriptOnce('occt-import-js', 'https://cdn.jsdelivr.net/npm/occt-import-js@0.0.23/dist/occt-import-js.js')
      .then(function() {
        if (typeof window.occtimportjs !== 'function') {
          throw new Error('occt-import-js not available.');
        }
        return window.occtimportjs({
          locateFile: function(path) {
            return 'https://cdn.jsdelivr.net/npm/occt-import-js@0.0.23/dist/' + path;
          }
        });
      });
    return self._occtPromise;
  },

  _ensureThreeScene: function(exposureValue, bgColor) {
    var self = this;
    return this._ensureThreeLibs().then(function(THREE) {
      if (self._threeCtx) return self._threeCtx;
      var host = self._threeHost;
      var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.outputEncoding = THREE.sRGBEncoding;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = parseFloat(exposureValue || 1);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.setSize(host.clientWidth || 300, host.clientHeight || 300);
      renderer.setClearColor(bgColor || '#101827', 1);
      host.innerHTML = '';
      host.appendChild(renderer.domElement);

      var scene = new THREE.Scene();
      var camera = new THREE.PerspectiveCamera(45, (host.clientWidth || 300) / (host.clientHeight || 300), 0.1, 20000);
      camera.position.set(2.5, 2, 2.5);

      var controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.08;
      controls.autoRotate = false;
      controls.autoRotateSpeed = 1.2;

      var ambient = new THREE.HemisphereLight(0xffffff, 0x445566, 0.8);
      scene.add(ambient);
      var key = new THREE.DirectionalLight(0xffffff, 1.15);
      key.position.set(3, 6, 4);
      scene.add(key);
      var fill = new THREE.DirectionalLight(0xffffff, 0.5);
      fill.position.set(-4, 2, -3);
      scene.add(fill);

      var ctx = {
        THREE: THREE,
        host: host,
        scene: scene,
        camera: camera,
        renderer: renderer,
        controls: controls,
        grid: null,
        gridVisible: false,
        gridSizeHint: 10,
        currentObject: null,
        resizeHandler: null,
        rafId: null
      };

      ctx.resizeHandler = function() {
        var w = host.clientWidth || 300;
        var h = host.clientHeight || 300;
        ctx.camera.aspect = w / h;
        ctx.camera.updateProjectionMatrix();
        ctx.renderer.setSize(w, h);
      };
      window.addEventListener('resize', ctx.resizeHandler);

      var animate = function() {
        ctx.rafId = requestAnimationFrame(animate);
        ctx.controls.update();
        ctx.renderer.render(ctx.scene, ctx.camera);
      };
      animate();

      self._threeCtx = ctx;
      return ctx;
    });
  },

  _setThreeObject: function(object) {
    var ctx = this._threeCtx;
    if (!ctx) return;
    if (ctx.currentObject) {
      ctx.scene.remove(ctx.currentObject);
      this._disposeThreeObject(ctx.currentObject);
      ctx.currentObject = null;
    }
    ctx.currentObject = object;
    ctx.controls.autoRotate = false;
    ctx.scene.add(object);
    this._frameThreeObject();
  },

  _frameThreeObject: function() {
    var ctx = this._threeCtx;
    if (!ctx || !ctx.currentObject) return;
    var THREE = ctx.THREE;
    var box = new THREE.Box3().setFromObject(ctx.currentObject);
    if (!isFinite(box.min.x) || !isFinite(box.max.x)) return;
    var size = new THREE.Vector3();
    box.getSize(size);
    var center = new THREE.Vector3();
    box.getCenter(center);
    var maxDim = Math.max(size.x, size.y, size.z);
    var radius = maxDim * 0.5;
    var dist = Math.max(radius * 2.8, 1.2);

    this._updateGridSize(Math.max(maxDim, 1));

    ctx.camera.near = Math.max(dist / 500, 0.01);
    ctx.camera.far = Math.max(dist * 80, 1000);
    ctx.camera.updateProjectionMatrix();
    ctx.controls.target.copy(center);
    ctx.camera.position.copy(center).add(new THREE.Vector3(dist, dist * 0.75, dist));
    ctx.controls.update();
  },

  _updateGridSize: function(maxDim) {
    var ctx = this._threeCtx;
    if (!ctx) return;
    ctx.gridSizeHint = Math.max(10, Math.ceil(maxDim * 2.5));
    if (!ctx.gridVisible) return;
    this._setGridVisible(true);
  },

  _setGridVisible: function(visible) {
    var ctx = this._threeCtx;
    if (!ctx) return;
    var THREE = ctx.THREE;
    var v = !!visible;
    ctx.gridVisible = v;

    if (!v) {
      if (ctx.grid) {
        ctx.scene.remove(ctx.grid);
        if (ctx.grid.geometry) ctx.grid.geometry.dispose();
        if (ctx.grid.material) {
          if (Array.isArray(ctx.grid.material)) {
            ctx.grid.material.forEach(function(m) { if (m && typeof m.dispose === 'function') m.dispose(); });
          } else if (typeof ctx.grid.material.dispose === 'function') {
            ctx.grid.material.dispose();
          }
        }
        ctx.grid = null;
      }
      return;
    }

    var size = Math.max(10, ctx.gridSizeHint || 10);
    var divisions = Math.max(10, Math.min(120, Math.round(size * 2)));
    var oldGrid = ctx.grid;
    var newGrid = new THREE.GridHelper(size, divisions, 0x3f4d61, 0x253040);
    newGrid.position.y = -0.001;
    ctx.scene.add(newGrid);
    ctx.grid = newGrid;
    if (oldGrid) {
      ctx.scene.remove(oldGrid);
      if (oldGrid.geometry) oldGrid.geometry.dispose();
      if (oldGrid.material) {
        if (Array.isArray(oldGrid.material)) {
          oldGrid.material.forEach(function(m) { if (m && typeof m.dispose === 'function') m.dispose(); });
        } else if (typeof oldGrid.material.dispose === 'function') {
          oldGrid.material.dispose();
        }
      }
    }
  },

  _disposeThreeObject: function(root) {
    root.traverse(function(node) {
      if (node.geometry) {
        node.geometry.dispose();
      }
      if (node.material) {
        if (Array.isArray(node.material)) {
          node.material.forEach(function(m) { if (m && typeof m.dispose === 'function') m.dispose(); });
        } else if (typeof node.material.dispose === 'function') {
          node.material.dispose();
        }
      }
    });
  },

  _loadObjectByType: function(file, ext) {
    var self = this;
    return this._ensureThreeScene().then(function() {
      if (ext === 'glb' || ext === 'gltf') return self._loadGltf(file);
      if (ext === 'obj') return self._loadObj(file);
      if (ext === 'stl') return self._loadStl(file);
      return self._loadStep(file);
    });
  },

  _loadGltf: function(file) {
    var self = this;
    return this._ensureThreeLibs().then(function(THREE) {
      return new Promise(function(resolve, reject) {
        var loader = new THREE.GLTFLoader();
        var url = URL.createObjectURL(file);
        self._objectUrl = url;
        loader.load(url, function(gltf) {
          URL.revokeObjectURL(url);
          self._objectUrl = null;
          var root = gltf && gltf.scene ? gltf.scene : (gltf && gltf.scenes && gltf.scenes[0] ? gltf.scenes[0] : null);
          if (!root) {
            reject(new Error('GLTF scene missing.'));
            return;
          }
          resolve(root);
        }, undefined, function(err) {
          URL.revokeObjectURL(url);
          self._objectUrl = null;
          reject(err);
        });
      });
    });
  },

  _loadObj: function(file) {
    return this._ensureThreeLibs().then(function(THREE) {
      return new Promise(function(resolve, reject) {
        var fr = new FileReader();
        fr.onload = function() {
          try {
            var loader = new THREE.OBJLoader();
            var obj = loader.parse(fr.result);
            resolve(obj);
          } catch (e) {
            reject(e);
          }
        };
        fr.onerror = reject;
        fr.readAsText(file);
      });
    });
  },

  _loadStl: function(file) {
    return this._ensureThreeLibs().then(function(THREE) {
      return new Promise(function(resolve, reject) {
        var fr = new FileReader();
        fr.onload = function() {
          try {
            var loader = new THREE.STLLoader();
            var geometry = loader.parse(fr.result);
            geometry.computeVertexNormals();
            geometry.computeBoundingBox();
            var material = new THREE.MeshStandardMaterial({
              color: 0xbfd6ff,
              metalness: 0.15,
              roughness: 0.72
            });
            var mesh = new THREE.Mesh(geometry, material);
            var box = geometry.boundingBox;
            if (box) {
              var center = new THREE.Vector3();
              box.getCenter(center);
              mesh.position.sub(center);
            }
            resolve(mesh);
          } catch (e) {
            reject(e);
          }
        };
        fr.onerror = reject;
        fr.readAsArrayBuffer(file);
      });
    });
  },

  _createMeshFromOcctData: function(meshData, THREE) {
    var geometry = new THREE.BufferGeometry();
    var pos = meshData && meshData.attributes && meshData.attributes.position && meshData.attributes.position.array;
    var nrm = meshData && meshData.attributes && meshData.attributes.normal && meshData.attributes.normal.array;
    var idx = meshData && meshData.index && meshData.index.array;
    if (!pos || !pos.length) return null;
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    if (nrm && nrm.length) {
      geometry.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
    } else {
      geometry.computeVertexNormals();
    }
    if (idx && idx.length) geometry.setIndex(idx);
    geometry.computeBoundingSphere();

    var color = 0xc9d8f0;
    if (meshData.color && meshData.color.length >= 3) {
      var r = meshData.color[0];
      var g = meshData.color[1];
      var b = meshData.color[2];
      if (r > 1 || g > 1 || b > 1) {
        r = r / 255;
        g = g / 255;
        b = b / 255;
      }
      color = new THREE.Color(r, g, b);
    }

    var material = new THREE.MeshStandardMaterial({
      color: color,
      metalness: 0.1,
      roughness: 0.78
    });
    var mesh = new THREE.Mesh(geometry, material);
    mesh.name = meshData.name || 'step-mesh';
    return mesh;
  },

  _buildOcctNode: function(node, meshPool, THREE) {
    var group = new THREE.Group();
    group.name = node.name || 'node';
    var i;
    if (Array.isArray(node.meshes)) {
      for (i = 0; i < node.meshes.length; i++) {
        var meshIndex = node.meshes[i];
        if (meshPool[meshIndex]) group.add(meshPool[meshIndex].clone());
      }
    }
    if (Array.isArray(node.children)) {
      for (i = 0; i < node.children.length; i++) {
        group.add(this._buildOcctNode(node.children[i], meshPool, THREE));
      }
    }
    return group;
  },

  _loadStep: function(file) {
    var self = this;
    return Promise.all([this._ensureThreeLibs(), this._ensureOcct()]).then(function(results) {
      var THREE = results[0];
      var occt = results[1];
      return new Promise(function(resolve, reject) {
        var fr = new FileReader();
        fr.onload = function() {
          try {
            var fileBuffer = new Uint8Array(fr.result);
            var result = occt.ReadStepFile(fileBuffer, null);
            if (!result || !result.success || !Array.isArray(result.meshes)) {
              reject(new Error('STEP import failed.'));
              return;
            }

            var meshPool = [];
            var i;
            for (i = 0; i < result.meshes.length; i++) {
              meshPool.push(self._createMeshFromOcctData(result.meshes[i], THREE));
            }

            var rootGroup;
            if (result.root) {
              rootGroup = self._buildOcctNode(result.root, meshPool, THREE);
            } else {
              rootGroup = new THREE.Group();
              for (i = 0; i < meshPool.length; i++) {
                if (meshPool[i]) rootGroup.add(meshPool[i].clone());
              }
            }

            if (!rootGroup.children.length) {
              reject(new Error('No renderable geometry in STEP file.'));
              return;
            }

            resolve(rootGroup);
          } catch (e) {
            reject(e);
          }
        };
        fr.onerror = reject;
        fr.readAsArrayBuffer(file);
      });
    });
  },

  _loadSampleGlb: function(url) {
    return this._ensureThreeLibs().then(function(THREE) {
      return new Promise(function(resolve, reject) {
        var loader = new THREE.GLTFLoader();
        loader.load(url, function(gltf) {
          var root = gltf && gltf.scene ? gltf.scene : null;
          if (!root) {
            reject(new Error('Sample GLB scene missing.'));
            return;
          }
          resolve(root);
        }, undefined, function(err) {
          reject(new Error('Sample fetch failed: ' + url));
        });
      });
    });
  },

  _downloadBlob: function(blob, filename) {
    var a = document.createElement('a');
    var url = URL.createObjectURL(blob);
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  },

  _exportCurrentObject: function(format) {
    var self = this;
    var ctx = this._threeCtx;
    var obj = ctx && ctx.currentObject;
    if (!obj) return Promise.reject(new Error('No object loaded.'));
    return this._ensureThreeLibs().then(function(THREE) {
      var filenameBase = 'converted_model';

      if (format === 'obj') {
        var objText = new THREE.OBJExporter().parse(obj);
        self._downloadBlob(new Blob([objText], { type: 'text/plain' }), filenameBase + '.obj');
        return filenameBase + '.obj';
      }

      if (format === 'stl') {
        var stlData = new THREE.STLExporter().parse(obj, { binary: true });
        self._downloadBlob(new Blob([stlData], { type: 'model/stl' }), filenameBase + '.stl');
        return filenameBase + '.stl';
      }

      return new Promise(function(resolve, reject) {
        var exporter = new THREE.GLTFExporter();
        exporter.parse(
          obj,
          function(result) {
            if (format === 'glb') {
              self._downloadBlob(new Blob([result], { type: 'model/gltf-binary' }), filenameBase + '.glb');
              resolve(filenameBase + '.glb');
            } else {
              var text = JSON.stringify(result, null, 2);
              self._downloadBlob(new Blob([text], { type: 'model/gltf+json' }), filenameBase + '.gltf');
              resolve(filenameBase + '.gltf');
            }
          },
          function(err) {
            reject(err);
          },
          { binary: format === 'glb', onlyVisible: true, trs: false }
        );
      });
    });
  },

  _destroyThreeScene: function() {
    var ctx = this._threeCtx;
    if (!ctx) return;
    if (ctx.rafId) cancelAnimationFrame(ctx.rafId);
    if (ctx.resizeHandler) window.removeEventListener('resize', ctx.resizeHandler);
    if (ctx.currentObject) this._disposeThreeObject(ctx.currentObject);
    if (ctx.grid) {
      ctx.scene.remove(ctx.grid);
      if (ctx.grid.geometry) ctx.grid.geometry.dispose();
      if (ctx.grid.material) {
        if (Array.isArray(ctx.grid.material)) {
          ctx.grid.material.forEach(function(m) { if (m && typeof m.dispose === 'function') m.dispose(); });
        } else if (typeof ctx.grid.material.dispose === 'function') {
          ctx.grid.material.dispose();
        }
      }
    }
    if (ctx.renderer) {
      ctx.renderer.dispose();
      if (ctx.renderer.domElement && ctx.renderer.domElement.parentNode) {
        ctx.renderer.domElement.parentNode.removeChild(ctx.renderer.domElement);
      }
    }
    this._threeCtx = null;
  },

  destroy: function() {
    if (this._dropEvents) {
      this._dropEvents.fileInput.removeEventListener('change', this._dropEvents.onFileSelect);
      this._dropEvents.dropzone.removeEventListener('dragover', this._dropEvents.onDragOver);
      this._dropEvents.dropzone.removeEventListener('dragleave', this._dropEvents.onDragLeave);
      this._dropEvents.dropzone.removeEventListener('drop', this._dropEvents.onDrop);
      this._dropEvents = null;
    }
    this._destroyThreeScene();
    if (this._objectUrl) {
      URL.revokeObjectURL(this._objectUrl);
      this._objectUrl = null;
    }
    this._threeHost = null;
  }
};
