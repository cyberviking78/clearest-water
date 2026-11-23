"""Add the Mountain Lakes tab (houses and land on the shore of montane, subalpine and alpine lakes and ponds in the western
mountains, named or not) and its map layers to the page, after the Rainforest tab. Idempotent: re-running only refreshes the ML
data. Usage: ml_tab.py page.html ml.json"""
import json, re, sys
page, mlp = sys.argv[1], sys.argv[2]
h = open(page).read()
ML = json.load(open(mlp))
data = "const ML=" + json.dumps(ML, separators=(",", ":"), ensure_ascii=False) + ";\n"
if 'id="t-ml"' in h:
    h = re.sub(r"const ML=\{.*?\};\n", lambda m: data, h, count=1, flags=re.S)
    open(page, "w").write(h); print("mountain lake data refreshed"); sys.exit()
def rep(old, new, count=1):
    global h
    assert h.count(old) == count, f"{h.count(old)}x: {old[:120]}"
    h = h.replace(old, new)
rep("--rf:#4a5a00; --rf-soft:#eef2d6; --rf-map:#5a6e00;", "--rf:#4a5a00; --rf-soft:#eef2d6; --rf-map:#5a6e00; --ml:#1a4fb5; --ml-soft:#e2eafb; --ml-map:#c2185b; --ml-water:#1557d6;")
rep("--rf:#c8dc6a; --rf-soft:#262c10; --rf-map:#b8cf3a;", "--rf:#c8dc6a; --rf-soft:#262c10; --rf-map:#b8cf3a; --ml:#8fb3ff; --ml-soft:#18233f; --ml-map:#ff6fa8; --ml-water:#5b8cff;", count=2)
CSS = """
/* mountain lakes */
.rk.ml{font-family:var(--mono);font-size:12px;color:var(--ml);font-weight:500;padding-top:3px}
.tt.ml{color:var(--ml);background:var(--ml-soft)}
.lg i.ml{background:var(--ml-map);border:2px solid var(--og-dot);box-shadow:0 0 0 1px var(--ml-map)} .lg i.mla{background:color-mix(in srgb,var(--ml-water) 60%,transparent);border:2px solid var(--ml-water);border-radius:3px;box-shadow:none}
.mc.mlc{background:var(--ml-map);border-color:var(--og-dot)}
"""
rep(".mc.rfc{background:var(--rf-map);border-color:var(--og-dot)}", ".mc.rfc{background:var(--rf-map);border-color:var(--og-dot)}" + CSS)
rep('<button id="t-rf" type="button" aria-pressed="false">Rainforest</button>',
    '<button id="t-rf" type="button" aria-pressed="false">Rainforest</button><button id="t-ml" type="button" aria-pressed="false">Mountain Lakes</button>')
rep('data-mode="lakes rivers national property springs heads trails cities og rf map"><option value="">All states</option>',
    'data-mode="lakes rivers national property springs heads trails cities og rf ml map"><option value="">All states</option>')
rep('<label class="toggle" data-mode="property springs heads trails cities og rf map" hidden><input id="newonly" type="checkbox"> Only new listings</label>',
    '<select id="mlelev" aria-label="Lake elevation" data-mode="ml" hidden><option value="0">Any elevation</option><option value="5000">5,000 ft and up</option><option value="7000">7,000 ft and up</option><option value="9000">9,000 ft and up</option></select>'
    '<select id="mlnamed" aria-label="Named or unnamed" data-mode="ml" hidden><option value="">Named and unnamed lakes</option><option value="n">Named lakes</option><option value="u">Unnamed lakes and ponds</option></select>'
    '<select id="mltype" aria-label="Houses or land" data-mode="ml" hidden><option value="">Houses and land</option><option value="h">Houses</option><option value="l">Land</option></select>'
    '<select id="mlprice" aria-label="Price" data-mode="ml" hidden><option value="750000">Up to $750k</option><option value="500000">Up to $500k</option><option value="350000">Up to $350k</option></select>\n'
    '  <label class="toggle" data-mode="property springs heads trails cities og rf ml map" hidden><input id="newonly" type="checkbox"> Only new listings</label>\n'
    '  <label class="toggle" data-mode="ml" hidden><input id="mlnear" type="checkbox"> Include listings near the lake (shore within about 250 m of the lot)</label>')
rep('<label class="toggle" data-mode="map" hidden><input id="showrf" type="checkbox"> Show rainforest country and 25+ acre listings in it</label>',
    '<label class="toggle" data-mode="map" hidden><input id="showrf" type="checkbox"> Show rainforest country and 25+ acre listings in it</label>\n'
    '  <label class="toggle" data-mode="map" hidden><input id="showml" type="checkbox" checked> Show mountain lakes with listings on the shore</label>')
rep('<span class="lg"><i class="rfa"></i>Rainforest country</span>',
    '<span class="lg"><i class="rfa"></i>Rainforest country</span><span class="lg"><i class="ml"></i>On a mountain lake</span><span class="lg"><i class="mla"></i>Mountain lake</span>')
SECTION = """<section class="extra" data-mode="ml" hidden>
  <h2>How the mountain lake search works</h2>
  <p><b>Lakes.</b> Every lake and pond of an acre or more in the western mountains, named or not, at montane, subalpine or alpine height: no more than 1,300 m (4,300 ft) below the regional treeline, with the land rising at least 350 m around it. That is roughly 6,700 ft and up in central Colorado, about 6,000 ft around Lake Tahoe, 4,300 ft in the Oregon Cascades, 2,800 ft in the Washington Cascades and 3,200 ft around Glacier. Big lakes (50 acres or more) in deep mountain valleys count too even when they sit lower, when they are at least 1,000 ft up and the land rises 600 m (2,000 ft) within 8 km: Priest, Pend Oreille, Coeur d'Alene, Chelan, Wenatchee, Wallowa and Bear Lake. Elevations are from PRISM's 800 m grid, so a lake's can be off by a couple of hundred feet.</p>
  <p><b>Checked against USGS water maps.</b> Every lake is checked against the USGS National Hydrography Dataset and kept only when it maps the water as a lake or pond that holds water all year. That removes river channels the Census map had drawn as lake area (the South Platte at Hartsel, the Big Thompson at Drake, Clear Creek at Dumont, the Salmon at Stanley), dry and seasonal ponds, marshes and stock tanks, and gives each lake its official USGS name. A lake listed as unnamed has no name on any federal map but is a real, year-round pond.</p>
  <p><b>Clarity.</b> Where the lake has been measured since 2000 (Secchi-disk readings from the Water Quality Portal, USGS, EPA and state agencies), the lake shows its measured clarity, and any lake measured under 15 ft, your cut-off, is left out: Grand Lake (10 ft), Lake Granby, Shadow Mountain, Steamboat, Upper Klamath (3 ft), Canyon Ferry, Koocanusa and others. Most high lakes have never been measured; cold, high lakes in rock and forest basins are usually clear and deep blue, but check each one with its <b>Satellite</b> link. Large man-made reservoirs with no clarity record are left out (Lake Almanor, Big Bear, Ennis, Hebgen, Alder, Lake Roosevelt), and so are lakes wholly inside a national park or wilderness area, where nothing is for sale. That leaves <span class="mlnl"></span> lakes.</p>
  <p><b>Why some states have so few.</b> <span class="mlhi"></span> Where a state has few listings at any price, as in Wyoming and Oregon, its mountain lakes lie almost entirely inside national forest, so the shore is public land. Where most listings are above the range, as at Lake Chelan, price is the barrier.</p>
  <p><b>Property.</b> Houses and land on Redfin priced $100,000 to $750,000, collected on <span class="mldate"></span>, whose lot reaches the lake's shore by the same test as the Property tab (the shore within a lot-sized reach of the listing's map point). Tick <i>Include listings near the lake</i> for those whose shore is within about 250 m more: across the road, a short walk. Listings on lakes the Lakes tab already measures appear there too.</p>
</section>

<section class="extra" data-mode="map" hidden>"""
rep('<section class="extra" data-mode="map" hidden>', SECTION)
rep("const SRC=[", data + "const SRC=[")
rep(' map:"Every', ' ml:"Houses and land on the shore of mountain lakes and ponds in the West, named or not: montane, subalpine and alpine lakes, the cold, clear, sapphire-blue kind, with a satellite link to check the water.",\n map:"Every')
rep('||sm==="og"||sm==="rf")mode=sm', '||sm==="og"||sm==="rf"||sm==="ml")mode=sm')
rep('if(location.hash==="#rainforest")mode="rf";', 'if(location.hash==="#rainforest")mode="rf";if(location.hash==="#mountainlakes")mode="ml";')
rep('  if(mode==="rf"){renderRF();return}', '  if(mode==="rf"){renderRF();return}\n  if(mode==="ml"){renderML();return}')
rep('  document.getElementById("t-rf").setAttribute("aria-pressed",m==="rf");',
    '  document.getElementById("t-rf").setAttribute("aria-pressed",m==="rf");\n  document.getElementById("t-ml").setAttribute("aria-pressed",m==="ml");')
rep('ph=m==="rf"?"Find a town, county or state"', 'ph=m==="ml"?"Find a lake, town or state":m==="rf"?"Find a town, county or state"')
rep('  if(m==="rf"){\n', '''  if(m==="ml"){
    const L0=ML.L.filter(x=>x[18]===0), nn=ML.L.filter(x=>x[14]).length, nu=new Set(L0.filter(x=>!ML.K[x[0]][0]).map(x=>x[0])).size;
    document.getElementById("facts").innerHTML=`<span class="chip"><b>${L0.length}</b> listings on the shore of ${new Set(L0.map(x=>x[0])).size} mountain lakes (${nu} unnamed)</span><span class="chip"><b>${ML.L.length-L0.length}</b> more near a lake</span><span class="chip"><b>${L0.filter(x=>x[2]==="h").length}</b> houses · <b>${L0.filter(x=>x[2]==="l").length}</b> land on the shore</span><span class="chip">${ML.nlakes.toLocaleString()} lakes searched</span>`+(ML.first?`<span class="chip">First check · new listings are flagged from the next refresh</span>`:`<span class="chip"><b>${nn}</b> new since ${fmtD(ML.prev)}</span>`)+`<span class="chip">Redfin, ${fmtD(ML.date)}</span>`;
    try{localStorage.setItem("secchi-mode",m)}catch(e){}
    render();return;}
  if(m==="rf"){
''')
rep('"rftype","rfprice","showrf"]', '"rftype","rfprice","showrf","mlelev","mlnamed","mltype","mlprice","mlnear","showml"]')
rep('document.getElementById("t-rf").addEventListener("click",()=>setMode("rf"));',
    'document.getElementById("t-rf").addEventListener("click",()=>setMode("rf"));\ndocument.getElementById("t-ml").addEventListener("click",()=>setMode("ml"));')
rep('document.querySelectorAll(".rfdate").forEach(e=>e.textContent=fmtD(RF.date));',
    'document.querySelectorAll(".rfdate").forEach(e=>e.textContent=fmtD(RF.date));\ndocument.querySelectorAll(".mldate").forEach(e=>e.textContent=fmtD(ML.date));\ndocument.querySelectorAll(".mlnl").forEach(e=>e.textContent=ML.nlakes.toLocaleString());')
MLJS = r'''
/* ---------- mountain lakes tab ---------- */
const mlName=k=>k[0]?k[0].replace(/\bLk\b/g,"Lake").replace(/\bLks\b/g,"Lakes"):"Unnamed lake";
function mlFilter(){
  const q=document.getElementById("q").value.trim().toLowerCase(), s=sel.value, emin=+document.getElementById("mlelev").value, nm=document.getElementById("mlnamed").value,
    ty=document.getElementById("mltype").value, pmax=+document.getElementById("mlprice").value, nw=document.getElementById("newonly").checked, nr=document.getElementById("mlnear").checked;
  const Ls=ML.L.filter(x=>{const k=ML.K[x[0]];return (nr||x[18]===0)&&(!s||k[1]===s)&&k[3]>=emin&&(!nm||(nm==="n"?!!k[0]:!k[0]))&&(!ty||x[2]===ty)&&x[1]<=pmax&&(!nw||x[14])&&
    (!q||(mlName(k)+" "+x[7]+" "+x[8]+" "+(NAMES[k[1]]||"")).toLowerCase().includes(q)||k[1].toLowerCase()===q)});
  return {s,nw,Ls}}
function mlItem(x){
  const [ki,price,ty,beds,baths,sqft,ac,addr,city,st,dom,dist,path,first,isNew,lat,lon,yr]=x;
  const facts=[ty==="l"?"Land":"House",beds!=null&&ty!=="l"?beds+" bd":null,baths!=null&&ty!=="l"?baths+" ba":null,sqft?sqft.toLocaleString()+" sq ft":null,ac?ac+" acres":null,yr?"built "+yr:null];
  const z="https://www.zillow.com/homes/"+encodeURIComponent(`${addr}, ${city}, ${st}`).replace(/%20/g,"-")+"_rb/";
  return `<li${isNew?' class="is-new"':""}><span class="pr">${money(price)}${isNew?' <span class="newb">New</span>':""}</span><span class="ad">${esc(addr)}, ${esc(city)}<small>${facts.filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}</small></span><span>${x[18]===0?`<span class="tier on" title="The listing's map point is ${dist} m from the shore; the lot reaches it">On the lake</span>`:`<span class="tier near" title="The listing's map point is ${dist} m from the shore">Near the lake · ${dist} m</span>`} <a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">Redfin</a> <a href="${z}" target="_blank" rel="noopener">Zillow</a></span></li>`}
function renderML(){
  const F=mlFilter(), byS=new Map();
  F.Ls.forEach(x=>{const k=ML.K[x[0]][1];if(!byS.has(k))byS.set(k,new Map());const m=byS.get(k);if(!m.has(x[0]))m.set(x[0],[]);m.get(x[0]).push(x)});
  let html="";
  keys.forEach(st=>{const m=byS.get(st); if(!m)return;
    const tot=[...m.values()].reduce((a,L)=>a+L.length,0), nn=[...m.values()].reduce((a,L)=>a+L.filter(x=>x[14]).length,0);
    html+=`<article class="state"><div class="shead"><h2>${esc(NAMES[st]||st)}<span class="ab">${st}</span></h2><span class="count">${tot} listing${tot===1?"":"s"} · ${m.size} lake${m.size===1?"":"s"}${nn&&!F.nw?` · ${nn} new`:""}</span></div><ol>`;
    [...m.entries()].sort((a,b)=>ML.K[b[0]][3]-ML.K[a[0]][3]).forEach(([ki,L])=>{const k=ML.K[ki], nnl=L.filter(x=>x[14]).length, z=k[2]>500?13:k[2]>60?15:17;
      html+=`<li class="row"><span class="rk ml">${k[3].toLocaleString()}<br><small>ft</small></span><div class="nm">${esc(mlName(k))}<small>${k[0]?"":'<span class="tt ml">No name on the map</span>'}${k[2]>=10?Math.round(k[2]).toLocaleString():k[2]} acres · ${k[3].toLocaleString()} ft · near ${esc(L[0][8])}</small></div><span></span>
        <details class="lst"${F.nw||(F.s&&m.size<=6)?" open":""}><summary>${L.length} listing${L.length===1?"":"s"}${L.some(x=>x[18])?` · ${L.filter(x=>x[18]===0).length} on the shore`:" on the shore"} ${nnl?`<span class="cnt new">${nnl} new</span>`:""}</summary><ul class="lsts">${L.sort((a,b)=>a[18]-b[18]||a[1]-b[1]).map(mlItem).join("")}</ul></details>
        <div class="links"><a href="${satUrl(k[4],k[5],z)}" target="_blank" rel="noopener">Satellite view of the water</a><a class="alt" href="https://www.openstreetmap.org/?mlat=${k[4]}&mlon=${k[5]}#map=${z}/${k[4]}/${k[5]}" target="_blank" rel="noopener">Map</a></div></li>`});
    html+="</ol></article>"});
  document.getElementById("list").innerHTML=html||`<p class="empty">${F.nw?"No new listings match.":"No mountain-lake listings match those filters."}</p>`;
}
function mlPopup(x){
  const [ki,price,ty,beds,baths,sqft,ac,addr,city,st,dom,dist,path,first,isNew,lat,lon]=x, k=ML.K[ki];
  const z="https://www.zillow.com/homes/"+encodeURIComponent(`${addr}, ${city}, ${st}`).replace(/%20/g,"-")+"_rb/";
  return `<div class="pp-price">${money(price)}${isNew?' <span class="newb">New</span>':""}</div>
    <div class="pp-sub">${[ty==="l"?"Land":"House",beds!=null&&ty!=="l"?beds+" bd":null,sqft?sqft.toLocaleString()+" sq ft":null,ac?ac+" acres":null].filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}</div>
    <div>${esc(addr)}, ${esc(city)}, ${st}</div>
    <div class="pp-water">On <b>${esc(mlName(k))}</b> · ${k[3].toLocaleString()} ft · ${k[2]>=10?Math.round(k[2]):k[2]} acres</div>
    <div class="pp-links"><a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">View listing on Redfin</a><a class="alt" href="${z}" target="_blank" rel="noopener">Find on Zillow</a><a class="alt" href="${satUrl(k[4],k[5],k[2]>500?13:k[2]>60?15:17)}" target="_blank" rel="noopener">Satellite</a></div>`;
}
'''
rep("/* ---------- map tab ---------- */", MLJS + "\n/* ---------- map tab ---------- */")
rep("MAPV.rfA=L.layerGroup();", "MAPV.rfA=L.layerGroup(); MAPV.mlA=L.layerGroup();")
i = h.index("MAPV.rfl=L.markerClusterGroup("); j = h.index("});", h.index('class="mc rfc"', i)) + 3
h = h[:j] + ('\n  MAPV.mll=L.markerClusterGroup({showCoverageOnHover:false,maxClusterRadius:42,spiderfyOnMaxZoom:true,chunkedLoading:true,\n'
             '    iconCreateFunction:c=>{const n=c.getChildCount(), s=n<10?30:n<50?36:44; return L.divIcon({html:`<div class="mc mlc" style="width:${s}px;height:${s}px">${n}</div>`,className:"",iconSize:[s,s]})}});') + h[j:]
rep("m.addLayer(MAPV.ogl); m.addLayer(MAPV.rfl);", "m.addLayer(MAPV.mlA); m.addLayer(MAPV.ogl); m.addLayer(MAPV.rfl); m.addLayer(MAPV.mll);")
rep("  const shownStates=new Set(L0.map(o=>o.st));",
    """  MAPV.mll.clearLayers(); MAPV.mlA.clearLayers(); let nM=0;
  if(document.getElementById("showml").checked){const mc=tok("--ml-map"), mw=tok("--ml-water"), od=tok("--og-dot");
    const ML2=ML.L.filter(x=>{const k=ML.K[x[0]];if(x[18]!==0)return false;if((s&&k[1]!==s)||(nw&&!x[14])||(pt&&x[2]!==pt))return false;
      if(q&&!(mlName(k)+" "+x[7]+" "+x[8]+" "+NAMES[k[1]]).toLowerCase().includes(q)&&k[1].toLowerCase()!==q)return false;return true});
    nM=ML2.length;
    [...new Set(ML2.map(x=>x[0]))].forEach(ki=>{const k=ML.K[ki];
      L.polygon(k[6].map(r=>geoDec(r,1e5)),{color:mw,weight:2,opacity:1,fillColor:mw,fillOpacity:.6}).bindTooltip(`<b>${esc(mlName(k))}</b><br>${k[3].toLocaleString()} ft · ${k[2]} acres`,{sticky:true}).addTo(MAPV.mlA)});
    MAPV.mll.addLayers(ML2.map(x=>L.circleMarker([x[15],x[16]],{radius:8,color:x[2]==="l"?mc:od,weight:x[2]==="l"?3.5:2.5,fillColor:x[2]==="l"?od:mc,fillOpacity:x[2]==="l"?.9:1}).bindPopup(()=>mlPopup(x),{maxWidth:300})));
    if(s)ML2.forEach(x=>{const b=STBOX[s]=STBOX[s]||[90,180,-90,-180];b[0]=Math.min(b[0],x[15]);b[1]=Math.min(b[1],x[16]);b[2]=Math.max(b[2],x[15]);b[3]=Math.max(b[3],x[16])});
  }
  const shownStates=new Set(L0.map(o=>o.st));""")
rep('+(nR?` · ${nR} of 25+ acres in rainforest country`:"");',
    '+(nR?` · ${nR} of 25+ acres in rainforest country`:"")+(nM?` · ${nM} on mountain lakes`:"");')
open(page, "w").write(h)
print("mountain lakes tab added")
