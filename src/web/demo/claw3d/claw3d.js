/*
3D Claw Machine Demo
- Walls that correctly block balls (using intersectsSphere).
- Reduced bounce.
- No spawning in goal zone.
Benchmark version: 1.0.1
*/

let scene, camera, renderer, orbitControls;
const machineSize = { x: 20, y: 20, z: 20 };

let machine, floorMesh, goalBin;
let claw, prongs = [];

let clawState = {
  speed: 1,
  targets: 3,
  grabbed: false
};

let pressedKeys = { w:false, a:false, s:false, d:false, q:false, e:false };
let isGrabbing = false;
let isMoving = false;

let targets = [];
let physicsObjects = [];

let totalDelivered = 0;

let grabUpdateFunctions = [];
let releaseUpdateFunctions = [];

let goalWalls = [];

function clamp(min, max, val) {
  return Math.max(min, Math.min(max, val));
}

function dist3D(a, b) {
  return Math.sqrt(
    (a.x - b.x) ** 2 +
    (a.y - b.y) ** 2 +
    (a.z - b.z) ** 2
  );
}

function showMessage(msg, color="green") {
  const el = document.getElementById("statusMessages");
  if (!el) return;
  el.style.color = color;
  el.textContent = msg;
  setTimeout(() => {
    if(el.textContent === msg) el.textContent = "";
  }, 3000);
}

function updateScore() {
  const s = document.getElementById("scoreValue");
  if (s) s.textContent = totalDelivered;
}

function init3D() {
  const container = document.getElementById("clawCanvas");
  container.innerHTML = "";

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0xeeeeee);

  const aspect = container.clientWidth / container.clientHeight;
  camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 1000);
  camera.position.set(25, 25, 25);
  camera.lookAt(0, 0, 0);

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  container.appendChild(renderer.domElement);

  orbitControls = new THREE.OrbitControls(camera, renderer.domElement);
  orbitControls.enableDamping = true;
  orbitControls.dampingFactor = 0.1;
  orbitControls.minDistance = 5;
  orbitControls.maxDistance = 60;
  orbitControls.maxPolarAngle = Math.PI / 2;

  const amb = new THREE.AmbientLight(0xffffff, 0.8);
  scene.add(amb);
  const dir = new THREE.DirectionalLight(0xffffff, 0.6);
  dir.position.set(10, 15, 10);
  scene.add(dir);

  const gridHelper = new THREE.GridHelper(20, 20);
  scene.add(gridHelper);

  createFloor();
  createMachine();
  createGoalBin();
  createGoalWalls();
  createClaw();
  randomizeObjects(clawState.targets);
}

function createFloor() {
  const floorGeo = new THREE.PlaneGeometry(machineSize.x, machineSize.z);
  const floorMat = new THREE.MeshPhongMaterial({
    color: 0x228b22,
    side: THREE.DoubleSide
  });
  floorMesh = new THREE.Mesh(floorGeo, floorMat);
  floorMesh.rotateX(-Math.PI / 2);
  floorMesh.position.y = -machineSize.y / 2;
  scene.add(floorMesh);
}

function createMachine() {
  const geo = new THREE.BoxGeometry(machineSize.x, machineSize.y, machineSize.z);
  const mat = new THREE.MeshPhongMaterial({
    color: 0x444444,
    wireframe: true,
    transparent: true,
    opacity: 0.3
  });
  machine = new THREE.Mesh(geo, mat);
  scene.add(machine);
}

function createGoalBin() {
  const binW = 4, binH = 2, binD = 4;
  const binGeo = new THREE.BoxGeometry(binW, binH, binD);
  const binMat = new THREE.MeshPhongMaterial({
    color: 0xff0000,
    transparent: true,
    opacity: 0.5
  });
  goalBin = new THREE.Mesh(binGeo, binMat);
  goalBin.position.set(
    0,
    -machineSize.y / 2 + binH / 2,
    machineSize.z / 2 - binD / 2
  );
  scene.add(goalBin);
}

function createGoalWalls() {
  goalWalls = [];

  const binW = 4, binH = 2, binD = 4;
  const fenceH = 2.5, fenceT = 0.2;
  const offsets = [
    { x: -binW / 2 - fenceT / 2, z: 0,               w: fenceT,            d: binD + fenceT },
    { x:  binW / 2 + fenceT / 2, z: 0,               w: fenceT,            d: binD + fenceT },
    { x: 0,                      z:  binD / 2 + fenceT / 2, w: binW + fenceT, d: fenceT },
    { x: 0,                      z: -binD / 2 - fenceT / 2, w: binW + fenceT, d: fenceT },
  ];
  offsets.forEach(o => {
    const wallGeo = new THREE.BoxGeometry(o.w, fenceH, o.d);
    const wallMat = new THREE.MeshPhongMaterial({ color: 0x888888 });
    const wall = new THREE.Mesh(wallGeo, wallMat);
    wall.position.set(
      goalBin.position.x + o.x,
      -machineSize.y / 2 + fenceH / 2, 
      goalBin.position.z + o.z
    );
    scene.add(wall);

    goalWalls.push(wall);
  });
}

function createClaw() {
  const clawGroup = new THREE.Group();

  const baseGeo = new THREE.BoxGeometry(1, 1, 1);
  const baseMat = new THREE.MeshPhongMaterial({ color: 0xffa500 });
  const baseMesh = new THREE.Mesh(baseGeo, baseMat);
  clawGroup.add(baseMesh);

  const prongGeo = new THREE.BoxGeometry(0.2, 1, 0.2);
  const prongMat = new THREE.MeshPhongMaterial({ color: 0x666666 });
  const offsets = [
    [-0.4, -0.5,  0.4],
    [ 0.4, -0.5,  0.4],
    [-0.4, -0.5, -0.4],
    [ 0.4, -0.5, -0.4]
  ];
  offsets.forEach(pos => {
    const p = new THREE.Mesh(prongGeo, prongMat);
    p.position.set(pos[0], pos[1], pos[2]);
    clawGroup.add(p);
    prongs.push(p);
  });

  clawGroup.position.set(0, 0, 0);
  scene.add(clawGroup);
  claw = clawGroup;
}

function randomizeObjects(count) {
  targets.forEach(t => {
    if (scene.children.includes(t)) scene.remove(t);
  });
  targets = [];
  physicsObjects = [];

  const colors = [0xffff00, 0x007bff, 0x6f42c1, 0xaaaaaa, 0xff69b4];
  const sphereGeo = new THREE.SphereGeometry(0.5, 16, 16);
  const margin = 2.0; 
  const radius = 0.5;

  const binBounds = {
    xMin: goalBin.position.x - 2 - margin,
    xMax: goalBin.position.x + 2 + margin,
    zMin: goalBin.position.z - 2 - margin,
    zMax: goalBin.position.z + 2 + margin
  };

  function inGoalZone(x, z) {
    return (
      x >= binBounds.xMin && x <= binBounds.xMax &&
      z >= binBounds.zMin && z <= binBounds.zMax
    );
  }

  for (let i = 0; i < count; i++) {
    let x, y, z;
    do {
      x = (Math.random() - 0.5) * (machineSize.x - 4);
      y = (Math.random() - 0.5) * (machineSize.y - 4);
      z = (Math.random() - 0.5) * (machineSize.z - 4);
    } while (inGoalZone(x, z));

    const color = colors[Math.floor(Math.random() * colors.length)];
    const mat = new THREE.MeshPhongMaterial({ color });
    const sphere = new THREE.Mesh(sphereGeo, mat);

    sphere.position.set(x, y, z);
    sphere.userData = { grabbed: false };
    sphere.velocity = new THREE.Vector3(0, 0, 0);

    scene.add(sphere);
    targets.push(sphere);
    physicsObjects.push(sphere);
  }
}

function updateClawPosition() {
  if (isGrabbing || isMoving) return;

  let spd = clawState.speed * 0.2;
  if (pressedKeys.w) claw.position.z -= spd;
  if (pressedKeys.s) claw.position.z += spd;
  if (pressedKeys.a) claw.position.x -= spd;
  if (pressedKeys.d) claw.position.x += spd;
  if (pressedKeys.q) claw.position.y -= spd;
  if (pressedKeys.e) claw.position.y += spd;

  let halfX = machineSize.x / 2 - 1;
  let halfY = machineSize.y / 2 - 1;
  let halfZ = machineSize.z / 2 - 1;

  claw.position.x = clamp(-halfX, halfX, claw.position.x);
  claw.position.y = clamp(-halfY, halfY, claw.position.y);
  claw.position.z = clamp(-halfZ, halfZ, claw.position.z);
}

function animateCloseProngs() {
  let stillClosing = false;
  const closeSpeed = 0.02;
  prongs.forEach(p => {
    if (Math.abs(p.position.x) > 0.12) {
      p.position.x -= closeSpeed * Math.sign(p.position.x);
      stillClosing = true;
    }
    if (Math.abs(p.position.z) > 0.12) {
      p.position.z -= closeSpeed * Math.sign(p.position.z);
      stillClosing = true;
    }
  });
  return stillClosing;
}

function grabClaw() {
  if (isGrabbing || isMoving) return;
  isGrabbing = true;
  isMoving = true;
  showMessage("Grabbing...");

  const startY = claw.position.y;
  const floorY = -machineSize.y / 2;
  const minY = floorY + 0.5;

  let phase = "moveDown";
  let grabbedSphere = null;

  function updateGrab() {
    if (!isGrabbing) return;

    switch(phase) {
      case "moveDown":
        if (claw.position.y > minY) {
          claw.position.y -= 0.1;
        } else {
          claw.position.y = minY;
          phase = "checkSphere";
        }
        break;

      case "checkSphere":
        for (let t of targets) {
          if (!t.userData.grabbed) {
            const clawPos = new THREE.Vector3().setFromMatrixPosition(claw.matrixWorld);
            const spherePos = new THREE.Vector3().setFromMatrixPosition(t.matrixWorld);
            if (dist3D(clawPos, spherePos) < 1.0) {
              grabbedSphere = t;
              break;
            }
          }
        }
        if (grabbedSphere) {
          phase = "closeProngs";
        } else {
          phase = "moveUp";
        }
        break;

      case "closeProngs":
        if (!animateCloseProngs()) {
          attachSphereToClaw(grabbedSphere);
          clawState.grabbed = true;
          showMessage("Object grabbed!");
          phase = "moveUp";
        }
        break;

      case "moveUp":
        if (claw.position.y < startY) {
          claw.position.y += 0.1;
        } else {
          claw.position.y = startY;
          phase = "done";
        }
        break;

      case "done":
        isGrabbing = false;
        isMoving = false;
        break;
    }
  }
  grabUpdateFunctions.push(updateGrab);
}

function attachSphereToClaw(sphere) {
  sphere.userData.grabbed = true;
  sphere.velocity = null;
  scene.remove(sphere);
  claw.add(sphere);
  sphere.position.set(0, -0.5, 0);
}

function releaseClaw() {
  if (!clawState.grabbed) {
    showMessage("No object to release!", "red");
    return;
  }
  showMessage("Releasing object...");

  let phase = "detachSphere";

  function updateRelease() {
    switch (phase) {
      case "detachSphere":
        const spheres = claw.children.filter(
          c => c.geometry && c.geometry.type === "SphereGeometry"
        );
        spheres.forEach(s => {
          s.userData.grabbed = false;
          claw.remove(s);
          scene.add(s);
          let clawPos = new THREE.Vector3().setFromMatrixPosition(claw.matrixWorld);
          s.position.copy(clawPos);
          s.position.y -= 1;
          s.velocity = new THREE.Vector3(0, 0, 0);
          physicsObjects.push(s);
        });
        clawState.grabbed = false;
        showMessage("Released!");
        phase = "done";
        break;

      case "done":
        releaseUpdateFunctions.splice(releaseUpdateFunctions.indexOf(updateRelease), 1);
        break;
    }
  }
  releaseUpdateFunctions.push(updateRelease);
}

function updatePhysics() {
  const floorY = -machineSize.y / 2;
  const bounce = 0.1;        
  const frictionFactor = 0.95; 

  physicsObjects.forEach(obj => {
    if (!obj.velocity) return;
    obj.velocity.y -= 0.01;
    obj.velocity.multiplyScalar(frictionFactor);
    obj.position.add(obj.velocity);
    if (obj.position.y - 0.5 <= floorY) {
      obj.position.y = floorY + 0.5;
      obj.velocity.y = 0;
    }
    let halfX = machineSize.x / 2 - 0.5;
    let halfZ = machineSize.z / 2 - 0.5;
    if (obj.position.x > halfX) {
      obj.position.x = halfX;
      obj.velocity.x *= -0.2;
    } else if (obj.position.x < -halfX) {
      obj.position.x = -halfX;
      obj.velocity.x *= -0.2;
    }
    if (obj.position.z > halfZ) {
      obj.position.z = halfZ;
      obj.velocity.z *= -0.2;
    } else if (obj.position.z < -halfZ) {
      obj.position.z = -halfZ;
      obj.velocity.z *= -0.2;
    }
    goalWalls.forEach(wall => {
      wall.updateMatrixWorld(true);
      const fenceBox = new THREE.Box3().setFromObject(wall);
      const sphere = new THREE.Sphere(obj.position.clone(), 0.5);
      if (fenceBox.intersectsSphere(sphere)) {
        const closestPoint = fenceBox.clampPoint(obj.position, new THREE.Vector3());
        const pushDir = new THREE.Vector3().subVectors(obj.position, closestPoint);
        const dist = pushDir.length();
        if (dist > 0) {
          pushDir.normalize();
          obj.position.copy(closestPoint).addScaledVector(pushDir, 0.5);
          obj.velocity.projectOnPlane(pushDir);
          obj.velocity.multiplyScalar(0.8);
        }
      }
    });
  });

  for (let i = 0; i < physicsObjects.length; i++) {
    const a = physicsObjects[i];
    if (!a.velocity) continue;
    for (let j = i + 1; j < physicsObjects.length; j++) {
      const b = physicsObjects[j];
      if (!b.velocity) continue;
      const dist = dist3D(a.position, b.position);
      const minDist = 1.0; 
      if (dist < minDist) {
        const overlap = minDist - dist;
        const dir = new THREE.Vector3().subVectors(a.position, b.position).normalize();
        a.position.addScaledVector(dir, overlap / 2);
        b.position.addScaledVector(dir, -overlap / 2);
        const relativeVel = new THREE.Vector3().subVectors(a.velocity, b.velocity);
        const sepVel = relativeVel.dot(dir);
        const impulse = (-(1 + bounce) * sepVel) / 2;
        a.velocity.addScaledVector(dir, impulse);
        b.velocity.addScaledVector(dir, -impulse);
      }
    }
  }
}

function checkGoalZone() {
  const binC = goalBin.position.clone();
  const hw = 2, hh = 1, hd = 2;
  for (let i = physicsObjects.length - 1; i >= 0; i--) {
    const s = physicsObjects[i];
    const p = s.position;
    if (
      p.x > binC.x - hw && p.x < binC.x + hw &&
      p.z > binC.z - hd && p.z < binC.z + hd &&
      p.y <= binC.y + hh
    ) {
      totalDelivered++;
      updateScore();
      showMessage("Delivered +1!");
      scene.remove(s);
      physicsObjects.splice(i, 1);
    }
  }
}

function animate() {
  requestAnimationFrame(animate);

  orbitControls.update();
  updateClawPosition();

  grabUpdateFunctions.forEach((fn, idx) => {
    fn();
    if (!isGrabbing) {
      grabUpdateFunctions.splice(idx, 1);
    }
  });
  releaseUpdateFunctions.forEach(fn => fn());

  updatePhysics();
  checkGoalZone();
  renderer.render(scene, camera);
}

function onWindowResize() {
  const container = document.getElementById("clawCanvas");
  let w = container.clientWidth;
  let h = container.clientHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}

window.addEventListener("DOMContentLoaded", () => {
  init3D();
  animate();
});
window.addEventListener("resize", onWindowResize);

const buttonIds = ["upBtn","downBtn","leftBtn","rightBtn","clawUpBtn","clawDownBtn"];
const buttonKeyMap = {
  upBtn:"w",
  downBtn:"s",
  leftBtn:"a",
  rightBtn:"d",
  clawUpBtn:"e",
  clawDownBtn:"q",
};
buttonIds.forEach(id => {
  const btn = document.getElementById(id);
  if(!btn) return;
  ["mousedown", "touchstart"].forEach(evt => {
    btn.addEventListener(evt, (e) => {
      e.preventDefault();
      pressedKeys[buttonKeyMap[id]] = true;
    }, { passive: false });
  });
  ["mouseup", "mouseleave", "touchend", "touchcancel"].forEach(evt => {
    btn.addEventListener(evt, (e) => {
      e.preventDefault();
      pressedKeys[buttonKeyMap[id]] = false;
    }, { passive: false });
  });
});

window.addEventListener("keydown",(e)=>{
  let k = e.key.toLowerCase();
  if(["w","a","s","d","q","e"].includes(k)){
    pressedKeys[k] = true;
  } else if(k === "f"){
    grabClaw();
  } else if(k === "r"){
    releaseClaw();
  }
});
window.addEventListener("keyup",(e)=>{
  let k = e.key.toLowerCase();
  if(["w","a","s","d","q","e"].includes(k)){
    pressedKeys[k] = false;
  }
});
window.addEventListener("blur",()=>{
  Object.keys(pressedKeys).forEach(k => pressedKeys[k] = false);
});

document.getElementById("grabBtn")?.addEventListener("click", grabClaw);
document.getElementById("releaseBtn")?.addEventListener("click", releaseClaw);

const speedRange = document.getElementById("speedRange");
if(speedRange){
  speedRange.addEventListener("input",(e)=>{
    clawState.speed = parseInt(e.target.value, 10);
  });
}

const generateBtn = document.getElementById("generateBtn");
const targetCount = document.getElementById("targetCount");
if(generateBtn && targetCount){
  generateBtn.addEventListener("click", ()=>{
    let val = parseInt(targetCount.value, 10);
    val = clamp(1, 100, val);
    clawState.targets = val;
    randomizeObjects(val);
  });
}

const resetBtn = document.getElementById("resetBtn");
if(resetBtn){
  resetBtn.addEventListener("click", ()=>{
    claw.position.set(0, 0, 0);
    isGrabbing = false;
    isMoving = false;
    clawState.grabbed = false;
    totalDelivered = 0;
    updateScore();
    randomizeObjects(clawState.targets);
    showMessage("Reset!");
  });
}
