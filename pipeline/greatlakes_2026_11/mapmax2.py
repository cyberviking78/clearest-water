"""Keep the full-screen map through a trip to a listing site and back.
- Leaving the page (a listing link opens in another tab, or the app switches away) makes the browser drop its full-screen mode;
  that no longer shrinks the map. It stays filling the window, and the next tap on the map goes back to true full screen.
- If the browser reloads the page on the way back, full-screen mode and the map's position (state, centre, zoom) come back.
  Remembered for this browser tab only (sessionStorage). Exit full screen, Esc or a back gesture on the page still close it.
Idempotent. Usage: mapmax2.py <page.html>"""
import sys
p = sys.argv[1]; h = open(p).read()
if "MAPMAX.away" in h: print("already applied"); sys.exit()
def rep(old, new):
    global h
    assert h.count(old) == 1, (h.count(old), old[:80]); h = h.replace(old, new)
rep('''const MAPMAX={on:false,ph:null,fs:false};''', '''const MAPMAX={on:false,ph:null,fs:false,away:false,armed:false,saved:null};
function mxSS(k,v){try{if(v===undefined)return sessionStorage.getItem(k); sessionStorage.setItem(k,v)}catch(e){return null}}
function mxFS(){const w=document.getElementById("mapwrap"), d=document, fs=w.requestFullscreen||w.webkitRequestFullscreen;
  if(!fs||d.fullscreenElement||d.webkitFullscreenElement)return;
  try{const r=fs.call(w,{navigationUI:"hide"}); if(r&&r.catch)r.catch(()=>{})}catch(e){}}
// after the browser drops full screen (another tab, app switch, reload), the next tap on the map goes back to it
function mxArm(){if(MAPMAX.armed)return; const w=document.getElementById("mapwrap"); MAPMAX.armed=true;
  const f=e=>{if(e.type==="pointerdown"&&e.pointerType!=="mouse")return; if(e.type==="pointerup"&&e.pointerType==="mouse")return;
    w.removeEventListener("pointerdown",f,true); w.removeEventListener("pointerup",f,true); MAPMAX.armed=false;
    if(MAPMAX.on&&!MAPMAX.away)mxFS()};
  w.addEventListener("pointerdown",f,true); w.addEventListener("pointerup",f,true)}''')
# entering: remember it; use the shared helper
rep('''    w.classList.add("max"); d.documentElement.classList.add("mapmax");
    const fs=w.requestFullscreen||w.webkitRequestFullscreen;
    if(fs&&!(d.fullscreenElement||d.webkitFullscreenElement)){try{const r=fs.call(w,{navigationUI:"hide"}); if(r&&r.catch)r.catch(()=>{})}catch(e){}}}''',
'''    w.classList.add("max"); d.documentElement.classList.add("mapmax"); mxSS("secchi-mapmax","1");
    if(navigator.userActivation&&!navigator.userActivation.isActive)mxArm(); else mxFS()}''')
rep('''    w.classList.remove("max","filt","leg"); d.documentElement.classList.remove("mapmax");''',
    '''    w.classList.remove("max","filt","leg"); d.documentElement.classList.remove("mapmax"); mxSS("secchi-mapmax","0");''')
# leaving the page doesn't close full-screen mode
rep('''    if(el===w)MAPMAX.fs=true; else if(MAPMAX.fs){MAPMAX.fs=false; if(MAPMAX.on)mapMaxSet(false)}''',
    '''    if(el===w)MAPMAX.fs=true; else if(MAPMAX.fs){MAPMAX.fs=false; if(MAPMAX.on){if(MAPMAX.away||d.hidden)mxArm(); else mapMaxSet(false)}}''')
rep('''  document.addEventListener("fullscreenchange",fsc);''', '''  // a listing link or an app switch takes the page away: mark it so the browser leaving full screen doesn't shrink the map
  document.getElementById("mapwrap").addEventListener("click",e=>{const a=e.target.closest&&e.target.closest("a[href]");
    if(a&&MAPMAX.on&&(a.target==="_blank"||/^https?:/.test(a.getAttribute("href")||""))){MAPMAX.away=true; setTimeout(()=>{if(!document.hidden)MAPMAX.away=false},2500)}},true);
  document.addEventListener("visibilitychange",()=>{if(document.hidden){if(MAPMAX.on)MAPMAX.away=true}
    else if(MAPMAX.on){setTimeout(()=>{MAPMAX.away=false; if(MAPMAX.on&&!(document.fullscreenElement||document.webkitFullscreenElement))mxArm()},600)}});
  document.addEventListener("fullscreenchange",fsc);''')
# remember the map's position; restore it (and full-screen mode) once after a reload
rep('''function mapMaxCtl(m){if(MAPMAX.ctl)return; MAPMAX.ctl=1; const C=''', '''function mapMaxCtl(m){if(MAPMAX.ctl)return; MAPMAX.ctl=1;
  m.on("moveend",()=>{if(!MAPMAX.restored)return; const c=m.getCenter(); mxSS("secchi-mapview",JSON.stringify({s:MAPV.lastS||"",lat:+c.lat.toFixed(5),lng:+c.lng.toFixed(5),z:m.getZoom()}))});
  if(mxSS("secchi-mapmax")==="1")setTimeout(()=>{if(!MAPMAX.on&&!document.getElementById("mapwrap").hidden)mapMaxSet(true)},0);
  const C=''')
rep('''  MAPV.fitted=true; MAPV.lastS=s;
  geoUpdate();''', '''  MAPV.fitted=true; MAPV.lastS=s;
  try{localStorage.setItem("secchi-st",s||"")}catch(e){}
  // after a reload, put the map back where it was (the page refreshes the map a few times while it loads)
  if(!MAPMAX.restored){MAPMAX.restored=1; let v=null; try{v=JSON.parse(mxSS("secchi-mapview")||"null")}catch(e){} if(v&&isFinite(v.lat))MAPMAX.hold={v,until:Date.now()+3000}}
  const hv=MAPMAX.hold; if(hv&&Date.now()<hv.until&&(hv.v.s||"")===(s||"")){const go=()=>m.setView([hv.v.lat,hv.v.lng],hv.v.z,{animate:false}); go(); setTimeout(go,450)} else MAPMAX.hold=null;   // again once the state zoom animation ends
  geoUpdate();''')
open(p, "w").write(h); print("full-screen map now survives leaving the page")
