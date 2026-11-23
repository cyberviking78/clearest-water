"""Add the Rainforest tab (land and homes of 25+ acres in temperate rainforest country) and its map layers to the page, after the
Old Growth tab. Also adds creek/pond badges and a satellite link to the Old Growth listings. Idempotent: re-running only
refreshes the RF data. Usage: rf_tab.py page.html rain.json zones.geojson"""
import json, re, sys
page, rfp, zp = sys.argv[1], sys.argv[2], sys.argv[3]
h = open(page).read()
RF = json.load(open(rfp))
data = "const RF=" + json.dumps(RF, separators=(",", ":"), ensure_ascii=False) + ";\n"
if 'id="t-rf"' in h:
    h = re.sub(r"const RF=\{.*?\};\n", lambda m: data, h, count=1, flags=re.S)
    open(page, "w").write(h); print("rainforest data refreshed"); sys.exit()
# zone shapes for the map, delta-encoded lon/lat at 1e3 (about 100 m; they are 800 m climate cells anyway)
def enc(coords):
    out = []; px = py = 0
    for x, y in coords:
        x, y = round(x * 1e3), round(y * 1e3)
        if (x, y) == (px, py) and out: continue
        out += [x - px, y - py]; px, py = x, y
    return out
ZN = {}
for f in json.load(open(zp))["features"]:
    g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    ZN[f["properties"]["kind"]] = [enc(p[0]) for p in polys]
zdata = "const RFZ=" + json.dumps(ZN, separators=(",", ":")) + ";\n"
def rep(old, new, count=1):
    global h
    assert h.count(old) == count, f"{h.count(old)}x: {old[:120]}"
    h = h.replace(old, new)
# ---- CSS
rep("--og:#2f5d22; --og-soft:#e5efdd; --og-map:#0b4a14; --og-dot:#ffffff;",
    "--og:#2f5d22; --og-soft:#e5efdd; --og-map:#0b4a14; --og-dot:#ffffff; --rf:#4a5a00; --rf-soft:#eef2d6; --rf-map:#5a6e00;")
rep("--og:#93c97c; --og-soft:#1d2c18; --og-map:#33b249; --og-dot:#0d1a0b;",
    "--og:#93c97c; --og-soft:#1d2c18; --og-map:#33b249; --og-dot:#0d1a0b; --rf:#c8dc6a; --rf-soft:#262c10; --rf-map:#b8cf3a;", count=2)
CSS = """
/* rainforest */
.tt.rf{color:var(--rf);background:var(--rf-soft)}
.rk.rf{font-family:var(--mono);font-size:12px;color:var(--rf);font-weight:500;padding-top:3px}
.ac50r{font-weight:700;color:var(--rf)}
.wb{display:inline-block;font-size:11.5px;font-weight:600;border-radius:4px;padding:0 6px;margin:2px 4px 0 0;color:var(--lake);background:var(--lake-soft)}
.lg i.rf{background:var(--rf-map);border:2px solid var(--og-dot);box-shadow:0 0 0 1px var(--rf-map)} .lg i.rfa{background:color-mix(in srgb,var(--rf-map) 22%,transparent);border:1.5px dashed var(--rf-map);border-radius:3px;box-shadow:none}
.mc.rfc{background:var(--rf-map);border-color:var(--og-dot)}
.rfsub{display:block;color:var(--muted);font-size:12px;margin-top:2px}
"""
rep(".mc.ogc{background:var(--og-map);border-color:var(--og-dot)}", ".mc.ogc{background:var(--og-map);border-color:var(--og-dot)}" + CSS)
# ---- tab and controls
rep('<button id="t-og" type="button" aria-pressed="false">Old Growth</button>',
    '<button id="t-og" type="button" aria-pressed="false">Old Growth</button><button id="t-rf" type="button" aria-pressed="false">Rainforest</button>')
rep('data-mode="lakes rivers national property springs heads trails cities og map"><option value="">All states</option>',
    'data-mode="lakes rivers national property springs heads trails cities og rf map"><option value="">All states</option>')
rep('<label class="toggle" data-mode="property springs heads trails cities og map" hidden><input id="newonly" type="checkbox"> Only new listings</label>',
    '<select id="rfzone" aria-label="Kind of rainforest" data-mode="rf" hidden><option value="">All rainforest country</option><option value="0">Pacific and Appalachian rainforest</option><option value="1">Redwood fog belt</option><option value="2">Inland cedar-hemlock rainforest</option><option value="3">Appalachian cloud forest</option><option value="4">Downeast Maine fog coast</option><option value="5">Southeast Alaska</option></select>'
    '<select id="rfac" aria-label="Acreage" data-mode="rf" hidden><option value="25">25 acres and up</option><option value="50">50 acres and up</option><option value="100">100 acres and up</option></select>'
    '<select id="rfwater" aria-label="Water on the lot" data-mode="rf" hidden><option value="">With or without water</option><option value="any">Creek or pond on the lot</option><option value="c">Creek on the lot</option><option value="p">Pond on the lot</option></select>'
    '<select id="rftype" aria-label="Houses or land" data-mode="rf" hidden><option value="">Land and houses</option><option value="l">Land only</option><option value="h">With a house</option></select>'
    '<select id="rfprice" aria-label="Price" data-mode="rf" hidden><option value="750000">Up to $750k</option><option value="500000">Up to $500k</option><option value="350000">Up to $350k</option></select>\n'
    '  <label class="toggle" data-mode="property springs heads trails cities og rf map" hidden><input id="newonly" type="checkbox"> Only new listings</label>')
rep('<label class="toggle" data-mode="map" hidden><input id="showog" type="checkbox" checked> Show old-growth forests and 25+ acre listings near them</label>',
    '<label class="toggle" data-mode="map" hidden><input id="showog" type="checkbox" checked> Show old-growth forests and 25+ acre listings near them</label>\n'
    '  <label class="toggle" data-mode="map" hidden><input id="showrf" type="checkbox"> Show rainforest country and 25+ acre listings in it</label>')
rep('<span class="lg"><i class="oga"></i>Old-growth forest</span>',
    '<span class="lg"><i class="oga"></i>Old-growth forest</span><span class="lg"><i class="rf"></i>25+ acres in rainforest country</span><span class="lg"><i class="rfa"></i>Rainforest country</span>')
SECTION = """<section class="extra" data-mode="rf" hidden>
  <h2>How the rainforest search works</h2>
  <p><b>Rainforest country.</b> The misty, big-tree forests with ferns, moss and wildflowers are temperate rainforests and cloud forests, and they follow the climate: lots of rain or fog, mild temperatures. The areas are drawn from PRISM's 30-year climate normals (Oregon State University; 800 m cells):</p>
  <ul>
    <li><b>Pacific and Appalachian rainforest:</b> 70 inches of rain or more a year and a mild average temperature (5 to 15 °C). That covers the Olympic Peninsula and the Coast Range, the west slope of the Cascades, the Klamath-Siskiyou, the wettest north Sierra, and in the East the Blue Ridge escarpment around Highlands, Cashiers and Brevard and the Smokies.</li>
    <li><b>Redwood fog belt:</b> the coast redwood's range, within 40 km of the Pacific from Big Sur to Oregon, where summer fog makes up for 40+ inches of rain.</li>
    <li><b>Inland cedar-hemlock rainforest:</b> the wet belt of north Idaho, northeast Washington and northwest Montana (40+ inches, cool), home of giant western red cedar groves.</li>
    <li><b>Appalachian cloud forest:</b> the spruce-fir and northern hardwood highlands that sit in the clouds, from the Smokies and Roan to West Virginia's Allegheny highlands, the Adirondacks, the Green Mountains and the White Mountains (50+ inches; above about 4,500 ft in the south, 3,800 ft in West Virginia and 2,500 ft in the North).</li>
    <li><b>Downeast Maine fog coast:</b> the boreal spruce-fir fog forest within 15 km of the sea east of Penobscot Bay.</li>
    <li><b>Southeast Alaska:</b> the Tongass rainforest and the towns and private land in and around it.</li>
  </ul>
  <p><b>Property.</b> Houses and land on Redfin of <b>25 acres or more</b> (50 or more in bold), priced $100,000 to $750,000, collected on <span class="rfdate"></span>, whose map point is inside rainforest country. Each listing shows its yearly rain and elevation (PRISM), the nearest old-growth forest within 10 miles, and whether a creek or pond likely crosses or touches the lot (Census TIGER water maps, with the lot taken as a circle of its acreage around the map point; check the plat). Rain is a guide to the forest, not a promise: a clear-cut, a pasture or a young plantation gets the same rain, so open the satellite view.</p>
</section>

<section class="extra" data-mode="map" hidden>"""
rep('<section class="extra" data-mode="map" hidden>', SECTION)
# ---- JS
rep("const SRC=[", data + zdata + "const SRC=[")
rep(' ["Water Quality Portal (EPA, USGS, NWQMC): Secchi depth and turbidity results"',
    ' ["PRISM Climate Group, Oregon State University: 30-year normals of annual precipitation (1991-2020, 800 m), mean temperature (1981-2010) and elevation","https://prism.oregonstate.edu/normals/"],\n'
    ' ["U.S. Census Bureau, TIGER/Line 2024 area and linear water (lakes, ponds, streams; creek and pond flags, mountain lakes)","https://www2.census.gov/geo/tiger/TIGER2024/"],\n'
    ' ["Water Quality Portal (EPA, USGS, NWQMC): Secchi depth and turbidity results"')
rep(' map:"Every', ' rf:"Land and homes of 25 acres or more, priced $100,000 to $750,000, in temperate rainforest country: the misty big-tree forests of the Pacific coast, the redwood fog belt, north Idaho\'s cedar groves, the southern Appalachians, the Appalachian cloud forests, the Downeast Maine fog coast and Southeast Alaska. Wettest first, with creeks and ponds flagged.",\n map:"Every')
rep('||sm==="cities"||sm==="og")mode=sm', '||sm==="cities"||sm==="og"||sm==="rf")mode=sm')
rep('if(location.hash==="#oldgrowth")mode="og";', 'if(location.hash==="#oldgrowth")mode="og";if(location.hash==="#rainforest")mode="rf";')
rep('  if(mode==="og"){renderOG();return}', '  if(mode==="og"){renderOG();return}\n  if(mode==="rf"){renderRF();return}')
rep('  document.getElementById("t-og").setAttribute("aria-pressed",m==="og");',
    '  document.getElementById("t-og").setAttribute("aria-pressed",m==="og");\n  document.getElementById("t-rf").setAttribute("aria-pressed",m==="rf");')
rep('ph=m==="og"?"Find a forest, town or state"', 'ph=m==="rf"?"Find a town, county or state":m==="og"?"Find a forest, town or state"')
rep('  if(m==="og"){\n', '''  if(m==="rf"){
    const nn=RF.L.filter(x=>x[15]).length, n50=RF.L.filter(x=>x[6]>=50).length, nc=RF.L.filter(x=>x[21]!=null).length, np=RF.L.filter(x=>x[22]).length;
    document.getElementById("facts").innerHTML=`<span class="chip"><b>${RF.L.length}</b> listings of 25+ acres in rainforest country</span><span class="chip"><b>${n50}</b> of 50+ acres</span><span class="chip"><b>${nc}</b> with a creek</span><span class="chip"><b>${np}</b> with a pond</span>`+(RF.first?`<span class="chip">First check · new listings are flagged from the next refresh</span>`:`<span class="chip"><b>${nn}</b> new since ${fmtD(RF.prev)}</span>`)+`<span class="chip">Redfin, ${fmtD(RF.date)}</span>`;
    try{localStorage.setItem("secchi-mode",m)}catch(e){}
    render();return;}
  if(m==="og"){
''')
rep('"ogall","showog"]', '"ogall","showog","rfzone","rfac","rfwater","rftype","rfprice","showrf"]')
rep('document.getElementById("t-og").addEventListener("click",()=>setMode("og"));',
    'document.getElementById("t-og").addEventListener("click",()=>setMode("og"));\ndocument.getElementById("t-rf").addEventListener("click",()=>setMode("rf"));')
rep('document.querySelectorAll(".ogdate").forEach(e=>e.textContent=fmtD(OG.date));',
    'document.querySelectorAll(".ogdate").forEach(e=>e.textContent=fmtD(OG.date));\ndocument.querySelectorAll(".rfdate").forEach(e=>e.textContent=fmtD(RF.date));')
RFJS = r'''
/* ---------- rainforest tab ---------- */
const RFK=["Pacific and Appalachian rainforest","Redwood fog belt","Inland cedar-hemlock rainforest","Appalachian cloud forest","Downeast Maine fog coast","Southeast Alaska rainforest"];
function satUrl(lat,lon,z){return `https://www.google.com/maps/@?api=1&map_action=map&center=${lat},${lon}&zoom=${z||16}&basemap=satellite`}
function wildBadges(creek,pond){return (creek!=null?`<span class="wb">${creek?esc(creek)+" on the lot":"Creek on the lot"}</span>`:"")+(pond?`<span class="wb">Pond or lake on the lot · ${pond>=10?Math.round(pond):pond} ac</span>`:"")}
function rfFilter(){
  const q=document.getElementById("q").value.trim().toLowerCase(), s=sel.value, z=document.getElementById("rfzone").value, amin=+document.getElementById("rfac").value,
    wt=document.getElementById("rfwater").value, ty=document.getElementById("rftype").value, pmax=+document.getElementById("rfprice").value, nw=document.getElementById("newonly").checked;
  const Ls=RF.L.filter(x=>(!s||x[9]===s)&&(z===""||x[0]===+z)&&x[6]>=amin&&(!ty||x[2]===ty)&&x[1]<=pmax&&(!nw||x[15])&&
    (!wt||(wt==="c"&&x[21]!=null)||(wt==="p"&&x[22])||(wt==="any"&&(x[21]!=null||x[22])))&&
    (!q||(x[7]+" "+x[8]+" "+(NAMES[x[9]]||"")+" "+RFK[x[0]]+" "+(x[19]!=null&&RF.og[x[19]]?RF.og[x[19]][0]:"")).toLowerCase().includes(q)||x[9].toLowerCase()===q));
  return {s,nw,Ls}}
function rfItem(x){
  const [k,price,ty,beds,baths,sqft,ac,addr,city,st,dom,rain,elev,path,first,isNew,lat,lon,yr,ogi,ogd,creek,pond]=x;
  const facts=[ty==="l"?"Land":"House",beds!=null&&ty!=="l"?beds+" bd":null,baths!=null&&ty!=="l"?baths+" ba":null,sqft?sqft.toLocaleString()+" sq ft":null,yr?"built "+yr:null];
  const z="https://www.zillow.com/homes/"+encodeURIComponent(`${addr}, ${city}, ${st}`).replace(/%20/g,"-")+"_rb/";
  const clim=[rain!=null?`${rain} in of rain a year`:null, elev!=null?`${elev.toLocaleString()} ft`:null].filter(Boolean).join(" · ");
  const og=ogi!=null&&RF.og[ogi]?`${ogd<=400?"Borders":(ogd/1609.34).toFixed(1)+" mi from"} ${esc(RF.og[ogi][0])} (old growth)`:"";
  return `<li${isNew?' class="is-new"':""}><span class="pr">${money(price)}${isNew?' <span class="newb">New</span>':""}</span><span class="ad"><span class="${ac>=50?"ac50r":""}">${ogAc(ac)} acres</span> · ${esc(addr)}, ${esc(city)}<small>${facts.filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}</small><span class="rfsub"><span class="tt rf">${RFK[k]}</span>${clim}${og?" · "+og:""}</span>${wildBadges(creek,pond)}</span><span><a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">Redfin</a> <a href="${z}" target="_blank" rel="noopener">Zillow</a> <a href="${satUrl(lat,lon)}" target="_blank" rel="noopener">Satellite</a></span></li>`}
function renderRF(){
  const F=rfFilter(), byS=new Map();
  F.Ls.forEach(x=>{if(!byS.has(x[9]))byS.set(x[9],[]);byS.get(x[9]).push(x)});
  let html="";
  keys.forEach(k=>{const L=byS.get(k); if(!L)return;
    const nn=L.filter(x=>x[15]).length, n50=L.filter(x=>x[6]>=50).length;
    html+=`<article class="state"><div class="shead"><h2>${esc(NAMES[k]||k)}<span class="ab">${k}</span></h2><span class="count">${L.length} listing${L.length===1?"":"s"}${n50?` · ${n50} of 50+ acres`:""}${nn&&!F.nw?` · ${nn} new`:""}</span></div><ol>`;
    [...new Set(L.map(x=>x[0]))].sort().forEach(zk=>{const Z=L.filter(x=>x[0]===zk).sort((a,b)=>(b[11]||0)-(a[11]||0)||b[6]-a[6]);
      const z50=Z.filter(x=>x[6]>=50).length, zn=Z.filter(x=>x[15]).length, zc=Z.filter(x=>x[21]!=null).length, zp=Z.filter(x=>x[22]).length, rs=Z.map(x=>x[11]).filter(v=>v!=null);
      html+=`<li class="row"><span class="rk rf">${Z.length}</span><div class="nm">${RFK[zk]}<small>${rs.length?`${Math.min(...rs)}–${Math.max(...rs)} in of rain a year · wettest first`:"Largest first"}${zc?` · ${zc} with a creek`:""}${zp?` · ${zp} with a pond`:""}</small></div><span></span>
      <details class="lst"${F.nw||F.s?" open":""}><summary>${Z.length} listing${Z.length===1?"":"s"} of 25+ acres${z50?` · <b>${z50}</b> of 50+`:""} ${zn?`<span class="cnt new">${zn} new</span>`:""}</summary><ul class="lsts">${Z.map(rfItem).join("")}</ul></details></li>`});
    html+="</ol></article>"});
  document.getElementById("list").innerHTML=html||`<p class="empty">${F.nw?"No new listings match.":"No listings of that size in rainforest country match those filters."}</p>`;
}
function rfPopup(x){
  const [k,price,ty,beds,baths,sqft,ac,addr,city,st,dom,rain,elev,path,first,isNew,lat,lon,yr,ogi,ogd,creek,pond]=x;
  const z="https://www.zillow.com/homes/"+encodeURIComponent(`${addr}, ${city}, ${st}`).replace(/%20/g,"-")+"_rb/";
  return `<div class="pp-price">${money(price)}${isNew?' <span class="newb">New</span>':""}</div>
    <div class="pp-sub"><b>${ogAc(ac)} acres</b> · ${[ty==="l"?"Land":"House",beds!=null&&ty!=="l"?beds+" bd":null,sqft?sqft.toLocaleString()+" sq ft":null].filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}</div>
    <div>${esc(addr)}, ${esc(city)}, ${st}</div>
    <div class="pp-water"><b>${RFK[k]}</b>${rain!=null?` · ${rain} in of rain`:""}${elev!=null?` · ${elev.toLocaleString()} ft`:""}</div>
    ${ogi!=null&&RF.og[ogi]?`<div class="pp-sub">${ogd<=400?"Borders":(ogd/1609.34).toFixed(1)+" mi from"} ${esc(RF.og[ogi][0])} (old growth)</div>`:""}${wildBadges(creek,pond)}
    <div class="pp-links"><a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">View listing on Redfin</a><a class="alt" href="${z}" target="_blank" rel="noopener">Find on Zillow</a><a class="alt" href="${satUrl(lat,lon)}" target="_blank" rel="noopener">Satellite</a></div>`;
}
'''
rep("/* ---------- map tab ---------- */", RFJS + "\n/* ---------- map tab ---------- */")
# Old Growth listings: creek/pond badges (OG rows 18 and 19) and a satellite link
rep('''<small>${facts.filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}</small></span><span><span class="tier og${dist<=400?" b":""}"''',
    '''<small>${facts.filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}</small>${wildBadges(x[18],x[19])}</span><span><span class="tier og${dist<=400?" b":""}"''')
rep('''<a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">Redfin</a> <a href="${z}" target="_blank" rel="noopener">Zillow</a></span></li>`}
function ogRow''', '''<a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">Redfin</a> <a href="${z}" target="_blank" rel="noopener">Zillow</a> <a href="${satUrl(lat,lon)}" target="_blank" rel="noopener">Satellite</a></span></li>`}
function ogRow''')
# ---- map layers
rep("MAPV.ogA=L.layerGroup();", "MAPV.ogA=L.layerGroup(); MAPV.rfA=L.layerGroup();")
i = h.index("MAPV.ogl=L.markerClusterGroup("); j = h.index("});", h.index('class="mc ogc"', i)) + 3
h = h[:j] + ('\n  MAPV.rfl=L.markerClusterGroup({showCoverageOnHover:false,maxClusterRadius:42,spiderfyOnMaxZoom:true,chunkedLoading:true,\n'
             '    iconCreateFunction:c=>{const n=c.getChildCount(), s=n<10?30:n<50?36:44; return L.divIcon({html:`<div class="mc rfc" style="width:${s}px;height:${s}px">${n}</div>`,className:"",iconSize:[s,s]})}});') + h[j:]
rep("m.addLayer(MAPV.ogA); m.addLayer(MAPV.heads); m.addLayer(MAPV.trl); m.addLayer(MAPV.ogl);",
    "m.addLayer(MAPV.rfA); m.addLayer(MAPV.ogA); m.addLayer(MAPV.heads); m.addLayer(MAPV.trl); m.addLayer(MAPV.ogl); m.addLayer(MAPV.rfl);")
rep("  const shownStates=new Set(L0.map(o=>o.st));",
    """  MAPV.rfl.clearLayers(); MAPV.rfA.clearLayers(); let nR=0;
  if(document.getElementById("showrf").checked){const rc=tok("--rf-map"), od=tok("--og-dot");
    if(!MAPV.rfZ){MAPV.rfZ=Object.entries(RFZ).map(([k,rs])=>[k,rs.map(r=>geoDec(r,1e3))])}
    MAPV.rfZ.forEach(([k,rs])=>L.polygon(rs,{color:rc,weight:1.5,opacity:.9,dashArray:"5 4",fillColor:rc,fillOpacity:.14,interactive:false}).addTo(MAPV.rfA));
    const RL=RF.L.filter(x=>{if((s&&x[9]!==s)||(nw&&!x[15])||(pt&&x[2]!==pt))return false;
      if(q&&!(x[7]+" "+x[8]+" "+NAMES[x[9]]).toLowerCase().includes(q)&&x[9].toLowerCase()!==q)return false;return true});
    nR=RL.length;
    MAPV.rfl.addLayers(RL.map(x=>L.circleMarker([x[16],x[17]],{radius:x[6]>=50?10:8,color:x[2]==="l"?rc:od,weight:x[2]==="l"?3.5:2.5,fillColor:x[2]==="l"?od:rc,fillOpacity:x[2]==="l"?.9:1}).bindPopup(()=>rfPopup(x),{maxWidth:300})));
    if(s)RL.forEach(x=>{const b=STBOX[s]=STBOX[s]||[90,180,-90,-180];b[0]=Math.min(b[0],x[16]);b[1]=Math.min(b[1],x[17]);b[2]=Math.max(b[2],x[16]);b[3]=Math.max(b[3],x[17])});
  }
  const shownStates=new Set(L0.map(o=>o.st));""")
rep('+(nO?` · ${nO} listing${nO===1?"":"s"} of 25+ acres near old growth`:"");',
    '+(nO?` · ${nO} listing${nO===1?"":"s"} of 25+ acres near old growth`:"")+(nR?` · ${nR} of 25+ acres in rainforest country`:"");')
open(page, "w").write(h)
print("rainforest tab added")
