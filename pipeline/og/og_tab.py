"""Add the Old Growth tab (private land and homes of 25+ acres near old-growth forests) and its map layers to the page.
Idempotent: re-running only refreshes the OG data. Usage: og_tab.py page.html og.json"""
import json, re, sys
page, ogp = sys.argv[1], sys.argv[2]
h = open(page).read()
OG = json.load(open(ogp))
data = "const OG=" + json.dumps(OG, separators=(",", ":"), ensure_ascii=False) + ";\n"
if 'id="t-og"' in h:
    h = re.sub(r"const OG=\{.*?\};\n", lambda m: data, h, count=1, flags=re.S)
    open(page, "w").write(h); print("old-growth data refreshed"); sys.exit()
def rep(old, new, count=1):
    global h
    assert h.count(old) == count, f"{h.count(old)}x: {old[:120]}"
    h = h.replace(old, new)
# ---- CSS
rep("--trail:#2347c8; --trail-soft:#e3e9fb; --trail-case:#ffffff;", "--trail:#2347c8; --trail-soft:#e3e9fb; --trail-case:#ffffff; --og:#2f5d22; --og-soft:#e5efdd; --og-map:#0b4a14; --og-dot:#ffffff;")
rep("--trail:#7d96ff; --trail-soft:#1c2445; --trail-case:#0b1020;", "--trail:#7d96ff; --trail-soft:#1c2445; --trail-case:#0b1020; --og:#93c97c; --og-soft:#1d2c18; --og-map:#33b249; --og-dot:#0d1a0b;", count=2)
CSS = """
/* old growth */
.tt.og{color:var(--og);background:var(--og-soft)}
.tt.fut{color:var(--muted);background:var(--rule)}
.rk.og{font-family:var(--mono);font-size:12px;color:var(--og);font-weight:500;padding-top:3px}
.tier.og{background:var(--og-soft);color:var(--og);white-space:normal;display:inline-block}
.tier.og.b{background:var(--og);color:var(--surface)}
.ac50{font-weight:700;color:var(--og)}
.lg i.og{background:var(--og-map);border:2px solid var(--og-dot);box-shadow:0 0 0 1px var(--og-map)} .lg i.oga{background:color-mix(in srgb,var(--og-map) 28%,transparent);border:2.5px solid var(--og-map);border-radius:3px;box-shadow:none}
.mc.ogc{background:var(--og-map);border-color:var(--og-dot)}
.ogdesc{display:block;margin-top:3px;color:var(--muted);font-size:12px;line-height:1.35}
"""
rep(".lg i.tr{background:var(--trail)}", ".lg i.tr{background:var(--trail)}" + CSS)
# ---- tab and controls
rep('<button id="t-cities" type="button" aria-pressed="false">Cities</button>',
    '<button id="t-cities" type="button" aria-pressed="false">Cities</button><button id="t-og" type="button" aria-pressed="false">Old Growth</button>')
rep('data-mode="lakes rivers national property springs heads trails cities map"><option value="">All states</option>',
    'data-mode="lakes rivers national property springs heads trails cities og map"><option value="">All states</option>')
rep('<label class="toggle" data-mode="property springs heads trails cities map" hidden><input id="newonly" type="checkbox"> Only new listings</label>',
    '<select id="ogac" aria-label="Acreage" data-mode="og" hidden><option value="25">25 acres and up</option><option value="50">50 acres and up</option><option value="100">100 acres and up</option></select>'
    '<select id="ogdist" aria-label="Distance to the forest" data-mode="og" hidden><option value="8047">Within 5 miles</option><option value="1609">Within 1 mile</option><option value="400">Bordering or inside</option></select>'
    '<select id="ogtype" aria-label="Houses or land" data-mode="og" hidden><option value="">Land and houses</option><option value="l">Land only</option><option value="h">With a house</option></select>'
    '<select id="ogprice" aria-label="Price" data-mode="og" hidden><option value="750000">Up to $750k</option><option value="500000">Up to $500k</option><option value="350000">Up to $350k</option></select>\n'
    '  <label class="toggle" data-mode="property springs heads trails cities og map" hidden><input id="newonly" type="checkbox"> Only new listings</label>\n'
    '  <label class="toggle" data-mode="og" hidden><input id="ogall" type="checkbox"> Also list forests with nothing for sale nearby</label>')
rep('<label class="toggle" data-mode="map" hidden><input id="showtr" type="checkbox" checked> Show houses near bike trails</label>',
    '<label class="toggle" data-mode="map" hidden><input id="showtr" type="checkbox" checked> Show houses near bike trails</label>\n'
    '  <label class="toggle" data-mode="map" hidden><input id="showog" type="checkbox" checked> Show old-growth forests and 25+ acre listings near them</label>')
rep('<span class="lg"><i class="tr"></i>House near a bike trail</span>',
    '<span class="lg"><i class="tr"></i>House near a bike trail</span><span class="lg"><i class="og"></i>25+ acres near old growth</span><span class="lg"><i class="oga"></i>Old-growth forest</span>')
SECTION = """<section class="extra" data-mode="og" hidden>
  <h2>How the old-growth search works</h2>
  <p><b>Forests.</b> Every forest in the Old-Growth Forest Network: forests its members have dedicated as old growth, or as mature forest on its way there, protected from logging and open to the public. A few are marked <i>future old growth</i> where the network says so. Large public old-growth landscapes from Wikipedia's list of old-growth forests that the network doesn't cover are added: Tongass National Forest in Alaska, Olympic, Mount Rainier, North Cascades, Yosemite, Sequoia, Kings Canyon, Lassen, Crater Lake and the Great Smokies national parks, the Boundary Waters and other wilderness areas, and several refuges. Acreage is what the network's description gives, so it may be the old growth or the whole forest.</p>
  <p><b>Shaded areas.</b> Where a forest lies in a park, wilderness, refuge or preserve with an official boundary (National Map and Census landmark boundaries), that boundary is shaded. Otherwise a circle the size of the stated acreage is drawn at the network's coordinates and marked approximate; the old growth itself may sit elsewhere in the property.</p>
  <p><b>Property.</b> These forests are public or protected, so the search looks for private land and homes for sale around them: houses and land on Redfin of <b>25 acres or more</b> (50 or more in bold), priced $100,000 to $750,000, collected on <span class="ogdate"></span>, within 5 miles of a forest's edge. <b>Bordering or inside</b> means within 400 m of the edge, which includes private inholdings inside a park or national forest boundary. Distances are straight lines from the listing's map point; check the plat and access before relying on them. A creek or pond is flagged when a stream or pond on the Census water maps likely crosses or touches the lot (the lot taken as a circle of its acreage around the map point), and every listing has a satellite link.</p>
</section>

<section class="extra" data-mode="map" hidden>"""
rep('<section class="extra" data-mode="map" hidden>', SECTION)
# ---- JS
rep("const SRC=[", data + "const SRC=[")
rep(' ["Water Quality Portal (EPA, USGS, NWQMC): Secchi depth and turbidity results"',
    ' ["Old-Growth Forest Network, dedicated forests (map export: names, counties, descriptions, coordinates)","https://www.oldgrowthforest.net/network-forests"],\n'
    ' ["Wikipedia, List of old-growth forests (United States)","https://en.wikipedia.org/wiki/List_of_old-growth_forests"],\n'
    ' ["USGS The National Map, governmental unit boundaries (national parks, monuments, wilderness, wildlife refuges, national forests)","https://carto.nationalmap.gov/arcgis/rest/services/govunits/MapServer"],\n'
    ' ["U.S. Census Bureau, TIGER/Line 2024 area landmarks (state and local parks, preserves)","https://www2.census.gov/geo/tiger/TIGER2024/AREALM/"],\n'
    ' ["Water Quality Portal (EPA, USGS, NWQMC): Secchi depth and turbidity results"')
rep(' map:"Every', ' og:"Private land and homes of 25 acres or more, priced $100,000 to $750,000, within 5 miles of an old-growth forest: the Old-Growth Forest Network\'s dedicated forests and the big public old-growth landscapes such as Tongass, Olympic and the Redwoods. Bordering parcels and inholdings first.",\n map:"Every')
rep('||sm==="heads"||sm==="trails"||sm==="cities")mode=sm', '||sm==="heads"||sm==="trails"||sm==="cities"||sm==="og")mode=sm')
rep('if(location.hash==="#cities")mode="cities";', 'if(location.hash==="#cities")mode="cities";if(location.hash==="#oldgrowth")mode="og";')
rep('function render(){\n  if(mode==="cities"){renderCities();return}', 'function render(){\n  if(mode==="og"){renderOG();return}\n  if(mode==="cities"){renderCities();return}')
rep('  document.getElementById("t-trails").setAttribute("aria-pressed",m==="trails");',
    '  document.getElementById("t-trails").setAttribute("aria-pressed",m==="trails");\n  document.getElementById("t-og").setAttribute("aria-pressed",m==="og");')
rep('ph=m==="trails"?"Find a trail, town or state"', 'ph=m==="og"?"Find a forest, town or state":m==="trails"?"Find a trail, town or state"')
rep('  if(m==="trails"){\n', '''  if(m==="og"){
    const nn=OG.L.filter(x=>x[14]).length, n50=OG.L.filter(x=>x[6]>=50).length, nb=OG.L.filter(x=>x[11]<=400).length, nf=new Set(OG.L.map(x=>x[0])).size;
    document.getElementById("facts").innerHTML=`<span class="chip"><b>${OG.S.length}</b> old-growth forests</span><span class="chip"><b>${OG.L.length}</b> listings of 25+ acres near ${nf} of them</span><span class="chip"><b>${n50}</b> of 50+ acres</span><span class="chip"><b>${nb}</b> bordering or inside</span>`+(OG.first?`<span class="chip">First check · new listings are flagged from the next refresh</span>`:`<span class="chip"><b>${nn}</b> new since ${fmtD(OG.prev)}</span>`)+`<span class="chip">Redfin, ${fmtD(OG.date)}</span>`;
    try{localStorage.setItem("secchi-mode",m)}catch(e){}
    render();return;}
  if(m==="trails"){
''')
rep('"showtr","trwat","ctboth","showct"]', '"showtr","trwat","ctboth","showct","ogac","ogdist","ogtype","ogprice","ogall","showog"]')
rep('document.getElementById("t-trails").addEventListener("click",()=>setMode("trails"));',
    'document.getElementById("t-trails").addEventListener("click",()=>setMode("trails"));\ndocument.getElementById("t-og").addEventListener("click",()=>setMode("og"));')
rep('document.querySelectorAll(".trdate").forEach(e=>e.textContent=fmtD(TR.date));',
    'document.querySelectorAll(".trdate").forEach(e=>e.textContent=fmtD(TR.date));\ndocument.querySelectorAll(".ogdate").forEach(e=>e.textContent=fmtD(OG.date));')
OGJS = r'''
/* ---------- old growth tab ---------- */
const ogMi=m=>m<=400?"Borders the forest or inside it":`${(m/1609.34).toFixed(m<1609?2:1)} mi from the forest's edge`;
const ogAc=a=>a>=100?Math.round(a).toLocaleString():a.toFixed(1).replace(/\.0$/,"");
function ogFilter(){
  const q=document.getElementById("q").value.trim().toLowerCase(), s=sel.value, amin=+document.getElementById("ogac").value,
    dmax=+document.getElementById("ogdist").value, ty=document.getElementById("ogtype").value, pmax=+document.getElementById("ogprice").value,
    nw=document.getElementById("newonly").checked;
  const fQ=f=>!q||(f[0]+" "+f[2]+" "+(NAMES[f[1]]||"")+" "+(f[11]||"")).toLowerCase().includes(q)||f[1].toLowerCase()===q;
  const Ls=OG.L.filter(x=>{const f=OG.S[x[0]];return (!s||f[1]===s)&&x[6]>=amin&&x[11]<=dmax&&(!ty||x[2]===ty)&&x[1]<=pmax&&(!nw||x[14])&&(fQ(f)||(x[7]+" "+x[8]).toLowerCase().includes(q))});
  return {q,s,nw,fQ,Ls}}
function ogItem(x){
  const [fi,price,ty,beds,baths,sqft,ac,addr,city,st,dom,dist,path,first,isNew,lat,lon,yr]=x;
  const facts=[ty==="l"?"Land":"House",beds!=null&&ty!=="l"?beds+" bd":null,baths!=null&&ty!=="l"?baths+" ba":null,sqft?sqft.toLocaleString()+" sq ft":null,yr?"built "+yr:null];
  const z="https://www.zillow.com/homes/"+encodeURIComponent(`${addr}, ${city}, ${st}`).replace(/%20/g,"-")+"_rb/";
  return `<li${isNew?' class="is-new"':""}><span class="pr">${money(price)}${isNew?' <span class="newb">New</span>':""}</span><span class="ad"><span class="${ac>=50?"ac50":""}">${ogAc(ac)} acres</span> · ${esc(addr)}, ${esc(city)}<small>${facts.filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}</small></span><span><span class="tier og${dist<=400?" b":""}" title="Straight-line distance from the listing's map point to the forest's edge">${ogMi(dist)}</span> <a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">Redfin</a> <a href="${z}" target="_blank" rel="noopener">Zillow</a></span></li>`}
function ogRow(fi,L,open){const f=OG.S[fi], [n,st,cty,ac,fut,src,pg,web,lat,lon,kind,bname]=f;
  const tags=(src==="ogfn"?'<span class="tt og">Network forest</span>':'<span class="tt og">Old-growth landscape</span>')+(fut?'<span class="tt fut">Future old growth</span>':"");
  const where=[cty?`${esc(cty)} Co.`:null, ac?`about ${ogAc(ac)} acres`:null, kind==="boundary"?`area: ${esc(bname)} boundary`:"area approximate"].filter(Boolean).join(" · ");
  const n50=L?L.filter(x=>x[6]>=50).length:0, nb=L?L.filter(x=>x[11]<=400).length:0, nn=L?L.filter(x=>x[14]).length:0;
  const links=[pg?`<a href="${esc(pg)}" target="_blank" rel="noopener">${src==="ogfn"?"Old-Growth Forest Network page":"Wikipedia list"}</a>`:"",web?`<a class="alt" href="${esc(web)}" target="_blank" rel="noopener">Forest's website</a>`:"",
    `<a class="alt" href="https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=13/${lat}/${lon}" target="_blank" rel="noopener">Map</a>`].join("");
  return `<li class="row"><span class="rk og">${L&&L.length?L.length:"·"}</span><div class="nm">${esc(n)}<small>${tags}${where}</small>${f[14]?`<span class="ogdesc">${esc(f[14].length>260?f[14].slice(0,257)+"…":f[14])}</span>`:""}</div><span></span>
    ${L&&L.length?`<details class="lst"${open?" open":""}><summary>${L.length} listing${L.length===1?"":"s"} of 25+ acres${n50?` · <b>${n50}</b> of 50+`:""}${nb?` · ${nb} bordering`:""} ${nn?`<span class="cnt new">${nn} new</span>`:""}</summary><ul class="lsts">${L.map(ogItem).join("")}</ul></details>`:`<div class="none-l">Nothing of 25+ acres for sale nearby right now that matches the filters.</div>`}
    <div class="links">${links}</div></li>`}
function renderOG(){
  const F=ogFilter(), all=document.getElementById("ogall").checked;
  const byS=new Map();
  F.Ls.forEach(x=>{const k=OG.S[x[0]][1];if(!byS.has(k))byS.set(k,new Map());const m=byS.get(k);if(!m.has(x[0]))m.set(x[0],[]);m.get(x[0]).push(x)});
  let html="";
  keys.forEach(k=>{if(F.s&&F.s!==k)return; const m=byS.get(k)||new Map();
    let extra=[];
    if(all){const has=new Set(m.keys());extra=OG.S.map((f,i)=>[f,i]).filter(([f,i])=>f[1]===k&&!has.has(i)&&F.fQ(f)).map(([f,i])=>i)}
    if(!m.size&&!extra.length)return;
    const tot=[...m.values()].reduce((a,L)=>a+L.length,0), nn=[...m.values()].reduce((a,L)=>a+L.filter(x=>x[14]).length,0);
    html+=`<article class="state"><div class="shead"><h2>${esc(NAMES[k]||k)}<span class="ab">${k}</span></h2><span class="count">${tot} listing${tot===1?"":"s"} · ${m.size} forest${m.size===1?"":"s"}${nn&&!F.nw?` · ${nn} new`:""}</span></div><ol>`;
    [...m.entries()].sort((a,b)=>b[1].filter(x=>x[11]<=400).length-a[1].filter(x=>x[11]<=400).length||b[1].length-a[1].length)
      .forEach(([fi,L])=>{html+=ogRow(fi,L.sort((a,b)=>a[11]-b[11]||b[6]-a[6]),F.nw||!!F.s&&m.size<=4)});
    extra.forEach(fi=>{html+=ogRow(fi,null,false)});
    html+="</ol></article>"});
  document.getElementById("list").innerHTML=html||`<p class="empty">${F.nw?"No new listings match.":"No listings of that size near an old-growth forest match those filters."}</p>`;
}
function ogPopup(x){
  const [fi,price,ty,beds,baths,sqft,ac,addr,city,st,dom,dist,path,first,isNew]=x, f=OG.S[fi];
  const size=[ty==="l"?"Land":"House",beds!=null&&ty!=="l"?beds+" bd":null,sqft?sqft.toLocaleString()+" sq ft":null];
  const z="https://www.zillow.com/homes/"+encodeURIComponent(`${addr}, ${city}, ${st}`).replace(/%20/g,"-")+"_rb/";
  return `<div class="pp-price">${money(price)}${isNew?' <span class="newb">New</span>':""}</div>
    <div class="pp-sub"><b>${ogAc(ac)} acres</b> · ${size.filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}</div>
    <div>${esc(addr)}, ${esc(city)}, ${st}</div>
    <div class="pp-water">${ogMi(dist)}: <b>${esc(f[0])}</b>${f[4]?' <span class="pp-sub">(future old growth)</span>':""}</div>
    <div class="pp-links"><a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">View listing on Redfin</a><a class="alt" href="${z}" target="_blank" rel="noopener">Find on Zillow</a></div>`;
}
function ogAreaTip(f){return `<b>${esc(f[0])}</b><br>${f[5]==="ogfn"?"Old-Growth Forest Network forest":"Old-growth landscape"}${f[3]?` · about ${ogAc(f[3])} acres`:""}${f[10]==="approx"?"<br>Area approximate":""}`}
'''
rep("/* ---------- map tab ---------- */", OGJS + "\n/* ---------- map tab ---------- */")
rep("  MAPV.waters=L.layerGroup(); MAPV.heads=L.layerGroup();",
    "  MAPV.waters=L.layerGroup(); MAPV.heads=L.layerGroup(); MAPV.ogA=L.layerGroup();\n"
    "  MAPV.ogl=L.markerClusterGroup({showCoverageOnHover:false,maxClusterRadius:42,spiderfyOnMaxZoom:true,chunkedLoading:true,\n"
    "    iconCreateFunction:c=>{const n=c.getChildCount(), s=n<10?30:n<50?36:44; return L.divIcon({html:`<div class=\"mc ogc\" style=\"width:${s}px;height:${s}px\">${n}</div>`,className:\"\",iconSize:[s,s]})}});")
rep("m.addLayer(MAPV.heads); m.addLayer(MAPV.trl);", "m.addLayer(MAPV.ogA); m.addLayer(MAPV.heads); m.addLayer(MAPV.trl); m.addLayer(MAPV.ogl);")
rep("  const shownStates=new Set(L0.map(o=>o.st));",
    """  MAPV.ogl.clearLayers(); MAPV.ogA.clearLayers(); let nO=0;
  if(document.getElementById("showog").checked){const oc=tok("--og-map"), od=tok("--og-dot");
    OG.S.forEach((f,i)=>{if(s&&f[1]!==s)return; if(q&&!(f[0]+" "+NAMES[f[1]]).toLowerCase().includes(q)&&f[1].toLowerCase()!==q)return;
      const st={color:oc,weight:2.5,opacity:1,fillColor:oc,fillOpacity:.26,dashArray:f[10]==="approx"?"6 4":null};
      const lyr=f[12]?L.polygon(f[12].map(r=>geoDec(r,1e4)),st):L.circle([f[8],f[9]],Object.assign({radius:f[13]||150},st));
      lyr.bindTooltip(()=>ogAreaTip(f),{sticky:true}).addTo(MAPV.ogA)});
    const OL=OG.L.filter(x=>{const f=OG.S[x[0]];if((s&&f[1]!==s)||(nw&&!x[14])||(pt&&x[2]!==pt))return false;
      if(q&&!(x[7]+" "+x[8]+" "+f[0]+" "+NAMES[f[1]]).toLowerCase().includes(q)&&f[1].toLowerCase()!==q)return false;return true});
    nO=OL.length;
    MAPV.ogl.addLayers(OL.map(x=>L.circleMarker([x[15],x[16]],{radius:x[6]>=50?10:8,color:x[2]==="l"?oc:od,weight:x[2]==="l"?3.5:2.5,fillColor:x[2]==="l"?od:oc,fillOpacity:x[2]==="l"?.9:1}).bindPopup(()=>ogPopup(x),{maxWidth:300})));
    if(s)OL.forEach(x=>{const b=STBOX[s]=STBOX[s]||[90,180,-90,-180];b[0]=Math.min(b[0],x[15]);b[1]=Math.min(b[1],x[16]);b[2]=Math.max(b[2],x[15]);b[3]=Math.max(b[3],x[16])});
  }
  const shownStates=new Set(L0.map(o=>o.st));""")
rep('+(nC?` · ${nC.toLocaleString()} city house${nC===1?"":"s"} near bike trails`:"");',
    '+(nC?` · ${nC.toLocaleString()} city house${nC===1?"":"s"} near bike trails`:"")+(nO?` · ${nO} listing${nO===1?"":"s"} of 25+ acres near old growth`:"");')
open(page, "w").write(h)
print("old growth tab added")
