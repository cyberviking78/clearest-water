"""Add the Trails tab (houses within 400 m of long bike trails) to the page. Idempotent: re-running only refreshes TR.
Usage: tr_tab.py page.html tr.json"""
import json, re, sys
page, trp = sys.argv[1], sys.argv[2]
h = open(page).read()
TR = json.load(open(trp))
data = "const TR=" + json.dumps(TR, separators=(",", ":"), ensure_ascii=False) + ";\n"

if 'id="t-trails"' in h:
    h = re.sub(r"const TR=\{.*?\};\n", lambda m: data, h, count=1, flags=re.S)
    open(page, "w").write(h); print("trails data refreshed"); sys.exit()

def rep(old, new, count=1):
    global h
    assert h.count(old) == count, f"{h.count(old)}x: {old[:120]}"
    h = h.replace(old, new)

# ---- CSS ----
rep("  --spring:#6a3fb5; --spring-soft:#efe8fa;", "  --trail:#2e7d3a; --trail-soft:#e2f2e4;\n  --spring:#6a3fb5; --spring-soft:#efe8fa;")
rep("  --spring:#b79cf0; --spring-soft:#2a2140;", "  --trail:#7fd38b; --trail-soft:#1b3420;\n  --spring:#b79cf0; --spring-soft:#2a2140;", count=2)
CSS = """
/* trails */
.tt{font-family:var(--body);font-size:11px;font-weight:600;letter-spacing:.03em;text-transform:uppercase;color:var(--trail);background:var(--trail-soft);border-radius:4px;padding:1px 6px;white-space:nowrap;margin-right:4px}
.rk.tr{font-family:var(--mono);font-size:12px;color:var(--trail);font-weight:500;padding-top:3px}
.tier.tr{background:var(--trail-soft);color:var(--trail);white-space:normal;display:inline-block}
.lg i.tr{background:var(--trail)}
.mc.trc{background:color-mix(in srgb,var(--trail) 85%,transparent)}
"""
rep(".lg i.sh{background:var(--spring)}\n</style>", ".lg i.sh{background:var(--spring)}\n" + CSS + "</style>")

# ---- tab, controls, sections ----
rep('<button id="t-heads" type="button" aria-pressed="false">Springheads</button>',
    '<button id="t-heads" type="button" aria-pressed="false">Springheads</button><button id="t-trails" type="button" aria-pressed="false">Trails</button>')
rep('data-mode="lakes rivers national property springs heads map"><option value="">All states</option>',
    'data-mode="lakes rivers national property springs heads trails map"><option value="">All states</option>')
rep('<label class="toggle" data-mode="property springs heads map" hidden><input id="newonly" type="checkbox"> Only new listings</label>',
    '<select id="trtype" aria-label="Trail type" data-mode="trails" hidden><option value="">All trail types</option><option value="g">Gravel and crushed stone</option><option value="m">Mountain bike</option><option value="p">Paved path</option></select>'
    '<select id="trdist" aria-label="Distance to the trail" data-mode="trails" hidden><option value="400">Within 400 m (¼ mile)</option><option value="200">Within 200 m</option><option value="100">Within 100 m</option></select>'
    '<select id="trprice" aria-label="Price" data-mode="trails" hidden><option value="750000">Up to $750k</option><option value="500000">Up to $500k</option><option value="350000">Up to $350k</option></select>\n'
    '  <label class="toggle" data-mode="property springs heads trails map" hidden><input id="newonly" type="checkbox"> Only new listings</label>\n'
    '  <label class="toggle" data-mode="trails" hidden><input id="trall" type="checkbox"> Also list trails with no houses for sale</label>')
rep('<label class="toggle" data-mode="map" hidden><input id="showsh" type="checkbox" checked> Show springhead listings</label>',
    '<label class="toggle" data-mode="map" hidden><input id="showsh" type="checkbox" checked> Show springhead listings</label>\n'
    '  <label class="toggle" data-mode="map" hidden><input id="showtr" type="checkbox" checked> Show houses near bike trails</label>')
rep('<span class="lg"><i class="sh"></i>Springhead on the lot</span>', '<span class="lg"><i class="sh"></i>Springhead on the lot</span><span class="lg"><i class="tr"></i>House near a bike trail</span>')
SECTION = """<section class="extra" data-mode="trails" hidden>
  <h2>How the trails search works</h2>
  <p><b>Trails.</b> Bike trails come from Overture Maps (built mostly from OpenStreetMap) and the USGS National Digital Trails. A segment counts when it's a dedicated bike path or multi-use path, or a trail where bicycles are explicitly allowed; trails closed to bikes, and forest roads open to cars, are left out. Segments that connect, or that share a name across a short gap such as a road crossing, are joined into one network. A network qualifies when it has <b>20 or more miles</b> of trail (loops and trail systems), or when its longest end-to-end route is <b>10 miles or more</b>, which makes 20 miles out and back. Large connected greenway systems, like the Denver area's or the Twin Cities', show as one network with their best-known trail names.</p>
  <p><b>Trail type</b> comes from the surface recorded on each segment. <b>Paved path</b> is asphalt or concrete; <b>gravel</b> is crushed stone, gravel or packed unpaved surface, which covers most rail-trails; <b>mountain bike</b> is dirt singletrack, or trails named as mountain bike trails. Many segments have no surface recorded, so each trail shows its mix, and a trail is tagged with every type that makes up at least 15% of it or 5 miles. Treat the labels as a guide and check a trail map.</p>
  <p><b>Houses.</b> Single-family houses for sale on Redfin, priced $100,000 to $750,000, collected on <span class="trdate"></span>. A house is listed when its map point is within <b>400 m (about a quarter mile)</b> of a named segment of a qualifying trail, measured in a straight line; the actual walk may be longer if there's no path through. Houses inside the limits of the 128 cities with more than 200,000 people (2024 Census estimates) are left out. Some of those cities, such as Anchorage, Nashville, Louisville, Lexington and Augusta, are consolidated with their county, so their whole county is excluded.</p>
  <p><b>New</b> marks houses that weren't listed at the previous monthly check.</p>
</section>

<section class="extra" data-mode="map" hidden>"""
rep('<section class="extra" data-mode="map" hidden>', SECTION)
rep("<p>Every listing from the Property, Springs and Springheads tabs on one map,", "<p>Every listing from the Property, Springs, Springheads and Trails tabs on one map,")

# ---- JS ----
rep("const SRC=[", data + "const SRC=[")
rep(' ["Water Quality Portal (EPA, USGS, NWQMC): Secchi depth and turbidity results"',
    ' ["Overture Maps Foundation, transportation segments (bike paths, trails and surfaces; largely OpenStreetMap)","https://docs.overturemaps.org/guides/transportation/"],\n'
    ' ["USGS National Digital Trails (The National Map), trails open to bicycles","https://www.usgs.gov/national-digital-trails"],\n'
    ' ["U.S. Census Bureau, 2024 city population estimates and cartographic place boundaries","https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html"],\n'
    ' ["Water Quality Portal (EPA, USGS, NWQMC): Secchi depth and turbidity results"')
rep(' map:"Every waterfront and springhead listing on one map.',
    ' trails:"Houses for sale within a quarter mile (400 m) of a long bike trail: gravel rail-trails, mountain bike trail systems and paved multi-use paths with 20 or more miles to ride. Priced $100,000 to $750,000, outside cities of more than 200,000 people.",\n'
    ' map:"Every waterfront, springhead and trail-side listing on one map.')
rep('||sm==="heads")mode=sm', '||sm==="heads"||sm==="trails")mode=sm')
rep('if(location.hash==="#springheads")mode="heads";', 'if(location.hash==="#springheads")mode="heads";if(location.hash==="#trails")mode="trails";')
rep('function render(){\n  if(mode==="heads"){renderHeads();return}', 'function render(){\n  if(mode==="trails"){renderTrails();return}\n  if(mode==="heads"){renderHeads();return}')
rep('  document.getElementById("t-heads").setAttribute("aria-pressed",m==="heads");',
    '  document.getElementById("t-heads").setAttribute("aria-pressed",m==="heads");\n  document.getElementById("t-trails").setAttribute("aria-pressed",m==="trails");\n'
    '  {const qi=document.getElementById("q"), ph=m==="trails"?"Find a trail, town or state":"Find a lake, river or state";qi.placeholder=ph;qi.setAttribute("aria-label",ph)}')
rep('  if(m==="heads"){\n', '''  if(m==="trails"){
    const nn=TR.L.filter(x=>x[14]).length, nt=new Set(TR.L.map(x=>x[0])).size;
    document.getElementById("facts").innerHTML=`<span class="chip"><b>${TR.trails.length.toLocaleString()}</b> bike trails of 20+ miles</span><span class="chip"><b>${TR.L.length.toLocaleString()}</b> houses within 400 m of ${nt.toLocaleString()} of them</span>`+(TR.prev?`<span class="chip"><b>${nn}</b> new since ${fmtD(TR.prev)}</span>`:`<span class="chip">First check · new houses are flagged from next month</span>`)+`<span class="chip">Redfin, ${fmtD(TR.date)}</span>`;
    try{localStorage.setItem("secchi-mode",m)}catch(e){}
    render();return;}
  if(m==="heads"){
''')
rep('+(SH.L.length?`<span class="chip"><b>${SH.L.length}</b> springhead listings</span>`:"")',
    '+(SH.L.length?`<span class="chip"><b>${SH.L.length}</b> springhead listings</span>`:"")+(TR.L.length?`<span class="chip"><b>${TR.L.length.toLocaleString()}</b> houses near bike trails</span>`:"")')
rep('"shrecent","showsh"]', '"shrecent","showsh","trtype","trdist","trprice","trall","showtr"]')
rep('document.getElementById("t-heads").addEventListener("click",()=>setMode("heads"));',
    'document.getElementById("t-heads").addEventListener("click",()=>setMode("heads"));\ndocument.getElementById("t-trails").addEventListener("click",()=>setMode("trails"));')
rep('document.querySelectorAll(".shdate").forEach(e=>e.textContent=fmtD(SH.date));',
    'document.querySelectorAll(".shdate").forEach(e=>e.textContent=fmtD(SH.date));\ndocument.querySelectorAll(".trdate").forEach(e=>e.textContent=fmtD(TR.date));')

TRJS = r'''
/* ---------- trails tab ---------- */
const TTN={g:"Gravel",m:"Mountain bike",p:"Paved path",u:"Surface not recorded"};
const trTags=t=>{const tg=t[5]||"";return tg?tg.split(""):[t[4]]};
const miTxt=n=>n>=100?Math.round(n).toLocaleString():n.toFixed(1).replace(/\.0$/,"");
function surfTxt(sh){const W={p:"paved",g:"gravel or crushed stone",m:"dirt singletrack",u:"surface not recorded"};
  return Object.entries(sh).sort((a,b)=>b[1]-a[1]).filter(([k,v])=>v>=.03).map(([k,v])=>`${Math.round(v*100)}% ${W[k]}`).join(" · ")}
function trMapUrl(b){const lat=(b[1]+b[3])/2, lon=(b[0]+b[2])/2, span=Math.max(b[2]-b[0],(b[3]-b[1])*1.3);
  const z=Math.max(8,Math.min(15,Math.round(Math.log2(360/Math.max(span,.005)))));
  return `https://www.openstreetmap.org/#map=${z}/${lat.toFixed(4)}/${lon.toFixed(4)}&layers=Y`}
function trFilter(){
  const q=document.getElementById("q").value.trim().toLowerCase(), s=sel.value, ty=document.getElementById("trtype").value,
    dmax=+document.getElementById("trdist").value, pmax=+document.getElementById("trprice").value, nw=document.getElementById("newonly").checked;
  const tOK=t=>!ty||trTags(t).includes(ty);
  const tQ=t=>!q||(t[0]+" "+t[1].join(" ")+" "+t[7].map(k=>NAMES[k]||k).join(" ")).toLowerCase().includes(q)||t[7].some(k=>k.toLowerCase()===q);
  const Ls=TR.L.filter(x=>{const t=TR.trails[x[0]];return (!s||x[8]===s)&&x[10]<=dmax&&x[1]<=pmax&&(!nw||x[14])&&tOK(t)&&(tQ(t)||(x[6]+" "+x[7]+" "+x[12]).toLowerCase().includes(q))});
  return {q,s,ty,nw,tOK,tQ,Ls}}
function trItem(x){
  const [ti,price,beds,baths,sqft,ac,addr,city,st,dom,dist,path,seg,first,isNew,lat,lon,yr]=x;
  const facts=[beds!=null?beds+" bd":null,baths!=null?baths+" ba":null,sqft?sqft.toLocaleString()+" sq ft":null,ac?ac+" ac":null,yr?"built "+yr:null];
  const z="https://www.zillow.com/homes/"+encodeURIComponent(`${addr}, ${city}, ${st}`).replace(/%20/g,"-")+"_rb/";
  const seen=first&&first!==TR.date?` · on our list since ${fmtD(first)}`:"";
  return `<li${isNew?' class="is-new"':""}><span class="pr">${money(price)}${isNew?' <span class="newb">New</span>':""}</span><span class="ad">${esc(addr)}, ${esc(city)}<small>${facts.filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}${seen}</small></span><span><span class="tier tr" title="Straight-line distance from the house's map point">${dist} m to ${esc(seg)}</span> <a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">Redfin</a> <a href="${z}" target="_blank" rel="noopener">Zillow</a></span></li>`}
function trailRow(ti,L,open){const t=TR.trails[ti], [n,also,mi,rmi,typ,tg,sh,sts,bb]=t;
  const tags=trTags(t).map(k=>`<span class="tt">${TTN[k]}</span>`).join("");
  const len=`${miTxt(mi)} mi of trail`+(rmi?` · ${miTxt(rmi)} mi end to end (${miTxt(rmi*2)} out and back)`:"");
  const nn=L?L.filter(x=>x[14]).length:0;
  return `<li class="row"><span class="rk tr">${miTxt(mi)} mi</span><div class="nm">${esc(n)}${sts.map(k=>`<span class="st-tag">${k}</span>`).join("")}<small>${tags}${len}${also.length?` · also ${also.map(esc).join(", ")}`:""}</small><small>${surfTxt(sh)}</small></div><span></span>
    ${L&&L.length?`<details class="lst"${open?" open":""}><summary>${L.length} house${L.length===1?"":"s"} ${nn?`<span class="cnt new">${nn} new</span>`:""}</summary><ul class="lsts">${L.map(trItem).join("")}</ul></details>`:`<div class="none-l">No houses for sale within 400 m right now that match the filters.</div>`}
    <div class="links"><a href="${trMapUrl(bb)}" target="_blank" rel="noopener">Trail map (CyclOSM)</a></div></li>`}
function renderTrails(){
  const F=trFilter(), all=document.getElementById("trall").checked;
  const byS=new Map();
  F.Ls.forEach(x=>{const k=x[8];if(!byS.has(k))byS.set(k,new Map());const m=byS.get(k);if(!m.has(x[0]))m.set(x[0],[]);m.get(x[0]).push(x)});
  let html="";
  keys.forEach(k=>{if(F.s&&F.s!==k)return; const m=byS.get(k)||new Map();
    let extra=[];
    if(all&&(F.s||F.q)){const has=new Set(m.keys());extra=TR.trails.map((t,i)=>[t,i]).filter(([t,i])=>t[7].includes(k)&&!has.has(i)&&F.tOK(t)&&F.tQ(t)).sort((a,b)=>b[0][2]-a[0][2]).map(([t,i])=>i)}
    if(!m.size&&!extra.length)return;
    const tot=[...m.values()].reduce((a,L)=>a+L.length,0), nn=[...m.values()].reduce((a,L)=>a+L.filter(x=>x[14]).length,0);
    html+=`<article class="state"><div class="shead"><h2>${esc(NAMES[k]||k)}<span class="ab">${k}</span></h2><span class="count">${tot} house${tot===1?"":"s"} · ${m.size} trail${m.size===1?"":"s"}${nn&&!F.nw?` · ${nn} new`:""}</span></div><ol>`;
    [...m.entries()].sort((a,b)=>b[1].length-a[1].length||TR.trails[b[0]][2]-TR.trails[a[0]][2]).forEach(([ti,L])=>{html+=trailRow(ti,L.sort((a,b)=>a[10]-b[10]),F.nw||!!F.s&&m.size<=3)});
    extra.slice(0,LIMIT).forEach(ti=>{html+=trailRow(ti,null,false)});
    html+="</ol></article>"});
  if(!F.s&&!F.q&&all)html=`<p class="empty">Pick a state or search for a trail to list trails with no houses for sale.</p>`+html;
  document.getElementById("list").innerHTML=html||`<p class="empty">${F.nw?"No new houses match.":"No houses near a trail match those filters."}</p>`;
}
function trPopup(x){
  const [ti,price,beds,baths,sqft,ac,addr,city,st,dom,dist,path,seg,first,isNew]=x, t=TR.trails[ti];
  const size=[beds!=null?beds+" bd":null,baths!=null?baths+" ba":null,sqft?sqft.toLocaleString()+" sq ft":null,ac?ac+" ac":null];
  const z="https://www.zillow.com/homes/"+encodeURIComponent(`${addr}, ${city}, ${st}`).replace(/%20/g,"-")+"_rb/";
  return `<div class="pp-price">${money(price)}${isNew?' <span class="newb">New</span>':""}</div>
    <div class="pp-sub">${size.filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}</div>
    <div>${esc(addr)}, ${esc(city)}, ${st}</div>
    <div class="pp-water">${dist} m to <b>${esc(seg)}</b> <span class="pp-sub">(${esc(t[0])} network, ${miTxt(t[2])} mi · ${trTags(t).map(k=>TTN[k].toLowerCase()).join(", ")})</span></div>
    <div class="pp-links"><a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">View listing on Redfin</a><a class="alt" href="${z}" target="_blank" rel="noopener">Find on Zillow</a></div>`;
}
'''
rep("/* ---------- map tab ---------- */", TRJS + "\n/* ---------- map tab ---------- */")
# map: separate cluster layer for trail-side houses
rep("  MAPV.waters=L.layerGroup(); MAPV.heads=L.layerGroup();",
    "  MAPV.waters=L.layerGroup(); MAPV.heads=L.layerGroup();\n"
    "  MAPV.trl=L.markerClusterGroup({showCoverageOnHover:false,maxClusterRadius:42,spiderfyOnMaxZoom:true,chunkedLoading:true,\n"
    "    iconCreateFunction:c=>{const n=c.getChildCount(), s=n<10?30:n<50?36:44; return L.divIcon({html:`<div class=\"mc trc\" style=\"width:${s}px;height:${s}px\">${n}</div>`,className:\"\",iconSize:[s,s]})}});")
rep("m.addLayer(MAPV.heads);", "m.addLayer(MAPV.heads); m.addLayer(MAPV.trl);")
rep("  const shownStates=new Set(L0.map(o=>o.st));",
    """  MAPV.trl.clearLayers(); let nT=0;
  if(document.getElementById("showtr").checked&&pt!=="l"){const tc=tok("--trail");
    const TL=TR.L.filter(x=>{if((s&&x[8]!==s)||(nw&&!x[14]))return false;
      if(q&&!(x[6]+" "+x[7]+" "+x[12]+" "+TR.trails[x[0]][0]+" "+NAMES[x[8]]).toLowerCase().includes(q)&&x[8].toLowerCase()!==q)return false;return true});
    nT=TL.length;
    MAPV.trl.addLayers(TL.map(x=>L.circleMarker([x[15],x[16]],{radius:7,color:surf,weight:1.5,fillColor:tc,fillOpacity:.95}).bindPopup(()=>trPopup(x),{maxWidth:300})));
    if(s)TL.forEach(x=>{const b=STBOX[s]=STBOX[s]||[90,180,-90,-180];b[0]=Math.min(b[0],x[15]);b[1]=Math.min(b[1],x[16]);b[2]=Math.max(b[2],x[15]);b[3]=Math.max(b[3],x[16])});
  }
  const shownStates=new Set(L0.map(o=>o.st));""")
rep('+(nH?` · ${nH} springhead listing${nH===1?"":"s"}`:"");', '+(nH?` · ${nH} springhead listing${nH===1?"":"s"}`:"")+(nT?` · ${nT.toLocaleString()} house${nT===1?"":"s"} near bike trails`:"");')
open(page, "w").write(h)
print("trails tab added")
