"""Add the Springheads tab to the page (idempotent for the data: re-running only refreshes SH). Usage: sh_tab.py page.html sh.json"""
import json, re, sys
page, shp = sys.argv[1], sys.argv[2]
h = open(page).read()
SH = json.load(open(shp))
data = "const SH=" + json.dumps(SH, separators=(",", ":"), ensure_ascii=False) + ";\n"

if 'id="t-heads"' in h:
    h = re.sub(r"const SH=\{.*?\};\n", lambda m: data, h, count=1, flags=re.S)
    open(page, "w").write(h); print("data refreshed"); sys.exit()

def rep(old, new, count=1):
    global h
    assert h.count(old) == count, f"{h.count(old)}x: {old[:100]}"
    h = h.replace(old, new)

# ---- CSS ----
for blk, col in (("--lake:#0d6b78;", "--spring:#6a3fb5; --spring-soft:#efe8fa;"),):
    rep("  --lake:#0d6b78; --lake-soft:#e0eff1;", "  --spring:#6a3fb5; --spring-soft:#efe8fa;\n  --lake:#0d6b78; --lake-soft:#e0eff1;")
rep("  --lake:#5cc3cf; --lake-soft:#173a3f;", "  --spring:#b79cf0; --spring-soft:#2a2140;\n  --lake:#5cc3cf; --lake-soft:#173a3f;", count=2)
CSS = """
/* springheads */
.mag{font-family:var(--mono);font-size:12px;font-weight:500;color:var(--spring);background:var(--spring-soft);border-radius:4px;padding:1px 6px;white-space:nowrap}
.rk.mg{font-family:var(--mono);font-size:13px;color:var(--spring);font-weight:500}
.tier.vh{background:var(--spring-soft);color:var(--spring)}
.law{grid-column:2/-1;font-size:12.5px;color:var(--muted);border-left:2px solid var(--rule);padding:2px 0 2px 10px;margin-top:6px}
.law a{color:var(--lake);font-weight:600}
ul.lsts li .xtra{grid-column:1/-1;font-size:12px;color:var(--muted);display:grid;gap:2px;margin-top:4px}
ul.lsts li .xtra b{color:var(--ink);font-weight:600}
.perm{font-family:var(--mono);font-size:11.5px}
.lg i.sh{background:var(--spring)}
"""
rep("</style>", CSS + "</style>")

# ---- tab, controls, sections ----
rep('<button id="t-map" type="button" aria-pressed="false">Map</button>',
    '<button id="t-heads" type="button" aria-pressed="false">Springheads</button><button id="t-map" type="button" aria-pressed="false">Map</button>')
rep('data-mode="lakes rivers national property springs map"><option value="">All states</option>',
    'data-mode="lakes rivers national property springs heads map"><option value="">All states</option>')
rep('<select id="ptype" aria-label="Property type" data-mode="property springs map" hidden>', '<select id="ptype" aria-label="Property type" data-mode="property springs heads map" hidden>')
rep('<label class="toggle" data-mode="property springs map" hidden><input id="newonly" type="checkbox"> Only new listings</label>',
    '<select id="shmag" aria-label="Spring size" data-mode="heads" hidden><option value="4">Magnitude 1–4 (100+ gpm)</option><option value="3">Magnitude 1–3 (1+ cfs)</option><option value="2">Magnitude 1–2 (10+ cfs)</option><option value="1">Magnitude 1 (100+ cfs)</option></select><select id="shprice" aria-label="Price" data-mode="heads" hidden><option value="">Any price</option><option value="750000">Up to $750k</option><option value="1500000">Up to $1.5M</option><option value="3000000">Up to $3M</option></select>\n'
    '  <label class="toggle" data-mode="property springs heads map" hidden><input id="newonly" type="checkbox"> Only new listings</label>\n'
    '  <label class="toggle" data-mode="heads" hidden><input id="shlist" type="checkbox"> Only springheads with listings</label>\n'
    '  <label class="toggle" data-mode="heads" hidden><input id="shrecent" type="checkbox"> Recent flow data only</label>')
rep('<label class="toggle" data-mode="map" hidden><input id="showwat" type="checkbox" checked> Show the ranked lakes, rivers and springs</label>',
    '<label class="toggle" data-mode="map" hidden><input id="showwat" type="checkbox" checked> Show the ranked lakes, rivers and springs</label>\n'
    '  <label class="toggle" data-mode="map" hidden><input id="showsh" type="checkbox" checked> Show springhead listings</label>')
rep('<span class="lg"><i class="wat"></i>Ranked lake, river or spring</span>', '<span class="lg"><i class="sh"></i>Springhead on the lot</span><span class="lg"><i class="wat"></i>Ranked lake, river or spring</span>')
SECTION = """<section class="extra" data-mode="heads" hidden>
  <h2>How the springheads search works</h2>
  <p><b>Magnitude</b> is the standard (Meinzer) scale for spring size, by average flow: <b>1</b> is 100 cubic feet per second (cfs) or more, about 65 million gallons a day; <b>2</b> is 10–100 cfs; <b>3</b> is 1–10 cfs; <b>4</b> is 100 gallons a minute up to 1 cfs. Magnitude 4 is still about 144,000 gallons a day, far more than a household uses.</p>
  <p>The inventory joins four sources: every USGS discharge measurement at a spring site (about 58,000 measurements at 10,000 sites, 1900s to 2026), the Florida DEP and Florida Geological Survey springs inventory, the Missouri Geological Survey springs database, and the USGS–TWDB database of Texas spring flows. Each spring's magnitude comes from the median of its measurements since 1990 when there are any, otherwise from all of them; for Florida and Missouri the state survey's magnitude is used unless newer USGS measurements disagree. Vents within 150 m, or with the same name within 3 km, are treated as one spring, keeping every vent's location. Missouri publishes spring locations rounded to about 1–10 km, so each Missouri spring was placed on its named USGS hydrography point; about half could be placed and the rest are left out. Stream gauges below a spring add flow measurements but never stand in for the vent's location. Maine has no spring with a measured flow of 100 gallons a minute or more, so it doesn't appear.</p>
  <p><b>Last measured</b> matters. Some springs here were measured once, decades ago, and springs can shrink or stop: Comanche Springs in Fort Stockton and the Pahrump Valley springs in Nevada were pumped dry, and Jacob's Well in Wimberley has stopped flowing in recent droughts. Where the latest measurement is far below the median, both are shown, and the 24 springs that were dry or nearly dry at their latest measurement are left out. Use <i>Recent flow data only</i> to keep springs measured since 2000 or rated by a current state survey.</p>
  <p>Listings come from Redfin, collected on <span class="shdate"></span>: houses and land priced $100,000 and up within about 1.5 km of a vent; use the price menu to narrow them. <b>Vent on the lot</b> means the vent falls inside the listing's parcel on the state parcel map (Florida Department of Revenue cadastral, Texas StratMap, Arkansas GIS Office, and Utah county parcels). <b>Vent at the lot's edge</b> means it's mapped within 30 m of the parcel line, inside the error of the spring's coordinates, or in unparceled water against the lot. <b>Adjoining land, same owner</b> means the vent's parcel has the same owner as the listing's, which may or may not be part of the sale. <b>Parent parcel</b> means the listing is a piece of a larger tax parcel that holds the vent. In states without a public parcel map, <b>Likely on the lot · estimated</b> means the vent sits within the radius of a circle the size of the listed lot around the listing's map point; treat these as leads to check.</p>
  <p><b>Permits near the vent</b> lists water-use permits within 400 m in Florida (Suwannee River, St. Johns River and Northwest Florida districts' permit areas, and Southwest Florida district withdrawal points with permitted gallons a day), and Texas water rights within 800 m from TCEQ, plus the groundwater conservation district. A permit nearby can mean an existing farm, utility or bottling claim on the same water. Names of individual permit holders are left out.</p>
  <p>The water-law note under each spring is general information, not legal advice. Whether a springhead's water can be used, sold or bottled depends on the state's rules and on rights already recorded, so have a water-rights attorney check before you buy.</p>
</section>

"""
rep('<section class="extra" data-mode="map" hidden>', SECTION + '<section class="extra" data-mode="map" hidden>')

# ---- sources ----
rep('const SRC=[\n', data + 'const SRC=[\n ["USGS Water Data API, discharge field measurements at springs and spring gauges","https://api.waterdata.usgs.gov/ogcapi/v0/collections/field-measurements"],\n'
    ' ["Florida DEP, Florida Springs (FGS spring inventory with magnitudes)","https://ca.dep.state.fl.us/arcgis/rest/services/OpenData/SPRINGS/MapServer/1"],\n'
    ' ["Missouri DNR / Missouri Geological Survey, springs database","https://gis.dnr.mo.gov/host/rest/services/water/water_springs/MapServer/0"],\n'
    ' ["USGS Open-File Report 03-315, historically documented springs and spring flows in Texas","https://pubs.usgs.gov/of/2003/ofr03-315/readme.htm"],\n'
    ' ["Florida Department of Revenue statewide cadastral, via Florida GIO","https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer"],\n'
    ' ["TxGIO StratMap land parcels","https://feature.geographic.texas.gov/arcgis/rest/services/Parcels/stratmap_land_parcels_48_most_recent/MapServer"],\n'
    ' ["Arkansas GIS Office parcel polygons","https://gis.arkansas.gov/arcgis/rest/services/FEATURESERVICES/Planning_Cadastre/FeatureServer/6"],\n'
    ' ["Utah UGRC county parcels","https://gis.utah.gov/products/sgid/cadastre/gop-parcels/"],\n'
    ' ["SRWMD, SJRWMD and NWFWMD consumptive use permits (ePermitting)","https://permitting.sjrwmd.com/arcgis02/rest/services"],\n'
    ' ["SWFWMD permitted water use withdrawal points","https://www25.swfwmd.state.fl.us/arcgis12/rest/services/OpenData/RegulatoryPro/MapServer/6"],\n'
    ' ["TCEQ Water Rights Viewer and groundwater conservation districts","https://www.tceq.texas.gov/gis/water-rights-viewer"],\n')

# ---- JS ----
rep(' map:"Every waterfront listing', ' heads:"Houses and land for sale with a spring vent of magnitude 1–4 (100 gallons a minute or more) on the lot, from USGS and state spring inventories, checked against parcel maps where states publish them, with water-use permits near each vent and each state\'s water rules.",\n map:"Every waterfront listing')
rep('if(sm==="rivers"||sm==="national"||sm==="property"||sm==="springs"||sm==="map")mode=sm;', 'if(sm==="rivers"||sm==="national"||sm==="property"||sm==="springs"||sm==="map"||sm==="heads")mode=sm;')
rep('if(location.hash==="#map")mode="map";', 'if(location.hash==="#map")mode="map";if(location.hash==="#springheads")mode="heads";')
JS = r"""
/* ---------- springheads tab ---------- */
const SHT=[["vh","Vent on the lot"],["vh","Vent at the lot's edge"],["near","Vent on adjoining land, same owner"],["near","Likely on the lot · estimated"],["un","Vent on the parent parcel"]];
const cfs=q=>q==null?null:q>=100?Math.round(q).toLocaleString():q>=10?q.toFixed(0):q>=1?q.toFixed(1):q.toFixed(2);
const gpm=q=>{const g=q*448.83;return g>=10000?Math.round(g/1000).toLocaleString()+"k":Math.round(g).toLocaleString()};
function flowTxt(hd){const [n,st,cty,mag,q,last,lastq]=hd;
  let t=q!=null?`${cfs(q)} cfs (≈${gpm(q)} gpm)`:"flow per state survey";
  if(last)t+=` · last measured ${last}`;
  if(lastq!=null&&q&&lastq<q*.4)t+=` at ${cfs(lastq)} cfs`;
  return t}
const recentOK=hd=>(hd[5]&&hd[5]>="2000")||(!hd[5]&&/fl|mo/.test(hd[7]));
function shFilter(){
  const q=document.getElementById("q").value.trim().toLowerCase(), s=sel.value, pt=document.getElementById("ptype").value,
    nw=document.getElementById("newonly").checked, mx=+document.getElementById("shmag").value, rc=document.getElementById("shrecent").checked, mp=+document.getElementById("shprice").value||Infinity;
  const headOK=hd=>(!s||hd[1]===s)&&hd[3]<=mx&&(!rc||recentOK(hd));
  const qH=hd=>!q||(hd[0]+" "+(hd[2]||"")+" "+NAMES[hd[1]]).toLowerCase().includes(q)||hd[1].toLowerCase()===q;
  const Ls=SH.L.filter(x=>{const hd=SH.heads[x[0]];return headOK(hd)&&x[2]<=mp&&(!pt||x[3]===pt)&&(!nw||x[15])&&(qH(hd)||(x[8]+" "+x[9]).toLowerCase().includes(q))});
  return {q,s,pt,nw,headOK,qH,Ls}}
function shItem(x){
  const [hi,t,price,ty,beds,baths,sqft,ac,addr,city,dom,gap,path,pac,first,isNew,lat,lon,note,perms,gcd]=x, st=SH.heads[hi][1];
  const facts=ty==="h"?[beds!=null?beds+" bd":null,baths!=null?baths+" ba":null,sqft?sqft.toLocaleString()+" sq ft":null,ac?ac+" ac":null]:["Land",ac?ac+" ac":null];
  if(pac&&ac&&Math.abs(pac-ac)>Math.max(.5,ac*.3))facts.push(`tax parcel ${pac} ac`); else if(pac&&!ac)facts.push(`parcel ${pac} ac`);
  const z="https://www.zillow.com/homes/"+encodeURIComponent(`${addr}, ${city}, ${st}`).replace(/%20/g,"-")+"_rb/";
  const seen=first&&first!==SH.date?` · on our list since ${fmtD(first)}`:"";
  const xs=[];
  if(note)xs.push(esc(note[0].toUpperCase()+note.slice(1))+".");
  if(perms&&perms.length)xs.push(`<span><b>${perms.length} permit${perms.length>1?"s":""} or water right${perms.length>1?"s":""} near the vent:</b> `+perms.slice(0,6).map(p=>`<span class="perm">${esc(p[0])} ${esc(p[1]??"")}</span>${p[2]?" "+esc(p[2]):""}${p[3]?" · "+esc(p[3]):""}${p[4]?" · "+esc(String(p[4]).toLowerCase()):""}${p[5]?", expires "+esc(p[5]):""}${p[6]?` · ${Number(p[6]).toLocaleString()} gal/day`:""}`).join("; ")+(perms.length>6?`; and ${perms.length-6} more`:"")+"</span>");
  else if(st==="FL"||st==="TX")xs.push("No permits or water rights on file within "+(st==="TX"?"800":"400")+" m of the vent.");
  if(gcd)xs.push(`Groundwater district: ${gcd[1]?`<a href="${esc(gcd[1])}" target="_blank" rel="noopener">${esc(gcd[0])}</a>`:esc(gcd[0])}.`);
  return `<li${isNew?' class="is-new"':""}><span class="pr">${money(price)}${isNew?' <span class="newb">New</span>':""}</span><span class="ad">${esc(addr)}, ${esc(city)}<small>${facts.filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}${seen}</small></span><span><span class="tier ${SHT[t][0]}">${SHT[t][1]}</span> <a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">Redfin</a> <a href="${z}" target="_blank" rel="noopener">Zillow</a></span>${xs.length?`<div class="xtra">${xs.map(s=>`<span>${s}</span>`).join("")}</div>`:""}</li>`}
function lawHtml(st){const l=SH.law[st];if(!l)return"";return `<div class="law"><b>${esc(NAMES[st])} water law.</b> ${esc(l[0])}${l[1]?` <a href="${esc(l[1])}" target="_blank" rel="noopener">State water rights</a>`:""}</div>`}
function headRow(hi,body,lw=true){const hd=SH.heads[hi],[n,st,cty,mag,q,last,lastq,src,lat,lon,usgs,pub]=hd;
  const zb=[lat-.012,lat+.012,lon-.015,lon+.015];
  return `<li class="row"><span class="rk mg" title="Magnitude ${mag}">M${mag}</span><div class="nm">${esc(n)}<span class="st-tag">${st}</span><small>${cty?esc(cty)+(st==="LA"?" Parish":" Co.")+", ":""}${esc(NAMES[st])} · <span class="mag">magnitude ${mag}</span> · ${flowTxt(hd)}${pub?" · on public land":""}</small></div><span></span>
    ${body||""}<div class="links"><a href="${zUrl(zb,null)}" target="_blank" rel="noopener">Zillow around the vent</a>${usgs?`<a class="alt" href="https://waterdata.usgs.gov/monitoring-location/${esc(usgs)}/" target="_blank" rel="noopener">USGS site</a>`:""}</div>${lw?lawHtml(st):""}</li>`}
function renderHeads(){
  const F=shFilter(), only=document.getElementById("shlist").checked;
  const by=new Map(); F.Ls.forEach(x=>{if(!by.has(x[0]))by.set(x[0],[]);by.get(x[0]).push(x)});
  const groups=[...by.entries()].sort((a,b)=>Math.min(...a[1].map(x=>x[1]))-Math.min(...b[1].map(x=>x[1]))||SH.heads[a[0]][3]-SH.heads[b[0]][3]||(SH.heads[b[0]][4]||0)-(SH.heads[a[0]][4]||0));
  let h=`<article class="state nat"><div class="shead"><h2>Listings with a springhead${F.s?" · "+esc(NAMES[F.s]):""}</h2><span class="count">${F.Ls.length} listing${F.Ls.length===1?"":"s"} · ${groups.length} spring${groups.length===1?"":"s"}</span></div><ol>`;
  groups.forEach(([hi,L])=>{h+=headRow(hi,`<ul class="lsts" style="grid-column:2/-1">${L.map(shItem).join("")}</ul>`)});
  if(!groups.length)h+=`<li class="row"><span></span><div class="nm"><small>No springhead listings match. Widen the magnitude, state or price filters, or check the inventory below for live Zillow searches around each vent.</small></div></li>`;
  h+="</ol></article>";
  if(!only){
    const withL=new Set(SH.L.map(x=>x[0]));
    const I=SH.heads.map((hd,i)=>[hd,i]).filter(([hd,i])=>F.headOK(hd)&&F.qH(hd)&&!withL.has(i)).sort((a,b)=>a[0][3]-b[0][3]||(b[0][4]||0)-(a[0][4]||0));
    h+=`<article class="state nat"><div class="shead"><h2>Springhead inventory${F.s?" · "+esc(NAMES[F.s]):""}</h2><span class="count">${I.length.toLocaleString()} without a current listing</span></div><ol>`+(F.s?`<li class="row"><span></span>${lawHtml(F.s)}</li>`:"");
    I.slice(0,LIMIT).forEach(([hd,i])=>{h+=headRow(i,"",false)});
    h+="</ol>";
    if(I.length>LIMIT)h+=`<div class="more"><button id="more" type="button">Show ${Math.min(100,I.length-LIMIT)} more</button></div>`;
    h+="</article>";
  }
  document.getElementById("list").innerHTML=h;
}
"""
rep('document.querySelectorAll(".rundate").forEach(e=>e.textContent=fmtD(e.textContent));', 'document.querySelectorAll(".rundate").forEach(e=>e.textContent=fmtD(e.textContent));\ndocument.querySelectorAll(".shdate").forEach(e=>e.textContent=fmtD(SH.date));')
rep("function render(){\n", JS + "function render(){\n  if(mode===\"heads\"){renderHeads();return}\n")
rep('  document.getElementById("t-map").setAttribute("aria-pressed",m==="map");\n',
    '  document.getElementById("t-map").setAttribute("aria-pressed",m==="map");\n  document.getElementById("t-heads").setAttribute("aria-pressed",m==="heads");\n')
rep('  if(m==="springs"){\n', '''  if(m==="heads"){
    const on=SH.L.filter(x=>x[1]<=1).length, ver=SH.L.length-on, nn=SH.L.filter(x=>x[15]).length;
    document.getElementById("facts").innerHTML=`<span class="chip"><b>${SH.heads.length.toLocaleString()}</b> springheads, magnitude 1–4, in ${SH.n_states} states</span><span class="chip"><b>${on}</b> listing${on===1?"":"s"} with the vent on or at the lot</span>`+(ver?`<span class="chip"><b>${ver}</b> more to verify</span>`:"")+(SH.prev&&nn?`<span class="chip"><b>${nn}</b> new since ${fmtD(SH.prev)}</span>`:"")+`<span class="chip">Redfin, ${fmtD(SH.date)}</span>`;
    try{localStorage.setItem("secchi-mode",m)}catch(e){}
    render();return;}
  if(m==="springs"){
''')
rep('["q","st","hide","kind","dir","ptype","haslist","newonly","incnear","showwat"]', '["q","st","hide","kind","dir","ptype","haslist","newonly","incnear","showwat","shmag","shprice","shlist","shrecent","showsh"]')
rep('document.getElementById("t-map").addEventListener("click",()=>setMode("map"));', 'document.getElementById("t-map").addEventListener("click",()=>setMode("map"));\ndocument.getElementById("t-heads").addEventListener("click",()=>setMode("heads"));')

# ---- map: springhead listings layer ----
rep('  MAPV.waters=L.layerGroup();\n  m.addLayer(MAPV.waters); m.addLayer(MAPV.cluster);',
    '  MAPV.waters=L.layerGroup(); MAPV.heads=L.layerGroup();\n  m.addLayer(MAPV.waters); m.addLayer(MAPV.cluster); m.addLayer(MAPV.heads);')
rep('  const shownStates=new Set(L0.map(o=>o.st));\n',
'''  MAPV.heads.clearLayers(); let nH=0;
  if(document.getElementById("showsh").checked){const sp=tok("--spring");
    SH.L.forEach(x=>{const hd=SH.heads[x[0]];
      if((s&&hd[1]!==s)||(pt&&x[3]!==pt)||(nw&&!x[15]))return;
      if(q&&!(x[8]+" "+x[9]+" "+hd[0]+" "+NAMES[hd[1]]).toLowerCase().includes(q))return;
      nH++; const land=x[3]==="l";
      L.circleMarker([x[16],x[17]],{radius:8,color:land?sp:surf,weight:land?2.5:1.5,fillColor:sp,fillOpacity:land?.2:.95})
        .bindPopup(()=>shPopup(x),{maxWidth:300}).addTo(MAPV.heads);
      if(s){const b=STBOX[s]=STBOX[s]||[90,180,-90,-180];b[0]=Math.min(b[0],x[16]);b[1]=Math.min(b[1],x[17]);b[2]=Math.max(b[2],x[16]);b[3]=Math.max(b[3],x[17])}});
  }
  const shownStates=new Set(L0.map(o=>o.st));
''')
rep('  document.getElementById("mapcount").textContent=`${L0.length.toLocaleString()} listing${L0.length===1?"":"s"} in ${shownStates.size} state${shownStates.size===1?"":"s"}`;',
    '  document.getElementById("mapcount").textContent=`${L0.length.toLocaleString()} waterfront listing${L0.length===1?"":"s"} in ${shownStates.size} state${shownStates.size===1?"":"s"}`+(nH?` · ${nH} springhead listing${nH===1?"":"s"}`:"");')
rep('function styleBase(){', '''function shPopup(x){
  const hd=SH.heads[x[0]], [hi,t,price,ty,beds,baths,sqft,ac,addr,city,dom,gap,path]=x;
  const size=ty==="h"?[beds!=null?beds+" bd":null,baths!=null?baths+" ba":null,sqft?sqft.toLocaleString()+" sq ft":null,ac?ac+" ac":null]:["Land",ac?ac+" ac":null];
  const z="https://www.zillow.com/homes/"+encodeURIComponent(`${addr}, ${city}, ${hd[1]}`).replace(/%20/g,"-")+"_rb/";
  return `<div class="pp-price">${money(price)}${x[15]?' <span class="newb">New</span>':""}</div>
    <div class="pp-sub">${size.filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}</div>
    <div>${esc(addr)}, ${esc(city)}, ${hd[1]}</div>
    <div class="pp-water">${SHT[t][1]}: <b>${esc(hd[0])}</b> <span class="pp-sub">(magnitude ${hd[3]}${hd[4]!=null?`, ${cfs(hd[4])} cfs`:""}${hd[5]?`, measured ${hd[5]}`:""})</span>${x[19]&&x[19].length?`<br><span class="pp-sub">${x[19].length} permit${x[19].length>1?"s":""} or water right${x[19].length>1?"s":""} near the vent</span>`:""}</div>
    <div class="pp-links"><a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">View listing on Redfin</a><a class="alt" href="${z}" target="_blank" rel="noopener">Find on Zillow</a></div>`;
}
function styleBase(){''')
rep('  if(m==="map"){\n    const A=allListings(), on=A.filter(o=>o.x[1]===0).length;\n    document.getElementById("facts").innerHTML=`<span class="chip"><b>${A.length.toLocaleString()}</b> listings mapped</span><span class="chip"><b>${on.toLocaleString()}</b> on the water</span>',
    '  if(m==="map"){\n    const A=allListings(), on=A.filter(o=>o.x[1]===0).length;\n    document.getElementById("facts").innerHTML=`<span class="chip"><b>${A.length.toLocaleString()}</b> listings mapped</span><span class="chip"><b>${on.toLocaleString()}</b> on the water</span>`+(SH.L.length?`<span class="chip"><b>${SH.L.length}</b> springhead listings</span>`:"")+`')
rep('<p>Every listing from the Property and Springs tabs on one map,', '<p>Every listing from the Property, Springs and Springheads tabs on one map,')
rep(' map:"Every waterfront listing from the Property and Springs tabs on one map.', ' map:"Every waterfront and springhead listing on one map.')
open(page, "w").write(h)
print("ok", len(h))
