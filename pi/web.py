"""
Flask web server — serves the controller UI and handles all API routes.
Port of the Arduino WebServer routes to Flask.
"""

import threading
from flask import Flask, request, jsonify, Response
from urllib.parse import unquote

from config import (
    VIEW_EYES_NORMAL, VIEW_EYES_SQUISH, VIEW_CODE, VIEW_DRAW,
    C_ORANGE, C_WHITE, WEB_PORT,
)


INDEX_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
<title>Clawd Mochi</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
body{background:#1c1c20;font-family:'Courier New',monospace;color:#e8e4dc;
  display:flex;flex-direction:column;align-items:center;
  padding:20px 14px 52px;gap:14px;min-height:100vh}

.hdr{text-align:center;padding:2px 0 4px}
.mascot{font-size:15px;color:#c96a3e;line-height:1.3;font-weight:bold;
  font-family:'Courier New',monospace;display:block;letter-spacing:1px}
.sitename{font-size:10px;color:#5a5048;margin-top:8px;letter-spacing:3px}

.sec{width:100%;max-width:390px;font-size:10px;color:#8a8278;
  letter-spacing:2px;font-weight:bold;padding:0 2px}

/* Busy bar */
.busy{width:100%;max-width:390px;height:2px;background:#2e2a28;
  border-radius:1px;overflow:hidden;opacity:0;transition:opacity .2s}
.busy.show{opacity:1}
.busy-i{height:100%;width:30%;background:#c96a3e;border-radius:1px;
  animation:sl 1s linear infinite}
@keyframes sl{0%{margin-left:-30%}100%{margin-left:100%}}

/* Controls */
.ctrl{display:flex;gap:8px;width:100%;max-width:390px}
.cbtn{flex:1;background:#252428;border:1.5px solid #38343a;border-radius:10px;
  color:#b8b4ac;font-family:'Courier New',monospace;font-size:11px;font-weight:bold;
  padding:12px 4px;cursor:pointer;text-align:center;transition:all .12s}
.cbtn:active:not(:disabled){transform:scale(.94)}
.cbtn:disabled{opacity:.3;cursor:default}
.cbtn.on{border-color:#c96a3e;color:#c96a3e;background:#201408}
.cbtn.dim{border-color:#2e2a28;color:#4a4540}

/* View grid */
.vgrid{display:grid;grid-template-columns:1fr 1fr;gap:8px;width:100%;max-width:390px}
.vbtn{background:#252428;border:1.5px solid #38343a;border-radius:12px;
  color:#d8d4cc;font-family:'Courier New',monospace;
  padding:14px 6px 10px;cursor:pointer;text-align:center;
  transition:all .12s;user-select:none}
.vbtn:active:not(:disabled){transform:scale(.94)}
.vbtn:disabled{opacity:.3;cursor:default}
.vbtn .ic{font-size:20px;display:block;margin-bottom:4px;line-height:1;color:#c96a3e}
.vbtn .nm{font-size:12px;font-weight:bold;color:#e8e4dc}
.vbtn .ht{font-size:9px;color:#8a8278;margin-top:3px}
.vbtn.active{border-color:#c96a3e;background:#201408}
.vbtn[data-v="1"].active{border-color:#c96a3e;background:#201408}
.vbtn[data-v="2"].active{border-color:#4a8acd;background:#0c1628}
.vbtn[data-v="3"].active{border-color:#38343a;background:#201c18}

/* Speed slider */
.speed-row{width:100%;max-width:390px;display:flex;align-items:center;gap:10px}
.sl{font-size:10px;color:#6a6058;white-space:nowrap;min-width:36px}
input[type=range]{flex:1;accent-color:#c96a3e;cursor:pointer;height:20px}
.sv{font-size:11px;color:#c96a3e;min-width:44px;text-align:right;font-weight:bold}

/* Terminal */
.twrap{width:100%;max-width:390px;display:none;flex-direction:column;gap:8px}
.twrap.open{display:flex}
.thdr{display:flex;justify-content:space-between;align-items:center}
.tttl{font-size:11px;color:#28b878;letter-spacing:1px;font-weight:bold}
.tx{background:#0c1e12;border:2px solid #1a4828;border-radius:9px;
  color:#28b878;font-family:'Courier New',monospace;font-size:13px;
  font-weight:bold;padding:10px 18px;cursor:pointer}
.tx:active{background:#081410}
.trow{display:flex;gap:6px}
.tin{flex:1;background:#0c1018;border:1.5px solid #1a2820;border-radius:9px;
  color:#40d880;font-family:'Courier New',monospace;font-size:15px;
  padding:11px;outline:none}
.tin::placeholder{color:#2a3828}
.tgo{background:#1a9060;border:none;border-radius:9px;color:#fff;
  font-family:'Courier New',monospace;font-size:22px;font-weight:bold;
  padding:11px 16px;cursor:pointer;min-width:52px}
.tgo:active{background:#0f6040}

/* Canvas */
.cwrap{width:100%;max-width:390px;background:#222028;border:1.5px solid #38343a;
  border-radius:12px;padding:12px;flex-direction:column;gap:10px;display:none}
.cwrap.open{display:flex}
.crow{display:flex;gap:8px}
.ci{display:flex;flex-direction:column;align-items:center;gap:4px;flex:1}
.cl{font-size:10px;color:#7a7068;letter-spacing:1px;font-weight:bold}
.cs{width:100%;height:38px;border-radius:7px;border:1.5px solid #38343a;cursor:pointer;padding:0}
.dacts{display:flex;gap:7px}
.db{flex:1;background:#1c1820;border:1.5px solid #38343a;border-radius:9px;
  color:#c0bab8;font-family:'Courier New',monospace;font-size:11px;
  font-weight:bold;padding:11px 4px;cursor:pointer;transition:all .12s}
.db:active{transform:scale(.95);background:#281838}
.db.hi{border-color:#c96a3e;color:#c96a3e}
canvas{width:100%;border-radius:8px;border:1.5px solid #38343a;
  touch-action:none;cursor:crosshair;display:block}

/* WiFi config */
.wifi-wrap{width:100%;max-width:390px;display:none;flex-direction:column;gap:8px}
.wifi-wrap.open{display:flex}
.wifi-list{max-height:150px;overflow-y:auto;display:flex;flex-direction:column;gap:4px}
.wifi-item{background:#252428;border:1.5px solid #38343a;border-radius:8px;
  padding:8px 12px;cursor:pointer;font-size:12px;color:#e8e4dc;
  font-family:'Courier New',monospace;transition:all .12s}
.wifi-item:hover{border-color:#c96a3e}
.wifi-item .sig{color:#8a8278;font-size:10px;float:right}
.wifi-input{background:#0c1018;border:1.5px solid #1a2820;border-radius:9px;
  color:#40d880;font-family:'Courier New',monospace;font-size:13px;
  padding:10px;outline:none;width:100%}
.wifi-input::placeholder{color:#2a3828}
.wifi-btn{background:#1a9060;border:none;border-radius:9px;color:#fff;
  font-family:'Courier New',monospace;font-size:12px;font-weight:bold;
  padding:10px 16px;cursor:pointer;width:100%}
.wifi-btn:active{background:#0f6040}
.wifi-status{font-size:11px;color:#8a8278;text-align:center;padding:4px}

/* Toast */
.toast{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);
  background:#252428;border:1.5px solid #38343a;border-radius:9px;
  font-size:12px;color:#d8d4cc;padding:7px 16px;opacity:0;
  transition:opacity .18s;pointer-events:none;white-space:nowrap;z-index:99}
.toast.show{opacity:1}
</style>
</head>
<body>

<div class="hdr">
  <span class="mascot">&#x2590;&#x259B;&#x2588;&#x2588;&#x2588;&#x259C;&#x258C;<br>&#x259C;&#x2588;&#x2588;&#x2588;&#x2588;&#x2588;&#x259B;<br>&#x2598;&#x2598;&nbsp;&#x259D;&#x259D;</span>
  <div class="sitename">CLAWD &middot; MOCHI &middot; CONTROLLER</div>
</div>

<div class="busy" id="busy"><div class="busy-i"></div></div>

<div class="sec">// controls</div>
<div class="ctrl">
  <button class="cbtn on" id="blBtn" onclick="toggleBL()">&#9728; display on</button>
  <button class="cbtn" id="wifiBtn" onclick="toggleWifi()">&#9783; wifi config</button>
</div>

<div class="sec">// views</div>
<div class="vgrid">
  <button class="vbtn active" data-v="0" onclick="setView(0)">
    <span class="ic">&#9632; &#9632;</span>
    <span class="nm">Normal eyes</span>
    <span class="ht">wiggle + blink</span>
  </button>
  <button class="vbtn" data-v="1" onclick="setView(1)">
    <span class="ic">&gt; &lt;</span>
    <span class="nm">Squish eyes</span>
    <span class="ht">open / close</span>
  </button>
  <button class="vbtn" data-v="2" onclick="setView(2)">
    <span class="ic">{ }</span>
    <span class="nm">Claude Code</span>
    <span class="ht">opens terminal</span>
  </button>
  <button class="vbtn" data-v="3" onclick="toggleCanvas()">
    <span class="ic">&#11035;</span>
    <span class="nm">Canvas</span>
    <span class="ht">draw on display</span>
  </button>
</div>

<div class="sec">// speed</div>
<div class="speed-row">
  <span class="sl">slow</span>
  <input type="range" id="spd" min="1" max="3" value="1" step="1" oninput="setSpeed(this.value)">
  <span class="sv" id="spdV">slow</span>
</div>

<div class="ctrl">
  <div class="ci" style="flex:1;display:flex;flex-direction:column;gap:4px;align-items:stretch">
    <span class="cl" style="font-size:10px;color:#8a8278;letter-spacing:1px;font-weight:bold;text-align:center">BACKGROUND</span>
    <input type="color" class="cs" id="bgCol" value="#aa4818" oninput="onBgChange(this.value)">
  </div>
  <div class="ci" style="flex:1;display:flex;flex-direction:column;gap:4px;align-items:stretch">
    <span class="cl" style="font-size:10px;color:#8a8278;letter-spacing:1px;font-weight:bold;text-align:center">PEN COLOR</span>
    <input type="color" class="cs" id="penCol" value="#000000">
  </div>
</div>

<div class="sec">// terminal</div>
<div class="twrap" id="twrap">
  <div class="thdr">
    <span class="tttl">&#9658; clawd:~$</span>
    <button class="tx" onclick="closeTerm()">&#x2715; exit terminal</button>
  </div>
  <div class="trow">
    <input class="tin" id="tin" type="text" placeholder="type here..."
           autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false">
    <button class="tgo" onclick="termEnter()">&#8629;</button>
  </div>
</div>

<div class="cwrap" id="cwrap">
  <div class="dacts">
    <button class="db hi" onclick="clearAll()">&#11035; clear</button>
    <button class="db" style="border-color:#28b878;color:#28b878" onclick="toggleCanvas()">&#10003; done</button>
  </div>
  <canvas id="cvs" width="240" height="240"></canvas>
</div>

<div class="sec">// wifi</div>
<div class="wifi-wrap" id="wifiWrap">
  <div class="wifi-status" id="wifiStatus">scanning...</div>
  <div class="wifi-list" id="wifiList"></div>
  <input class="wifi-input" id="wifiSsid" type="text" placeholder="SSID">
  <input class="wifi-input" id="wifiPass" type="password" placeholder="Password">
  <button class="wifi-btn" onclick="connectWifi()">Connect to WiFi</button>
  <button class="wifi-btn" style="background:#c96a3e" onclick="switchToAP()">Switch to AP Mode</button>
</div>

<div class="toast" id="toast"></div>

<script>
let activeView  = 0;
let termOpen    = false;
let canvasOpen  = false;
let wifiOpen    = false;
let blOn        = true;
let isBusy      = false;
let drawing     = false;
let lastX = 0, lastY = 0;
let tt;

const spdLabels = ['','slow','normal','fast'];

function toast(msg, ok=true) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.style.borderColor = ok ? '#28b878' : '#c96a3e';
  el.classList.add('show');
  clearTimeout(tt);
  tt = setTimeout(() => el.classList.remove('show'), 1300);
}

function setBusy(b) {
  isBusy = b;
  document.getElementById('busy').classList.toggle('show', b);
  const locked = b || termOpen;
  document.querySelectorAll('.vbtn').forEach(el => {
    el.disabled = canvasOpen ? parseInt(el.dataset.v) !== 3 : locked;
  });
  document.querySelectorAll('.cbtn').forEach(el => {
    if (el.id !== 'blBtn' && el.id !== 'wifiBtn') el.disabled = locked;
  });
}

async function req(path) {
  try { const r = await fetch(path); return r.ok; }
  catch(e) { toast('no connection', false); return false; }
}

async function waitNotBusy() {
  for (let i = 0; i < 100; i++) {
    try {
      const r = await fetch('/state');
      const j = await r.json();
      if (!j.busy) return;
    } catch(e) {}
    await new Promise(r => setTimeout(r, 150));
  }
}

async function onBgChange(hex) {
  if (canvasOpen) {
    await req('/draw/clear?bg=' + encodeURIComponent(hex));
  } else {
    await req('/redraw?bg=' + encodeURIComponent(hex));
  }
  redrawCanvas(hex);
}

async function setSpeed(v) {
  document.getElementById('spdV').textContent = spdLabels[v];
  await req('/speed?v=' + v);
}

async function setView(v) {
  if (isBusy || termOpen || canvasOpen) return;
  if (v === 3) { toggleCanvas(); return; }
  const keys = ['w','s','d'];
  if (!await req('/cmd?k=' + keys[v])) return;
  activeView = v;
  document.querySelectorAll('.vbtn').forEach(b =>
    b.classList.toggle('active', parseInt(b.dataset.v) === v));
  if (v === 2) {
    termOpen = true;
    document.getElementById('twrap').classList.add('open');
    setBusy(false);
    document.querySelectorAll('.vbtn,.lbtn').forEach(b => b.disabled = true);
    document.getElementById('tin').focus();
    toast('terminal open');
    return;
  }
  setBusy(true);
  await waitNotBusy();
  setBusy(false);
}

async function toggleBL() {
  blOn = !blOn;
  await req('/backlight?on=' + (blOn ? 1 : 0));
  const b = document.getElementById('blBtn');
  b.textContent = blOn ? '\u2600 display on' : '\u25cb display off';
  b.classList.toggle('on', blOn);
  b.classList.toggle('dim', !blOn);
}

async function toggleCanvas() {
  canvasOpen = !canvasOpen;
  document.getElementById('cwrap').classList.toggle('open', canvasOpen);
  document.querySelectorAll('.vbtn').forEach(btn =>
    btn.classList.toggle('active', canvasOpen && parseInt(btn.dataset.v) === 3));
  await req('/canvas?on=' + (canvasOpen ? 1 : 0));
  if (canvasOpen) {
    const bg = document.getElementById('bgCol').value;
    redrawCanvas(bg);
    await req('/draw/clear?bg=' + encodeURIComponent(bg));
    document.querySelectorAll('.vbtn,.lbtn').forEach(b => b.disabled = true);
    toast('canvas active');
  } else {
    setBusy(false);
    toast('canvas off');
  }
}

// Terminal
const tin = document.getElementById('tin');
let lastVal = '';
tin.addEventListener('input', async () => {
  const cur = tin.value, prev = lastVal;
  if (cur.length > prev.length) {
    await req('/char?c=' + encodeURIComponent(cur[cur.length - 1]));
  } else if (cur.length < prev.length) {
    await req('/char?c=%08');
  }
  lastVal = cur;
});
async function termEnter() {
  await req('/char?c=%0A');
  tin.value = ''; lastVal = ''; tin.focus();
}
tin.addEventListener('keydown', e => {
  if (e.key === 'Enter') { e.preventDefault(); termEnter(); }
});
async function closeTerm() {
  await req('/cmd?k=q');
  termOpen = false;
  document.getElementById('twrap').classList.remove('open');
  setBusy(false);
  toast('terminal closed');
}

// Canvas drawing
const cvs = document.getElementById('cvs');
const ctx = cvs.getContext('2d');
let strokePts = [];

function getPos(e) {
  const r = cvs.getBoundingClientRect();
  const sx = cvs.width / r.width, sy = cvs.height / r.height;
  const s = e.touches ? e.touches[0] : e;
  return { x: (s.clientX - r.left) * sx, y: (s.clientY - r.top) * sy };
}

function redrawCanvas(hex) {
  ctx.fillStyle = hex;
  ctx.fillRect(0, 0, cvs.width, cvs.height);
}

function startDraw(e) {
  e.preventDefault();
  drawing = true;
  strokePts = [];
  const p = getPos(e); lastX = p.x; lastY = p.y;
  strokePts.push({ x: Math.round(p.x), y: Math.round(p.y) });
  ctx.beginPath(); ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
  ctx.fillStyle = document.getElementById('penCol').value; ctx.fill();
}
function moveDraw(e) {
  if (!drawing) return; e.preventDefault();
  const p = getPos(e);
  ctx.beginPath(); ctx.moveTo(lastX, lastY); ctx.lineTo(p.x, p.y);
  ctx.strokeStyle = document.getElementById('penCol').value;
  ctx.lineWidth = 4; ctx.lineCap = 'round'; ctx.stroke();
  strokePts.push({ x: Math.round(p.x), y: Math.round(p.y) });
  lastX = p.x; lastY = p.y;
}
async function endDraw(e) {
  if (!drawing) return; drawing = false;
  if (!canvasOpen || strokePts.length < 1) return;
  const pen = document.getElementById('penCol').value.replace('#', '');
  const pts = strokePts.map(p => p.x + ',' + p.y).join(';');
  await req('/draw/stroke?pen=' + pen + '&pts=' + encodeURIComponent(pts));
  strokePts = [];
}

cvs.addEventListener('mousedown',  startDraw);
cvs.addEventListener('mousemove',  moveDraw);
cvs.addEventListener('mouseup',    endDraw);
cvs.addEventListener('mouseleave', endDraw);
cvs.addEventListener('touchstart', startDraw, {passive:false});
cvs.addEventListener('touchmove',  moveDraw,  {passive:false});
cvs.addEventListener('touchend',   endDraw);

async function clearAll() {
  const bg = document.getElementById('bgCol').value;
  redrawCanvas(bg);
  await req('/draw/clear?bg=' + encodeURIComponent(bg));
  toast('cleared');
}

// WiFi config
function toggleWifi() {
  wifiOpen = !wifiOpen;
  document.getElementById('wifiWrap').classList.toggle('open', wifiOpen);
  const b = document.getElementById('wifiBtn');
  b.classList.toggle('on', wifiOpen);
  if (wifiOpen) scanWifi();
}

async function scanWifi() {
  document.getElementById('wifiStatus').textContent = 'scanning...';
  try {
    const r = await fetch('/wifi/scan');
    const networks = await r.json();
    const list = document.getElementById('wifiList');
    list.innerHTML = '';
    networks.forEach(n => {
      const el = document.createElement('div');
      el.className = 'wifi-item';
      el.innerHTML = n.ssid + '<span class="sig">' + n.signal + '%</span>';
      el.onclick = () => { document.getElementById('wifiSsid').value = n.ssid; };
      list.appendChild(el);
    });
    document.getElementById('wifiStatus').textContent = networks.length + ' networks found';
  } catch(e) {
    document.getElementById('wifiStatus').textContent = 'scan failed';
  }
}

async function connectWifi() {
  const ssid = document.getElementById('wifiSsid').value;
  const pass = document.getElementById('wifiPass').value;
  if (!ssid) { toast('enter SSID', false); return; }
  document.getElementById('wifiStatus').textContent = 'connecting...';
  try {
    const r = await fetch('/wifi/connect?ssid=' + encodeURIComponent(ssid) + '&password=' + encodeURIComponent(pass));
    const j = await r.json();
    if (j.ok) {
      toast('connected to ' + ssid);
      document.getElementById('wifiStatus').textContent = 'connected: ' + (j.ip || ssid);
    } else {
      toast('failed to connect', false);
      document.getElementById('wifiStatus').textContent = 'connection failed';
    }
  } catch(e) {
    toast('connection error', false);
  }
}

async function switchToAP() {
  document.getElementById('wifiStatus').textContent = 'switching to AP...';
  try {
    await fetch('/wifi/ap');
    toast('AP mode active');
    document.getElementById('wifiStatus').textContent = 'AP mode: ClaWD-Mochi';
  } catch(e) {
    toast('error switching to AP', false);
  }
}

// Init: sync state
(async () => {
  try {
    const r = await fetch('/state');
    const j = await r.json();
    const spd = j.speed || 1;
    document.getElementById('spd').value = spd;
    document.getElementById('spdV').textContent = spdLabels[spd];
    if (j.bl === false) {
      blOn = false;
      const b = document.getElementById('blBtn');
      b.textContent = '\u25cb display off';
      b.classList.remove('on'); b.classList.add('dim');
    }
    if (j.wifi_mode) {
      document.getElementById('wifiStatus').textContent =
        j.wifi_mode === 'ap' ? 'AP mode: ClaWD-Mochi' : 'connected: ' + (j.wifi_ip || '');
    }
  } catch(e) {}
  document.getElementById('bgCol').value = '#aa4818';
  redrawCanvas('#aa4818');
})();
</script>
</body>
</html>"""


def hex_to_rgb(hex_str):
    """Convert '#RRGGBB' or 'RRGGBB' to an (R, G, B) tuple."""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) != 6:
        return C_ORANGE
    return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))


def create_app(mochi):
    """Create and configure the Flask app with all routes.

    Args:
        mochi: The main Mochi application instance with display, terminal,
               canvas, audio, wifi, and state attributes.
    """
    app = Flask(__name__)

    @app.after_request
    def add_no_cache(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        return response

    @app.route("/")
    def route_root():
        return Response(INDEX_HTML, mimetype="text/html")

    @app.route("/cmd")
    def route_cmd():
        k = request.args.get("k", "")
        if not k:
            return jsonify(e=1), 400

        if mochi.terminal.active:
            if k == "q":
                mochi.terminal.deactivate()
                from faces import draw_code_view
                draw_code_view(mochi.display)
                mochi.audio.play("switch")
            return jsonify(ok=1)

        # Run animation in a thread to avoid blocking the web server
        def do_cmd():
            mochi.busy = True
            if k == "w":
                mochi.current_view = VIEW_EYES_NORMAL
                from faces import anim_normal_eyes
                anim_normal_eyes(mochi.display, mochi.anim_bg_color, mochi.speed_ms)
                mochi.audio.play("switch")
            elif k == "s":
                mochi.current_view = VIEW_EYES_SQUISH
                from faces import anim_squish_eyes
                anim_squish_eyes(mochi.display, mochi.anim_bg_color, mochi.speed_ms)
                mochi.audio.play("switch")
            elif k == "d":
                mochi.current_view = VIEW_CODE
                from faces import draw_code_view
                draw_code_view(mochi.display)
                mochi.terminal.activate()
                mochi.audio.play("terminal")
            elif k == "a":
                mochi.current_view = VIEW_EYES_NORMAL
                from faces import anim_logo_reveal
                anim_logo_reveal(mochi.display, mochi.anim_bg_color, mochi.speed_ms)
                mochi.audio.play("switch")
            mochi.busy = False

        threading.Thread(target=do_cmd, daemon=True).start()
        return jsonify(ok=1)

    @app.route("/char")
    def route_char():
        if not mochi.terminal.active:
            return jsonify(ok=1)
        c = request.args.get("c", "")
        if c:
            mochi.terminal.add_char(c[0])
            mochi.audio.play("click")
        return jsonify(ok=1)

    @app.route("/speed")
    def route_speed():
        v = request.args.get("v", "1")
        mochi.anim_speed = max(1, min(3, int(v)))
        return jsonify(ok=1)

    @app.route("/redraw")
    def route_redraw():
        bg = request.args.get("bg", "#da1100")
        mochi.anim_bg_color = hex_to_rgb(bg)
        mochi.draw_bg_color = mochi.anim_bg_color

        if mochi.current_view == VIEW_EYES_NORMAL:
            from faces import draw_normal_eyes
            draw_normal_eyes(mochi.display, mochi.anim_bg_color)
        elif mochi.current_view == VIEW_EYES_SQUISH:
            from faces import draw_squish_eyes
            draw_squish_eyes(mochi.display, mochi.anim_bg_color)
        elif mochi.current_view == VIEW_CODE:
            from faces import draw_code_view
            draw_code_view(mochi.display)
        elif mochi.current_view == VIEW_DRAW:
            mochi.display.fill_content(mochi.draw_bg_color)
            mochi.display.push_frame()
        return jsonify(ok=1)

    @app.route("/canvas")
    def route_canvas():
        on = request.args.get("on", "0") == "1"
        if on:
            mochi.current_view = VIEW_DRAW
            mochi.canvas.activate(mochi.draw_bg_color)
            mochi.audio.play("canvas")
        return jsonify(ok=1)

    @app.route("/draw/clear")
    def route_draw_clear():
        bg = request.args.get("bg", "#aa4818")
        mochi.draw_bg_color = hex_to_rgb(bg)
        mochi.anim_bg_color = mochi.draw_bg_color
        mochi.current_view = VIEW_DRAW
        mochi.terminal.deactivate()
        mochi.canvas.clear(mochi.draw_bg_color)
        return jsonify(ok=1)

    @app.route("/draw/stroke")
    def route_draw_stroke():
        pts_str = request.args.get("pts", "")
        pen_str = request.args.get("pen", "000000")
        if not pts_str or not pen_str:
            return jsonify(ok=1)

        pen_color = hex_to_rgb(pen_str)
        mochi.current_view = VIEW_DRAW

        points = []
        for entry in pts_str.split(";"):
            parts = entry.split(",")
            if len(parts) == 2:
                try:
                    points.append((int(parts[0]), int(parts[1])))
                except ValueError:
                    continue

        if points:
            mochi.canvas.draw_stroke(points, pen_color)
        return jsonify(ok=1)

    @app.route("/backlight")
    def route_backlight():
        on = request.args.get("on", "1") == "1"
        mochi.display.set_backlight(on)
        return jsonify(ok=1)

    @app.route("/state")
    def route_state():
        return jsonify(
            view=mochi.current_view,
            busy=mochi.busy,
            term=mochi.terminal.active,
            bl=mochi.display.backlight_on,
            speed=mochi.anim_speed,
            wifi_mode=mochi.wifi.mode,
            wifi_ip=mochi.wifi.get_ip(),
        )

    # ── WiFi config routes ────────────────────────────────────

    @app.route("/wifi/scan")
    def route_wifi_scan():
        networks = mochi.wifi.scan_networks()
        return jsonify(networks)

    @app.route("/wifi/connect")
    def route_wifi_connect():
        ssid = request.args.get("ssid", "")
        password = request.args.get("password", "")
        if not ssid:
            return jsonify(ok=False, error="SSID required")

        def do_connect():
            success = mochi.wifi.connect_to_wifi(ssid, password)
            if success:
                from faces import draw_wifi_info
                draw_wifi_info(
                    mochi.display, ssid, "****",
                    mochi.wifi.get_ip(), mode="Client"
                )

        # Run in thread since it takes time
        threading.Thread(target=do_connect, daemon=True).start()
        return jsonify(ok=True, ip=mochi.wifi.get_ip())

    @app.route("/wifi/ap")
    def route_wifi_ap():
        def do_ap():
            mochi.wifi.start_ap()
            from faces import draw_wifi_info
            draw_wifi_info(
                mochi.display, mochi.wifi_ssid, mochi.wifi_pass,
                "192.168.4.1", mode="AP"
            )

        threading.Thread(target=do_ap, daemon=True).start()
        return jsonify(ok=True)

    @app.route("/wifi/status")
    def route_wifi_status():
        return jsonify(
            mode=mochi.wifi.mode,
            ip=mochi.wifi.get_ip(),
            ssid=mochi.wifi.client_ssid,
        )

    return app
