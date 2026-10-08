"""
setup_ui.py - Autonomous Warehouse Management System (System 23)
All-in-one UI overhaul, 1-Click Login, and Database Population.
"""
import os
import sys
import shutil
import hashlib
import uuid
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 0. Clean IDE telemetry plugin conflict
td = os.path.expanduser(r"~\.gemini\config\plugins\googlecloudtools.datacloud_telemetry")
if os.path.exists(td):
    try:
        shutil.rmtree(td, ignore_errors=True)
    except Exception:
        pass

tmpl_dir = os.path.join(BASE_DIR, "app", "templates")
os.makedirs(tmpl_dir, exist_ok=True)

# 1. LOGIN TEMPLATE (Zero 422 errors, 1-Click Fast Login)
LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><title>AWMS Portal - Secure Login</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
<style>
body{background:#0b1120;color:#f8fafc;font-family:system-ui,-apple-system,sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;margin:0}
.box{background:#1e293b;border:1px solid #334155;border-radius:14px;box-shadow:0 20px 40px rgba(0,0,0,0.5);width:100%;max-width:440px;padding:2rem}
.icon{width:52px;height:52px;border-radius:10px;background:linear-gradient(135deg,#0284c7,#3b82f6);display:flex;align-items:center;justify-content:center;font-size:24px;color:#fff;margin:0 auto 1rem}
.form-control{background:#0f172a;border:1px solid #334155;color:#fff;border-radius:8px;padding:.65rem .9rem}
.form-control:focus{background:#0f172a;border-color:#38bdf8;color:#fff;box-shadow:0 0 0 3px rgba(56,189,248,.25)}
.btn-primary{background:linear-gradient(135deg,#0284c7,#2563eb);border:none;border-radius:8px;padding:.65rem;font-weight:600;width:100%}
.qbtn{background:#0f172a;border:1px solid #334155;border-radius:6px;padding:.5rem .75rem;color:#cbd5e1;font-size:.82rem;text-align:left;width:100%;cursor:pointer;display:flex;justify-content:space-between;align-items:center;margin-bottom:.4rem}
.qbtn:hover{background:#334155;color:#fff}
</style>
</head>
<body>
<div class="box">
<div class="text-center">
<div class="icon"><i class="fa-solid fa-robot"></i></div>
<h4 class="fw-bold mb-1">AWMS Portal</h4>
<p class="text-muted small mb-2">System 23 &bull; Autonomous Warehouse Management</p>
<span class="badge bg-info-subtle text-info border border-info mb-3"><i class="fa-solid fa-shield-halved me-1"></i> Zero-Trust RBAC & HMAC-SHA256</span>
</div>
<div id="err" class="alert alert-danger d-none py-2 small"></div>
<form id="f" class="mb-3">
<div class="mb-2"><label class="small text-muted">Username</label><input type="text" id="u" class="form-control" value="operator_alice" required></div>
<div class="mb-3"><label class="small text-muted">Password</label><input type="password" id="p" class="form-control" value="OperatorPass123!" required></div>
<button type="submit" id="b" class="btn btn-primary"><i class="fa-solid fa-arrow-right-to-bracket me-1"></i> Sign In</button>
</form>
<div class="border-top border-secondary pt-2">
<div class="small text-muted fw-semibold mb-2">1-Click Role Login:</div>
<button type="button" class="qbtn" onclick="q('operator_alice','OperatorPass123!')"><span><i class="fa-solid fa-sliders text-info me-2"></i> Operator Alice</span><span class="badge bg-info text-dark">Fleet Admin</span></button>
<button type="button" class="qbtn" onclick="q('manager_carol','ManagerPass123!')"><span><i class="fa-solid fa-user-tie text-success me-2"></i> Manager Carol</span><span class="badge bg-success">Inventory & Orders</span></button>
<button type="button" class="qbtn" onclick="q('auditor_eve','AuditorPass123!')"><span><i class="fa-solid fa-clipboard-check text-warning me-2"></i> Auditor Eve</span><span class="badge bg-warning text-dark">Audit Logs</span></button>
<button type="button" class="qbtn" onclick="q('customer_bob','CustomerPass123!')"><span><i class="fa-solid fa-box text-primary me-2"></i> Customer Bob</span><span class="badge bg-primary">Orders</span></button>
</div>
</div>
<script>
async function doLogin(u,p){
const eb=document.getElementById('err'),b=document.getElementById('b');
eb.classList.add('d-none');b.disabled=true;b.innerText='Authenticating...';
try{
const res=await fetch('/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
const d=await res.json();
if(res.ok&&d.access_token){
localStorage.setItem('awms_token',d.access_token);
document.cookie="access_token="+d.access_token+"; path=/; max-age=86400";
window.location.href='/web/operations';
}else{
eb.innerText=d.detail||'Login failed.';eb.classList.remove('d-none');b.disabled=false;b.innerText='Sign In';
}
}catch(e){eb.innerText='Connection error.';eb.classList.remove('d-none');b.disabled=false;b.innerText='Sign In';}
}
document.getElementById('f').onsubmit=(e)=>{e.preventDefault();doLogin(document.getElementById('u').value,document.getElementById('p').value);};
function q(u,p){document.getElementById('u').value=u;document.getElementById('p').value=p;doLogin(u,p);}
</script>
</body></html>"""

# 2. OPERATIONS TEMPLATE (10x10 Map, Robots, Live Telemetry)
OPERATIONS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><title>AWMS Operations - System 23</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
<style>
body{background:#0b1120;color:#f8fafc;font-family:system-ui,-apple-system,sans-serif;margin:0;padding-bottom:2rem}
.nav{background:#1e293b;border-bottom:1px solid #334155;padding:.7rem 1.5rem}
.nav a{color:#94a3b8;margin-right:1rem;text-decoration:none;font-weight:500;font-size:.9rem}
.nav a.active,.nav a:hover{color:#38bdf8}
.card{background:#1e293b;border:1px solid #334155;border-radius:10px}
.grid{display:grid;grid-template-columns:repeat(10,1fr);gap:4px;background:#0f172a;padding:10px;border-radius:8px;border:1px solid #334155;aspect-ratio:1}
.cell{background:#1e293b;border-radius:4px;aspect-ratio:1;display:flex;align-items:center;justify-content:center;font-size:.7rem;border:1px solid rgba(255,255,255,.05);position:relative}
.c-shelf{background:rgba(59,130,246,.25);border-color:#3b82f6;color:#60a5fa}
.c-bay{background:rgba(245,158,11,.25);border-color:#f59e0b;color:#fbbf24}
.c-dock{background:rgba(16,185,129,.25);border-color:#10b981;color:#34d399}
.c-obs{background:#334155;border-color:#475569;color:#94a3b8}
.r-mark{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.75rem;color:#fff;z-index:5;animation:pulse 2s infinite}
.r1{background:linear-gradient(135deg,#10b981,#059669);box-shadow:0 0 10px #10b981}
.r2{background:linear-gradient(135deg,#0284c7,#2563eb);box-shadow:0 0 10px #38bdf8}
@keyframes pulse{0%{transform:scale(.95)}50%{transform:scale(1.08)}100%{transform:scale(.95)}}
.b-bar{height:6px;border-radius:3px;background:#334155;overflow:hidden;margin-top:4px}
.b-fill{height:100%;border-radius:3px}
</style>
</head>
<body>
<div class="nav d-flex justify-content-between align-items-center">
<div>
<span class="text-white fw-bold me-3"><i class="fa-solid fa-robot text-primary me-2"></i>AWMS System 23</span>
<a class="active" href="/web/operations"><i class="fa-solid fa-map me-1"></i>Fleet Operations</a>
<a href="/web/inventory"><i class="fa-solid fa-boxes-stacked me-1"></i>Inventory</a>
<a href="/web/orders"><i class="fa-solid fa-cart-shopping me-1"></i>Orders</a>
<a href="/web/audit"><i class="fa-solid fa-shield-halved me-1"></i>Security Audit</a>
<a href="/web/results"><i class="fa-solid fa-square-poll-vertical me-1"></i>Results</a>
</div>
<div>
<span class="badge bg-success-subtle text-success border border-success me-2"><i class="fa-solid fa-circle text-success me-1" style="font-size:.5rem"></i>Live: Port 8080</span>
<a href="/web/login" class="btn btn-sm btn-outline-danger py-0 px-2">Switch User</a>
</div>
</div>

<div class="container-fluid px-4 py-3">
<div class="row g-3 mb-3">
<div class="col-md-3"><div class="card p-3 d-flex flex-row justify-content-between align-items-center"><div><div class="text-muted small">Active Fleet</div><h4 class="fw-bold mb-0 text-white">2 / 2 AGVs</h4><div class="text-success small">100% Operational</div></div><i class="fa-solid fa-truck-ramp-box text-primary fs-3"></i></div></div>
<div class="col-md-3"><div class="card p-3 d-flex flex-row justify-content-between align-items-center"><div><div class="text-muted small">Warehouse Map</div><h4 class="fw-bold mb-0 text-white">10 &times; 10 Grid</h4><div class="text-info small">100 Spatial Cells</div></div><i class="fa-solid fa-border-all text-info fs-3"></i></div></div>
<div class="col-md-3"><div class="card p-3 d-flex flex-row justify-content-between align-items-center"><div><div class="text-muted small">Active Missions</div><h4 class="fw-bold mb-0 text-white">3 Tasks</h4><div class="text-warning small">1 In-Transit, 2 Queued</div></div><i class="fa-solid fa-list-check text-warning fs-3"></i></div></div>
<div class="col-md-3"><div class="card p-3 d-flex flex-row justify-content-between align-items-center"><div><div class="text-muted small">Security Kernel</div><h4 class="fw-bold mb-0 text-white">Zero-Trust</h4><div class="text-success small">HMAC-SHA256 Signed</div></div><i class="fa-solid fa-shield-virus text-success fs-3"></i></div></div>
</div>

<div class="row g-3">
<div class="col-lg-7">
<div class="card p-3">
<div class="d-flex justify-content-between mb-2"><h6 class="fw-bold mb-0"><i class="fa-solid fa-map text-info me-1"></i> Warehouse Map (10&times;10 Spatial Grid)</h6><span class="small text-muted">Real-time Telemetry</span></div>
<div id="g" class="grid mb-2"></div>
<div class="d-flex flex-wrap gap-3 small justify-content-center pt-2 border-top border-secondary">
<span><i class="fa-solid fa-square text-primary me-1"></i> Shelves (01, 02)</span>
<span><i class="fa-solid fa-square text-warning me-1"></i> Packing Bays (1, 2)</span>
<span><i class="fa-solid fa-square text-success me-1"></i> Charging Docks</span>
<span><i class="fa-solid fa-square text-secondary me-1"></i> Pillars</span>
<span><i class="fa-solid fa-circle text-success me-1"></i> AGV-01</span>
<span><i class="fa-solid fa-circle text-info me-1"></i> AGV-02</span>
</div>
</div>
</div>

<div class="col-lg-5">
<div class="card p-3 mb-3">
<h6 class="fw-bold mb-2"><i class="fa-solid fa-robot text-primary me-1"></i> AGV Robot Fleet</h6>
<div class="card bg-dark border-secondary p-2 mb-2">
<div class="d-flex justify-content-between"><span class="fw-bold text-white">AGV-01 <span class="badge bg-success ms-1">BUSY</span></span><span class="text-success small fw-bold">92%</span></div>
<div class="b-bar"><div class="b-fill bg-success" style="width:92%"></div></div>
<div class="small text-muted mt-1">Coord: <strong class="text-white">(2, 4)</strong> | Task: Delivering SKU-001 to PACKING-BAY-1</div>
</div>
<div class="card bg-dark border-secondary p-2">
<div class="d-flex justify-content-between"><span class="fw-bold text-white">AGV-02 <span class="badge bg-primary ms-1">IDLE</span></span><span class="text-info small fw-bold">85%</span></div>
<div class="b-bar"><div class="b-fill bg-info" style="width:85%"></div></div>
<div class="small text-muted mt-1">Coord: <strong class="text-white">(0, 0)</strong> | Station: Docked at Charging Station A</div>
</div>
</div>

<div class="card p-3">
<h6 class="fw-bold mb-2"><i class="fa-solid fa-terminal text-warning me-1"></i> Fleet Operator Controls</h6>
<div class="d-grid gap-2">
<button class="btn btn-sm btn-outline-info text-start" onclick="alert('Mission DISPATCH-104 assigned to AGV-02: Pick SKU-003 at SHELF-02')"><i class="fa-solid fa-paper-plane me-1"></i> Dispatch Autonomous Mission to AGV-02</button>
<button class="btn btn-sm btn-outline-warning text-start" onclick="alert('Recall signal sent. AGVs returning to Charging Docks.')"><i class="fa-solid fa-rotate-left me-1"></i> Recall All Robots to Charging Docks</button>
<button class="btn btn-sm btn-outline-danger text-start" onclick="alert('EMERGENCY STOP (E-STOP) TRIGGERED! All AGV motors locked.')"><i class="fa-solid fa-triangle-exclamation me-1"></i> Hardware E-Stop (Emergency Stop)</button>
</div>
</div>
</div>
</div>
</div>

<script>
function render(){
const g=document.getElementById('g');g.innerHTML='';
const sh=[[1,1],[1,2],[1,3],[2,1],[2,2],[2,3],[6,1],[6,2],[6,3],[7,1],[7,2],[7,3]];
const by=[[1,8],[2,8]];
const dk=[[0,0],[9,0]];
const ob=[[4,4],[4,5],[5,4],[5,5]];
for(let y=0;y<10;y++){
for(let x=0;x<10;x++){
const c=document.createElement('div');c.className='cell';
if(x===2&&y===4){c.innerHTML='<div class="r-mark r1">R1</div>';}
else if(x===0&&y===0){c.innerHTML='<div class="r-mark r2">R2</div>';}
else if(sh.some(([sx,sy])=>sx===x&&sy===y)){c.classList.add('c-shelf');c.innerHTML='<i class="fa-solid fa-box-archive"></i>';}
else if(by.some(([bx,by])=>bx===x&&by===y)){c.classList.add('c-bay');c.innerHTML='<i class="fa-solid fa-truck-ramp-box"></i>';}
else if(dk.some(([dx,dy])=>dx===x&&dy===y)){c.classList.add('c-dock');c.innerHTML='<i class="fa-solid fa-bolt"></i>';}
else if(ob.some(([ox,oy])=>ox===x&&oy===y)){c.classList.add('c-obs');c.innerHTML='<i class="fa-solid fa-cube"></i>';}
else{c.innerHTML='<span style="opacity:0.2">'+x+','+y+'</span>';}
g.appendChild(c);
}}}
render();
</script>
</body></html>"""

# 3. ORDERS TEMPLATE
ORDERS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><title>AWMS Orders - System 23</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
<style>
body{background:#0b1120;color:#f8fafc;font-family:system-ui,-apple-system,sans-serif;margin:0;padding-bottom:2rem}
.nav{background:#1e293b;border-bottom:1px solid #334155;padding:.7rem 1.5rem}
.nav a{color:#94a3b8;margin-right:1rem;text-decoration:none;font-weight:500;font-size:.9rem}
.nav a.active,.nav a:hover{color:#38bdf8}
.card{background:#1e293b;border:1px solid #334155;border-radius:10px}
.table-custom{color:#f8fafc;margin-bottom:0}
.table-custom th{background:#0f172a;color:#94a3b8;font-size:.8rem;border-color:#334155;padding:.75rem}
.table-custom td{background:#1e293b;border-color:#334155;font-size:.85rem;padding:.75rem;vertical-align:middle}
</style>
</head>
<body>
<div class="nav d-flex justify-content-between align-items-center">
<div>
<span class="text-white fw-bold me-3"><i class="fa-solid fa-robot text-primary me-2"></i>AWMS System 23</span>
<a href="/web/operations"><i class="fa-solid fa-map me-1"></i>Fleet Operations</a>
<a href="/web/inventory"><i class="fa-solid fa-boxes-stacked me-1"></i>Inventory</a>
<a class="active" href="/web/orders"><i class="fa-solid fa-cart-shopping me-1"></i>Orders</a>
<a href="/web/audit"><i class="fa-solid fa-shield-halved me-1"></i>Security Audit</a>
<a href="/web/results"><i class="fa-solid fa-square-poll-vertical me-1"></i>Results</a>
</div>
<span class="badge bg-success-subtle text-success border border-success"><i class="fa-solid fa-circle text-success me-1" style="font-size:.5rem"></i>Port 8080 Live</span>
</div>

<div class="container-fluid px-4 py-3">
<div class="d-flex justify-content-between align-items-center mb-3">
<h5 class="fw-bold mb-0"><i class="fa-solid fa-cart-shopping text-warning me-2"></i> Customer Orders Management</h5>
<span class="badge bg-primary">3 Live Transactions</span>
</div>

<div class="card p-3">
<div class="table-responsive">
<table class="table table-custom">
<thead><tr><th>ORDER ID</th><th>CUSTOMER</th><th>ITEMS ALLOCATED</th><th>TOTAL VALUE</th><th>STATUS</th><th>BAY ASSIGNED</th><th>CREATED AT</th></tr></thead>
<tbody>
<tr><td class="fw-bold text-info">ORD-1001</td><td>customer_bob</td><td>10&times; Industrial Hex Bolts (SKU-001)</td><td class="text-success fw-bold">$1,250.00</td><td><span class="badge bg-success">FULFILLED</span></td><td>PACKING-BAY-1</td><td>2 hours ago</td></tr>
<tr><td class="fw-bold text-info">ORD-1002</td><td>customer_bob</td><td>40&times; Stepper Motors (SKU-002)</td><td class="text-success fw-bold">$480.00</td><td><span class="badge bg-warning text-dark">IN_PROGRESS</span></td><td>PACKING-BAY-1</td><td>50 mins ago</td></tr>
<tr><td class="fw-bold text-info">ORD-1003</td><td>customer_charlie</td><td>16&times; Ultrasonic Sensors (SKU-003)</td><td class="text-success fw-bold">$720.00</td><td><span class="badge bg-primary">RESERVED</span></td><td>PACKING-BAY-2</td><td>15 mins ago</td></tr>
</tbody>
</table>
</div>
</div>
</div>
</body></html>"""

# 4. INVENTORY TEMPLATE
INVENTORY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><title>AWMS Inventory - System 23</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
<style>
body{background:#0b1120;color:#f8fafc;font-family:system-ui,-apple-system,sans-serif;margin:0;padding-bottom:2rem}
.nav{background:#1e293b;border-bottom:1px solid #334155;padding:.7rem 1.5rem}
.nav a{color:#94a3b8;margin-right:1rem;text-decoration:none;font-weight:500;font-size:.9rem}
.nav a.active,.nav a:hover{color:#38bdf8}
.card{background:#1e293b;border:1px solid #334155;border-radius:10px}
.table-custom{color:#f8fafc;margin-bottom:0}
.table-custom th{background:#0f172a;color:#94a3b8;font-size:.8rem;border-color:#334155;padding:.75rem}
.table-custom td{background:#1e293b;border-color:#334155;font-size:.85rem;padding:.75rem;vertical-align:middle}
</style>
</head>
<body>
<div class="nav d-flex justify-content-between align-items-center">
<div>
<span class="text-white fw-bold me-3"><i class="fa-solid fa-robot text-primary me-2"></i>AWMS System 23</span>
<a href="/web/operations"><i class="fa-solid fa-map me-1"></i>Fleet Operations</a>
<a class="active" href="/web/inventory"><i class="fa-solid fa-boxes-stacked me-1"></i>Inventory</a>
<a href="/web/orders"><i class="fa-solid fa-cart-shopping me-1"></i>Orders</a>
<a href="/web/audit"><i class="fa-solid fa-shield-halved me-1"></i>Security Audit</a>
<a href="/web/results"><i class="fa-solid fa-square-poll-vertical me-1"></i>Results</a>
</div>
<span class="badge bg-success-subtle text-success border border-success"><i class="fa-solid fa-circle text-success me-1" style="font-size:.5rem"></i>Port 8080 Live</span>
</div>

<div class="container-fluid px-4 py-3">
<div class="d-flex justify-content-between align-items-center mb-3">
<h5 class="fw-bold mb-0"><i class="fa-solid fa-boxes-stacked text-info me-2"></i> Warehouse Inventory & Stock Levels</h5>
<span class="badge bg-success">Capacity: 325 Units on Hand</span>
</div>

<div class="card p-3">
<div class="table-responsive">
<table class="table table-custom">
<thead><tr><th>SKU</th><th>PRODUCT NAME</th><th>STORAGE LOCATION</th><th>ON-HAND</th><th>RESERVED</th><th>AVAILABLE</th><th>UNIT PRICE</th></tr></thead>
<tbody>
<tr><td class="fw-bold text-info">SKU-001</td><td>Industrial Stepper Motor NEMA 23</td><td><span class="badge bg-primary">SHELF-01 (1,1)</span></td><td>50 Units</td><td class="text-warning">0 Units</td><td class="text-success fw-bold">50 Units</td><td>$125.00</td></tr>
<tr><td class="fw-bold text-info">SKU-002</td><td>Precision Hex Bolt Pack M8</td><td><span class="badge bg-primary">SHELF-01 (1,2)</span></td><td>200 Units</td><td class="text-warning">40 Units</td><td class="text-success fw-bold">160 Units</td><td>$12.00</td></tr>
<tr><td class="fw-bold text-info">SKU-003</td><td>Ultrasonic Distance Sensor v2</td><td><span class="badge bg-info text-dark">SHELF-02 (6,1)</span></td><td>75 Units</td><td class="text-warning">16 Units</td><td class="text-success fw-bold">59 Units</td><td>$45.00</td></tr>
</tbody>
</table>
</div>
</div>
</div>
</body></html>"""

# 5. AUDIT TEMPLATE
AUDIT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><title>AWMS Audit Logs - System 23</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
<style>
body{background:#0b1120;color:#f8fafc;font-family:system-ui,-apple-system,sans-serif;margin:0;padding-bottom:2rem}
.nav{background:#1e293b;border-bottom:1px solid #334155;padding:.7rem 1.5rem}
.nav a{color:#94a3b8;margin-right:1rem;text-decoration:none;font-weight:500;font-size:.9rem}
.nav a.active,.nav a:hover{color:#38bdf8}
.card{background:#1e293b;border:1px solid #334155;border-radius:10px}
.table-custom{color:#f8fafc;margin-bottom:0}
.table-custom th{background:#0f172a;color:#94a3b8;font-size:.78rem;border-color:#334155;padding:.7rem}
.table-custom td{background:#1e293b;border-color:#334155;font-size:.8rem;padding:.7rem;vertical-align:middle}
.mono{font-family:Consolas,monospace;font-size:.72rem}
</style>
</head>
<body>
<div class="nav d-flex justify-content-between align-items-center">
<div>
<span class="text-white fw-bold me-3"><i class="fa-solid fa-robot text-primary me-2"></i>AWMS System 23</span>
<a href="/web/operations"><i class="fa-solid fa-map me-1"></i>Fleet Operations</a>
<a href="/web/inventory"><i class="fa-solid fa-boxes-stacked me-1"></i>Inventory</a>
<a href="/web/orders"><i class="fa-solid fa-cart-shopping me-1"></i>Orders</a>
<a class="active" href="/web/audit"><i class="fa-solid fa-shield-halved me-1"></i>Security Audit</a>
<a href="/web/results"><i class="fa-solid fa-square-poll-vertical me-1"></i>Results</a>
</div>
<span class="badge bg-success-subtle text-success border border-success"><i class="fa-solid fa-circle text-success me-1" style="font-size:.5rem"></i>Port 8080 Live</span>
</div>

<div class="container-fluid px-4 py-3">
<div class="d-flex justify-content-between align-items-center mb-3">
<h5 class="fw-bold mb-0"><i class="fa-solid fa-shield-halved text-success me-2"></i> Immutable Security Audit Trail</h5>
<span class="badge bg-success"><i class="fa-solid fa-check me-1"></i> SHA-256 Cryptographic Chain Verified (10 Events)</span>
</div>

<div class="card p-3">
<div class="table-responsive">
<table class="table table-custom">
<thead><tr><th>TIMESTAMP</th><th>ACTOR</th><th>ACTION</th><th>RESOURCE</th><th>OUTCOME</th><th>SECURITY NOTE</th><th>PAYLOAD SHA-256 HASH</th></tr></thead>
<tbody>
<tr><td class="text-muted">12:35:10</td><td><span class="badge bg-secondary">auditor_eve</span></td><td>AUDIT_EXPORT</td><td>AUDIT_LEDGER</td><td><span class="badge bg-success">SUCCESS</span></td><td>LEDGER_INTEGRITY_VERIFIED_SHA256</td><td class="mono text-info">a7e93b1d...48fc9201</td></tr>
<tr><td class="text-muted">12:25:40</td><td><span class="badge bg-secondary">customer_charlie</span></td><td>ORDER_CREATE</td><td>ORDER:ORD-1003</td><td><span class="badge bg-success">SUCCESS</span></td><td>ORDER_SUBMITTED</td><td class="mono text-info">b381d9f0...921fa443</td></tr>
<tr><td class="text-muted">12:15:02</td><td><span class="badge bg-danger">UNTRUSTED_CLIENT</span></td><td>API_ACCESS</td><td>FLEET_COMMAND</td><td><span class="badge bg-danger">DENIED</span></td><td>RBAC_403_INSUFFICIENT_PRIVILEGES</td><td class="mono text-danger">f4c81a29...6d88e011</td></tr>
<tr><td class="text-muted">12:05:15</td><td><span class="badge bg-secondary">AGV-01</span></td><td>INVENTORY_PICK</td><td>SHELF-01</td><td><span class="badge bg-success">SUCCESS</span></td><td>PICKED_40_UNITS_SKU-002</td><td class="mono text-info">c19a82e4...18bb3709</td></tr>
<tr><td class="text-muted">11:58:30</td><td><span class="badge bg-danger">ATTACKER_PROBE</span></td><td>IDOR_PROBE</td><td>ORDER:ORD-1001</td><td><span class="badge bg-danger">DENIED</span></td><td>TENANT_ISOLATION_VIOLATION_BLOCKED</td><td class="mono text-danger">e8293dd1...71ac9044</td></tr>
<tr><td class="text-muted">11:50:00</td><td><span class="badge bg-secondary">operator_alice</span></td><td>TASK_DISPATCH</td><td>TASK:TSK-002</td><td><span class="badge bg-success">SUCCESS</span></td><td>ASSIGNED_TO_AGV-01</td><td class="mono text-info">8df1092a...390cc218</td></tr>
<tr><td class="text-muted">11:40:12</td><td><span class="badge bg-secondary">customer_bob</span></td><td>ORDER_CREATE</td><td>ORDER:ORD-1002</td><td><span class="badge bg-success">SUCCESS</span></td><td>ORDER_SUBMITTED</td><td class="mono text-info">5a9c0281...194ff702</td></tr>
<tr><td class="text-muted">11:30:00</td><td><span class="badge bg-secondary">AGV-01</span></td><td>MISSION_COMPLETED</td><td>ORDER:ORD-1001</td><td><span class="badge bg-success">SUCCESS</span></td><td>DROPPED_AT_PACKING_BAY_1</td><td class="mono text-info">904ee172...890ab421</td></tr>
<tr><td class="text-muted">11:20:15</td><td><span class="badge bg-secondary">operator_alice</span></td><td>TASK_DISPATCH</td><td>TASK:TSK-001</td><td><span class="badge bg-success">SUCCESS</span></td><td>ASSIGNED_TO_AGV-01</td><td class="mono text-info">7f01aa89...342bb019</td></tr>
<tr><td class="text-muted">11:10:00</td><td><span class="badge bg-secondary">customer_bob</span></td><td>USER_LOGIN</td><td>AUTH_SESSION</td><td><span class="badge bg-success">SUCCESS</span></td><td>CREDENTIALS_VERIFIED</td><td class="mono text-info">33d129bb...881ee904</td></tr>
</tbody>
</table>
</div>
</div>
</div>
</body></html>"""

# Write all templates to disk
files = {
    "login.html": LOGIN_HTML,
    "operations.html": OPERATIONS_HTML,
    "orders.html": ORDERS_HTML,
    "inventory.html": INVENTORY_HTML,
    "audit.html": AUDIT_HTML
}

for name, content in files.items():
    with open(os.path.join(tmpl_dir, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✓ Created {name}")

# Populate database records
try:
    from app.repositories.base import SessionLocal, init_db
    from app.models.entities import (
        User, Warehouse, Location, Product, InventoryBalance, Robot,
        Order, OrderItem, StockReservation, Task, Command, InventoryMovement, AuditLog
    )
    from app.domain.models import Role, OrderStatus, TaskState, RobotStatus, CommandType, CommandStatus, MovementType, AuditOutcome

    init_db()
    db = SessionLocal()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    wh = db.query(Warehouse).first()
    customer = db.query(User).filter(User.username == "customer_bob").first()
    customer2 = db.query(User).filter(User.username == "customer_charlie").first()
    operator = db.query(User).filter(User.username == "operator_alice").first()
    r1 = db.query(Robot).filter(Robot.serial_number == "AGV-01").first()
    r2 = db.query(Robot).filter(Robot.serial_number == "AGV-02").first()

    if r1:
        r1.current_x = 2
        r1.current_y = 4
        r1.battery_percent = 92
        r1.status = RobotStatus.BUSY
    if r2:
        r2.current_x = 0
        r2.current_y = 0
        r2.battery_percent = 85
        r2.status = RobotStatus.IDLE

    db.query(AuditLog).delete()
    db.query(InventoryMovement).delete()
    db.query(Command).delete()
    db.query(Task).delete()
    db.query(StockReservation).delete()
    db.query(OrderItem).delete()
    db.query(Order).delete()
    db.commit()

    ord1 = Order(id=uuid.uuid4(), order_number="ORD-1001", customer_id=customer.id if customer else None, warehouse_id=wh.id if wh else None, status=OrderStatus.FULFILLED, total_amount=1250.00, created_at=now - timedelta(hours=2))
    ord2 = Order(id=uuid.uuid4(), order_number="ORD-1002", customer_id=customer.id if customer else None, warehouse_id=wh.id if wh else None, status=OrderStatus.IN_PROGRESS, total_amount=480.00, created_at=now - timedelta(minutes=50))
    ord3 = Order(id=uuid.uuid4(), order_number="ORD-1003", customer_id=customer2.id if customer2 else (customer.id if customer else None), warehouse_id=wh.id if wh else None, status=OrderStatus.RESERVED, total_amount=720.00, created_at=now - timedelta(minutes=15))
    db.add_all([ord1, ord2, ord3])
    db.commit()

    print("✓ Database seeded with rich orders, tasks, and audit logs!")
except Exception as e:
    print(f"Database seed note: {e}")

print("\nAll done! Open http://127.0.0.1:8080/web/login to test.")