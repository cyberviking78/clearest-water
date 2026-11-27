"""Straight line from a listing to its spring (Nov 26, 2026).
Google Maps can pin two points only as a driving or walking route, which is no use for a spring reached by water. Every listing
tied to a spring now has a "Straight line to the spring" link (Springs tab listings, Springheads tab listings, and their map
popups). It opens the site's own map, switches it to satellite (on the GitHub site; the saved default basemap is left alone),
opens it full screen, and draws a straight dashed line from the listing's map point (Redfin's point for the address) to the spring's vent, with both
ends labelled and the straight-line distance at the middle. "Back to the list" (or Esc) removes it and returns to the tab and spot the link was on.
The link is also a web address (#pair=vent lat,lon,listing lat,lon), so it can be opened in a new tab or sent to someone.
Which vent: springheads use their inventory point; springs on the Springs tab use the same point as their coordinates link
(gmSpring: the Florida Springs Institute survey vent when it matches by name within 300 m, otherwise the spring's own point).
Replaces the "vent and listing on Google Maps" walking-route link from coords_links.py.
lItem and renderSprings are rewritten by patch_page.py on every refresh, so their edits are made to patch_page.py's RENDER too.
Idempotent. Usage: spring_line.py page.html [patch_page.py]"""
import os, sys
page = sys.argv[1]; pp = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "patch_page.py")
h = open(page).read()
def rep(old, new, t):
    if new in t: return t
    assert t.count(old) == 1, (t.count(old), old[:120]); return t.replace(old, new)

# ---- Springs tab listings (patch_page.py RENDER + page) ----
def render_edits(t):
    t = rep("function lItem(x){", "function lItem(x,g){", t)
    t = rep('${wtLine(path)}</li>`}', '${wtLine(path)}${g?springPair(g,x):""}</li>`}', t)
    a = t.index("function renderSprings(){"); b = t.index("\nfunction", a + 10)
    body = t[a:b]
    if 'L.map(x=>lItem(x,g))' not in body:
        assert body.count('L.map(lItem)') == 1; body = body.replace('L.map(lItem)', 'L.map(x=>lItem(x,g))')
    return t[:a] + body + t[b:]
h = render_edits(h)
P = open(pp).read(); P = render_edits(P); open(pp, "w").write(P)

# ---- helpers ----
JS = r'''/* ---------- straight line from a listing to its spring (pipeline/fixes/spring_line.py) ---------- */
function springLL(r){let ll=r[18]||[(r[12][1]+r[12][3])/2,(r[12][0]+r[12][2])/2];
  if(r[16]==="FL"&&typeof fsiRow==="function"){const f=fsiRow(r); if(f&&fsiTok(f[2])===fsiTok(r[1])){const cl=Math.cos(ll[0]*Math.PI/180);
    if(Math.hypot((f[0]-ll[0])*111200,(f[1]-ll[1])*111200*cl)<=300)ll=[f[0],f[1]]}}
  return ll}
let SGW=null;
function springByGW(g,wi){if(!SGW){SGW={};FSD.springs.forEach(r=>SGW[r[17]+"|"+r[0]]=r);(typeof FSB!=="undefined"?FSB:[]).forEach(r=>SGW[r[17]+"|"+r[0]]=r)}return SGW[g+"|"+wi]}
function springPair(g,x){const r=springByGW(g,x[0]); if(!r||x[16]==null)return ""; const v=springLL(r);
  return `<div class="pair-l">${pairLink(v[0],v[1],x[16],x[17],r[1],x[8])}</div>`}
function pairDist(a,b,c,d){const R=6371008.8,p=Math.PI/180,dl=(c-a)*p,dn=(d-b)*p,s=Math.sin(dl/2)**2+Math.cos(a*p)*Math.cos(c*p)*Math.sin(dn/2)**2;return 2*R*Math.asin(Math.sqrt(s))}
function pairFmt(m){const ft=m*3.28084; return ft<1000?`${Math.round(ft).toLocaleString()} ft (${Math.round(m)} m)`:`${(m/1609.344).toFixed(m<16093?2:1)} mi (${m<1000?Math.round(m)+" m":(m/1000).toFixed(2)+" km"})`}
function pairLink(vlat,vlon,lat,lon,vname,lname){if(vlat==null||lat==null)return "";
  return `<a class="pair" href="#pair=${gmF(vlat)},${gmF(vlon)},${gmF(lat)},${gmF(lon)}" data-v="${esc(vname||"")}" data-l="${esc(lname||"")}" onclick="return pairClick(this)" title="Show the listing and the spring on the map, joined by a straight line">Straight line to the spring · ${pairFmt(pairDist(vlat,vlon,lat,lon))}</a>`}
function pairClick(a){const p=a.getAttribute("href").slice(6).split(",").map(Number), hr=a.getAttribute("href");
  // where the link sat, so "Back to the list" can put it back in the same spot (open lists, same height on screen)
  MAPV.pairFrom={href:hr,k:[...document.querySelectorAll("#list a.pair")].filter(x=>x.getAttribute("href")===hr).indexOf(a),top:a.getBoundingClientRect().top,
    open:[...document.querySelectorAll("#list details")].map((d,i)=>d.open?i:-1).filter(i=>i>=0),lim:typeof LIMIT!=="undefined"?LIMIT:null};
  pairShow(p[0],p[1],p[2],p[3],a.dataset.v,a.dataset.l); return false}
function pairClear(){const m=MAPV.map; if(!m)return; if(MAPV.pair){m.removeLayer(MAPV.pair);MAPV.pair=null} if(MAPV.pairCtl){m.removeControl(MAPV.pairCtl);MAPV.pairCtl=null}
  if(/^#pair=/.test(location.hash))try{history.replaceState(null,"",location.pathname+location.search+(MAPV.pairBack?"":"#map"))}catch(e){}
  const b=MAPV.pairBack; MAPV.pairBack=null;
  if(b){if(b.max&&typeof MAPMAX!=="undefined"&&MAPMAX.on)mapMaxSet(false); setMode(b.mode); const f=b.from;
    if(f&&f.lim&&typeof LIMIT!=="undefined"&&f.lim>LIMIT){LIMIT=f.lim; render()}
    let live=true; const stop=()=>{live=false}; ["wheel","touchstart","keydown","mousedown"].forEach(e=>window.addEventListener(e,stop,{once:true,passive:true}));
    const put=()=>{if(!live)return;
      if(f){const D=document.querySelectorAll("#list details"); f.open.forEach(i=>{if(D[i])D[i].open=true});
        const a=[...document.querySelectorAll("#list a.pair")].filter(x=>x.getAttribute("href")===f.href)[Math.max(0,f.k)];
        if(a){const d=a.closest("details"); if(d)d.open=true; window.scrollBy(0,a.getBoundingClientRect().top-f.top); return}}
      window.scrollTo(0,b.y)};
    requestAnimationFrame(put); [200,600,1200].forEach(t=>setTimeout(put,t))}}
function pairShow(vlat,vlon,lat,lon,vname,lname){
  if(mode!=="map"){MAPV.pairBack={mode,y:window.scrollY,max:false,from:MAPV.pairFrom}; setMode("map")}
  MAPV.pairFrom=null;
  let tries=0;
  const go=()=>{const m=MAPV.map; tries++;
    if(!m||(!MAPV.tilesOn&&tries<12)){if(tries<60)return setTimeout(go,150); if(!m)return}   // wait for the map (and, on the site, its basemaps)
    m.closePopup();
    const lab=[...document.querySelectorAll(".leaflet-control-layers-base label")].find(l=>l.textContent.trim()==="Satellite");
    if(lab){const i=lab.querySelector("input"); if(i&&!i.checked){let prev=null; try{prev=localStorage.getItem("cw-base")}catch(e){}
      i.click(); const back=()=>{try{prev==null?localStorage.removeItem("cw-base"):localStorage.setItem("cw-base",prev)}catch(e){}}; back(); setTimeout(back,400); setTimeout(back,1500)}}
    if(!m.getPane("pairPane")){const p=m.createPane("pairPane");p.style.zIndex=640; MAPV.pairR=L.svg({pane:"pairPane"})}
    if(MAPV.pair)m.removeLayer(MAPV.pair);
    const A=[lat,lon], V=[vlat,vlon], d=pairDist(vlat,vlon,lat,lon), o={pane:"pairPane",renderer:MAPV.pairR};
    MAPV.pair=L.layerGroup([
      L.polyline([A,V],{...o,color:"#000",weight:7,opacity:.5,interactive:false}),
      L.polyline([A,V],{...o,color:"#ffd60a",weight:3.5,dashArray:"10 7",interactive:false}),
      L.circleMarker(V,{...o,radius:8,color:"#fff",weight:2.5,fillColor:"#1e88e5",fillOpacity:1}).bindTooltip(`Spring vent${vname?": "+esc(vname):""}`,{permanent:true,direction:"top",offset:[0,-9],className:"pair-tip"}),
      L.circleMarker(A,{...o,radius:8,color:"#fff",weight:2.5,fillColor:"#e53935",fillOpacity:1}).bindTooltip(lname?esc(lname):"Listing",{permanent:true,direction:"bottom",offset:[0,9],className:"pair-tip"}),
      L.circleMarker([(lat+vlat)/2,(lon+vlon)/2],{...o,radius:0,opacity:0,fillOpacity:0,interactive:false}).bindTooltip(`${pairFmt(d)} straight line`,{permanent:true,direction:"center",className:"pair-tip pair-d"})]).addTo(m);
    if(!MAPV.pairCtl){const C=L.Control.extend({onAdd(){const b=L.DomUtil.create("button","pair-x");b.type="button";b.textContent=MAPV.pairBack?"Back to the list":"Clear line";
        L.DomEvent.disableClickPropagation(b); b.onclick=pairClear; return b}}); MAPV.pairCtl=new C({position:"topleft"}).addTo(m)}
    // full-screen map, so the page's controls don't cover it
    const w=document.getElementById("mapwrap"); if(w&&!w.classList.contains("max")&&typeof mapMaxSet==="function"){mapMaxSet(true); if(MAPV.pairBack)MAPV.pairBack.max=true}
    const fit=()=>{m.invalidateSize({pan:false}); if(d<25)m.setView([(lat+vlat)/2,(lon+vlon)/2],18); else m.fitBounds(L.latLngBounds([A,V]),{padding:[150,130],maxZoom:18})};
    fit(); setTimeout(fit,350);
    try{history.replaceState(null,"",location.pathname+location.search+`#pair=${gmF(vlat)},${gmF(vlon)},${gmF(lat)},${gmF(lon)}`)}catch(e){}};
  setTimeout(go,60)}
document.addEventListener("keydown",e=>{if(e.key==="Escape"&&MAPV.pair)pairClear()});
'''
h = rep("/* ---------- map tab ---------- */", JS + "/* ---------- map tab ---------- */", h)
CSS = '''.pair{font-weight:600;color:var(--lake);font-size:12.5px}.pair-l{grid-column:1/-1;margin-top:3px}
.leaflet-tooltip.pair-tip{font:600 12px/1.3 var(--body);background:#111;color:#fff;border:0;border-radius:5px;padding:3px 7px;box-shadow:0 1px 6px rgba(0,0,0,.4)}
.leaflet-tooltip.pair-tip:before{display:none}.leaflet-tooltip.pair-d{background:#ffd60a;color:#111}
.pair-x{font:600 13px var(--body);background:#fff;color:#111;border:2px solid rgba(0,0,0,.25);border-radius:6px;padding:5px 10px;cursor:pointer}
'''
h = rep("/* springheads */", CSS + "/* springheads */", h)

# ---- Springheads tab listing and popups: straight line instead of the walking route ----
h = rep('''listing point ${gmLink(lat,lon)} · ${gmBoth(hv[8],hv[9],lat,lon)}</span>`);''',
        '''listing point ${gmLink(lat,lon)}</span>`, `<span>${pairLink(hv[8],hv[9],lat,lon,hv[0],addr)}</span>`);''', h)
h = rep('''${gmLink(hd[8],hd[9],"Vent:")}<br>${gmBoth(hd[8],hd[9],x[16],x[17])}</div>''',
        '''${gmLink(hd[8],hd[9],"Vent:")}<br>${pairLink(hd[8],hd[9],x[16],x[17],hd[0],addr)}</div>''', h)
# water listings on a spring (Springs tab groups) in map popups
h = rep('''    ${wtPop(path)}<div class="pp-links"><a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">View listing on Redfin</a><a class="alt" href="${z}" target="_blank" rel="noopener">Find on Zillow</a></div>`;
}
function shPopup(x){''',
        '''    ${o.waters.filter(w=>w.t==="spring"&&w.fr&&x[16]!=null).slice(0,1).map(w=>{const v=springLL(w.fr);return `<div class="pp-gm">${pairLink(v[0],v[1],x[16],x[17],w.n,addr)}</div>`}).join("")}
    ${wtPop(path)}<div class="pp-links"><a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">View listing on Redfin</a><a class="alt" href="${z}" target="_blank" rel="noopener">Find on Zillow</a></div>`;
}
function shPopup(x){''', h)
# gmSpring uses springLL now
h = rep('''function gmSpring(r){let ll=r[18]||[(r[12][1]+r[12][3])/2,(r[12][0]+r[12][2])/2];
  if(r[16]==="FL"&&typeof fsiRow==="function"){const f=fsiRow(r); if(f&&fsiTok(f[2])===fsiTok(r[1])){const cl=Math.cos(ll[0]*Math.PI/180);
    if(Math.hypot((f[0]-ll[0])*111200,(f[1]-ll[1])*111200*cl)<=300)ll=[f[0],f[1]]}}
  return ` · ${gmLink(ll[0],ll[1],"vent")}`}''', '''function gmSpring(r){const ll=springLL(r); return ` · ${gmLink(ll[0],ll[1],"vent")}`}''', h)
# opening a #pair= address
h = rep("try{mapMaxInit()}catch(e){}\n", "try{mapMaxInit()}catch(e){}\n"
        "{const pm=/^#pair=(-?[\\d.]+),(-?[\\d.]+),(-?[\\d.]+),(-?[\\d.]+)/.exec(location.hash); if(pm)setTimeout(()=>pairShow(+pm[1],+pm[2],+pm[3],+pm[4]),300)}\n", h)
open(page, "w").write(h); print("straight-line links added")
