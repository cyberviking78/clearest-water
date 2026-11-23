"""Add the Oceanfront tab (houses and land with direct frontage on clear open Atlantic or Pacific coast) and its map layers, after
the Wild Lakes tab. Idempotent: re-running only refreshes the OC data. Usage: oc_tab.py page.html oc.json"""
import json, re, sys
page, ocp = sys.argv[1], sys.argv[2]
h = open(page).read()
OC = json.load(open(ocp))
data = "const OC=" + json.dumps(OC, separators=(",", ":"), ensure_ascii=False) + ";\n"
if 'id="t-oc"' in h:
    h = re.sub(r"const OC=\{.*?\};\n", lambda m: data, h, count=1, flags=re.S)
    open(page, "w").write(h); print("oceanfront data refreshed"); sys.exit()
def rep(old, new, count=1):
    global h
    assert h.count(old) == count, f"{h.count(old)}x: {old[:120]}"
    h = h.replace(old, new)
# ---- CSS: colours (light, then the two dark-mode blocks)
rep("--ml-water:#1557d6;", "--ml-water:#1557d6; --oc:#00678a; --oc-soft:#ddf1f7; --oc-map:#e8590c; --oc-line:#00a6c8;")
dark = [m.start() for m in re.finditer(r"--ml-water:#[0-9a-fA-F]{6};", h)][1:]
for pos in reversed(dark):
    end = h.index(";", pos) + 1
    h = h[:end] + " --oc:#7fd3ea; --oc-soft:#11303a; --oc-map:#ff8c42; --oc-line:#3fd0f0;" + h[end:]
CSS = """
/* oceanfront */
.tt.oc{color:var(--oc);background:var(--oc-soft)}
.rk.oc{font-family:var(--mono);font-size:12px;color:var(--oc);font-weight:500;padding-top:3px}
.lg i.oc{background:var(--oc-map);border:2px solid var(--og-dot);box-shadow:0 0 0 1px var(--oc-map)}
.lg i.ocl{background:var(--oc-line);height:4px;border-radius:2px;box-shadow:none;border:0}
.mc.occ{background:var(--oc-map);border-color:var(--og-dot)}
.ocsub{display:block;color:var(--muted);font-size:12px;margin-top:2px}
"""
rep(".mc.mlc{background:var(--ml-map);border-color:var(--og-dot)}", ".mc.mlc{background:var(--ml-map);border-color:var(--og-dot)}" + CSS)
# ---- tab and controls
rep('<button id="t-ml" type="button" aria-pressed="false">Wild Lakes</button>',
    '<button id="t-ml" type="button" aria-pressed="false">Wild Lakes</button><button id="t-oc" type="button" aria-pressed="false">Oceanfront</button>')
rep('data-mode="lakes rivers national property springs heads trails cities og rf ml map"><option value="">All states',
    'data-mode="lakes rivers national property springs heads trails cities og rf ml oc map"><option value="">All states')
rep('<label class="toggle" data-mode="property springs heads trails cities og rf ml map" hidden><input id="newonly"',
    '<select id="octype" aria-label="Houses or land" data-mode="oc" hidden><option value="">Houses and land</option><option value="h">Houses only</option><option value="l">Land only</option></select>'
    '<select id="ocprice" aria-label="Price" data-mode="oc" hidden><option value="750000">Up to $750k</option><option value="500000">Up to $500k</option><option value="350000">Up to $350k</option></select>\n'
    '  <label class="toggle" data-mode="property springs heads trails cities og rf ml oc map" hidden><input id="newonly"')
rep('<label class="toggle" data-mode="map" hidden><input id="showml" type="checkbox" checked> Show wild lakes with listings on the shore</label>',
    '<label class="toggle" data-mode="map" hidden><input id="showml" type="checkbox" checked> Show wild lakes with listings on the shore</label>\n'
    '  <label class="toggle" data-mode="map" hidden><input id="showoc" type="checkbox" checked> Show clear open-ocean coast and oceanfront listings</label>')
rep('<span class="lg"><i class="mla"></i>Wild lake</span>',
    '<span class="lg"><i class="mla"></i>Wild lake</span><span class="lg"><i class="oc"></i>Oceanfront</span><span class="lg"><i class="ocl"></i>Clear open-ocean coast</span>')
SECTION = """<section class="extra" data-mode="oc" hidden>
  <h2>How the oceanfront search works</h2>
  <p><b>Open ocean only.</b> The coast is the Census Bureau's coastline for the Atlantic (Maine to Florida) and the Pacific (California, Oregon and Washington), cut into pieces about a kilometer long. That line also runs around bays and sounds, so each piece is tested for open sea: from just offshore, straight lines are drawn every 5 degrees, and the piece counts only if they run 40 km (25 miles) without touching land across a quarter of the compass or more. Beaches facing the ocean pass, including the ocean side of barrier islands. Shores on Chesapeake Bay, Delaware Bay, Long Island Sound, Cape Cod Bay, Narragansett Bay, Pamlico Sound, Biscayne Bay, Puget Sound, the Strait of Juan de Fuca and San Francisco Bay, and the bay side of barrier islands, don't.</p>
  <p><b>Clear water.</b> Clarity comes from the VIIRS satellite (NOAA CoastWatch): Kd490, how fast blue light fades with depth, measured in the water just off each piece of coast. Atlantic values are the U.S. East Coast 750 m product, typical over 2015 to 2025; Pacific values are the global 4 km product, typical over 2021 to 2025. A piece is clear when Kd490 is <span class="ockd"></span> per meter or less, which works out to about 15 ft of visibility, the same bar as the Lakes tab. The page shows each listing's water as an estimated visibility (about <span class="ock"></span> meters divided by Kd490, in feet), a rough guide: the satellite reads the water 1 to 3 km out on the Atlantic and 4 to 8 km out on the Pacific (its pixels there are coarser), and the surf line is often murkier, especially after a storm. By this measure the clear open coast is most of Maine, Rhode Island, New Hampshire's short coast, more than half of Massachusetts and of Florida's Atlantic side, part of North Carolina's Outer Banks, a little of Long Island, nearly all of California and Oregon, and a small part of Washington. The ocean coast from New Jersey to Virginia, and South Carolina and Georgia, reads murkier.</p>
  <p><b>Direct frontage.</b> Houses and land on Redfin priced $100,000 to $750,000, collected on <span class="ocdate"></span>, that the listing agent marked waterfront and whose map point sits within reach of a clear open-ocean piece: 90 m plus the width of a square of the lot's size (at most 250 m; 120 m for a house and 150 m for land when no lot size is given), with no bay or sound shore closer. Condos and other units in a building, boat slips and timeshare weeks aren't included. The distance runs from the listing's map point to the Census coastline at the water's edge, so a wide beach puts even a front-row house 100 m or more from the line, while a house across the beach road can come close; check the satellite view and the plat before you call.</p>
</section>

<section class="extra" data-mode="map" hidden>"""
rep('<section class="extra" data-mode="map" hidden>', SECTION)
# ---- JS
rep("const SRC=[", data + "const SRC=[")
rep(' ["Water Quality Portal (EPA, USGS, NWQMC): Secchi depth and turbidity results"',
    ' ["NOAA CoastWatch: S-NPP VIIRS Kd490, science quality (U.S. East Coast 750 m annual; global 4 km monthly), oceanfront clarity","https://coastwatch.noaa.gov/erddap/"],\n'
    ' ["U.S. Census Bureau, TIGER/Line 2024 coastline and cartographic state outlines (oceanfront)","https://www2.census.gov/geo/tiger/TIGER2024/COASTLINE/"],\n'
    ' ["Natural Earth 1:10m land (Canada, Mexico and the Bahamas, for the open-ocean test)","https://www.naturalearthdata.com/"],\n'
    ' ["Water Quality Portal (EPA, USGS, NWQMC): Secchi depth and turbidity results"')
rep(' map:"Every', ' oc:"Houses and land priced $100,000 to $750,000 with direct frontage on the open Atlantic or Pacific where the water is clear from satellite: no bays, sounds or inlets, and the agent must have marked the listing waterfront. Each has a satellite link.",\n map:"Every')
rep('||sm==="ml")mode=sm', '||sm==="ml"||sm==="oc")mode=sm')
rep('if(location.hash==="#mountainlakes")mode="ml";', 'if(location.hash==="#mountainlakes")mode="ml";if(location.hash==="#oceanfront")mode="oc";')
rep('  if(mode==="ml"){renderML();return}', '  if(mode==="ml"){renderML();return}\n  if(mode==="oc"){renderOC();return}')
rep('document.getElementById("t-ml").setAttribute("aria-pressed",m==="ml");',
    'document.getElementById("t-ml").setAttribute("aria-pressed",m==="ml");\n  document.getElementById("t-oc").setAttribute("aria-pressed",m==="oc");')
rep('ph=m==="ml"?"Find a lake, town or state"', 'ph=m==="oc"?"Find a town, county or state":m==="ml"?"Find a lake, town or state"')
rep('  if(m==="ml"){\n', '''  if(m==="oc"){
    const nn=OC.L.filter(x=>x[14]).length, km=OC.P.length, kmall=Object.values(OC.kmall).reduce((a,b)=>a+b,0);
    document.getElementById("facts").innerHTML=`<span class="chip"><b>${OC.L.length}</b> oceanfront listings on clear open coast</span><span class="chip"><b>${OC.L.filter(x=>x[2]==="h").length}</b> house${OC.L.filter(x=>x[2]==="h").length===1?"":"s"} · <b>${OC.L.filter(x=>x[2]==="l").length}</b> land</span><span class="chip"><b>${km.toLocaleString()}</b> of ${kmall.toLocaleString()} km of open coast clear enough</span>`+(OC.first?`<span class="chip">First check · new listings are flagged from the next refresh</span>`:`<span class="chip"><b>${nn}</b> new since ${fmtD(OC.prev)}</span>`)+`<span class="chip">Redfin, ${fmtD(OC.date)}</span>`;
    try{localStorage.setItem("secchi-mode",m)}catch(e){}
    render();return;}
  if(m==="ml"){
''')
rep('"mlnear","showml"]', '"mlnear","showml","octype","ocprice","showoc"]')
rep('document.getElementById("t-ml").addEventListener("click",()=>setMode("ml"));',
    'document.getElementById("t-ml").addEventListener("click",()=>setMode("ml"));\ndocument.getElementById("t-oc").addEventListener("click",()=>setMode("oc"));')
rep('document.querySelectorAll(".mldate").forEach(e=>e.textContent=fmtD(ML.date));',
    'document.querySelectorAll(".mldate").forEach(e=>e.textContent=fmtD(ML.date));\ndocument.querySelectorAll(".ocdate").forEach(e=>e.textContent=fmtD(OC.date));'
    '\ndocument.querySelectorAll(".ockd").forEach(e=>e.textContent=OC.kdmax);\ndocument.querySelectorAll(".ock").forEach(e=>e.textContent=OC.k);')
OCJS = r'''
/* ---------- oceanfront tab ---------- */
const ocFt=kd=>Math.round(OC.k/kd*3.28084);
function ocFilter(){
  const q=document.getElementById("q").value.trim().toLowerCase(), s=sel.value, ty=document.getElementById("octype").value,
    pmax=+document.getElementById("ocprice").value, nw=document.getElementById("newonly").checked;
  const Ls=OC.L.filter(x=>(!s||x[9]===s)&&(!ty||x[2]===ty)&&x[1]<=pmax&&(!nw||x[14])&&
    (!q||(x[7]+" "+x[8]+" "+(NAMES[x[9]]||"")).toLowerCase().includes(q)||x[9].toLowerCase()===q));
  return {s,nw,Ls}}
function ocItem(x){
  const [pi,price,ty,beds,baths,sqft,ac,addr,city,st,dom,dist,path,first,isNew,lat,lon,yr]=x, kd=OC.P[pi][1];
  const facts=[ty==="l"?"Land":"House",beds!=null&&ty!=="l"?beds+" bd":null,baths!=null&&ty!=="l"?baths+" ba":null,sqft?sqft.toLocaleString()+" sq ft":null,ac?ac+" acres":null,yr?"built "+yr:null];
  const z="https://www.zillow.com/homes/"+encodeURIComponent(`${addr}, ${city}, ${st}`).replace(/%20/g,"-")+"_rb/";
  return `<li${isNew?' class="is-new"':""}><span class="pr">${money(price)}${isNew?' <span class="newb">New</span>':""}</span><span class="ad">${esc(addr)}, ${esc(city)}<small>${facts.filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}</small><span class="ocsub"><span class="tt oc">Oceanfront</span>${dist} m from the coastline · water about ${ocFt(kd)} ft clear (satellite)</span></span><span><a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">Redfin</a> <a href="${z}" target="_blank" rel="noopener">Zillow</a> <a href="${satUrl(lat,lon,18)}" target="_blank" rel="noopener">Satellite</a></span></li>`}
function renderOC(){
  const F=ocFilter(), byS=new Map();
  F.Ls.forEach(x=>{if(!byS.has(x[9]))byS.set(x[9],[]);byS.get(x[9]).push(x)});
  let html="";
  keys.forEach(k=>{const L=byS.get(k); if(!L)return;
    const nn=L.filter(x=>x[14]).length, km=OC.km[k]||0, kmall=OC.kmall[k]||0;
    html+=`<article class="state"><div class="shead"><h2>${esc(NAMES[k]||k)}<span class="ab">${k}</span></h2><span class="count">${L.length} listing${L.length===1?"":"s"} · ${km} of ${kmall} km of open coast clear${nn&&!F.nw?` · ${nn} new`:""}</span></div><ol>`;
    const byT=new Map(); L.forEach(x=>{const t=x[8]||"";if(!byT.has(t))byT.set(t,[]);byT.get(t).push(x)});
    [...byT.entries()].sort((a,b)=>b[1].length-a[1].length||a[0].localeCompare(b[0])).forEach(([t,T])=>{
      const kds=T.map(x=>OC.P[x[0]][1]), zn=T.filter(x=>x[14]).length;
      html+=`<li class="row"><span class="rk oc">${T.length}</span><div class="nm">${esc(t||"Unnamed place")}<small>Water about ${ocFt(Math.max(...kds))}${Math.max(...kds)!==Math.min(...kds)?"–"+ocFt(Math.min(...kds)):""} ft clear · ${T.filter(x=>x[2]==="h").length} house${T.filter(x=>x[2]==="h").length===1?"":"s"}, ${T.filter(x=>x[2]==="l").length} land</small></div><span></span>
      <details class="lst"${F.nw||F.s?" open":""}><summary>${T.length} oceanfront listing${T.length===1?"":"s"} ${zn?`<span class="cnt new">${zn} new</span>`:""}</summary><ul class="lsts">${T.sort((a,b)=>a[1]-b[1]).map(ocItem).join("")}</ul></details></li>`});
    html+="</ol></article>"});
  document.getElementById("list").innerHTML=html||`<p class="empty">${F.nw?"No new oceanfront listings match.":"No oceanfront listings on clear open coast match those filters."}</p>`;
}
function ocPopup(x){
  const [pi,price,ty,beds,baths,sqft,ac,addr,city,st,dom,dist,path,first,isNew,lat,lon,yr]=x, kd=OC.P[pi][1];
  const z="https://www.zillow.com/homes/"+encodeURIComponent(`${addr}, ${city}, ${st}`).replace(/%20/g,"-")+"_rb/";
  return `<div class="pp-price">${money(price)}${isNew?' <span class="newb">New</span>':""}</div>
    <div class="pp-sub">${[ty==="l"?"Land":"House",beds!=null&&ty!=="l"?beds+" bd":null,sqft?sqft.toLocaleString()+" sq ft":null,ac?ac+" acres":null].filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}</div>
    <div>${esc(addr)}, ${esc(city)}, ${st}</div>
    <div class="pp-water"><b>Oceanfront</b> · ${dist} m from the coastline · water about ${ocFt(kd)} ft clear (satellite)</div>
    <div class="pp-links"><a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">View listing on Redfin</a><a class="alt" href="${z}" target="_blank" rel="noopener">Find on Zillow</a><a class="alt" href="${satUrl(lat,lon,18)}" target="_blank" rel="noopener">Satellite</a></div>`;
}
'''
rep("/* ---------- map tab ---------- */", OCJS + "\n/* ---------- map tab ---------- */")
# ---- map layers
rep("MAPV.mlA=L.layerGroup();", "MAPV.mlA=L.layerGroup(); MAPV.ocA=L.layerGroup();")
i = h.index("MAPV.mll=L.markerClusterGroup("); j = h.index("});", h.index('class="mc mlc"', i)) + 3
h = h[:j] + ('\n  MAPV.ocl=L.markerClusterGroup({showCoverageOnHover:false,maxClusterRadius:42,spiderfyOnMaxZoom:true,chunkedLoading:true,\n'
             '    iconCreateFunction:c=>{const n=c.getChildCount(), s=n<10?30:n<50?36:44; return L.divIcon({html:`<div class="mc occ" style="width:${s}px;height:${s}px">${n}</div>`,className:"",iconSize:[s,s]})}});') + h[j:]
rep("m.addLayer(MAPV.mll);", "m.addLayer(MAPV.mll); m.addLayer(MAPV.ocA); m.addLayer(MAPV.ocl);")
rep("  const shownStates=new Set(L0.map(o=>o.st));",
    """  MAPV.ocl.clearLayers(); MAPV.ocA.clearLayers(); let nOC=0;
  if(document.getElementById("showoc").checked){const oc=tok("--oc-map"), ol=tok("--oc-line"), od=tok("--og-dot");
    if(!MAPV.ocP)MAPV.ocP=OC.M?OC.M.map(([st,ls])=>[st,ls.map(e=>geoDec(e,1e4))]):OC.P.map(p=>[p[0],[geoDec(p[2],1e4)]]);
    MAPV.ocP.forEach(([st,ll])=>{if(!s||st===s)L.polyline(ll,{color:ol,weight:4,opacity:.85,interactive:false}).addTo(MAPV.ocA)});
    const OL=OC.L.filter(x=>{if((s&&x[9]!==s)||(nw&&!x[14])||(pt&&x[2]!==pt))return false;
      if(q&&!(x[7]+" "+x[8]+" "+NAMES[x[9]]).toLowerCase().includes(q)&&x[9].toLowerCase()!==q)return false;return true});
    nOC=OL.length;
    MAPV.ocl.addLayers(OL.map(x=>L.circleMarker([x[15],x[16]],{radius:8,color:x[2]==="l"?oc:od,weight:x[2]==="l"?3.5:2.5,fillColor:x[2]==="l"?od:oc,fillOpacity:x[2]==="l"?.9:1}).bindPopup(()=>ocPopup(x),{maxWidth:300})));
    if(s)OL.forEach(x=>{const b=STBOX[s]=STBOX[s]||[90,180,-90,-180];b[0]=Math.min(b[0],x[15]);b[1]=Math.min(b[1],x[16]);b[2]=Math.max(b[2],x[15]);b[3]=Math.max(b[3],x[16])});
  }
  const shownStates=new Set(L0.map(o=>o.st));""")
rep('+(nM?` · ${nM} on wild lakes`:"");', '+(nM?` · ${nM} on wild lakes`:"")+(nOC?` · ${nOC} oceanfront`:"");')
open(page, "w").write(h)
print("oceanfront tab added")
