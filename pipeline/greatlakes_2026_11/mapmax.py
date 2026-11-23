"""Full-screen map: a "Full screen" button (bar above the map and a button on the map) expands the map to fill the screen.
Uses the browser's full-screen mode where allowed (GitHub copy, offline file, Android tablets) and otherwise fills the window.
Filters and the legend open as panels over the map. Esc, the Exit button or the browser's back/exit gesture closes it.
Idempotent. Usage: mapmax.py <page.html>"""
import sys
p = sys.argv[1]; h = open(p).read()
if 'id="mapmax"' in h: print("already applied"); sys.exit()
def rep(old, new):
    global h
    assert h.count(old) == 1, (h.count(old), old[:80]); h = h.replace(old, new)
rep('''<div id="mapwrap" data-mode="map" hidden>
  <div class="mapbar">''', '''<div id="mapwrap" data-mode="map" hidden>
  <div class="mxbar"><button id="mxf" class="mxbtn" type="button" aria-expanded="false">Filters</button><button id="mxl" class="mxbtn" type="button" aria-expanded="false">Legend &amp; layers</button><span class="mxsp"></span><button id="mxx" class="mxbtn" type="button">✕ Exit full screen</button></div>
  <div id="mxfilt" class="mxpanel"></div>
  <div class="mxleg">
  <div class="mapbar"><button id="mapmax" class="mxbtn" type="button" aria-pressed="false">⤢ Full screen</button>''')
rep('''<span class="lg"><i class="cl"></i>City limits</span></div>
  <div id="leafmap"''', '''<span class="lg"><i class="cl"></i>City limits</span></div>
  </div>
  <div id="leafmap"''')
rep('Green ring: water listing within 1 mile of a major bike trail', 'Blue ring: water listing within 1 mile of a major bike trail')
CSS = '''
.mxbtn{font:inherit;font-size:13px;line-height:1.2;padding:6px 12px;border:1px solid var(--rule);border-radius:8px;background:var(--surface);color:var(--ink);cursor:pointer}
.mxbtn:hover{border-color:var(--muted)} .mxbtn[aria-expanded="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
#mapmax{font-weight:600}
.mxbar,#mxfilt{display:none}
.mxleg{display:grid;gap:10px}
#mapwrap.max{position:fixed;inset:0;z-index:1000;margin:0;gap:0;background:var(--bg);display:flex;flex-direction:column;
  padding:env(safe-area-inset-top,0px) env(safe-area-inset-right,0px) env(safe-area-inset-bottom,0px) env(safe-area-inset-left,0px)}
#mapwrap.max .mxbar{display:flex;align-items:center;gap:8px;padding:8px 10px;border-bottom:1px solid var(--rule);flex:none}
#mapwrap.max .mxsp{flex:1}
#mapwrap.max #mapmax{display:none}
#mapwrap.max .mxleg,#mapwrap.max #mxfilt{display:none;position:absolute;left:8px;right:8px;top:var(--mxtop,52px);z-index:1002;max-height:min(70vh,560px);overflow:auto;
  background:var(--bg);border:1px solid var(--rule);border-radius:10px;padding:12px 14px;box-shadow:0 8px 28px rgba(0,0,0,.28)}
@media (min-width:900px){#mapwrap.max .mxleg,#mapwrap.max #mxfilt{right:auto;width:560px}}
#mapwrap.max.leg .mxleg,#mapwrap.max.filt #mxfilt{display:grid}
#mxfilt .controls{position:static;border:0;padding:0;background:none}
#mapwrap.max #leafmap{flex:1 1 auto;height:auto;min-height:0;border:0;border-radius:0}
html.mapmax,html.mapmax body{overflow:hidden}
.leaflet-control.mxctl a{font-size:17px;font-weight:700;line-height:30px;text-align:center;text-decoration:none;cursor:pointer}
'''
i = h.find("</style>"); h = h[:i] + CSS + h[i:]
JS = '''
// full-screen map
const MAPMAX={on:false,ph:null,fs:false};
function mxPanel(which){const w=document.getElementById("mapwrap");
  ["filt","leg"].forEach(k=>w.classList.toggle(k,which===k&&!w.classList.contains(k)));
  document.getElementById("mxf").setAttribute("aria-expanded",w.classList.contains("filt"));
  document.getElementById("mxl").setAttribute("aria-expanded",w.classList.contains("leg"));
  w.style.setProperty("--mxtop",(w.querySelector(".mxbar").offsetHeight+6)+"px")}
function mapMaxSet(on){const w=document.getElementById("mapwrap"), c=document.querySelector(".controls"), d=document;
  if(on===MAPMAX.on)return; MAPMAX.on=on;
  if(on){MAPMAX.ph=d.createComment("controls"); c.parentNode.insertBefore(MAPMAX.ph,c); document.getElementById("mxfilt").appendChild(c);
    w.classList.add("max"); d.documentElement.classList.add("mapmax");
    const fs=w.requestFullscreen||w.webkitRequestFullscreen;
    if(fs&&!(d.fullscreenElement||d.webkitFullscreenElement)){try{const r=fs.call(w,{navigationUI:"hide"}); if(r&&r.catch)r.catch(()=>{})}catch(e){}}}
  else{if(MAPMAX.ph){MAPMAX.ph.parentNode.insertBefore(c,MAPMAX.ph); MAPMAX.ph.remove(); MAPMAX.ph=null}
    w.classList.remove("max","filt","leg"); d.documentElement.classList.remove("mapmax");
    if(d.fullscreenElement||d.webkitFullscreenElement){try{const r=(d.exitFullscreen||d.webkitExitFullscreen).call(d); if(r&&r.catch)r.catch(()=>{})}catch(e){}}
    w.scrollIntoView({block:"start"})}
  document.getElementById("mapmax").setAttribute("aria-pressed",on);
  document.querySelectorAll(".mxctl a").forEach(a=>{a.textContent=on?"✕":"⤢";a.title=on?"Exit full screen":"Full screen map"});
  [50,300,700].forEach(t=>setTimeout(()=>MAPV.map&&MAPV.map.invalidateSize(),t))}
function mapMaxInit(){
  document.getElementById("mapmax").onclick=()=>mapMaxSet(true);
  document.getElementById("mxx").onclick=()=>mapMaxSet(false);
  document.getElementById("mxf").onclick=()=>mxPanel("filt");
  document.getElementById("mxl").onclick=()=>mxPanel("leg");
  const fsc=()=>{const d=document, w=document.getElementById("mapwrap"), el=d.fullscreenElement||d.webkitFullscreenElement;
    if(el===w)MAPMAX.fs=true; else if(MAPMAX.fs){MAPMAX.fs=false; if(MAPMAX.on)mapMaxSet(false)}
    [50,300].forEach(t=>setTimeout(()=>MAPV.map&&MAPV.map.invalidateSize(),t))};
  document.addEventListener("fullscreenchange",fsc); document.addEventListener("webkitfullscreenchange",fsc);
  document.addEventListener("keydown",e=>{if(e.key==="Escape"&&MAPMAX.on){const w=document.getElementById("mapwrap");
    if(w.classList.contains("filt")||w.classList.contains("leg"))mxPanel(null); else mapMaxSet(false)}});
  window.addEventListener("resize",()=>{if(MAPMAX.on&&MAPV.map)MAPV.map.invalidateSize()});
  // the map's tab buttons hide the map; leave full screen first
  document.querySelectorAll('[id^="t-"]').forEach(b=>b.addEventListener("click",()=>{if(MAPMAX.on)mapMaxSet(false)},true))}
function mapMaxCtl(m){if(MAPMAX.ctl)return; MAPMAX.ctl=1; const C=L.Control.extend({options:{position:"topleft"},onAdd(){const d=L.DomUtil.create("div","leaflet-bar leaflet-control mxctl"),a=L.DomUtil.create("a","",d);
  a.href="#";a.role="button";a.textContent="⤢";a.title="Full screen map";L.DomEvent.disableClickPropagation(d);
  L.DomEvent.on(a,"click",e=>{L.DomEvent.preventDefault(e);mapMaxSet(!MAPMAX.on)});return d}}); new C().addTo(m)}
'''
rep('''function geoOrder(){''', JS + '''function geoOrder(){''')
rep('''  setTimeout(()=>m.invalidateSize(),0);''', '''  setTimeout(()=>m.invalidateSize(),0); mapMaxCtl(m);''')
# wire the buttons once the page has loaded
i = h.rfind("</script>"); h = h[:i] + "\ntry{mapMaxInit()}catch(e){}\n" + h[i:]
open(p, "w").write(h); print("full-screen map added")
