const G = 9.81;
const DT = 1 / 240;
const HIST = 10;
const N = Math.round(HIST / DT);

function makeAxis(cfg) {
  const b = {
    t: new Float32Array(N),
    r: new Float32Array(N),
    y: new Float32Array(N),
    e: new Float32Array(N),
    p: new Float32Array(N),
    i: new Float32Array(N),
    d: new Float32Array(N),
  };
  let head = 0;
  let len = 0;

  const ax = {
    y: 0,
    v: 0,
    intE: 0,
    prevE: 0,
    prevD: 0,
    p: 0,
    i: 0,
    d: 0,
    u: 0,
    gustForce: 0,
    gustTimer: 0,
    overshootMax: 0,
    lastSP: 0,
    buf: b,
    head: () => head,
    len: () => len,
    latest: () => (len === 0 ? 0 : b.t[(head - 1 + N) % N]),
    push(t, r, y, e, p, i, d) {
      b.t[head] = t;
      b.r[head] = r;
      b.y[head] = y;
      b.e[head] = e;
      b.p[head] = p;
      b.i[head] = i;
      b.d[head] = d;
      head = (head + 1) % N;
      if (len < N) len++;
    },
    forEach(fn) {
      const start = (head - len + N) % N;
      for (let k = 0; k < len; k++) {
        const idx = (start + k) % N;
        fn(b.t[idx], b.r[idx], b.y[idx], b.e[idx], b.p[idx], b.i[idx], b.d[idx]);
      }
    },
    reset() {
      ax.y = cfg.y0 ?? 0;
      ax.v = 0;
      ax.intE = 0;
      ax.prevE = 0;
      ax.prevD = 0;
      ax.p = 0;
      ax.i = 0;
      ax.d = 0;
      ax.u = 0;
      ax.gustForce = 0;
      ax.gustTimer = 0;
      ax.overshootMax = 0;
      ax.lastSP = 0;
      head = 0;
      len = 0;
    },
    step(t, dt, r, gains, sharedState) {
      let yMeas = ax.y;
      if (sharedState.noise) yMeas += (Math.random() - 0.5) * cfg.noiseMag;

      const e = r - yMeas;
      const dRaw = (e - ax.prevE) / dt;
      const dSm = 0.85 * ax.prevD + 0.15 * dRaw;
      ax.prevD = dSm;

      let intNew = ax.intE + e * dt;
      const pp = gains.kp * e;
      const ii = gains.ki * intNew;
      const dd = gains.kd * dSm;

      let u = cfg.ff(ax, sharedState) + pp + ii + dd;
      const unclamped = u;
      if (sharedState.sat) u = Math.max(cfg.uMin, Math.min(cfg.uMax, u));

      if (sharedState.awu) {
        const maxedHigh = u === cfg.uMax && unclamped > cfg.uMax && e > 0;
        const maxedLow = u === cfg.uMin && unclamped < cfg.uMin && e < 0;
        if (maxedHigh || maxedLow) intNew = ax.intE;
      }

      ax.intE = intNew;
      ax.prevE = e;

      if (sharedState.gust) {
        ax.gustTimer -= dt;
        if (ax.gustTimer <= 0) {
          ax.gustTimer = 2 + Math.random() * 3;
          ax.gustForce = (Math.random() - 0.5) * cfg.gustMag;
        }
      } else {
        ax.gustForce *= Math.exp(-dt * 2);
      }

      if (sharedState._gustAx === ax) {
        ax.gustForce = (Math.random() > 0.5 ? 1 : -1) * cfg.gustMag;
        sharedState._gustAx = null;
      }

      cfg.integrate(ax, u, dt, sharedState);
      ax.u = u;
      ax.p = pp;
      ax.i = ii;
      ax.d = dd;

      if (Math.abs(r - ax.lastSP) > cfg.spThresh) {
        ax.lastSP = r;
        ax.overshootMax = 0;
      }
      if (Math.abs(r) > 0.01) {
        const overshoot = (ax.y - r) / Math.abs(r);
        if (overshoot > ax.overshootMax) ax.overshootMax = overshoot;
      }

      ax.push(t, r, ax.y, e, pp, ii, dd);
    },
  };

  return ax;
}

const altGains = { kp: 6, ki: 2, kd: 3, sp: 5 };
const altAxis = makeAxis({
  y0: 0,
  noiseMag: 0.06,
  gustMag: 15,
  uMin: 0,
  uMax: 30,
  spThresh: 0.1,
  ff: (ax, sh) => sh.mass * G,
  integrate(ax, u, dt, sh) {
    const a = (u - sh.mass * G - sh.drag * ax.v + ax.gustForce) / sh.mass;
    ax.v += a * dt;
    ax.y += ax.v * dt;
    if (ax.y < 0) {
      ax.y = 0;
      if (ax.v < 0) ax.v = 0;
    }
  },
});

const pitGains = { kp: 8, ki: 1, kd: 2, sp: 15 };
const pitAxis = makeAxis({
  y0: 0,
  noiseMag: 0.3,
  gustMag: 30,
  uMin: -80,
  uMax: 80,
  spThresh: 0.5,
  ff: () => 0,
  integrate(ax, u, dt, sh) {
    const J = sh.mass * 0.04;
    const bRot = sh.drag * 0.12;
    ax.v += ((u - bRot * ax.v + ax.gustForce) / J) * dt;
    ax.y += ax.v * dt;
    if (Math.abs(ax.y) > 90) {
      ax.y = Math.sign(ax.y) * 90;
      ax.v = 0;
    }
  },
});

const shared = {
  mass: 1.0,
  drag: 0.6,
  gust: false,
  noise: false,
  sat: true,
  awu: true,
  speed: 1.0,
  running: true,
  _gustAx: null,
};

let sigType = "step";
let globalT = 0;

function sigVal(sp, sig, t) {
  switch (sig) {
    case "square":
      return Math.floor(t / 3) % 2 === 0 ? sp : sp * 0.3;
    case "sine":
      return sp * 0.5 + sp * 0.5 * Math.sin((2 * Math.PI * t) / 5);
    default:
      return sp;
  }
}

function resetAll() {
  globalT = 0;
  altAxis.reset();
  pitAxis.reset();
}

const CLR = (() => {
  const s = getComputedStyle(document.documentElement);
  const g = (v) => s.getPropertyValue(v).trim();
  return {
    alt: g("--cAlt"),
    pit: g("--cPit"),
    P: g("--cP"),
    I: g("--cI"),
    D: g("--cD"),
    altP: g("--cAltP") || g("--cP"),
    altI: g("--cAltI") || g("--cI"),
    altD: g("--cAltD") || g("--cD"),
    pitP: g("--cPitP") || g("--cP"),
    pitI: g("--cPitI") || g("--cI"),
    pitD: g("--cPitD") || g("--cD"),
    muted: g("--muted"),
    sub: g("--sub"),
    ink: g("--ink"),
    s1: g("--s1"),
    s2: g("--s2"),
    bg: g("--bg"),
    fontUi: g("--font-ui") || "ui-sans-serif, system-ui, sans-serif",
    fontMono: g("--font-mono") || "ui-monospace, monospace",
    glowBlur: parseFloat(g("--glow-blur")) || 0,
    glowAlpha: parseFloat(g("--glow-alpha")) || 0,
  };
})();

const cvDims = new Map();
const cvRO = new ResizeObserver((entries) => {
  for (const { target, contentRect } of entries) {
    cvDims.set(target, {
      W: Math.max(1, contentRect.width),
      H: Math.max(1, contentRect.height),
    });
  }
});

document.querySelectorAll("canvas").forEach((cv) => {
  const rect = cv.getBoundingClientRect();
  cvDims.set(cv, { W: Math.max(1, rect.width), H: Math.max(1, rect.height) });
  cvRO.observe(cv);
});

function hdpi(cv) {
  const dpr = window.devicePixelRatio || 1;
  const { W, H } = cvDims.get(cv) || { W: 1, H: 1 };
  if (cv.width !== W * dpr || cv.height !== H * dpr) {
    cv.width = W * dpr;
    cv.height = H * dpr;
  }
  const ctx = cv.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, W, H };
}

function rr(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function withAlpha(color, alpha) {
  if (!color || color[0] !== "#") return color;
  let hex = color.slice(1);
  if (hex.length === 3) hex = hex.split("").map((ch) => ch + ch).join("");
  if (hex.length !== 6) return color;
  const n = parseInt(hex, 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  return `rgba(${r},${g},${b},${alpha})`;
}

function glow(ctx, color) {
  if (CLR.glowBlur > 0) {
    ctx.shadowBlur = CLR.glowBlur;
    ctx.shadowColor = withAlpha(color, CLR.glowAlpha);
  }
}

function noGlow(ctx) {
  ctx.shadowBlur = 0;
}

function drawChart(cv, axis, series) {
  if (!cv) return;
  const { ctx, W, H } = hdpi(cv);
  ctx.clearRect(0, 0, W, H);
  if (axis.len() === 0) return;

  const tEnd = axis.latest();
  const tStart = Math.max(0, tEnd - HIST);
  const dur = tEnd - tStart || 1;

  let mn = Infinity;
  let mx = -Infinity;
  axis.forEach((t, r, y, e, p, i, d) => {
    if (t < tStart) return;
    for (const s of series) {
      const v = s.p({ r, y, e, p, i, d });
      if (v < mn) mn = v;
      if (v > mx) mx = v;
    }
  });

  if (!Number.isFinite(mn)) {
    mn = -1;
    mx = 1;
  }
  if (mn === mx) {
    mn -= 1;
    mx += 1;
  }

  const pad = (mx - mn) * 0.12;
  mn -= pad;
  mx += pad;
  mn = Math.min(mn, 0);
  mx = Math.max(mx, 0);

  const L = 30;
  const R = 6;
  const T = 4;
  const B = 4;
  const cW = W - L - R;
  const cH = H - T - B;
  const tx = (t) => L + ((t - tStart) / dur) * cW;
  const ty = (v) => T + cH - ((v - mn) / (mx - mn)) * cH;

  ctx.strokeStyle = "rgba(255,255,255,0.05)";
  ctx.lineWidth = 1;
  ctx.font = `11px ${CLR.fontMono}`;
  ctx.fillStyle = CLR.muted;
  for (let i = 0; i <= 4; i++) {
    const yy = T + (i / 4) * cH;
    ctx.beginPath();
    ctx.moveTo(L, yy + 0.5);
    ctx.lineTo(W - R, yy + 0.5);
    ctx.stroke();
    ctx.fillText((mx - (i / 4) * (mx - mn)).toFixed(1), 1, yy + 3);
  }

  if (mn < 0 && mx > 0) {
    const yz = ty(0);
    ctx.strokeStyle = "rgba(255,255,255,0.12)";
    ctx.beginPath();
    ctx.moveTo(L, yz + 0.5);
    ctx.lineTo(W - R, yz + 0.5);
    ctx.stroke();
  }

  for (const s of series) {
    ctx.save();
    glow(ctx, s.c);
    ctx.strokeStyle = s.c;
    ctx.lineWidth = s.w ?? 1.6;
    if (s.dash) ctx.setLineDash([4, 3]);
    ctx.beginPath();

    let started = false;
    const pts = [];
    axis.forEach((t, r, y, e, p, i, d) => {
      if (t < tStart) return;
      const x = tx(t);
      const yy = ty(s.p({ r, y, e, p, i, d }));
      if (!started) {
        ctx.moveTo(x, yy);
        started = true;
      } else {
        ctx.lineTo(x, yy);
      }
      pts.push([x, yy]);
    });
    ctx.stroke();

    if (s.fill && pts.length > 1) {
      ctx.lineTo(pts[pts.length - 1][0], ty(0));
      ctx.lineTo(pts[0][0], ty(0));
      ctx.closePath();
      ctx.globalAlpha = 0.18;
      ctx.fillStyle = s.c;
      ctx.fill();
    }

    ctx.globalAlpha = 1;
    ctx.setLineDash([]);
    noGlow(ctx);

    if (pts.length > 0) {
      const idx = (axis.head() - 1 + N) % N;
      const lv = s.p({
        r: axis.buf.r[idx],
        y: axis.buf.y[idx],
        e: axis.buf.e[idx],
        p: axis.buf.p[idx],
        i: axis.buf.i[idx],
        d: axis.buf.d[idx],
      });
      const yTag = ty(lv);
      if (yTag > T + 2 && yTag < H - B - 2) {
        ctx.font = `11px ${CLR.fontMono}`;
        const txt = lv.toFixed(1);
        const tw = ctx.measureText(txt).width + 7;
        ctx.fillStyle = CLR.bg;
        ctx.fillRect(W - R - tw, yTag - 7, tw, 13);
        ctx.fillStyle = s.c;
        ctx.fillText(txt, W - R - tw + 2, yTag + 3);
      }
    }

    ctx.restore();
  }
}

function drawAlt() {
  const cv = document.getElementById("altCv");
  if (!cv) return;
  const { ctx, W, H } = hdpi(cv);
  ctx.clearRect(0, 0, W, H);

  const YMAX = 12;
  const LP = 28;
  const RP = 10;
  const TP = 10;
  const BP = 20;
  const toY = (m) => (H - BP) - (m / YMAX) * (H - TP - BP);
  const fromY = (py) => (((H - BP) - py) / (H - TP - BP)) * YMAX;
  cv._fromY = fromY;

  ctx.font = `9px ${CLR.fontMono}`;
  ctx.fillStyle = CLR.muted;
  ctx.strokeStyle = "rgba(255,255,255,0.04)";
  ctx.lineWidth = 1;
  for (let m = 0; m <= YMAX; m++) {
    const y = toY(m) + 0.5;
    ctx.beginPath();
    ctx.moveTo(LP, y);
    ctx.lineTo(W - RP, y);
    ctx.stroke();
    ctx.fillText(`${m}m`, 2, y + 3);
  }

  ctx.fillStyle = "rgba(63,185,80,0.2)";
  ctx.fillRect(LP, toY(0), W - LP - RP, 3);

  const r = sigVal(altGains.sp, sigType, globalT);
  const sy = toY(r);
  ctx.fillStyle = "rgba(63,185,80,0.06)";
  ctx.fillRect(LP, sy - 20, W - LP - RP, 40);
  glow(ctx, CLR.alt);
  ctx.strokeStyle = CLR.alt;
  ctx.setLineDash([5, 4]);
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(LP, sy);
  ctx.lineTo(W - RP, sy);
  ctx.stroke();
  ctx.setLineDash([]);
  noGlow(ctx);

  ctx.font = `10px ${CLR.fontUi}`;
  const lbl = `${r.toFixed(1)} m`;
  const lw = ctx.measureText(lbl).width + 10;
  ctx.fillStyle = "rgba(63,185,80,0.12)";
  ctx.fillRect(W - RP - lw, sy - 8, lw, 16);
  ctx.strokeStyle = "rgba(63,185,80,0.3)";
  ctx.lineWidth = 1;
  ctx.strokeRect(W - RP - lw + 0.5, sy - 7.5, lw - 1, 15);
  ctx.fillStyle = CLR.alt;
  ctx.fillText(lbl, W - RP - lw + 4, sy + 3.5);

  ctx.fillStyle = CLR.alt;
  [LP, W - RP].forEach((x) => {
    ctx.beginPath();
    ctx.arc(x, sy, 3.5, 0, Math.PI * 2);
    ctx.fill();
  });

  const dy = toY(altAxis.y);
  const cx = W / 2;
  const tilt = Math.max(-0.3, Math.min(0.3, -altAxis.v * 0.04));
  ctx.save();
  ctx.translate(cx, dy);
  ctx.rotate(tilt);
  ctx.fillStyle = CLR.s2;
  ctx.strokeStyle = CLR.alt;
  ctx.lineWidth = 1.5;
  glow(ctx, CLR.alt);
  rr(ctx, -28, -6, 56, 12, 3);
  ctx.fill();
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(-28, 0);
  ctx.lineTo(-46, 0);
  ctx.moveTo(28, 0);
  ctx.lineTo(46, 0);
  ctx.stroke();

  const thr = Math.min(1, Math.max(0, altAxis.u / 30));
  const spin = prefersReducedMotion ? 0 : (thr * performance.now()) / 35;
  for (const mx of [-46, 46]) {
    ctx.save();
    ctx.translate(mx, 0);
    ctx.strokeStyle = `rgba(63,185,80,${0.4 + 0.55 * thr})`;
    ctx.lineWidth = 1;
    for (let k = 0; k < 3; k++) {
      const a = spin + k * 2.094;
      ctx.beginPath();
      ctx.moveTo(-13 * Math.cos(a), -1.5 * Math.sin(a));
      ctx.lineTo(13 * Math.cos(a), 1.5 * Math.sin(a));
      ctx.stroke();
    }
    ctx.fillStyle = CLR.alt;
    ctx.beginPath();
    ctx.arc(0, 0, 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  noGlow(ctx);
  const al = 40 * thr;
  ctx.strokeStyle = `rgba(63,185,80,${0.4 + 0.5 * thr})`;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, 8);
  ctx.lineTo(0, 8 + al);
  ctx.stroke();
  ctx.fillStyle = `rgba(63,185,80,${0.4 + 0.5 * thr})`;
  ctx.beginPath();
  ctx.moveTo(-3.5, 8 + al);
  ctx.lineTo(3.5, 8 + al);
  ctx.lineTo(0, 13 + al);
  ctx.closePath();
  ctx.fill();
  ctx.restore();

  if (Math.abs(altAxis.gustForce) > 0.5) {
    const dir = altAxis.gustForce > 0 ? 1 : -1;
    ctx.fillStyle = CLR.P;
    ctx.font = `10px ${CLR.fontUi}`;
    ctx.fillText(dir > 0 ? "↑ gust" : "↓ gust", W - 52, dy - dir * 22);
  }

  ctx.font = `10px ${CLR.fontUi}`;
  ctx.fillStyle = CLR.muted;
  ctx.fillText(`y=${altAxis.y.toFixed(2)}  v=${altAxis.v.toFixed(2)} m/s`, LP + 2, H - 5);
}

function drawPitch() {
  const cv = document.getElementById("pitCv");
  if (!cv) return;
  const { ctx, W, H } = hdpi(cv);
  ctx.clearRect(0, 0, W, H);

  const LP = 34;
  const RP = 14;
  const TP = 16;
  const BP = 22;
  const cx = W / 2;
  const cy = H / 2;
  const curAngle = pitAxis.y;
  const spAngle = sigVal(pitGains.sp, sigType, globalT);
  const degToY = (d) => cy - (d / 45) * (cy - TP);

  ctx.fillStyle = CLR.s1;
  rr(ctx, LP - 2, TP - 2, W - LP - RP + 4, H - TP - BP + 4, 4);
  ctx.fill();

  ctx.font = `11px ${CLR.fontUi}`;
  for (let deg = -45; deg <= 45; deg += 15) {
    const y = degToY(deg) + 0.5;
    const isZero = deg === 0;
    ctx.strokeStyle = isZero ? CLR.sub : "rgba(255,255,255,0.07)";
    ctx.lineWidth = isZero ? 1.5 : 1;
    ctx.beginPath();
    ctx.moveTo(LP, y);
    ctx.lineTo(W - RP, y);
    ctx.stroke();
    ctx.fillStyle = isZero ? CLR.sub : CLR.muted;
    ctx.textAlign = "right";
    ctx.fillText(`${deg > 0 ? "+" : ""}${deg}°`, LP - 4, y + 4);
  }
  ctx.textAlign = "left";

  const armHalf = Math.min(W * 0.3, 80);
  function drawDroneBody(angle, color, alpha, dashed) {
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.translate(cx, cy);
    ctx.rotate((-angle * Math.PI) / 180);
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.8;
    if (dashed) ctx.setLineDash([5, 4]);
    glow(ctx, color);
    ctx.beginPath();
    ctx.moveTo(-armHalf, 0);
    ctx.lineTo(armHalf, 0);
    ctx.stroke();
    ctx.setLineDash([]);

    for (const mx of [-armHalf, armHalf]) {
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      if (dashed) ctx.setLineDash([4, 3]);
      ctx.beginPath();
      ctx.arc(mx, 0, 9, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    ctx.fillStyle = dashed ? "transparent" : CLR.s2;
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.8;
    if (dashed) ctx.setLineDash([5, 4]);
    rr(ctx, -18, -5, 36, 10, 3);
    ctx.fill();
    ctx.stroke();
    ctx.setLineDash([]);

    if (!dashed) {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.moveTo(20, 0);
      ctx.lineTo(27, -4);
      ctx.lineTo(27, 4);
      ctx.closePath();
      ctx.fill();
    }

    noGlow(ctx);
    ctx.restore();
  }

  drawDroneBody(spAngle, CLR.pit, 0.45, true);

  const spY = degToY(spAngle);
  ctx.fillStyle = CLR.pit;
  ctx.beginPath();
  ctx.arc(LP, spY, 4, 0, Math.PI * 2);
  ctx.fill();
  ctx.font = `11px ${CLR.fontUi}`;
  ctx.fillStyle = CLR.pit;
  ctx.fillText(`SP ${spAngle >= 0 ? "+" : ""}${spAngle.toFixed(0)}°`, W - RP - 54, spY - 5);

  drawDroneBody(curAngle, CLR.pit, 1, false);

  const curY = degToY(curAngle);
  ctx.fillStyle = CLR.ink;
  ctx.beginPath();
  ctx.moveTo(LP, curY - 5);
  ctx.lineTo(LP + 8, curY);
  ctx.lineTo(LP, curY + 5);
  ctx.closePath();
  ctx.fill();

  ctx.font = `13px ${CLR.fontUi}`;
  ctx.fillStyle = CLR.ink;
  ctx.textAlign = "center";
  ctx.fillText(`${curAngle.toFixed(1)}°`, cx, H - 6);
  ctx.textAlign = "left";

  if (Math.abs(pitAxis.gustForce) > 0.5) {
    ctx.font = `11px ${CLR.fontUi}`;
    ctx.fillStyle = CLR.P;
    ctx.textAlign = "center";
    ctx.fillText(pitAxis.gustForce > 0 ? "↑ torque" : "↓ torque", cx, TP + 10);
    ctx.textAlign = "left";
  }
}

const PRESETS = [
  { name: "Open loop", a1kp: 0, a1ki: 0, a1kd: 0, a2kp: 0, a2ki: 0, a2kd: 0 },
  { name: "P only", a1kp: 6, a1ki: 0, a1kd: 0, a2kp: 8, a2ki: 0, a2kd: 0 },
  { name: "PI", a1kp: 6, a1ki: 2, a1kd: 0, a2kp: 8, a2ki: 1, a2kd: 0 },
  { name: "PD", a1kp: 6, a1ki: 0, a1kd: 3, a2kp: 8, a2ki: 0, a2kd: 2 },
  { name: "Tuned PID", a1kp: 6, a1ki: 2, a1kd: 3, a2kp: 8, a2ki: 1, a2kd: 2 },
  { name: "Oscillating", a1kp: 22, a1ki: 0, a1kd: 0, a2kp: 25, a2ki: 0, a2kd: 0 },
  { name: "I windup", a1kp: 6, a1ki: 10, a1kd: 3, a2kp: 8, a2ki: 8, a2kd: 2 },
  { name: "Noisy D", a1kp: 6, a1ki: 2, a1kd: 12, a2kp: 8, a2ki: 1, a2kd: 8 },
];

function applyPreset(preset) {
  const set = (id, obj, key, value) => {
    obj[key] = +value;
    const el = document.getElementById(id);
    if (el) el.value = value;
    const val = document.getElementById(`${id}V`);
    if (val) val.textContent = (+value).toFixed(2);
  };

  set("a1kp", altGains, "kp", preset.a1kp);
  set("a1ki", altGains, "ki", preset.a1ki);
  set("a1kd", altGains, "kd", preset.a1kd);
  set("a2kp", pitGains, "kp", preset.a2kp);
  set("a2ki", pitGains, "ki", preset.a2ki);
  set("a2kd", pitGains, "kd", preset.a2kd);

  updateCls();
  resetAll();

  document.querySelectorAll(".chip[data-preset]").forEach((chip) => {
    const on = PRESETS[+chip.dataset.preset] === preset;
    chip.classList.toggle("on", on);
    chip.setAttribute("aria-pressed", String(on));
  });
}

document.querySelectorAll(".chip[data-preset]").forEach((chip) => {
  chip.addEventListener("click", () => applyPreset(PRESETS[+chip.dataset.preset]));
});

function bindSlider(id, obj, key, valId) {
  const el = document.getElementById(id);
  const val = document.getElementById(valId);
  if (!el || !val) return;
  const sync = () => {
    obj[key] = parseFloat(el.value);
    val.textContent = obj[key].toFixed(2);
    updateCls();
  };
  el.addEventListener("input", sync);
  sync();
}

function updateCls() {
  const cls = (kp, ki, kd) => (!kp && !ki && !kd ? "OPEN" : `${kp ? "P" : ""}${ki ? "I" : ""}${kd ? "D" : ""}`);
  const a1 = document.getElementById("a1cls");
  const a2 = document.getElementById("a2cls");
  if (a1) a1.textContent = cls(altGains.kp, altGains.ki, altGains.kd);
  if (a2) a2.textContent = cls(pitGains.kp, pitGains.ki, pitGains.kd);
}

bindSlider("a1kp", altGains, "kp", "a1kpV");
bindSlider("a1ki", altGains, "ki", "a1kiV");
bindSlider("a1kd", altGains, "kd", "a1kdV");
bindSlider("a2kp", pitGains, "kp", "a2kpV");
bindSlider("a2ki", pitGains, "ki", "a2kiV");
bindSlider("a2kd", pitGains, "kd", "a2kdV");

const bindInput = (id, fn, event = "input") => {
  const el = document.getElementById(id);
  if (el) el.addEventListener(event, fn);
};

bindInput("a1sp", (e) => {
  altGains.sp = parseFloat(e.target.value) || 0;
});
bindInput("a2sp", (e) => {
  pitGains.sp = Math.max(-45, Math.min(45, parseFloat(e.target.value) || 0));
});
bindInput("eGust", (e) => {
  shared.gust = e.target.checked;
}, "change");
bindInput("eNoise", (e) => {
  shared.noise = e.target.checked;
}, "change");
bindInput("eSat", (e) => {
  shared.sat = e.target.checked;
}, "change");
bindInput("eAWU", (e) => {
  shared.awu = e.target.checked;
}, "change");
bindInput("eMass", (e) => {
  shared.mass = Math.max(0.1, parseFloat(e.target.value) || 1);
});
bindInput("eSpeed", (e) => {
  shared.speed = Math.max(0.1, parseFloat(e.target.value) || 1);
});

function forceSig(s) {
  sigType = s;
  document.querySelectorAll("#sigChips .chip").forEach((chip) => {
    const on = chip.dataset.sig === s;
    chip.classList.toggle("on", on);
    chip.setAttribute("aria-pressed", String(on));
  });
}

document.querySelectorAll("#sigChips .chip").forEach((chip) => {
  chip.addEventListener("click", () => forceSig(chip.dataset.sig));
});

const btnPlay = document.getElementById("btnPlay");

function syncRunningUI() {
  if (btnPlay) {
    btnPlay.setAttribute("aria-label", shared.running ? "Pause" : "Play");
    btnPlay.innerHTML = shared.running ? "&#9646;&#9646;" : "&#9654;";
  }
  const led = document.getElementById("ledDot");
  if (led) led.className = `led${shared.running ? "" : " off"}`;
  const txt = document.getElementById("ledTxt");
  if (txt) txt.textContent = shared.running ? "Running" : "Paused";
}

btnPlay?.addEventListener("click", () => {
  shared.running = !shared.running;
  syncRunningUI();
});

document.getElementById("btnReset")?.addEventListener("click", () => {
  resetAll();
});

document.getElementById("btnGust")?.addEventListener("click", () => {
  shared._gustAx = altAxis;
  setTimeout(() => {
    shared._gustAx = pitAxis;
  }, 150);
});

(function setupAltitudeDrag() {
  const cv = document.getElementById("altCv");
  if (!cv) return;
  let drag = false;
  cv.style.cursor = "ns-resize";
  cv.addEventListener("pointerdown", (e) => {
    drag = true;
    cv.setPointerCapture(e.pointerId);
    forceSig("step");
    move(e);
  });
  cv.addEventListener("pointermove", (e) => {
    if (drag) move(e);
  });
  window.addEventListener("pointerup", () => {
    drag = false;
  });

  function move(e) {
    if (!cv._fromY) return;
    const rect = cv.getBoundingClientRect();
    altGains.sp = Math.round(Math.max(0.2, Math.min(11.5, cv._fromY(e.clientY - rect.top))) * 10) / 10;
    const input = document.getElementById("a1sp");
    if (input) input.value = altGains.sp;
  }
})();

(function setupPitchDrag() {
  const cv = document.getElementById("pitCv");
  if (!cv) return;
  let drag = false;
  let lastY = 0;
  let startSP = 0;
  cv.style.cursor = "ns-resize";
  cv.addEventListener("pointerdown", (e) => {
    drag = true;
    lastY = e.clientY;
    startSP = pitGains.sp;
    cv.setPointerCapture(e.pointerId);
    forceSig("step");
  });
  cv.addEventListener("pointermove", (e) => {
    if (!drag) return;
    pitGains.sp = Math.round(Math.max(-45, Math.min(45, startSP + (lastY - e.clientY) * 0.4)));
    const input = document.getElementById("a2sp");
    if (input) input.value = pitGains.sp;
  });
  window.addEventListener("pointerup", () => {
    drag = false;
  });
})();

function toggleTunePanel(force) {
  const drawer = document.getElementById("drawer");
  if (!drawer) return;
  const open = force !== undefined ? force : !drawer.classList.contains("open");
  drawer.classList.toggle("open", open);
  const btn = document.getElementById("btnTune");
  if (btn) {
    btn.setAttribute("aria-expanded", String(open));
    btn.setAttribute("aria-label", open ? "Close tuning panel" : "Open tuning panel");
  }
}

document.getElementById("btnTune")?.addEventListener("click", () => toggleTunePanel());
if (window.innerWidth >= 1200) toggleTunePanel(true);

(function setupResizer() {
  const resizer = document.getElementById("colResizer");
  const app = document.querySelector(".app");
  if (!resizer || !app) return;
  let drag = false;
  let startX = 0;
  let startPct = 50;

  resizer.addEventListener("pointerdown", (e) => {
    drag = true;
    startX = e.clientX;
    startPct = parseFloat(getComputedStyle(app).getPropertyValue("--col-split")) || 50;
    resizer.setPointerCapture(e.pointerId);
  });

  window.addEventListener("pointermove", (e) => {
    if (!drag) return;
    const pct = Math.max(20, Math.min(80, startPct + ((e.clientX - startX) / app.offsetWidth) * 100));
    app.style.setProperty("--col-split", `${pct}%`);
  });

  window.addEventListener("pointerup", () => {
    drag = false;
  });
})();

function isTypingTarget(target) {
  return target instanceof HTMLInputElement ||
    target instanceof HTMLTextAreaElement ||
    target instanceof HTMLSelectElement ||
    target?.isContentEditable;
}

document.addEventListener("keydown", (e) => {
  if (isTypingTarget(e.target)) return;
  switch (e.key) {
    case " ":
      e.preventDefault();
      btnPlay?.click();
      break;
    case "r":
    case "R":
      resetAll();
      break;
    case "g":
    case "G":
      document.getElementById("btnGust")?.click();
      break;
    case "t":
    case "T":
      toggleTunePanel();
      break;
    case "s":
    case "S":
      forceSig("step");
      break;
    case "q":
    case "Q":
      forceSig("square");
      break;
    case "e":
    case "E":
      forceSig("sine");
      break;
    default: {
      const n = parseInt(e.key, 10);
      if (n >= 1 && n <= 8) applyPreset(PRESETS[n - 1]);
    }
  }
});

let lastNow = performance.now();

function frame(now) {
  const wall = Math.min(0.05, (now - lastNow) / 1000);
  lastNow = now;

  if (shared.running) {
    const sim = wall * shared.speed;
    const ns = Math.max(1, Math.round(sim / DT));
    const sdt = sim / ns;
    for (let s = 0; s < ns; s++) {
      altAxis.step(globalT, sdt, sigVal(altGains.sp, sigType, globalT), altGains, shared);
      pitAxis.step(globalT, sdt, sigVal(pitGains.sp, sigType, globalT), pitGains, shared);
      globalT += sdt;
    }
  }

  drawAlt();
  drawPitch();

  drawChart(document.getElementById("a1mainCv"), altAxis, [
    { p: (s) => s.r, c: CLR.alt, w: 1.8, dash: true },
    { p: (s) => s.y, c: CLR.ink, w: 1.8 },
  ]);
  drawChart(document.getElementById("a1pidCv"), altAxis, [
    { p: (s) => s.p, c: CLR.altP, fill: true },
    { p: (s) => s.i, c: CLR.altI, fill: true },
    { p: (s) => s.d, c: CLR.altD, fill: true },
  ]);
  drawChart(document.getElementById("a2mainCv"), pitAxis, [
    { p: (s) => s.r, c: CLR.pit, w: 1.8, dash: true },
    { p: (s) => s.y, c: CLR.ink, w: 1.8 },
  ]);
  drawChart(document.getElementById("a2pidCv"), pitAxis, [
    { p: (s) => s.p, c: CLR.pitP, fill: true },
    { p: (s) => s.i, c: CLR.pitI, fill: true },
    { p: (s) => s.d, c: CLR.pitD, fill: true },
  ]);

  const rA = sigVal(altGains.sp, sigType, globalT);
  const rP = sigVal(pitGains.sp, sigType, globalT);
  const setText = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  };

  setText("r_ay", altAxis.y.toFixed(2));
  setText("r_ae", (rA - altAxis.y).toFixed(2));
  setText("r_au", altAxis.u.toFixed(2));
  setText("r_ap", altAxis.p.toFixed(2));
  setText("r_ai", altAxis.i.toFixed(2));
  setText("r_ad", altAxis.d.toFixed(2));
  setText("r_py", pitAxis.y.toFixed(1));
  setText("r_pe", (rP - pitAxis.y).toFixed(1));
  setText("r_pu", pitAxis.u.toFixed(1));
  setText("r_pp", pitAxis.p.toFixed(2));
  setText("r_pi", pitAxis.i.toFixed(2));
  setText("r_pd", pitAxis.d.toFixed(2));
  setText("a1ep", `e=${(rA - altAxis.y).toFixed(2)}`);
  setText("a2ep", `e=${(rP - pitAxis.y).toFixed(1)}°`);
  setText("hdrT", globalT.toFixed(2));

  requestAnimationFrame(frame);
}

forceSig("sine");
applyPreset(PRESETS[4]);
syncRunningUI();
resetAll();
requestAnimationFrame(frame);
