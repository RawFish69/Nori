let hoverThrottle = 0.34;
let maxThrustAccel = 30;
let throttleSensitivity = 1.4;
let currentDroneType = "micro";
const stage = document.getElementById("viewport");
const viewportFrame = document.getElementById("viewport-frame");
const hudHorizon = document.getElementById("hud-horizon");

// Drone type profiles
const droneProfiles = {
  tinywhoop: {
    name: "Tinywhoop",
    hoverThrottle: 0.38,
    maxThrustAccel: 45,
    maxTiltAngle: 1.2,
    acroRotationRate: 3.2,
    angleRotationRate: 0.8,
    description: "Ultra-responsive indoor flyer",
  },
  micro: {
    name: "Micro",
    hoverThrottle: 0.34,
    maxThrustAccel: 30,
    maxTiltAngle: 1.0,
    acroRotationRate: 2.9,
    angleRotationRate: 0.72,
    description: "Balanced all-rounder",
  },
  longrange: {
    name: "Long Range",
    hoverThrottle: 0.28,
    maxThrustAccel: 18,
    maxTiltAngle: 0.65,
    acroRotationRate: 2.0,
    angleRotationRate: 0.45,
    description: "Stable, efficient cruiser",
  },
  racing: {
    name: "Racing",
    hoverThrottle: 0.44,
    maxThrustAccel: 85,
    maxTiltAngle: 1.55,
    acroRotationRate: 5.5,
    angleRotationRate: 1.1,
    description: "Max performance speed racer",
  },
};

const leftStickPad = document.getElementById("left-stick-pad");
const leftStickHandle = document.getElementById("left-stick-handle");
const rightStickPad = document.getElementById("right-stick-pad");
const rightStickHandle = document.getElementById("right-stick-handle");

const ui = {
  leftStickReadout: document.getElementById("left-stick-readout"),
  rightStickReadout: document.getElementById("right-stick-readout"),
  pitchReadout: document.getElementById("pitch-readout"),
  throttleReadout: document.getElementById("throttle-readout"),
  headingReadout: document.getElementById("heading-readout"),
  speedReadout: document.getElementById("speed-readout"),
  altitudeReadout: document.getElementById("altitude-readout"),
  modeReadout: document.getElementById("mode-readout"),
  modeToggle: document.getElementById("mode-toggle"),
  sticksToggle: document.getElementById("sticks-toggle"),
  rightInputToggle: document.getElementById("right-input-toggle"),
  fullscreenToggle: document.getElementById("fullscreen-toggle"),
  keybindsHint: document.getElementById("keybinds-hint"),
};

const keyboardState = {
  KeyW: false,
  KeyA: false,
  KeyS: false,
  KeyD: false,
  KeyI: false,
  KeyJ: false,
  KeyK: false,
  KeyL: false,
};

const targetChannels = {
  throttle: hoverThrottle,
  yaw: 0,
  roll: 0,
  pitch: 0,
};

const liveChannels = {
  throttle: hoverThrottle,
  yaw: 0,
  roll: 0,
  pitch: 0,
};

const dragState = {
  leftStick: false,
  rightStick: false,
};

const droneState = {
  position: new THREE.Vector3(0, 1.8, 20),
  velocity: new THREE.Vector3(),
  yaw: 0,
  pitch: 0,
  roll: 0,
  pitchRate: 0,
  rollRate: 0,
};

let flightMode = "acro";
let sticksVisible = true;
let rightInputMode = "mouse";
let mouseRightStickActive = false;
let fullscreenActive = false;

const settings = {
  mapSeed: Math.random(),
  throttleSensitivity: 1.4,
  droneType: "micro",
  weather: "day",
};

const courseElements = {
  rings: [],
  mounds: [],
  rocks: [],
  trees: [],
  markers: [],
};

let renderer;
let scene;
let fpvCamera;
let chaseCamera;
let drone;
let rotorGroups = [];
let lastFrame = performance.now();
const tempQuat = new THREE.Quaternion();
const tempUp = new THREE.Vector3();
let currentSkybox = null;
let currentStarfield = null;
let currentTimeOfDay = "day";

function getRandomTimeOfDay() {
  const times = ["night", "day", "sunset", "cloudy"];
  return times[Math.floor(Math.random() * times.length)];
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function seededRandom(seed) {
  const x = Math.sin(seed++) * 10000;
  return x - Math.floor(x);
}

function generateRandomMap(seed) {
  const positions = { rings: [], mounds: [], rocks: [], trees: [], markers: [] };
  let rng = seed * 73856093;

  // Generate ring positions (waypoints)
  const ringCount = 6 + Math.floor(seededRandom(rng++) * 4);
  for (let i = 0; i < ringCount; i++) {
    positions.rings.push([
      (seededRandom(rng++) - 0.5) * 50,
      3.5 + seededRandom(rng++) * 3,
      -16 - i * 15 - seededRandom(rng++) * 12,
    ]);
  }

  // Generate mounds (terrain features)
  const moundCount = 8 + Math.floor(seededRandom(rng++) * 6);
  for (let i = 0; i < moundCount; i++) {
    positions.mounds.push({
      x: (seededRandom(rng++) - 0.5) * 80,
      y: -1.5 - seededRandom(rng++) * 1.5,
      z: -25 - seededRandom(rng++) * 110,
      s: 6 + seededRandom(rng++) * 10,
    });
  }

  // Generate rock walls
  const rockCount = 6 + Math.floor(seededRandom(rng++) * 5);
  for (let i = 0; i < rockCount; i++) {
    positions.rocks.push({
      x: (seededRandom(rng++) - 0.5) * 70,
      y: 1.0 + seededRandom(rng++) * 0.5,
      z: -30 - seededRandom(rng++) * 100,
      sx: 3 + seededRandom(rng++) * 5,
      sy: 1.8 + seededRandom(rng++) * 1.2,
      sz: 0.8 + seededRandom(rng++) * 0.6,
    });
  }

  // Generate trees
  const treeCount = 7 + Math.floor(seededRandom(rng++) * 6);
  for (let i = 0; i < treeCount; i++) {
    const h = 5 + seededRandom(rng++) * 5;
    positions.trees.push({
      x: (seededRandom(rng++) - 0.5) * 75,
      z: -20 - seededRandom(rng++) * 110,
      h: h,
    });
  }

  // Generate accent markers
  const markerCount = 5 + Math.floor(seededRandom(rng++) * 4);
  for (let i = 0; i < markerCount; i++) {
    positions.markers.push({
      x: (seededRandom(rng++) - 0.5) * 60,
      y: 2.0 + seededRandom(rng++) * 2.0,
      z: -25 - seededRandom(rng++) * 105,
    });
  }

  return positions;
}

function damp(current, target, lambda, dt) {
  return THREE.MathUtils.damp(current, target, lambda, dt);
}

function percent(value) {
  return `${Math.round(value * 100)}%`;
}

function signedPercent(value) {
  const rounded = Math.round(value * 100);
  return `${rounded > 0 ? "+" : ""}${rounded}%`;
}

function createDaySky() {
  const canvas = document.createElement("canvas");
  canvas.width = 2048;
  canvas.height = 1024;
  const ctx = canvas.getContext("2d");

  // Gradient from blue at top to lighter blue at horizon
  const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
  gradient.addColorStop(0, "#87ceeb");
  gradient.addColorStop(0.6, "#87d6ff");
  gradient.addColorStop(1, "#e0f6ff");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Sparse small clouds in upper half only
  for (let i = 0; i < 5; i++) {
    const cx = Math.random() * canvas.width;
    const cy = 80 + Math.random() * 280;
    // Build each cloud from several overlapping small ellipses
    const puffs = 3 + Math.floor(Math.random() * 3);
    for (let p = 0; p < puffs; p++) {
      const px = cx + (p - puffs / 2) * (28 + Math.random() * 20);
      const py = cy + (Math.random() - 0.5) * 14;
      const rx = 22 + Math.random() * 18;
      const ry = 10 + Math.random() * 8;
      const alpha = 0.55 + Math.random() * 0.25;
      ctx.fillStyle = `rgba(255,255,255,${alpha})`;
      ctx.beginPath();
      ctx.ellipse(px, py, rx, ry, 0, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  return texture;
}

function createSunsetSky() {
  const canvas = document.createElement("canvas");
  canvas.width = 2048;
  canvas.height = 1024;
  const ctx = canvas.getContext("2d");

  // Gradient from orange/red at horizon to purple at top
  const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
  gradient.addColorStop(0, "#4a0e4e");
  gradient.addColorStop(0.3, "#7b3ff2");
  gradient.addColorStop(0.6, "#ff6b35");
  gradient.addColorStop(1, "#ffa500");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Add sun
  ctx.fillStyle = "#ffdd00";
  ctx.beginPath();
  ctx.arc(canvas.width * 0.75, canvas.height * 0.7, 120, 0, Math.PI * 2);
  ctx.fill();

  // Sun glow
  ctx.fillStyle = "rgba(255, 200, 0, 0.3)";
  ctx.beginPath();
  ctx.arc(canvas.width * 0.75, canvas.height * 0.7, 200, 0, Math.PI * 2);
  ctx.fill();

  const texture = new THREE.CanvasTexture(canvas);
  return texture;
}

function createStarfield() {
  const starfieldGroup = new THREE.Group();
  const starCount = 300;

  // Create a small canvas to use as star texture
  const canvas = document.createElement('canvas');
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext('2d');
  // Soft point star: bright center fading to transparent
  const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  gradient.addColorStop(0, 'rgba(255,255,255,1)');
  gradient.addColorStop(0.15, 'rgba(255,255,255,0.8)');
  gradient.addColorStop(0.4, 'rgba(255,255,255,0.15)');
  gradient.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 64, 64);

  const starTexture = new THREE.CanvasTexture(canvas);

  for (let i = 0; i < starCount; i++) {
    // Random position on a sphere
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.random() * Math.PI;
    const radius = 350;

    const x = radius * Math.sin(phi) * Math.cos(theta);
    const y = radius * Math.cos(phi);
    const z = radius * Math.sin(phi) * Math.sin(theta);

    // Create sprite material
    let color;
    const colorChoice = Math.random();
    if (colorChoice < 0.6) {
      color = new THREE.Color(1, 1, 1); // White
    } else if (colorChoice < 0.8) {
      color = new THREE.Color(0.4, 0.8, 1); // Cyan
    } else {
      color = new THREE.Color(1, 1, 0.4); // Golden
    }

    const spriteMaterial = new THREE.SpriteMaterial({
      map: starTexture,
      color: color,
      sizeAttenuation: true,
      transparent: true,
      fog: false
    });

    const sprite = new THREE.Sprite(spriteMaterial);
    sprite.scale.set(Math.random() * 1.5 + 0.5, Math.random() * 1.5 + 0.5, 1);
    sprite.position.set(x, y, z);
    starfieldGroup.add(sprite);
  }

  return starfieldGroup;
}

function createNightSky() {
  const canvas = document.createElement("canvas");
  canvas.width = 2048;
  canvas.height = 1024;
  const ctx = canvas.getContext("2d");

  // Very dark base - pure black in upper regions for contrast
  const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
  gradient.addColorStop(0, "#000000");
  gradient.addColorStop(0.4, "#050510");
  gradient.addColorStop(1, "#0a0f20");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // White stars
  ctx.globalAlpha = 1.0;
  ctx.fillStyle = "#ffffff";
  for (let i = 0; i < 400; i++) {
    const x = Math.random() * canvas.width;
    const y = Math.random() * canvas.height * 0.85; // keep out of horizon band
    const radius = Math.random() * 1.5 + 0.5; // 0.5-2 pixels
    ctx.globalAlpha = Math.random() * 0.5 + 0.5;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
  }

  // Cyan stars
  for (let i = 0; i < 80; i++) {
    const x = Math.random() * canvas.width;
    const y = Math.random() * canvas.height * 0.85;
    const colors = ["#00ffff", "#00ddff", "#00bbff"];
    ctx.fillStyle = colors[Math.floor(Math.random() * colors.length)];
    const radius = Math.random() * 1.2 + 0.5;
    ctx.globalAlpha = Math.random() * 0.4 + 0.6;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
  }

  // Golden/yellow stars
  ctx.fillStyle = "#ffe080";
  for (let i = 0; i < 60; i++) {
    const x = Math.random() * canvas.width;
    const y = Math.random() * canvas.height * 0.85;
    const radius = Math.random() * 1.2 + 0.5;
    ctx.globalAlpha = Math.random() * 0.4 + 0.6;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1.0;

  const texture = new THREE.CanvasTexture(canvas);
  texture.magFilter = THREE.LinearFilter;
  texture.minFilter = THREE.LinearFilter;
  return texture;
}

function createCloudySky() {
  const canvas = document.createElement("canvas");
  canvas.width = 2048;
  canvas.height = 1024;
  const ctx = canvas.getContext("2d");

  // Cloudy gradient
  const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
  gradient.addColorStop(0, "#5a7a8a");
  gradient.addColorStop(0.5, "#8aa5b8");
  gradient.addColorStop(1, "#b0c4d4");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Overcast layer — medium cloud masses, upper 60% of texture
  for (let i = 0; i < 7; i++) {
    const cx = Math.random() * canvas.width;
    const cy = 60 + Math.random() * 340;
    const puffs = 4 + Math.floor(Math.random() * 4);
    for (let p = 0; p < puffs; p++) {
      const px = cx + (p - puffs / 2) * (32 + Math.random() * 22);
      const py = cy + (Math.random() - 0.5) * 16;
      const rx = 28 + Math.random() * 22;
      const ry = 12 + Math.random() * 10;
      ctx.fillStyle = `rgba(200,210,220,${0.45 + Math.random() * 0.25})`;
      ctx.beginPath();
      ctx.ellipse(px, py, rx, ry, 0, 0, Math.PI * 2);
      ctx.fill();
      // Bright top highlight
      ctx.fillStyle = `rgba(255,255,255,${0.2 + Math.random() * 0.15})`;
      ctx.beginPath();
      ctx.ellipse(px, py - ry * 0.35, rx * 0.7, ry * 0.5, 0, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  return texture;
}

function createSkyTexture(timeOfDay) {
  let texture;

  switch (timeOfDay) {
    case "day":
      texture = createDaySky();
      break;
    case "sunset":
      texture = createSunsetSky();
      break;
    case "cloudy":
      texture = createCloudySky();
      break;
    case "night":
    default:
      texture = createNightSky();
      break;
  }

  texture.magFilter = THREE.LinearFilter;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  return texture;
}

function createSkybox(timeOfDay = "night") {
  const skyboxGroup = new THREE.Group();

  const texture = createSkyTexture(timeOfDay);
  const geometry = new THREE.SphereGeometry(400, 32, 32);
  const material = new THREE.MeshBasicMaterial({
    map: texture,
    side: THREE.BackSide,
    toneMapped: false,
    fog: false,
    depthWrite: false
  });
  const skybox = new THREE.Mesh(geometry, material);

  skyboxGroup.add(skybox);
  return skyboxGroup;
}

function setupScene() {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setScissorTest(true);
  renderer.outputEncoding = THREE.sRGBEncoding;
  stage.appendChild(renderer.domElement);

  scene = new THREE.Scene();

  // Set initial time of day and colors
  currentTimeOfDay = settings.weather;

  let bgColor, fogColor, fogNear, fogFar, hemiBgColor, sunIntensity;

  switch (currentTimeOfDay) {
    case "day":
      bgColor = new THREE.Color(0x87d6ff);
      fogColor = 0x87d6ff;
      fogNear = 50;
      fogFar = 300;
      hemiBgColor = 0xa8e6ff;
      sunIntensity = 1.5;
      break;
    case "sunset":
      bgColor = new THREE.Color(0xff8a3d);
      fogColor = 0xff8a3d;
      fogNear = 40;
      fogFar = 250;
      hemiBgColor = 0xff6b35;
      sunIntensity = 1.3;
      break;
    case "cloudy":
      bgColor = new THREE.Color(0x8aa5b8);
      fogColor = 0x9db5c8;
      fogNear = 30;
      fogFar = 180;
      hemiBgColor = 0x9db5c8;
      sunIntensity = 0.8;
      break;
    case "night":
    default:
      bgColor = new THREE.Color(0x0a1a23);
      fogColor = 0x0a1a23;
      fogNear = 60;
      fogFar = 500;
      hemiBgColor = 0x1c2f28;
      sunIntensity = 0.4;
      break;
  }

  scene.background = bgColor;
  scene.fog = new THREE.Fog(fogColor, fogNear, fogFar);

  fpvCamera = new THREE.PerspectiveCamera(78, 1, 0.05, 500);
  chaseCamera = new THREE.PerspectiveCamera(62, 1, 0.1, 500);

  // Add skybox
  currentSkybox = createSkybox(currentTimeOfDay);
  scene.add(currentSkybox);

  // Add starfield for night sky
  if (currentTimeOfDay === "night") {
    currentStarfield = createStarfield();
    currentStarfield.frustumCulled = false;
    scene.add(currentStarfield);
  }

  const hemi = new THREE.HemisphereLight(0xbfe5ff, hemiBgColor, sunIntensity);
  scene.add(hemi);

  const sun = new THREE.DirectionalLight(0xfff0d5, sunIntensity);
  sun.position.set(18, 30, 12);
  scene.add(sun);

  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(220, 220),
    new THREE.MeshStandardMaterial({ color: 0x143328, roughness: 0.94, metalness: 0.02 })
  );
  ground.rotation.x = -Math.PI / 2;
  scene.add(ground);

  const grid = new THREE.GridHelper(220, 36, 0x4c8873, 0x20413a);
  grid.material.transparent = true;
  grid.material.opacity = 0.34;
  scene.add(grid);

  buildCourse();
  drone = buildDrone();
  scene.add(drone);

  updateCameras(true);
  syncStickUI();
  syncTelemetry();
}

function buildCourse() {
  // Clear existing elements
  courseElements.rings.forEach(ring => scene.remove(ring));
  courseElements.mounds.forEach(mound => scene.remove(mound));
  courseElements.rocks.forEach(rock => scene.remove(rock));
  courseElements.trees.forEach(tree => {
    scene.remove(tree.trunk);
    scene.remove(tree.crown);
  });
  courseElements.markers.forEach(marker => scene.remove(marker));

  courseElements.rings = [];
  courseElements.mounds = [];
  courseElements.rocks = [];
  courseElements.trees = [];
  courseElements.markers = [];

  const positions = generateRandomMap(settings.mapSeed);

  const ringMaterial = new THREE.MeshStandardMaterial({
    color: 0x6ae3ff,
    emissive: 0x1c7b8a,
    roughness: 0.28,
    metalness: 0.35,
  });

  positions.rings.forEach(([x, y, z], index) => {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(3.5, 0.28, 16, 64), ringMaterial.clone());
    ring.position.set(x, y, z);
    ring.rotation.y = index % 2 === 0 ? 0 : 0.35;
    scene.add(ring);
    courseElements.rings.push(ring);
  });

  const moundMaterial = new THREE.MeshStandardMaterial({ color: 0x305c3a, roughness: 0.96, metalness: 0.01 });
  const rockMaterial = new THREE.MeshStandardMaterial({ color: 0x5f6a70, roughness: 0.9, metalness: 0.04 });
  const accentMaterial = new THREE.MeshStandardMaterial({
    color: 0xff8a3d,
    emissive: 0x7d3208,
    emissiveIntensity: 0.7,
    roughness: 0.38,
    metalness: 0.14,
  });

  positions.mounds.forEach(({ x, y, z, s }) => {
    const mound = new THREE.Mesh(new THREE.SphereGeometry(s, 28, 28), moundMaterial);
    mound.position.set(x, y, z);
    mound.scale.y = 0.45;
    scene.add(mound);
    courseElements.mounds.push(mound);
  });

  positions.rocks.forEach(({ x, y, z, sx, sy, sz }) => {
    const wall = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), rockMaterial);
    wall.position.set(x, y, z);
    scene.add(wall);
    courseElements.rocks.push(wall);
  });

  positions.trees.forEach(({ x, z, h }) => {
    const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.34, h, 10), new THREE.MeshStandardMaterial({ color: 0x5b4128, roughness: 0.92 }));
    trunk.position.set(x, h / 2, z);
    scene.add(trunk);
    courseElements.trees.push({ trunk });

    const crown = new THREE.Mesh(new THREE.ConeGeometry(2.1, 4.5, 12), moundMaterial);
    crown.position.set(x, h + 2.2, z);
    scene.add(crown);
    courseElements.trees[courseElements.trees.length - 1].crown = crown;
  });

  positions.markers.forEach(({ x, y, z }) => {
    const marker = new THREE.Mesh(new THREE.OctahedronGeometry(1.1, 0), accentMaterial);
    marker.position.set(x, y, z);
    scene.add(marker);
    courseElements.markers.push(marker);
  });
}

function buildDrone() {
  const quad = new THREE.Group();

  const bodyMaterial = new THREE.MeshStandardMaterial({ color: 0x122734, roughness: 0.45, metalness: 0.2 });
  const topPlateMaterial = new THREE.MeshStandardMaterial({ color: 0xff8a3d, roughness: 0.35, metalness: 0.18 });
  const armMaterial = new THREE.MeshStandardMaterial({ color: 0x203845, roughness: 0.38, metalness: 0.28 });
  const propMaterial = new THREE.MeshStandardMaterial({
    color: 0x9af1ff,
    emissive: 0x1d6776,
    emissiveIntensity: 0.3,
    roughness: 0.16,
    metalness: 0.12,
    transparent: true,
    opacity: 0.82,
  });

  const body = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.18, 1.16), bodyMaterial);
  quad.add(body);

  const topPlate = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.1, 0.7), topPlateMaterial);
  topPlate.position.y = 0.14;
  quad.add(topPlate);

  const cameraPod = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.16, 0.24), topPlateMaterial);
  cameraPod.position.set(0, 0.08, -0.56);
  cameraPod.rotation.x = THREE.MathUtils.degToRad(-12);
  quad.add(cameraPod);

  const antenna = new THREE.Mesh(
    new THREE.CylinderGeometry(0.018, 0.018, 0.52, 10),
    new THREE.MeshStandardMaterial({ color: 0x6ae3ff })
  );
  antenna.position.set(0, 0.36, 0.4);
  quad.add(antenna);

  const armGeometry = new THREE.BoxGeometry(2.2, 0.08, 0.12);
  const armA = new THREE.Mesh(armGeometry, armMaterial);
  armA.rotation.y = Math.PI / 4;
  quad.add(armA);

  const armB = new THREE.Mesh(armGeometry, armMaterial);
  armB.rotation.y = -Math.PI / 4;
  quad.add(armB);

  const motorGeo = new THREE.CylinderGeometry(0.13, 0.15, 0.12, 16);
  const motorMaterial = new THREE.MeshStandardMaterial({ color: 0x08131b, roughness: 0.3, metalness: 0.45 });
  const bladeGeo = new THREE.BoxGeometry(0.82, 0.016, 0.11);
  const rotorPositions = [
    [0.78, 0.1, -0.78],
    [-0.78, 0.1, -0.78],
    [-0.78, 0.1, 0.78],
    [0.78, 0.1, 0.78],
  ];

  rotorGroups = [];
  rotorPositions.forEach(([x, y, z], index) => {
    const motor = new THREE.Mesh(motorGeo, motorMaterial);
    motor.position.set(x, y - 0.05, z);
    quad.add(motor);

    const rotor = new THREE.Group();
    rotor.position.set(x, y, z);
    const bladeA = new THREE.Mesh(bladeGeo, propMaterial);
    const bladeB = new THREE.Mesh(bladeGeo, propMaterial);
    bladeB.rotation.y = Math.PI / 2;
    rotor.add(bladeA, bladeB);
    quad.add(rotor);
    rotorGroups.push({ group: rotor, direction: index % 2 === 0 ? 1 : -1 });
  });

  const noseStrip = new THREE.Mesh(
    new THREE.BoxGeometry(0.1, 0.04, 0.46),
    new THREE.MeshStandardMaterial({ color: 0xff5b41 })
  );
  noseStrip.position.set(0, 0.02, -0.64);
  quad.add(noseStrip);

  return quad;
}

function updateViewportMetrics() {
  const width = stage.clientWidth;
  const height = stage.clientHeight;
  renderer.setSize(width, height, false);

  const insetWidth = Math.min(220, Math.max(150, width * 0.28));
  const insetHeight = insetWidth * 0.625;
  fpvCamera.aspect = width / height;
  fpvCamera.updateProjectionMatrix();
  chaseCamera.aspect = insetWidth / insetHeight;
  chaseCamera.updateProjectionMatrix();

  return { width, height, insetWidth, insetHeight };
}

function updateCameras(force = false) {
  const quat = drone.quaternion;
  const dronePos = drone.position;
  const fpvOffset = new THREE.Vector3(0, 0.17, -0.48).applyQuaternion(quat);
  const pitchDown = new THREE.Quaternion().setFromEuler(new THREE.Euler(THREE.MathUtils.degToRad(-2), 0, 0));

  fpvCamera.position.copy(dronePos).add(fpvOffset);
  fpvCamera.quaternion.copy(quat).multiply(pitchDown);

  const chaseOffset = new THREE.Vector3(0, 2.4, 7.2).applyAxisAngle(new THREE.Vector3(0, 1, 0), droneState.yaw);
  const desired = dronePos.clone().add(chaseOffset);
  if (force) {
    chaseCamera.position.copy(desired);
  } else {
    chaseCamera.position.lerp(desired, 0.08);
  }
  chaseCamera.lookAt(dronePos.clone().add(new THREE.Vector3(0, 0.55, 0)));
}

function syncStickUI() {
  positionLeftStick();
  positionRightStick();
  ui.leftStickReadout.textContent = `T ${percent(targetChannels.throttle)} · Y ${signedPercent(targetChannels.yaw)}`;
  ui.rightStickReadout.textContent = `R ${signedPercent(targetChannels.roll)} · P ${signedPercent(targetChannels.pitch)}`;
}

function positionLeftStick() {
  const rect = leftStickPad.getBoundingClientRect();
  const radius = Math.min(rect.width, rect.height) * 0.34;
  leftStickHandle.style.left = `${rect.width / 2 + targetChannels.yaw * radius}px`;
  leftStickHandle.style.top = `${(1 - targetChannels.throttle) * (rect.height - 2 * (rect.height / 2 - radius)) + (rect.height / 2 - radius)}px`;
}

function positionRightStick() {
  const rect = rightStickPad.getBoundingClientRect();
  const radius = Math.min(rect.width, rect.height) * 0.34;
  rightStickHandle.style.left = `${rect.width / 2 + targetChannels.roll * radius}px`;
  rightStickHandle.style.top = `${rect.height / 2 - targetChannels.pitch * radius}px`;
}

function syncTelemetry() {
  const horizontalSpeed = Math.hypot(droneState.velocity.x, droneState.velocity.z);
  const headingDeg = ((THREE.MathUtils.radToDeg(droneState.yaw) % 360) + 360) % 360;
  const pitchDeg = THREE.MathUtils.radToDeg(droneState.pitch);
  const rollDeg = THREE.MathUtils.radToDeg(droneState.roll);

  ui.pitchReadout.textContent = `${pitchDeg >= 0 ? "+" : ""}${pitchDeg.toFixed(1)}°`;
  ui.throttleReadout.textContent = percent(liveChannels.throttle);
  ui.headingReadout.textContent = `${headingDeg.toFixed(0)}°`;
  ui.speedReadout.textContent = `${horizontalSpeed.toFixed(1)} m/s`;
  ui.altitudeReadout.textContent = `${(droneState.position.y - 0.9).toFixed(1)} m`;
  ui.modeReadout.textContent = flightMode === "acro" ? "Acro" : "Angle";
  ui.modeToggle.textContent = `Mode: ${flightMode === "acro" ? "Acro" : "Angle"} (M)`;
  ui.sticksToggle.textContent = `Sticks: ${sticksVisible ? "On" : "Off"} (V)`;
  ui.rightInputToggle.textContent = `Right Input: ${rightInputMode === "mouse" ? "Mouse" : "IJKL"} (B)`;
  ui.fullscreenToggle.textContent = `Fullscreen: ${fullscreenActive ? "On" : "Off"} (F)`;
  ui.keybindsHint.textContent = rightInputMode === "mouse"
    ? "Keys: WASD left stick · Mouse right stick by default (click FPV) · B switch to IJKL · M mode toggle · V show/hide sticks · F fullscreen"
    : "Keys: WASD left stick · IJKL right stick · B switch to Mouse · M mode toggle · V show/hide sticks · F fullscreen";
  hudHorizon.style.transform = `translateY(${pitchDeg * 2.6}px) rotate(${rollDeg.toFixed(2)}deg)`;
}

function updateKeyboardDrivenTargets(dt) {
  if (!dragState.leftStick) {
    targetChannels.yaw = clamp((keyboardState.KeyD ? 1 : 0) + (keyboardState.KeyA ? -1 : 0), -1, 1);
    const throttleVelocity = (keyboardState.KeyW ? 1 : 0) + (keyboardState.KeyS ? -1 : 0);
    targetChannels.throttle = clamp(targetChannels.throttle + throttleVelocity * dt * 0.72, 0, 1);
  }

  if (!dragState.rightStick && rightInputMode === "keyboard") {
    targetChannels.pitch = clamp((keyboardState.KeyI ? 1 : 0) + (keyboardState.KeyK ? -1 : 0), -1, 1);
    targetChannels.roll = clamp((keyboardState.KeyL ? 1 : 0) + (keyboardState.KeyJ ? -1 : 0), -1, 1);
  } else if (!dragState.rightStick && rightInputMode === "mouse" && !mouseRightStickActive) {
    targetChannels.pitch = damp(targetChannels.pitch, 0, 10, dt);
    targetChannels.roll = damp(targetChannels.roll, 0, 10, dt);
  }
}

function updateDrone(dt) {
  liveChannels.throttle = damp(liveChannels.throttle, targetChannels.throttle, 7 * settings.throttleSensitivity, dt);
  liveChannels.yaw = damp(liveChannels.yaw, targetChannels.yaw, 11, dt);
  liveChannels.roll = damp(liveChannels.roll, targetChannels.roll, 10, dt);
  liveChannels.pitch = damp(liveChannels.pitch, targetChannels.pitch, 10, dt);

  const profile = window.currentProfile || droneProfiles[settings.droneType];
  const acroRotationRate = profile.acroRotationRate;
  const angleRotationRate = profile.angleRotationRate;
  const maxTiltAngle = profile.maxTiltAngle;

  if (flightMode === "acro") {
    droneState.rollRate = damp(droneState.rollRate, -liveChannels.roll * acroRotationRate, 6, dt);
    droneState.pitchRate = damp(droneState.pitchRate, -liveChannels.pitch * (acroRotationRate * 0.88), 6, dt);
    droneState.roll += droneState.rollRate * dt;
    droneState.pitch += droneState.pitchRate * dt;
  } else {
    droneState.rollRate = 0;
    droneState.pitchRate = 0;
    droneState.roll = damp(droneState.roll, -liveChannels.roll * maxTiltAngle, 8, dt);
    droneState.pitch = damp(droneState.pitch, -liveChannels.pitch * (maxTiltAngle * 0.8), 8, dt);
  }

  droneState.yaw -= liveChannels.yaw * 1.9 * dt;

  tempQuat.setFromEuler(new THREE.Euler(droneState.pitch, droneState.yaw, droneState.roll, "YXZ"));
  tempUp.set(0, 1, 0).applyQuaternion(tempQuat);

  const acceleration = new THREE.Vector3();
  const thrustAccel = Math.max(0, liveChannels.throttle * maxThrustAccel);
  acceleration.addScaledVector(tempUp, thrustAccel);
  acceleration.y -= 9.81;
  acceleration.addScaledVector(droneState.velocity, -1.85);

  droneState.velocity.addScaledVector(acceleration, dt);
  droneState.velocity.clampLength(0, 30);
  droneState.position.addScaledVector(droneState.velocity, dt);

  if (droneState.position.y < 0.9) {
    droneState.position.y = 0.9;
    if (droneState.velocity.y < 0) droneState.velocity.y = 0;
  }

  droneState.position.x = clamp(droneState.position.x, -70, 70);
  droneState.position.z = clamp(droneState.position.z, -120, 34);

  drone.rotation.order = "YXZ";
  drone.position.copy(droneState.position);
  drone.rotation.set(droneState.pitch, droneState.yaw, droneState.roll);

  const rotorSpeed = 24 + liveChannels.throttle * 48 + droneState.velocity.length() * 0.35;
  rotorGroups.forEach(({ group, direction }) => {
    group.rotation.y += direction * rotorSpeed * dt;
  });

  updateCameras();
}

function render(now) {
  const dt = Math.min(0.05, (now - lastFrame) / 1000);
  lastFrame = now;

  updateKeyboardDrivenTargets(dt);
  updateDrone(dt);
  syncStickUI();
  syncTelemetry();

  const { width, height, insetWidth, insetHeight } = updateViewportMetrics();
  const insetMargin = 12;
  const insetX = width - insetWidth - insetMargin;
  const insetY = height - insetHeight - insetMargin;

  drone.visible = false;
  renderer.setViewport(0, 0, width, height);
  renderer.setScissor(0, 0, width, height);
  renderer.render(scene, fpvCamera);

  drone.visible = true;
  renderer.clearDepth();
  renderer.setViewport(insetX, insetY, insetWidth, insetHeight);
  renderer.setScissor(insetX, insetY, insetWidth, insetHeight);
  renderer.render(scene, chaseCamera);

  requestAnimationFrame(render);
}

function bindLeftStick() {
  const update = (clientX, clientY) => {
    const rect = leftStickPad.getBoundingClientRect();
    const radius = Math.min(rect.width, rect.height) * 0.34;
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = clamp((clientX - cx) / radius, -1, 1);
    const minY = cy - radius;
    const maxY = cy + radius;
    const throttle = 1 - (clamp(clientY, minY, maxY) - minY) / (maxY - minY);
    targetChannels.yaw = dx;
    targetChannels.throttle = clamp(throttle, 0, 1);
  };

  leftStickPad.addEventListener("pointerdown", (event) => {
    dragState.leftStick = true;
    leftStickPad.setPointerCapture(event.pointerId);
    update(event.clientX, event.clientY);
    syncStickUI();
  });

  leftStickPad.addEventListener("pointermove", (event) => {
    if (!dragState.leftStick) return;
    update(event.clientX, event.clientY);
    syncStickUI();
  });

  const end = () => {
    dragState.leftStick = false;
    targetChannels.yaw = 0;
    syncStickUI();
  };

  leftStickPad.addEventListener("pointerup", end);
  leftStickPad.addEventListener("pointercancel", end);
}

function bindRightStick() {
  const update = (clientX, clientY) => {
    const rect = rightStickPad.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = clientX - cx;
    const dy = clientY - cy;
    const maxRadius = Math.min(rect.width, rect.height) * 0.34;
    const distance = Math.hypot(dx, dy);
    const scale = distance > maxRadius ? maxRadius / distance : 1;
    targetChannels.roll = clamp((dx * scale) / maxRadius, -1, 1);
    targetChannels.pitch = clamp((-dy * scale) / maxRadius, -1, 1);
  };

  rightStickPad.addEventListener("pointerdown", (event) => {
    dragState.rightStick = true;
    rightStickPad.setPointerCapture(event.pointerId);
    update(event.clientX, event.clientY);
    syncStickUI();
  });

  rightStickPad.addEventListener("pointermove", (event) => {
    if (!dragState.rightStick) return;
    update(event.clientX, event.clientY);
    syncStickUI();
  });

  const end = () => {
    dragState.rightStick = false;
    targetChannels.roll = 0;
    targetChannels.pitch = 0;
    syncStickUI();
  };

  rightStickPad.addEventListener("pointerup", end);
  rightStickPad.addEventListener("pointercancel", end);
}

function bindKeyboard() {
  const ignoredTags = new Set(["INPUT", "TEXTAREA", "SELECT"]);

  window.addEventListener("keydown", (event) => {
    if (ignoredTags.has(event.target?.tagName) || event.target?.isContentEditable) return;
    if ((event.code === "KeyM" || event.key === "m" || event.key === "M") && !event.repeat) {
      toggleFlightMode();
      event.preventDefault();
      return;
    }
    if ((event.code === "KeyV" || event.key === "v" || event.key === "V") && !event.repeat) {
      toggleSticks();
      event.preventDefault();
      return;
    }
    if ((event.code === "KeyB" || event.key === "b" || event.key === "B") && !event.repeat) {
      toggleRightInputMode();
      event.preventDefault();
      return;
    }
    if ((event.code === "KeyF" || event.key === "f" || event.key === "F") && !event.repeat) {
      toggleFullscreen();
      event.preventDefault();
      return;
    }
    if (event.code in keyboardState) {
      keyboardState[event.code] = true;
      event.preventDefault();
    }
  });

  window.addEventListener("keyup", (event) => {
    if (event.code in keyboardState) {
      keyboardState[event.code] = false;
      event.preventDefault();
    }
  });

  window.addEventListener("blur", () => {
    Object.keys(keyboardState).forEach((key) => {
      keyboardState[key] = false;
    });
  });
}

function resetTrainer() {
  targetChannels.throttle = hoverThrottle;
  targetChannels.yaw = 0;
  targetChannels.roll = 0;
  targetChannels.pitch = 0;

  liveChannels.throttle = hoverThrottle;
  liveChannels.yaw = 0;
  liveChannels.roll = 0;
  liveChannels.pitch = 0;

  droneState.position.set(0, 1.8, 20);
  droneState.velocity.set(0, 0, 0);
  droneState.yaw = 0;
  droneState.pitch = 0;
  droneState.roll = 0;
  droneState.pitchRate = 0;
  droneState.rollRate = 0;

  drone.position.copy(droneState.position);
  drone.rotation.set(0, droneState.yaw, 0);
  updateCameras(true);
  syncStickUI();
  syncTelemetry();
}

function applyDroneProfile(profileName) {
  const profile = droneProfiles[profileName];
  if (!profile) return;

  hoverThrottle = profile.hoverThrottle;
  maxThrustAccel = profile.maxThrustAccel;
  currentDroneType = profileName;
  settings.droneType = profileName;

  targetChannels.throttle = hoverThrottle;
  liveChannels.throttle = hoverThrottle;
  droneState.velocity.set(0, 0, 0);

  const acroRotationRate = profile.acroRotationRate;
  const angleRotationRate = profile.angleRotationRate;

  // Store these for use in updateDrone
  window.currentProfile = {
    acroRotationRate,
    angleRotationRate,
    maxTiltAngle: profile.maxTiltAngle,
  };

  updateCameras(true);
  syncStickUI();
  syncTelemetry();
}

function toggleFlightMode() {
  flightMode = flightMode === "acro" ? "angle" : "acro";
  droneState.pitchRate = 0;
  droneState.rollRate = 0;
  syncTelemetry();
}

function toggleSticks() {
  sticksVisible = !sticksVisible;
  document.getElementById("sim-root").classList.toggle("controls-hidden", !sticksVisible);
  syncTelemetry();
}

function bindMouseRightStick() {
  viewportFrame.addEventListener("click", () => {
    if (rightInputMode !== "mouse") return;
    stage.requestPointerLock?.();
  });

  document.addEventListener("pointerlockchange", () => {
    mouseRightStickActive = document.pointerLockElement === stage;
    if (!mouseRightStickActive && rightInputMode === "mouse" && !dragState.rightStick) {
      targetChannels.pitch = 0;
      targetChannels.roll = 0;
    }
    syncTelemetry();
  });

  document.addEventListener("mousemove", (event) => {
    if (rightInputMode !== "mouse" || !mouseRightStickActive || dragState.rightStick) return;
    const mouseScale = 0.0034;
    targetChannels.roll = clamp(targetChannels.roll + event.movementX * mouseScale, -1, 1);
    targetChannels.pitch = clamp(targetChannels.pitch - event.movementY * mouseScale, -1, 1);
  });
}

function toggleRightInputMode() {
  rightInputMode = rightInputMode === "mouse" ? "keyboard" : "mouse";
  if (rightInputMode !== "mouse" && document.pointerLockElement === stage) {
    document.exitPointerLock?.();
  }
  if (!dragState.rightStick) {
    targetChannels.roll = 0;
    targetChannels.pitch = 0;
  }
  syncStickUI();
  syncTelemetry();
}

function toggleFullscreen() {
  if (document.fullscreenElement === viewportFrame) {
    document.exitFullscreen?.();
    return;
  }
  viewportFrame.requestFullscreen?.();
}

function updateDroneStats(droneType) {
  const profile = droneProfiles[droneType];
  if (!profile) return;

  const set = (barId, valId, pct, label, color) => {
    const bar = document.getElementById(barId);
    const val = document.getElementById(valId);
    if (bar) { bar.style.width = `${Math.round(pct * 100)}%`; bar.style.background = color; }
    if (val) val.textContent = label;
  };

  const tiltDeg = Math.round(profile.maxTiltAngle * 180 / Math.PI);
  // stability = inverse of acro rate, normalized (longrange is most stable)
  const stabilityPct = 1 - (profile.acroRotationRate - 2.0) / (5.5 - 2.0);

  const thrust = profile.maxThrustAccel / 85;
  const rotation = profile.acroRotationRate / 5.5;
  const tilt = profile.maxTiltAngle / 1.55;

  // color shifts green→amber→red as value increases
  const barColor = (pct) => {
    const r = Math.round(Math.min(255, pct * 2 * 255));
    const g = Math.round(Math.min(255, (1 - pct) * 2 * 255) * 0.8 + 50);
    return `rgb(${r},${g},50)`;
  };

  set("stat-bar-thrust",    "stat-val-thrust",    thrust,       `${profile.maxThrustAccel} m/s²`, barColor(thrust));
  set("stat-bar-rotation",  "stat-val-rotation",  rotation,     `${profile.acroRotationRate} rad/s`, barColor(rotation));
  set("stat-bar-tilt",      "stat-val-tilt",      tilt,         `${tiltDeg}°`, barColor(tilt));
  set("stat-bar-stability", "stat-val-stability", stabilityPct, `${Math.round(stabilityPct * 100)}%`, barColor(1 - stabilityPct));

  const desc = document.getElementById("drone-stats-desc");
  if (desc) desc.textContent = profile.description;
}

function openSettings() {
  const settingsModal = document.getElementById("settings-modal");
  if (settingsModal) {
    settingsModal.style.display = "flex";
    document.getElementById("weather-select").value = settings.weather;
    document.getElementById("drone-type-select").value = settings.droneType;
    document.getElementById("throttle-sensitivity-input").value = settings.throttleSensitivity;
    updateDroneStats(settings.droneType);
  }
}

document.getElementById("drone-type-select")?.addEventListener("change", (e) => {
  updateDroneStats(e.target.value);
});

function closeSettings() {
  const settingsModal = document.getElementById("settings-modal");
  if (settingsModal) {
    settingsModal.style.display = "none";
  }
}

function changeSky(timeOfDay) {
  // Remove old skybox
  if (currentSkybox) {
    scene.remove(currentSkybox);
  }

  // Remove old starfield
  if (currentStarfield) {
    scene.remove(currentStarfield);
    currentStarfield = null;
  }

  currentTimeOfDay = timeOfDay;

  // Create new skybox
  currentSkybox = createSkybox(timeOfDay);
  scene.add(currentSkybox);

  // Add starfield only for night sky
  if (timeOfDay === "night") {
    currentStarfield = createStarfield();
    currentStarfield.frustumCulled = false;
    scene.add(currentStarfield);
  }

  // Update lighting and fog based on time of day
  let bgColor, fogColor, fogNear, fogFar, hemiBgColor, sunIntensity;

  switch (timeOfDay) {
    case "day":
      bgColor = new THREE.Color(0x87d6ff);
      fogColor = 0x87d6ff;
      fogNear = 50;
      fogFar = 300;
      hemiBgColor = 0xa8e6ff;
      sunIntensity = 1.5;
      break;
    case "sunset":
      bgColor = new THREE.Color(0xff8a3d);
      fogColor = 0xff8a3d;
      fogNear = 40;
      fogFar = 250;
      hemiBgColor = 0xff6b35;
      sunIntensity = 1.3;
      break;
    case "cloudy":
      bgColor = new THREE.Color(0x8aa5b8);
      fogColor = 0x9db5c8;
      fogNear = 30;
      fogFar = 180;
      hemiBgColor = 0x9db5c8;
      sunIntensity = 0.8;
      break;
    case "night":
    default:
      bgColor = new THREE.Color(0x0a1a23);
      fogColor = 0x0a1a23;
      fogNear = 60;
      fogFar = 500;
      hemiBgColor = 0x1c2f28;
      sunIntensity = 0.4;
      break;
  }

  scene.background = bgColor;
  scene.fog = new THREE.Fog(fogColor, fogNear, fogFar);

  // Update lights
  const lights = scene.children.filter(child => child instanceof THREE.Light);
  lights.forEach(light => {
    if (light instanceof THREE.HemisphereLight) {
      light.groundColor.setHex(hemiBgColor);
      light.intensity = sunIntensity;
    } else if (light instanceof THREE.DirectionalLight) {
      light.intensity = sunIntensity;
    }
  });
}

function regenerateMap() {
  settings.mapSeed = Math.random();
  buildCourse();
  changeSky(getRandomTimeOfDay()); // Also change the sky randomly
  resetTrainer();
  closeSettings();
}

function applySettings() {
  const weather = document.getElementById("weather-select").value;
  const droneType = document.getElementById("drone-type-select").value;
  const throttleSensitivity = parseFloat(document.getElementById("throttle-sensitivity-input").value);

  settings.weather = weather;
  settings.throttleSensitivity = throttleSensitivity;
  changeSky(weather);
  applyDroneProfile(droneType);

  document.getElementById("throttle-sensitivity-value").textContent = (throttleSensitivity * 100).toFixed(0) + "%";
  closeSettings();
}

document.addEventListener("fullscreenchange", () => {
  fullscreenActive = document.fullscreenElement === viewportFrame;
  syncTelemetry();
});

setupScene();
bindLeftStick();
bindRightStick();
bindMouseRightStick();
bindKeyboard();
ui.modeToggle.addEventListener("click", toggleFlightMode);
ui.sticksToggle.addEventListener("click", toggleSticks);
ui.rightInputToggle.addEventListener("click", toggleRightInputMode);
ui.fullscreenToggle.addEventListener("click", toggleFullscreen);

// Settings modal events
const settingsButton = document.getElementById("settings-button");
if (settingsButton) {
  settingsButton.addEventListener("click", openSettings);
}

const settingsModal = document.getElementById("settings-modal");
const settingsCloseBtn = document.getElementById("settings-close");
const settingsApplyBtn = document.getElementById("settings-apply");
const settingsRegenBtn = document.getElementById("settings-regen");

if (settingsCloseBtn) {
  settingsCloseBtn.addEventListener("click", closeSettings);
}

if (settingsApplyBtn) {
  settingsApplyBtn.addEventListener("click", applySettings);
}

if (settingsRegenBtn) {
  settingsRegenBtn.addEventListener("click", regenerateMap);
}

if (settingsModal) {
  settingsModal.addEventListener("click", (e) => {
    if (e.target === settingsModal) {
      closeSettings();
    }
  });
}

// Rotate-notice dismiss
const rotateNotice = document.getElementById("rotate-notice");
const rotateDismiss = document.getElementById("rotate-dismiss");
if (rotateDismiss && rotateNotice) {
  rotateDismiss.addEventListener("click", () => {
    rotateNotice.style.display = "none";
  });
}

// Landscape floating settings button
const landscapeSettingsBtn = document.getElementById("landscape-settings-btn");
if (landscapeSettingsBtn) {
  landscapeSettingsBtn.addEventListener("click", openSettings);
}

// Initialize with default profile
applyDroneProfile("micro");
resetTrainer();
requestAnimationFrame(render);
