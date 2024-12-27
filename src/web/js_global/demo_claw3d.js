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

function clamp(min, max, val) {
  return Math.max(min, Math.min(max, val));
}

function dist3D(a, b) {
  return Math.sqrt(
    (a.x - b.x)**2 + 
    (a.y - b.y)**2 + 
    (a.z - b.z)**2
  );
}

function showMessage(msg, color="green") {
  const el = document.getElementById("statusMessages");
  if (!el) return;
  el.style.color = color;
  el.textContent = msg;
  setTimeout(()=> {
    if(el.textContent === msg) el.textContent = "";
  }, 3000);
}

function updateScore() {
  const s = document.getElementById("scoreValue");
  if (s) s.textContent = totalDelivered;
}

function init3D() {
  console.log("Initializing 3D scene...");
  const container = document.getElementById("clawCanvas");
  container.innerHTML = "";

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0xeeeeee);

  const aspect = container.clientWidth/container.clientHeight;
  camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 1000);
  camera.position.set(25,25,25);
  camera.lookAt(0,0,0);

  renderer = new THREE.WebGLRenderer({ antialias:true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  container.appendChild(renderer.domElement);

  orbitControls = new THREE.OrbitControls(camera, renderer.domElement);
  orbitControls.enableDamping = true;
  orbitControls.dampingFactor = 0.1;
  orbitControls.minDistance = 5;
  orbitControls.maxDistance = 60;
  orbitControls.maxPolarAngle = Math.PI/2;

  const amb = new THREE.AmbientLight(0xffffff, 0.8);
  scene.add(amb);
  const dir = new THREE.DirectionalLight(0xffffff, 0.6);
  dir.position.set(10,15,10);
  scene.add(dir);

  const gridHelper = new THREE.GridHelper(20,20);
  scene.add(gridHelper);

  createFloor();
  createMachine();
  createGoalBin();
  createClaw();
  randomizeObjects(clawState.targets);
}

function createFloor() {
  console.log("Creating floor...");
  const floorGeo = new THREE.PlaneGeometry(machineSize.x, machineSize.z);
  const floorMat = new THREE.MeshPhongMaterial({
    color: 0x228b22,
    side: THREE.DoubleSide
  });
  floorMesh = new THREE.Mesh(floorGeo, floorMat);
  floorMesh.rotateX(-Math.PI/2);
  floorMesh.position.y = -machineSize.y/2;
  scene.add(floorMesh);
}

function createMachine() {
  console.log("Creating machine...");
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
  console.log("Creating goal bin...");
  const binW = 4, binH=2, binD=4;
  const binGeo = new THREE.BoxGeometry(binW, binH, binD);
  const binMat = new THREE.MeshPhongMaterial({
    color: 0xff0000,
    transparent:true,
    opacity:0.5
  });
  goalBin = new THREE.Mesh(binGeo, binMat);
  goalBin.position.set(
    0,
    -machineSize.y/2 + binH/2,
    machineSize.z/2 - 3
  );
  scene.add(goalBin);
}

function createClaw() {
  console.log("Creating claw...");
  const clawGroup = new THREE.Group();

  const baseGeo = new THREE.BoxGeometry(1,1,1);
  const baseMat = new THREE.MeshPhongMaterial({ color: 0xffa500 });
  const baseMesh = new THREE.Mesh(baseGeo, baseMat);
  clawGroup.add(baseMesh);

  const prongGeo = new THREE.BoxGeometry(0.2,1,0.2);
  const prongMat = new THREE.MeshPhongMaterial({ color: 0x666666 });
  const offsets = [
    [-0.4,-0.5, 0.4],
    [ 0.4,-0.5, 0.4],
    [-0.4,-0.5,-0.4],
    [ 0.4,-0.5,-0.4]
  ];
  offsets.forEach(pos => {
    const p = new THREE.Mesh(prongGeo, prongMat);
    p.position.set(pos[0], pos[1], pos[2]);
    clawGroup.add(p);
    prongs.push(p);
  });

  clawGroup.position.set(0,0,0);
  scene.add(clawGroup);
  claw = clawGroup;
}

function randomizeObjects(count) {
  console.log("Randomizing objects...");
  targets.forEach(t => {
    if (scene.children.includes(t)) scene.remove(t);
  });
  targets = [];
  physicsObjects = [];

  const colors = [0xffff00, 0x007bff, 0x6f42c1, 0xaaaaaa, 0xff69b4];
  const sphereGeo = new THREE.SphereGeometry(0.5,16,16);

  for (let i=0; i<count; i++){
    const color = colors[Math.floor(Math.random()*colors.length)];
    const mat = new THREE.MeshPhongMaterial({ color });
    const sphere = new THREE.Mesh(sphereGeo, mat);

    sphere.position.x = (Math.random()-0.5)*(machineSize.x -2);
    sphere.position.y = (Math.random()-0.5)*(machineSize.y -4);
    sphere.position.z = (Math.random()-0.5)*(machineSize.z -2);

    sphere.userData = { grabbed:false };
    sphere.velocity = new THREE.Vector3(0,0,0);

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

  let halfX = machineSize.x/2-1;
  let halfY = machineSize.y/2-1;
  let halfZ = machineSize.z/2-1;

  claw.position.x = clamp(-halfX, halfX, claw.position.x);
  claw.position.y = clamp(-halfY, halfY, claw.position.y);
  claw.position.z = clamp(-halfZ, halfZ, claw.position.z);
  claw.position.y = Math.max(claw.position.y, 0);
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
  const floorY = -machineSize.y/2;
  const minY = floorY + 0.5;

  let phase = "moveDown";
  let grabbedSphere = null;

  function updateGrab() {
    if (!isGrabbing) return;

    switch(phase){
      case "moveDown":
        if(claw.position.y > minY){
          claw.position.y -= 0.1;
        } else {
          claw.position.y = minY;
          phase = "checkSphere";
        }
        break;

      case "checkSphere":
        for(let t of targets){
          if(!t.userData.grabbed){
            const clawPos = new THREE.Vector3().setFromMatrixPosition(claw.matrixWorld);
            const spherePos = new THREE.Vector3().setFromMatrixPosition(t.matrixWorld);
            if(dist3D(clawPos, spherePos)<1.0){
              grabbedSphere = t;
              break;
            }
          }
        }
        if(grabbedSphere){
          phase="closeProngs";
        } else {
          phase="moveUp";
        }
        break;

      case "closeProngs":
        if(!animateCloseProngs()){
          attachSphereToClaw(grabbedSphere);
          clawState.grabbed = true;
          showMessage("Object grabbed!");
          phase="moveUp";
        }
        break;

      case "moveUp":
        if(claw.position.y < startY){
          claw.position.y += 0.1;
        } else {
          claw.position.y = startY;
          phase="done";
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
  if(!clawState.grabbed){
    showMessage("No object to release!", "red");
    return;
  }
  showMessage("Releasing object...");

  let phase="detachSphere";

  function updateRelease(){
    switch(phase){
      case "detachSphere":
        const spheres = claw.children.filter(
          c=> c.geometry && c.geometry.type==="SphereGeometry"
        );
        spheres.forEach(s=>{
          s.userData.grabbed=false;
          claw.remove(s);
          scene.add(s);
          let clawPos = new THREE.Vector3().setFromMatrixPosition(claw.matrixWorld);
          s.position.copy(clawPos);
          s.position.y -=1;
          s.velocity=new THREE.Vector3(0,0,0);
          physicsObjects.push(s);
        });
        clawState.grabbed=false;
        showMessage("Released!");
        phase="done";
        break;

      case "done":
        releaseUpdateFunctions.splice(releaseUpdateFunctions.indexOf(updateRelease),1);
        break;
    }
  }
  releaseUpdateFunctions.push(updateRelease);
}

function updatePhysics() {
  const floorY = -machineSize.y/2;
  physicsObjects.forEach(obj => {
    if(!obj.velocity) return; 
    obj.velocity.y -=0.01;
    obj.position.add(obj.velocity);

    if(obj.position.y -0.5<=floorY){
      obj.position.y=floorY+0.5;
      obj.velocity.y=0;
    }
  });
}

function checkGoalZone() {
  const binC = goalBin.position.clone();
  const hw=2, hh=1, hd=2;
  for(let i=physicsObjects.length-1; i>=0; i--){
    const s = physicsObjects[i];
    const p = s.position;
    if(
      p.x > binC.x - hw && p.x < binC.x + hw &&
      p.z > binC.z - hd && p.z < binC.z + hd &&
      p.y <= binC.y+hh
    ){
      totalDelivered++;
      updateScore();
      showMessage("Delivered +1!");
      scene.remove(s);
      physicsObjects.splice(i,1);
    }
  }
}

function animate() {
  requestAnimationFrame(animate);

  orbitControls.update();
  updateClawPosition();

  grabUpdateFunctions.forEach((fn, idx)=>{
    fn();
    if(!isGrabbing){
      grabUpdateFunctions.splice(idx,1);
    }
  });
  releaseUpdateFunctions.forEach(fn => fn());

  updatePhysics();
  checkGoalZone();
  renderer.render(scene, camera);
}

function onWindowResize(){
  const container = document.getElementById("clawCanvas");
  let w=container.clientWidth;
  let h=container.clientHeight;
  camera.aspect=w/h;
  camera.updateProjectionMatrix();
  renderer.setSize(w,h);
}

window.addEventListener("DOMContentLoaded", ()=>{
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
buttonIds.forEach(id=>{
  const btn=document.getElementById(id);
  if(!btn)return;
  ["mousedown","touchstart"].forEach(evt=>{
    btn.addEventListener(evt,(e)=>{
      e.preventDefault();
      pressedKeys[buttonKeyMap[id]]=true;
    },{ passive:false });
  });
  ["mouseup","mouseleave","touchend","touchcancel"].forEach(evt=>{
    btn.addEventListener(evt,(e)=>{
      e.preventDefault();
      pressedKeys[buttonKeyMap[id]]=false;
    },{ passive:false });
  });
});

window.addEventListener("keydown",(e)=>{
  let k=e.key.toLowerCase();
  if(["w","a","s","d","q","e"].includes(k)){
    pressedKeys[k]=true;
  } else if(k==="f"){
    grabClaw();
  } else if(k==="r"){
    releaseClaw();
  }
});
window.addEventListener("keyup",(e)=>{
  let k=e.key.toLowerCase();
  if(["w","a","s","d","q","e"].includes(k)){
    pressedKeys[k]=false;
  }
});
window.addEventListener("blur",()=>{
  Object.keys(pressedKeys).forEach(k=>pressedKeys[k]=false);
});

document.getElementById("grabBtn")?.addEventListener("click", grabClaw);
document.getElementById("releaseBtn")?.addEventListener("click", releaseClaw);

const speedRange=document.getElementById("speedRange");
if(speedRange){
  speedRange.addEventListener("input",(e)=>{
    clawState.speed=parseInt(e.target.value,10);
  });
}

const generateBtn=document.getElementById("generateBtn");
const targetCount=document.getElementById("targetCount");
if(generateBtn && targetCount){
  generateBtn.addEventListener("click",()=>{
    let val=parseInt(targetCount.value,10);
    val=clamp(1,50,val);
    clawState.targets=val;
    randomizeObjects(val);
  });
}

const resetBtn=document.getElementById("resetBtn");
if(resetBtn){
  resetBtn.addEventListener("click",()=>{
    claw.position.set(0,0,0);
    isGrabbing=false;
    isMoving=false;
    clawState.grabbed=false;
    totalDelivered=0;
    updateScore();
    randomizeObjects(clawState.targets);
    showMessage("Game reset!");
  });
}
