"""One-time page edits for the detailed map (idempotent: exits if already applied).
Adds real trail lines, ranked-water shapes, every springhead vent, city limits, rivers, lakes, creeks and ponds,
highways, roads and town names, loaded from map/nat.json, map/st/<ST>.json and map/hy/<ST>.json as you zoom in.
Also: a 400 m band along trails when zoomed in close, a dashed line from each springhead listing to its vent,
a Satellite view link in every listing popup, and layer switches. The monthly refresh scripts never touch this code.
Usage: python3 map_detail.py <page.html>"""
import sys
page = sys.argv[1]
h = open(page).read()
# ---- fixes (Nov 10): hover and click on trails, waters and springheads; ranked markers stay at every zoom
def apply_fixes():
    global h
    if "GEO.top=" in h: return False
    def fx(old, new, count=1):
        global h
        n = h.count(old); assert n == count, (n, old[:90]); h = h.replace(old, new)
    # interactive map lines and springheads share the listings' canvas, so the mouse reaches them
    fx("GEO.labels=L.layerGroup().addTo(m);", "GEO.labels=L.layerGroup().addTo(m); GEO.top=m.getRenderer(L.circleMarker([0,0])); GEO.top.options.tolerance=5;")
    fx("renderer:R.geoTrail,", "renderer:GEO.top,", 2)
    fx("const o={renderer:R.geoRanked,grp,wi,kind,nm,color:lk};", "const o={renderer:GEO.top,grp,wi,kind,nm,color:lk};")
    fx("{renderer:R.geoVent,radius:", "{renderer:GEO.top,radius:")
    fx("{renderer:R.geoWater,interactive:!!nm,nm,", "{renderer:nm?GEO.top:R.geoWater,interactive:!!nm,nm,")
    fx("function geoShow(m,g,on){if(!g)return; if(on){if(!m.hasLayer(g))m.addLayer(g)}",
       "function geoShow(m,g,on){if(!g)return; if(on){if(!m.hasLayer(g)){m.addLayer(g);GEO.dirty=true}}")
    # ranked lakes, rivers and springs keep their markers when zoomed in (a spring pool is too small to see as a shape)
    fx('  if(MAPV.waters)geoShow(m,MAPV.waters,z<10&&document.getElementById("showwat").checked);\n', "")
    fx("  geoLabels(vis);\n}", "  if(GEO.dirty){GEO.dirty=false;geoOrder()}\n  geoLabels(vis);\n}")
    fx("function geoLabels(vis){", """function geoOrder(){const m=MAPV.map,gs=[]; // map lines under the listings, springheads above the lines
  Object.values(GEO.S).forEach(G=>{if(G.hd)gs.push(G.hd)}); if(GEO.natG)gs.push(GEO.natG.tr);
  Object.values(GEO.S).forEach(G=>{if(G.tr)gs.push(G.tr)}); Object.values(GEO.H).forEach(G=>{if(G.l)gs.push(G.l)});
  Object.values(GEO.S).forEach(G=>{if(G.wt)gs.push(G.wt)});
  gs.forEach(g=>{if(m.hasLayer(g))g.bringToBack()})}
function geoCfs(q){q=+q;return q.toLocaleString(undefined,{maximumFractionDigits:q<10?1:0})}
const GEO_MAG=["","more than 100","10 to 100","1 to 10","0.1 to 1"];
function geoLabels(vis){""")
    fx('G.hd.bindTooltip(l=>`<b>${esc(l.options.nm)}</b><br>Magnitude ${l.options.mag} springhead${l.options.q!=null?` · about ${cfs(l.options.q)} cfs`:""}`,{direction:"top",className:"gt"});',
       'G.hd.bindTooltip(l=>`<b>${esc(l.options.nm)}</b><br>Springhead, magnitude ${l.options.mag}${l.options.q!=null?` · about ${geoCfs(l.options.q)} cfs`:""}`,{direction:"top",className:"gt"})'
       '.bindPopup(l=>`<div class="pp-price">${esc(l.options.nm)}</div><div class="pp-sub">Magnitude ${l.options.mag} springhead (${GEO_MAG[l.options.mag]||"unknown"} cubic feet per second)${l.options.q!=null?`; last measured at about ${geoCfs(l.options.q)} cfs`:""}</div><div class="pp-links"></div>`,{maxWidth:300});')
    fx('in city limits`:""}</div></div>`', 'in city limits`:""}</div><div class="pp-links"></div></div>`')
    fx('G.wt.bindTooltip(geoWaterTip,{sticky:true,className:"gt"});',
       'G.wt.bindTooltip(geoWaterTip,{sticky:true,className:"gt"}).bindPopup(l=>`<div class="pp-sub" style="font-size:14px">${geoWaterTip(l)}</div><div class="pp-links"></div>`,{maxWidth:300});')


    return True


# ---- Nov 10 (2): Street View and Google Earth 3D links beside Satellite view in every map popup
def apply_fixes2():
    global h
    if "map_action=pano" in h: return False
    old = 'box.insertAdjacentHTML("beforeend",`<a class="alt sat" href="https://www.google.com/maps/@?api=1&map_action=map&center=${ll.lat.toFixed(6)},${ll.lng.toFixed(6)}&zoom=18&basemap=satellite" target="_blank" rel="noopener">Satellite view</a>`)'
    assert h.count(old) == 1
    h = h.replace(old, 'const la=ll.lat.toFixed(6),lo=ll.lng.toFixed(6); box.insertAdjacentHTML("beforeend",'
        '`<a class="alt sat" href="https://www.google.com/maps/@?api=1&map_action=map&center=${la},${lo}&zoom=18&basemap=satellite" target="_blank" rel="noopener">Satellite view</a>'
        '<a class="alt" href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${la},${lo}" target="_blank" rel="noopener">Street View</a>'
        '<a class="alt" href="https://earth.google.com/web/@${la},${lo},250a,700d,35y,0h,60t,0r" target="_blank" rel="noopener">3D view</a>`)')
    old2 = "Every listing has a Satellite view link that opens the spot on Google Maps; local streets and imagery aren't drawn here."
    if old2 in h:
        h = h.replace(old2, "Every listing popup has Satellite view, Street View and 3D view links that open the spot in Google Maps or Google Earth; local streets and imagery aren't drawn here.")
    return True

if 'id="geotr"' in h:
    if apply_fixes() | apply_fixes2():
        open(page, "w").write(h); print("map fixes applied")
    else:
        print("map detail already present")
    sys.exit()
def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, (n, old[:90])
    h = h.replace(old, new)

# ---- colour tokens (light, dark via media query, dark via data-theme)
LIGHT = "--map-hydro:#b3d7df; --map-hydro-line:#6fb0bf; --map-road:#e3d9c4; --map-road-major:#dcc18e; --map-label:#3a4c4f;"
DARK = "--map-hydro:#1c4952; --map-hydro-line:#2f7482; --map-road:#33413f; --map-road-major:#6b5c3d; --map-label:#b9c9cb;"
rep("--map-land:#ffffff; --map-water:#dfeaec; --map-line:#c4d2d4;", "--map-land:#ffffff; --map-water:#dfeaec; --map-line:#c4d2d4; " + LIGHT)
rep("--map-land:#182629; --map-water:#0b1314; --map-line:#2c3f42;", "--map-land:#182629; --map-water:#0b1314; --map-line:#2c3f42; " + DARK, count=2)

CSS = """
.lg i.ln{width:20px;height:0;border-radius:0;border:0;border-top:3px solid var(--trail);box-shadow:none}
.lg i.ln.g{border-top-style:dashed}
.lg i.band{width:20px;height:11px;border-radius:6px;background:color-mix(in srgb,var(--trail) 20%,transparent);border:0;box-shadow:none}
.lg i.vent{width:10px;height:10px;background:var(--surface);border:2px solid var(--spring);box-shadow:none}
.lg i.cl{width:16px;height:10px;border-radius:2px;background:none;border:1.5px dashed var(--city);box-shadow:none}
.lg i.hy{width:16px;height:10px;border-radius:3px;background:var(--map-hydro);border:1px solid var(--map-hydro-line);box-shadow:none}
.lg i.rk{width:16px;height:10px;border-radius:3px;background:color-mix(in srgb,var(--lake) 35%,transparent);border:1.5px solid var(--lake);box-shadow:none}
.geobar{display:flex;flex-wrap:wrap;align-items:center;gap:6px 14px;font-size:13px;color:var(--muted);margin:2px 0 8px}
.geobar b{color:var(--ink);font-weight:600}
.geobar label{display:inline-flex;align-items:center;gap:5px;cursor:pointer}
.geobar .hint{font-size:12px}
.plab span{display:block;transform:translate(-50%,-50%);font:500 11px/1.1 var(--body);color:var(--map-label);white-space:nowrap;pointer-events:none;
  text-shadow:0 0 2px var(--map-land),0 0 2px var(--map-land),0 0 3px var(--map-land),0 0 4px var(--map-land)}
.plab.big span{font-size:12.5px;font-weight:650;color:var(--ink)}
.plab.c span{font-size:13.5px;font-weight:700;color:var(--ink);letter-spacing:.01em}
.leaflet-tooltip.gt{background:var(--surface);color:var(--ink);border:1px solid var(--rule);box-shadow:0 2px 8px rgba(0,0,0,.15);font:12.5px/1.35 var(--body);padding:5px 8px}
.leaflet-tooltip.gt:before{display:none}
.pp-trail .pp-sub{display:block}
#mapwrap{max-width:100%;grid-template-columns:minmax(0,1fr)}
.mapbar .count{white-space:normal}
#leafmap{contain:paint}
.leaflet-container .leaflet-control-attribution{background:color-mix(in srgb,var(--surface) 85%,transparent);color:var(--muted)}
.leaflet-container .leaflet-control-attribution a{color:var(--muted)}
"""
rep("\n/* leaflet */\n", CSS + "\n/* leaflet */\n")

# ---- legend and layer switches
rep('<span class="lg"><i class="wat"></i>Ranked lake, river or spring</span></div>',
    '<span class="lg"><i class="wat"></i>Ranked lake, river or spring</span></div>\n'
    '  <div class="geobar"><b>Map detail</b>'
    '<label><input id="geotr" type="checkbox" checked> Bike trails</label>'
    '<label><input id="geowt" type="checkbox" checked> Water</label>'
    '<label><input id="georoad" type="checkbox" checked> Roads and towns</label>'
    '<span class="lg"><i class="ln"></i>Paved trail</span><span class="lg"><i class="ln g"></i>Gravel or mountain bike</span>'
    '<span class="lg"><i class="band"></i>400 m each side of a trail (zoom in)</span>'
    '<span class="lg"><i class="rk"></i>Ranked water</span><span class="lg"><i class="hy"></i>Other water</span>'
    '<span class="lg"><i class="vent"></i>Springhead (bigger = stronger flow)</span><span class="lg"><i class="cl"></i>City limits</span></div>')

# ---- base outlines go to their own pane, under everything
rep('MAPV.base=L.geoJSON(topojson.feature(t,t.objects.states),{interactive:false}).addTo(m);',
    'MAPV.base=L.geoJSON(topojson.feature(t,t.objects.states),{interactive:false,pane:"geoBase"}).addTo(m);')
rep('MAPV.counties=L.geoJSON(topojson.feature(t,t.objects.counties),{interactive:false});',
    'MAPV.counties=L.geoJSON(topojson.feature(t,t.objects.counties),{interactive:false,pane:"geoBase"});')
rep('maxZoom:15,worldCopyJump:false', 'maxZoom:17,worldCopyJump:false')
rep("m.attributionControl.addAttribution('Outlines: US Census via us-atlas · Listings: Redfin');",
    "m.attributionControl.addAttribution('Outlines, roads, towns: US Census TIGER · Water: USGS NHD via TIGER, Natural Earth · Trails: © OpenStreetMap contributors, USGS · Listings: Redfin');\n  geoInit(m);")

# ---- springhead listing: dashed line to its vent
rep("""        .bindPopup(()=>shPopup(x),{maxWidth:300}).addTo(MAPV.heads);""",
    """        .bindPopup(()=>shPopup(x),{maxWidth:300}).addTo(MAPV.heads);
      if(hd[8]!=null&&(Math.abs(hd[8]-x[16])>2e-5||Math.abs(hd[9]-x[17])>2e-5))L.polyline([[x[16],x[17]],[hd[8],hd[9]]],{color:sp,weight:1.6,dashArray:"4 4",opacity:.9,interactive:false}).addTo(MAPV.heads);""")
# geo layers follow the state menu and redraw after each render
rep("  MAPV.fitted=true; MAPV.lastS=s;\n}", "  MAPV.fitted=true; MAPV.lastS=s;\n  geoUpdate();\n}")

JS = r"""
/* ---------- detailed map layers (map/nat.json, map/st/<ST>.json, map/hy/<ST>.json) ---------- */
const GEO={nat:null,natG:null,S:{},H:{},sb:null,labels:null,lastLab:""};
function geoDec(a,sc){const o=new Array(a.length/2);let x=0,y=0;for(let i=0,j=0;i<a.length;i+=2,j++){x+=a[i];y+=a[i+1];o[j]=[y/sc,x/sc]}return o}
const geoRings=(p,sc)=>p.map(r=>geoDec(r,sc));
const geoOn=id=>{const e=document.getElementById(id);return !e||e.checked};
function geoBandW(){const m=MAPV.map,z=m.getZoom();return Math.max(4,800/(40075016.686*Math.cos(m.getCenter().lat*Math.PI/180)/(256*Math.pow(2,z))))}
function geoTW(z){return z<6?1.1:z<8?1.6:z<10?2.4:z<12?3:z<14?3.6:4.2}
function geoTrailStyle(ty,z){const c=tok("--trail");return {color:c,weight:geoTW(z),opacity:ty==="u"?.7:.95,dashArray:ty==="g"||ty==="m"?(ty==="m"?"2 5":"7 5"):null,lineCap:"round"}}
function geoTrailTip(l){const t=TR.trails[l.options.tid];if(!t)return"";const seg=l.options.seg;
  return `<b>${esc(seg||t[0])}</b>${seg&&seg!==t[0]?`<br>${esc(t[0])} network`:""}<br>${miTxt(t[2])} mi · ${trTags(t).map(k=>TTN[k]).join(", ")||"Surface not recorded"}`}
function geoTrailPop(l){const tid=l.options.tid,t=TR.trails[tid];if(!t)return"";
  const n=TR.L.filter(x=>x[0]===tid).length, nc=CT.L.filter(x=>x[1]===tid).length;
  return `<div class="pp-trail"><div class="pp-price">${esc(l.options.seg||t[0])}</div>${l.options.seg&&l.options.seg!==t[0]?`<span class="pp-sub">Part of ${esc(t[0])}</span>`:""}
    <div class="pp-sub">${miTxt(t[2])} miles · ${trTags(t).map(k=>TTN[k]).join(", ")||"Surface not recorded"}</div>
    <div>${n?`<b>${n.toLocaleString()}</b> house${n===1?"":"s"} for sale within 400 m`:"No houses for sale within 400 m outside big cities"}${nc?` · <b>${nc.toLocaleString()}</b> in city limits`:""}</div></div>`}
function geoWaterTip(l){const o=l.options;let w=null;try{if(!WIDX)allListings();w=(WIDX[o.grp]||{})[o.wi]}catch(e){}
  const k={l:"lake",r:"river",s:"spring",f:"spring-fed river"}[o.kind];
  return w?`<b>${esc(w.n)}</b><br>#${w.rank} ${w.t}${w.t==="lake"||w.t==="river"?" in "+esc(NAMES[w.st]):""}`:`<b>${esc(o.nm||"Ranked "+k)}</b>`}
function geoInit(m){
  [["geoBase",200],["geoWater",320],["geoRanked",340],["geoRoad",350],["geoCity",355],["geoBand",360],["geoTrail",370],["geoVent",380],["geoLabel",390]].forEach(([p,z])=>{const e=m.createPane(p);e.style.zIndex=z;if(p==="geoLabel"||p==="geoBand"||p==="geoBase")e.style.pointerEvents="none"; if(p==="geoBand")e.style.opacity=".2"});
  GEO.R={};["geoBase","geoWater","geoRanked","geoRoad","geoCity","geoBand","geoTrail","geoVent"].forEach(p=>GEO.R[p]=L.canvas({pane:p,padding:.4,tolerance:p==="geoTrail"?6:p==="geoRanked"||p==="geoWater"?3:0}));
  GEO.labels=L.layerGroup().addTo(m);
  m.on("zoomend",geoZoomStyle); m.on("moveend",geoUpdate);
  m.on("popupopen",e=>{const el=e.popup.getElement(), box=el&&el.querySelector(".pp-links"); if(!box||box.querySelector(".sat"))return; const ll=e.popup.getLatLng();
    box.insertAdjacentHTML("beforeend",`<a class="alt sat" href="https://www.google.com/maps/@?api=1&map_action=map&center=${ll.lat.toFixed(6)},${ll.lng.toFixed(6)}&zoom=18&basemap=satellite" target="_blank" rel="noopener">Satellite view</a>`)});
  ["geotr","geowt","georoad"].forEach(id=>document.getElementById(id).addEventListener("change",geoUpdate));
  if(typeof fetch==="function")fetch("map/nat.json").then(r=>r.json()).then(d=>{GEO.nat=d;GEO.sb=d.sb;geoBuildNat();geoUpdate()}).catch(()=>{});
}
function geoGroup(){return L.featureGroup()}
function geoBuildNat(){const d=GEO.nat,R=GEO.R,z=MAPV.map.getZoom(),G=GEO.natG={tr:geoGroup(),rd:geoGroup(),rv:geoGroup(),lk:geoGroup()};
  d.tr.forEach(([tid,ty,e])=>G.tr.addLayer(L.polyline(geoDec(e,1e4),{renderer:R.geoTrail,tid,ty,...geoTrailStyle(ty,z)})));
  G.tr.bindTooltip(geoTrailTip,{sticky:true,className:"gt"}).bindPopup(geoTrailPop,{maxWidth:300});
  d.rd.forEach(([nm,rt,e])=>G.rd.addLayer(L.polyline(geoDec(e,1e4),{renderer:R.geoRoad,interactive:false,color:tok("--map-road-major"),weight:1.1,opacity:.85})));
  d.rv.forEach(([nm,sr,e])=>G.rv.addLayer(L.polyline(geoDec(e,1e4),{renderer:R.geoWater,interactive:false,color:tok("--map-hydro-line"),weight:sr<=4?1.6:sr<=6?1.1:.8})));
  d.lk.forEach(([nm,ps])=>G.lk.addLayer(L.polygon(ps.map(p=>geoRings(p,1e4)),{renderer:R.geoWater,interactive:false,color:tok("--map-hydro-line"),weight:.6,fillColor:tok("--map-hydro"),fillOpacity:1})));
}
function geoBuildState(s,d){["tr","wt","hd","cl","rd","rv","lk","pl"].forEach(k=>d[k]=d[k]||[]);const R=GEO.R,z=MAPV.map.getZoom(),G={tr:geoGroup(),band:geoGroup(),wt:geoGroup(),hd:geoGroup(),cl:geoGroup(),rdM:geoGroup(),rdm:geoGroup(),rv:geoGroup(),lk:geoGroup(),pl:d.pl};
  const hy=tok("--map-hydro"),hyl=tok("--map-hydro-line"),lk=tok("--lake"),sp=tok("--spring"),surf=tok("--surface"),cc=tok("--city"),rM=tok("--map-road-major"),rm=tok("--map-road"),tc=tok("--trail"),bw=geoBandW();
  d.tr.forEach(([tid,ty,seg,e])=>{const ll=geoDec(e,1e5);G.tr.addLayer(L.polyline(ll,{renderer:R.geoTrail,tid,ty,seg:seg||null,...geoTrailStyle(ty,z)}));
    G.band.addLayer(L.polyline(ll,{renderer:R.geoBand,interactive:false,color:tc,opacity:1,weight:bw,lineCap:"round",lineJoin:"round"}))});
  G.tr.bindTooltip(geoTrailTip,{sticky:true,className:"gt"}).bindPopup(geoTrailPop,{maxWidth:300});
  d.wt.forEach(([grp,wi,kind,nm,ps,ls])=>{const o={renderer:R.geoRanked,grp,wi,kind,nm,color:lk};
    ps.forEach(p=>G.wt.addLayer(L.polygon(geoRings(p,1e5),{...o,weight:1.4,fillColor:lk,fillOpacity:.32})));
    ls.forEach(e=>G.wt.addLayer(L.polyline(geoDec(e,1e5),{...o,weight:kind==="f"||kind==="s"?3:3.2,opacity:.85})))});
  G.wt.bindTooltip(geoWaterTip,{sticky:true,className:"gt"});
  d.hd.forEach(([nm,mag,lat,lon,q])=>G.hd.addLayer(L.circleMarker([lat,lon],{renderer:R.geoVent,radius:[0,8,6.5,5,4][mag]||4,color:sp,weight:2,fillColor:surf,fillOpacity:.9,nm,mag,q})));
  G.hd.bindTooltip(l=>`<b>${esc(l.options.nm)}</b><br>Magnitude ${l.options.mag} springhead${l.options.q!=null?` · about ${cfs(l.options.q)} cfs`:""}`,{direction:"top",className:"gt"});
  d.cl.forEach(([nm,ps])=>ps.forEach(p=>G.cl.addLayer(L.polygon(geoRings(p,1e5),{renderer:R.geoCity,interactive:false,color:cc,weight:1.3,dashArray:"5 4",opacity:.7,fill:false}))));
  d.rd.forEach(([nm,rt,e])=>(rt==="s"?G.rdm:G.rdM).addLayer(L.polyline(geoDec(e,1e5),{renderer:R.geoRoad,interactive:false,rt,color:rt==="s"?rm:rM,weight:(rt==="i"?1.8:rt==="u"?1.3:1)*(z>=12&&rt!=="s"?1.4:1),opacity:.8})));
  d.rv.forEach(([nm,sr,e])=>G.rv.addLayer(L.polyline(geoDec(e,1e5),{renderer:R.geoWater,interactive:false,color:hyl,weight:sr<=4?1.8:sr<=6?1.3:1})));
  d.lk.forEach(([nm,ps])=>G.lk.addLayer(L.polygon(ps.map(p=>geoRings(p,1e5)),{renderer:R.geoWater,interactive:false,color:hyl,weight:.6,fillColor:hy,fillOpacity:1})));
  return G;
}
function geoBuildHydro(s,d){d.a=d.a||[];d.l=d.l||[];const R=GEO.R,G={a:geoGroup(),l:geoGroup()},hy=tok("--map-hydro"),hyl=tok("--map-hydro-line");
  d.a.forEach(([nm,ps])=>G.a.addLayer(L.polygon(ps.map(p=>geoRings(p,1e5)),{renderer:R.geoWater,interactive:false,color:hyl,weight:.6,fillColor:hy,fillOpacity:1})));
  d.l.forEach(([nm,cn,e])=>G.l.addLayer(L.polyline(geoDec(e,1e5),{renderer:R.geoWater,interactive:!!nm,nm,color:hyl,weight:nm?1.4:.9,opacity:nm?1:.8,dashArray:cn?"4 3":null})));
  G.l.bindTooltip(l=>esc(l.options.nm),{sticky:true,className:"gt"});
  return G;
}
function geoLoad(kind,s){const C=kind==="st"?GEO.S:GEO.H; if(C[s])return; C[s]={loading:true};
  fetch(`map/${kind}/${s}.json`).then(r=>{if(!r.ok)throw 0;return r.json()}).then(d=>{C[s]=kind==="st"?geoBuildState(s,d):geoBuildHydro(s,d);geoUpdate()}).catch(()=>{C[s]={none:true}})}
function geoShow(m,g,on){if(!g)return; if(on){if(!m.hasLayer(g))m.addLayer(g)}else if(m.hasLayer(g))m.removeLayer(g)}
function geoZoomStyle(){const m=MAPV.map,z=m.getZoom(),w=geoTW(z);
  const set=g=>g&&g.eachLayer(l=>l.setStyle({weight:w}));
  if(GEO.natG)set(GEO.natG.tr);
  Object.values(GEO.S).forEach(G=>{if(!G.tr)return;set(G.tr);
    if(z>=12){const bw=geoBandW();G.band.eachLayer(l=>l.setStyle({weight:bw}))}
    if(G.zr!==(z>=12)){G.zr=z>=12;G.rdM.eachLayer(l=>l.setStyle({weight:(l.options.rt==="i"?1.8:1.3)*(z>=12?1.4:1)}))}});
}
function geoUpdate(){const m=MAPV.map; if(!m||!GEO.nat)return;
  const z=m.getZoom(), b=m.getBounds().pad(.15), det=z>=8, tr=geoOn("geotr"), wt=geoOn("geowt"), rd=geoOn("georoad");
  const N=GEO.natG; geoShow(m,N.tr,tr&&!det); geoShow(m,N.rd,rd&&!det&&z>=5); geoShow(m,N.rv,wt&&!det); geoShow(m,N.lk,wt&&!det);
  const vis=new Set(); if(det)Object.entries(GEO.sb).forEach(([s,bb])=>{if(b.intersects(L.latLngBounds([bb[1],bb[0]],[bb[3],bb[2]])))vis.add(s)});
  vis.forEach(s=>{geoLoad("st",s); if(z>=11&&wt)geoLoad("hy",s)});
  Object.entries(GEO.S).forEach(([s,G])=>{if(!G.tr)return; const v=vis.has(s);
    geoShow(m,G.tr,v&&tr); geoShow(m,G.band,v&&tr&&z>=12); geoShow(m,G.wt,v&&wt); geoShow(m,G.hd,v&&wt&&z>=8);
    geoShow(m,G.cl,v&&rd); geoShow(m,G.rdM,v&&rd); geoShow(m,G.rdm,v&&rd&&z>=10);
    const hyOn=z>=11&&GEO.H[s]&&GEO.H[s].a; geoShow(m,G.rv,v&&wt&&!hyOn); geoShow(m,G.lk,v&&wt&&!hyOn)});
  Object.entries(GEO.H).forEach(([s,G])=>{if(!G.a)return; const v=vis.has(s)&&z>=11&&wt; geoShow(m,G.a,v); geoShow(m,G.l,v)});
  if(MAPV.waters)geoShow(m,MAPV.waters,z<10&&document.getElementById("showwat").checked);
  geoLabels(vis);
}
function geoLabels(vis){const m=MAPV.map,z=m.getZoom(),g=GEO.labels; g.clearLayers(); if(!geoOn("georoad"))return;
  const th=z<4.5?2e6:z<5.5?6e5:z<6.5?2e5:z<7.5?7e4:z<8.5?2.5e4:z<9.5?1e4:z<10.5?4e3:z<11.5?1500:300;
  const b=m.getBounds(), sz=m.getSize(), boxes=[]; let cand=[];
  if(z<8)cand=GEO.nat.pl.map(p=>[p[0],p[2],p[3],p[4]]); else vis.forEach(s=>{const G=GEO.S[s];if(G&&G.pl)cand=cand.concat(G.pl)});
  cand=cand.filter(p=>p[3]>=th&&b.contains([p[1],p[2]])).sort((a,c)=>c[3]-a[3]);
  let n=0; for(const [nm,lat,lon,pop] of cand){ if(n>=110)break;
    const pt=m.latLngToContainerPoint([lat,lon]), big=pop>=th*8, w=nm.length*(big?7.4:6.4)+8, h=big?17:15, bx=[pt.x-w/2,pt.y-h/2,pt.x+w/2,pt.y+h/2];
    if(bx[0]<0||bx[1]<0||bx[2]>sz.x||bx[3]>sz.y)continue;
    if(boxes.some(o=>!(bx[2]<o[0]||bx[0]>o[2]||bx[3]<o[1]||bx[1]>o[3])))continue;
    boxes.push(bx); n++;
    L.marker([lat,lon],{pane:"geoLabel",interactive:false,keyboard:false,icon:L.divIcon({className:"plab"+(pop>=5e5?" c":big?" big":""),html:`<span>${esc(nm)}</span>`,iconSize:null})}).addTo(g)}
}
function geoRestyle(){ // theme change: rebuild with new colours
  const m=MAPV.map; if(!m||!GEO.nat)return;
  const drop=G=>G&&Object.values(G).forEach(l=>{if(l&&l.eachLayer&&m.hasLayer(l))m.removeLayer(l)});
  drop(GEO.natG); geoBuildNat();
  Object.keys(GEO.S).forEach(s=>{drop(GEO.S[s]); delete GEO.S[s]}); Object.keys(GEO.H).forEach(s=>{drop(GEO.H[s]); delete GEO.H[s]});
  geoUpdate();
}
"""
rep("function initMap(){", JS + "function initMap(){")
rep("  const re=()=>{styleBase(); if(mode===\"map\")renderMap()};", "  const re=()=>{styleBase(); geoRestyle(); if(mode===\"map\")renderMap()};")
rep("<p>The map draws state and county lines itself because published pages can't load outside map imagery, so there's no street or satellite layer. Open a listing on Redfin to see the property on its aerial map.</p>",
    "<p>The map carries its own geography, so the page still opens for anyone you share it with. Zoomed out it shows every qualifying bike trail, the interstates and the larger towns. Zoom into a state and it adds the trails' true routes (solid for paved, dashed for gravel and mountain bike), the actual shorelines and courses of the ranked lakes, rivers and springs, every magnitude 1–4 springhead, city limits, highways and town names. Closer still, it shades the 400 m on each side of a trail that qualifies a house, and draws ponds, lakes, rivers and creeks near the trails, ranked waters and springheads. A dashed purple line joins each springhead listing to its vent. Hover a trail or water for its name, or click a trail for how many houses are for sale along it. Every listing has a Satellite view link that opens the spot on Google Maps; local streets and imagery aren't drawn here.</p>\n  <p>Sources: trails from OpenStreetMap and the USGS National Digital Trails; ponds, rivers and creeks from the USGS National Hydrography Dataset through the Census Bureau's TIGER files, with Natural Earth for the large rivers and lakes; roads, towns and outlines from the Census Bureau.</p>")
apply_fixes(); apply_fixes2()
open(page, "w").write(h)
print("map detail added")
