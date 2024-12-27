/*
  2D Claw Machine Demo
  Simple 2D claw machine simulation with basic physics and collision detection.
  Query string schema: 
  ?direction=string&grabbed=boolean&speed=int&targets=int
  For usage with MCU or any embedded system, use the query string to control the claw machine.
  Example: ?direction=up&grabbed=true&speed=2&targets=5
  This will set the claw direction to 'up', item grabbed, speed to 2 and 5 targets to deliver.
*/
function getQueryParam(name) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(name);
}

function setQueryParam(params) {
  const urlParams = new URLSearchParams(window.location.search);
  for (const [key, value] of Object.entries(params)) urlParams.set(key, value);
  const newUrl = window.location.pathname + '?' + urlParams.toString();
  window.history.replaceState(null, '', newUrl);
}

function clamp(min, max, val) { return Math.min(max, Math.max(min, val)); }
function dist(ax, ay, bx, by) { return Math.hypot(ax - bx, ay - by); }

let directionFromURL = getQueryParam('direction') || 'none';
let grabbedFromURL = (getQueryParam('grabbed') === 'true');
let speedFromURL = parseInt(getQueryParam('speed') || '1', 10);
let targetsFromURL = parseInt(getQueryParam('targets') || '3', 10);

let clawState = {
  x: 50,
  y: 50,
  grabbed: grabbedFromURL,
  speed: (isNaN(speedFromURL) || speedFromURL < 1 || speedFromURL > 5) ? 1 : speedFromURL,
  targets: (isNaN(targetsFromURL) || targetsFromURL < 1 || targetsFromURL > 10) ? 3 : targetsFromURL,
  direction: directionFromURL
};

setQueryParam({
  direction: clawState.direction,
  grabbed: clawState.grabbed,
  speed: clawState.speed,
  targets: clawState.targets
});

const gravity = 0.3;
let pressedKeys = { w: false, a: false, s: false, d: false };
let objects = [];
let destination = { x: 90, y: 90, width: 10, height: 10 };
let lastUpdate = 0;
let isGrabbing = false;
let isMoving = false; 
let totalDelivered = 0;

function randomizeObjects(count) {
  const colors = ['#FFFF00','#007BFF','#6f42c1','#aaa'];
  objects = [];
  for (let i = 0; i < count; i++) {
    objects.push({
      x: Math.random() * 60 + 20,
      y: Math.random() * 20 + 5,
      radius: 5,
      color: colors[Math.floor(Math.random()*colors.length)],
      vx: 0,
      vy: 0,
      inClaw: false,
      delivered: false
    });
  }
}

function resetAll() {
  console.log('Resetting game state');
  clawState.x = 50;
  clawState.y = 50;
  clawState.speed = 1;
  clawState.grabbed = false;
  clawState.targets = 3;
  setQueryParam(clawState);
  randomizeObjects(clawState.targets);
  isGrabbing = false;
  isMoving = false;
  totalDelivered = 0;
  if (window.grabInterval) {
    clearInterval(window.grabInterval);
  }
}

randomizeObjects(clawState.targets);

const clawCanvas = document.getElementById('clawCanvas');
const ctx = clawCanvas.getContext('2d');
const upBtn = document.getElementById('upBtn');
const downBtn = document.getElementById('downBtn');
const leftBtn = document.getElementById('leftBtn');
const rightBtn = document.getElementById('rightBtn');
const grabBtn = document.getElementById('grabBtn');
const releaseBtn = document.getElementById('releaseBtn');
const speedRange = document.getElementById('speedRange');
const targetCount = document.getElementById('targetCount');
const generateBtn = document.getElementById('generateBtn');
const resetBtn = document.getElementById('resetBtn');

speedRange.value = clawState.speed;
targetCount.value = clawState.targets;

function showMessage(msg) {
  const el = document.getElementById('statusMessages');
  if (el) {
    if (msg.toLowerCase().includes('delivered') || msg.toLowerCase().includes('grabbed')) {
      el.style.color = '#28a745';
    } else {
      el.style.color = '#d9534f';
    }
    el.innerHTML = `${msg} | <span style="color:#000000">Total delivered: ${totalDelivered}</span>`;
    setTimeout(() => {
      if (el) el.innerHTML = `<span style="color:#000000">Total delivered: ${totalDelivered}</span>`;
    }, 2000);
  }
}

function draw() {
  ctx.clearRect(0, 0, clawCanvas.width, clawCanvas.height);
  let cx = (clawState.x / 100) * clawCanvas.width;
  let cy = (clawState.y / 100) * clawCanvas.height;
  ctx.strokeStyle = '#333'; ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(cx, 0);
  ctx.lineTo(cx, cy - 10);
  ctx.stroke();
  ctx.fillStyle = '#FFA500';
  ctx.fillRect(cx - 10, cy - 10, 20, 20);
  ctx.strokeStyle = '#555'; ctx.lineWidth = 2;
  ctx.beginPath();
  if (clawState.grabbed) {
    ctx.moveTo(cx - 10, cy + 10); ctx.lineTo(cx - 5, cy + 5);
    ctx.moveTo(cx + 10, cy + 10); ctx.lineTo(cx + 5, cy + 5);
  } else {
    ctx.moveTo(cx - 10, cy + 10); ctx.lineTo(cx - 15, cy + 15);
    ctx.moveTo(cx + 10, cy + 10); ctx.lineTo(cx + 15, cy + 15);
  }
  ctx.stroke();

  ctx.beginPath();
  ctx.strokeStyle = '#5bc0de';
  ctx.lineWidth = 2;
  let zoneX = (destination.x / 100) * clawCanvas.width;
  let zoneY = (destination.y / 100) * clawCanvas.height;
  let zoneW = (destination.width / 100) * clawCanvas.width;
  let zoneH = (destination.height / 100) * clawCanvas.height;
  ctx.rect(zoneX, zoneY, zoneW, zoneH);
  ctx.stroke();
  ctx.fillStyle = '#5bc0de';
  ctx.fillRect(zoneX - 5, zoneY, 5, zoneH);

  ctx.setLineDash([5, 5]);
  ctx.beginPath();
  let halfY = clawCanvas.height * 0.5;
  ctx.moveTo(0, halfY);
  ctx.lineTo(clawCanvas.width, halfY);
  ctx.stroke();
  ctx.setLineDash([]);

  for (let obj of objects) {
    if (obj.delivered) {
      if (obj.fade == null) obj.fade = 1.0;
      obj.fade -= 0.01;
      if (obj.fade <= 0) {
        objects = objects.filter(o => o !== obj);
        continue;
      }
      obj.color = 'rgba(92,184,92,' + obj.fade + ')';
    }
    let ox = (obj.x / 100) * clawCanvas.width;
    let oy = (obj.y / 100) * clawCanvas.height;
    ctx.beginPath();
    ctx.fillStyle = obj.color;
    ctx.arc(ox, oy, obj.radius * (clawCanvas.width / 100), 0, 2*Math.PI);
    ctx.fill();
  }
}

function updateDirection() {
  let newDirection = 'none';
  if (pressedKeys.w) newDirection = 'up';
  else if (pressedKeys.s) newDirection = 'down';
  else if (pressedKeys.a) newDirection = 'left';
  else if (pressedKeys.d) newDirection = 'right';

  if (clawState.direction !== newDirection) {
    clawState.direction = newDirection;
    setQueryParam({
      direction: newDirection,
      grabbed: clawState.grabbed,
      speed: clawState.speed,
      targets: clawState.targets
    });
  }
}

function gameLoop() {
  if (!isGrabbing && !isMoving) {
    let spd = clawState.speed * 0.5;
    let dx = 0, dy = 0;
    if (pressedKeys.w) dy -= spd;
    if (pressedKeys.s) dy += spd;
    if (pressedKeys.a) dx -= spd;
    if (pressedKeys.d) dx += spd;
    
    if (dx !== 0 || dy !== 0) {
      console.debug('Moving claw:', { dx, dy, newPos: { x: clawState.x + dx, y: clawState.y + dy } });
    }
    
    clawState.x = clamp(0, 100, clawState.x + dx);
    clawState.y = clamp(0, 50, clawState.y + dy); 
    
    updateDirection();
  }
  
  const now = performance.now();
  if (now - lastUpdate >= 100) {
    lastUpdate = now;
  }

  for (let obj of objects) {
    if (!obj.delivered) {
      if (!obj.inClaw) {
        obj.vy += gravity;
        obj.y += obj.vy * 0.5;
        if (obj.y > 98) { obj.y = 98; obj.vy = 0; }
        for (let other of objects) {
          if (other !== obj && !other.delivered) {
            let d = dist(obj.x, obj.y, other.x, other.y);
            if (d < (obj.radius + other.radius)) {
              let overlap = (obj.radius + other.radius) - d;
              let angle = Math.atan2(obj.y - other.y, obj.x - other.x);
              obj.x += Math.cos(angle) * overlap;
              obj.y += Math.sin(angle) * overlap;
              obj.vy = 0;
            }
          }
        }
      } else {
        obj.x = clawState.x;
        obj.y = clawState.y;
      }
      if (!obj.inClaw) {
        let ox = obj.x;
        let oy = obj.y;
        if (ox >= destination.x && oy >= destination.y &&
            ox <= (destination.x + destination.width) &&
            oy <= (destination.y + destination.height)) {
          obj.delivered = true;
          totalDelivered++;
          showMessage('Item delivered successfully!');
        }
      }
    }
  }

  if (objects.length > 0 && objects.every(o => o.delivered)) {
    showMessage('All delivered, spawning new wave!');
    clawState.targets = clamp(1, 20, clawState.targets + 1);
    randomizeObjects(clawState.targets);
    setQueryParam({
      direction: clawState.direction,
      grabbed: clawState.grabbed,
      speed: clawState.speed,
      targets: clawState.targets
    });
  }

  draw();
  requestAnimationFrame(gameLoop);
}

function grabClaw() {
  if (clawState.grabbed) {
    console.log('Item already in claw, cannot grab');
    return;
  }
  if (isGrabbing || isMoving) {
    console.log('Movement in progress, cannot grab');
    return;
  }
  
  console.log('Starting grab sequence');
  let startY = clawState.y;
  let foundObject = false;
  let isDescending = true;
  let startTime = Date.now();
  isGrabbing = true;
  isMoving = true; 
  
  if (window.grabInterval) {
    console.log('Clearing existing grab interval');
    clearInterval(window.grabInterval);
  }
  
  window.grabInterval = setInterval(() => {
    if (Date.now() - startTime > 5000) {
      console.warn('Grab sequence timed out');
      clearInterval(window.grabInterval);
      clawState.y = startY;
      isGrabbing = false;
      isMoving = false; 
      return;
    }

    if (isDescending) {
      if (clawState.y < 100) {
        clawState.y++;
        for (let obj of objects) {
          if (!obj.delivered && !obj.inClaw && dist(clawState.x, clawState.y, obj.x, obj.y) < 5) {
            console.log('Object grabbed at position:', { x: obj.x, y: obj.y });
            clawState.grabbed = true;
            setQueryParam({
              direction: clawState.direction,
              grabbed: true,
              speed: clawState.speed,
              targets: clawState.targets
            });
            obj.inClaw = true;
            foundObject = true;
            isDescending = false;
            showMessage('Object grabbed!');
            break;
          }
        }
      } else {
        console.log('Reached bottom, returning');
        isDescending = false;
      }
    } else {
      if (clawState.y > startY) {
        clawState.y--;
      } else {
        console.log('Grab sequence completed', { foundObject, position: { x: clawState.x, y: clawState.y } });
        clearInterval(window.grabInterval);
        isGrabbing = false;
        isMoving = false;
      }
    }
  }, 20);
}

function releaseClaw() {
  console.log('Releasing claw');
  clawState.grabbed = false;
  setQueryParam({
    direction: clawState.direction,
    grabbed: false,
    speed: clawState.speed,
    targets: clawState.targets
  });
  for (let obj of objects) {
    if (obj.inClaw) {
      console.log('Released object at:', { x: obj.x, y: obj.y });
      obj.inClaw = false;
      obj.vy = 0;
    }
  }
}

upBtn.addEventListener('click', () => { clawState.y = clamp(0, 50, clawState.y - clawState.speed); });
downBtn.addEventListener('click', () => { clawState.y = clamp(0, 50, clawState.y + clawState.speed); });
leftBtn.addEventListener('click', () => { clawState.x = clamp(0, 100, clawState.x - clawState.speed); });
rightBtn.addEventListener('click', () => { clawState.x = clamp(0, 100, clawState.x + clawState.speed); });
grabBtn.addEventListener('click', grabClaw);
releaseBtn.addEventListener('click', releaseClaw);

speedRange.addEventListener('input', () => {
  clawState.speed = parseInt(speedRange.value, 10);
  setQueryParam({
    direction: clawState.direction,
    grabbed: clawState.grabbed,
    speed: clawState.speed,
    targets: clawState.targets
  });
});

generateBtn.addEventListener('click', () => {
  clawState.targets = parseInt(targetCount.value, 10) || 3;
  randomizeObjects(clawState.targets);
});

resetBtn.addEventListener('click', resetAll);

['upBtn','downBtn','leftBtn','rightBtn'].forEach(id => {
  const btn = document.getElementById(id);
  let keyMap = { upBtn:'w', downBtn:'s', leftBtn:'a', rightBtn:'d' };
  
  btn.addEventListener('mousedown', (e) => {
    e.preventDefault();
    pressedKeys[keyMap[id]] = true;
  });
  btn.addEventListener('mouseup', (e) => {
    e.preventDefault();
    pressedKeys[keyMap[id]] = false;
  });
  btn.addEventListener('mouseleave', (e) => {
    e.preventDefault();
    pressedKeys[keyMap[id]] = false;
  });
  
  btn.addEventListener('touchstart', (e) => {
    e.preventDefault();
    e.stopPropagation();
    pressedKeys[keyMap[id]] = true;
  }, { passive: false });
  
  btn.addEventListener('touchend', (e) => {
    e.preventDefault();
    e.stopPropagation();
    pressedKeys[keyMap[id]] = false;
  }, { passive: false });
  
  btn.addEventListener('touchcancel', (e) => {
    e.preventDefault();
    e.stopPropagation();
    pressedKeys[keyMap[id]] = false;
  }, { passive: false });
});

window.addEventListener('blur', () => {
  Object.keys(pressedKeys).forEach(key => pressedKeys[key] = false);
});

window.addEventListener('keydown', (e) => {
  if (e.key.toLowerCase() === 'w') pressedKeys.w = true;
  if (e.key.toLowerCase() === 's') pressedKeys.s = true;
  if (e.key.toLowerCase() === 'a') pressedKeys.a = true;
  if (e.key.toLowerCase() === 'd') pressedKeys.d = true;
  if (e.key.toLowerCase() === 'f') grabClaw();
  if (e.key.toLowerCase() === 'r') releaseClaw();
});
window.addEventListener('keyup', (e) => {
  if (e.key.toLowerCase() === 'w') pressedKeys.w = false;
  if (e.key.toLowerCase() === 's') pressedKeys.s = false;
  if (e.key.toLowerCase() === 'a') pressedKeys.a = false;
  if (e.key.toLowerCase() === 'd') pressedKeys.d = false;
});

draw();
requestAnimationFrame(gameLoop);