"""Add the Cities tab (houses near major bike trails inside cities over 200k, with water + trail overlaps highlighted) and a
map toggle. Idempotent: re-running only refreshes the CT data. Usage: ct_tab.py page.html ct.json"""
import json, re, sys
page, ctp = sys.argv[1], sys.argv[2]
h = open(page).read()
CT = json.load(open(ctp))
data = "const CT=" + json.dumps(CT, separators=(",", ":"), ensure_ascii=False) + ";\n"
if 'id="t-cities"' in h:
    h = re.sub(r"const CT=\{.*?\};\n", lambda m: data, h, count=1, flags=re.S)
    open(page, "w").write(h); print("cities data refreshed"); sys.exit()

def rep(old, new, count=1):
    global h
    assert h.count(old) == count, f"{h.count(old)}x: {old[:110]}"
    h = h.replace(old, new)
def rep_between(start, end, old, new):
    """replace every `old` inside the text between markers start..end"""
    global h
    i = h.index(start); j = h.index(end, i)
    seg = h[i:j]; assert old in seg, old
    h = h[:i] + seg.replace(old, new) + h[j:]

# ---- CSS ----
rep("  --trail:#2e7d3a; --trail-soft:#e2f2e4;", "  --city:#b0502a; --city-soft:#f8e7de;\n  --trail:#2e7d3a; --trail-soft:#e2f2e4;")
rep("  --trail:#7fd38b; --trail-soft:#1b3420;", "  --city:#f0a27c; --city-soft:#3a2419;\n  --trail:#7fd38b; --trail-soft:#1b3420;", count=2)
rep(".chip.trc b{color:var(--trail)}", ".chip.trc b{color:var(--trail)}\n"
    "/* cities */\n.lg i.ct{background:var(--city)}\n.mc.ctc{background:color-mix(in srgb,var(--city) 88%,transparent)}\n"
    ".tt.ct{color:var(--city);background:var(--city-soft)}\n.rk.ct{font-family:var(--mono);font-size:12px;color:var(--city);font-weight:500;padding-top:3px}\n"
    "ul.lsts li.both{border-color:var(--trail);box-shadow:inset 3px 0 0 var(--lake)}\n.state.both{border-color:color-mix(in srgb,var(--trail) 55%,var(--rule))}\n"
    ".state.both .shead h2::after{content:\"Water + trail\";font-family:var(--body);font-size:11px;font-weight:600;letter-spacing:.03em;text-transform:uppercase;color:var(--trail);background:var(--trail-soft);border-radius:4px;padding:2px 7px;margin-left:10px;vertical-align:3px}")

# ---- tab and controls ----
rep('<button id="t-trails" type="button" aria-pressed="false">Trails</button>',
    '<button id="t-trails" type="button" aria-pressed="false">Trails</button><button id="t-cities" type="button" aria-pressed="false">Cities</button>')
rep('data-mode="lakes rivers national property springs heads trails map"><option value="">All states</option>',
    'data-mode="lakes rivers national property springs heads trails cities map"><option value="">All states</option>')
rep('<select id="trtype" aria-label="Trail type" data-mode="trails" hidden>', '<select id="trtype" aria-label="Trail type" data-mode="trails cities" hidden>')
rep('<select id="trdist" aria-label="Distance to the trail" data-mode="trails" hidden>', '<select id="trdist" aria-label="Distance to the trail" data-mode="trails cities" hidden>')
rep('<select id="trprice" aria-label="Price" data-mode="trails" hidden>', '<select id="trprice" aria-label="Price" data-mode="trails cities" hidden>')
rep('<label class="toggle" data-mode="property springs heads trails map" hidden><input id="newonly" type="checkbox"> Only new listings</label>',
    '<label class="toggle" data-mode="cities" hidden><input id="ctboth" type="checkbox"> <b>Only listings with both water and trail access</b></label>\n'
    '  <label class="toggle" data-mode="property springs heads trails cities map" hidden><input id="newonly" type="checkbox"> Only new listings</label>')
rep('<label class="toggle" data-mode="map" hidden><input id="showtr" type="checkbox" checked> Show houses near bike trails</label>',
    '<label class="toggle" data-mode="map" hidden><input id="showtr" type="checkbox" checked> Show houses near bike trails</label>\n'
    '  <label class="toggle" data-mode="map" hidden><input id="showct" type="checkbox"> Show city houses near bike trails (cities over 200,000)</label>')
rep('<span class="lg"><i class="tr"></i>House near a bike trail</span>', '<span class="lg"><i class="tr"></i>House near a bike trail</span><span class="lg"><i class="ct"></i>City house near a bike trail</span>')
SECTION = """<section class="extra" data-mode="cities" hidden>
  <h2>How the cities search works</h2>
  <p>This is the city counterpart of the Trails tab, which leaves out the 128 cities with more than 200,000 people (2024 Census estimates). It lists single-family houses for sale on Redfin inside those cities' limits, priced $100,000 to $750,000, collected on <span class="ctdate"></span>, whose map point is within <b>400 m (about a quarter mile)</b> of a named segment of a major bike trail: the same networks as the Trails tab, with 20 or more miles of trail or 10 or more miles end to end. Distances are straight-line, so the actual walk may be longer. Consolidated city-counties, such as Nashville, Louisville, Lexington, Augusta and Anchorage, count as their whole county.</p>
  <p><b>Water and trail access</b>, at the top, brings together the city listings that have both. It includes houses near a trail that are also waterfront listings on the Property, Springs or Springheads tabs, and those tabs' listings inside these cities that sit within a mile of a major trail. The other tabs' water-and-trail highlight leaves cities out, so city overlaps appear only here and on the map when city houses are switched on. Use <i>Only listings with both water and trail access</i> to see just those.</p>
  <p>The Lakes, Rivers, Springs and Springheads searches never left cities out. Only the trail searches did.</p>
</section>

<section class="extra" data-mode="map" hidden>"""
rep('<section class="extra" data-mode="map" hidden>', SECTION)
rep("<p>Every listing from the Property, Springs, Springheads and Trails tabs on one map,", "<p>Every listing from the Property, Springs, Springheads, Trails and Cities tabs on one map (city houses appear when you switch them on),")

# ---- JS wiring ----
rep("const SRC=[", data + "const SRC=[")
rep(' trails:"Houses for sale within a quarter mile', ' cities:"Houses for sale within a quarter mile (400 m) of a major bike trail inside the 128 cities of more than 200,000 people, priced $100,000 to $750,000, with listings that have both water and trail access brought to the top.",\n trails:"Houses for sale within a quarter mile')
rep('||sm==="trails")mode=sm', '||sm==="trails"||sm==="cities")mode=sm')
rep('if(location.hash==="#trails")mode="trails";', 'if(location.hash==="#trails")mode="trails";if(location.hash==="#cities")mode="cities";')
rep('function render(){\n  if(mode==="trails"){renderTrails();return}', 'function render(){\n  if(mode==="cities"){renderCities();return}\n  if(mode==="trails"){renderTrails();return}')
rep('  document.getElementById("t-trails").setAttribute("aria-pressed",m==="trails");',
    '  document.getElementById("t-trails").setAttribute("aria-pressed",m==="trails");\n  document.getElementById("t-cities").setAttribute("aria-pressed",m==="cities");')
rep('ph=m==="trails"?"Find a trail, town or state"', 'ph=m==="trails"?"Find a trail, town or state":m==="cities"?"Find a city, trail or state"')
rep('  if(m==="trails"){\n', '''  if(m==="cities"){
    const nn=CT.L.filter(x=>x[15]).length, nc=new Set(CT.L.map(x=>x[0])).size, nb=CT.L.filter(x=>x[19]).length+CT.W.length;
    document.getElementById("facts").innerHTML=`<span class="chip"><b>${CT.L.length.toLocaleString()}</b> houses within 400 m of a major bike trail in ${nc} of the ${CT.cities.length} cities over 200,000</span><span class="chip trc"><b>${nb}</b> with both water and trail access</span>`+(CT.prev?`<span class="chip"><b>${nn}</b> new since ${fmtD(CT.prev)}</span>`:`<span class="chip">First check · new houses are flagged from next month</span>`)+`<span class="chip">Redfin, ${fmtD(CT.date)}</span>`;
    try{localStorage.setItem("secchi-mode",m)}catch(e){}
    render();return;}
  if(m==="trails"){
''')
rep('"wtd","trwat"]', '"wtd","trwat","ctboth","showct"]') if '"wtd","trwat"]' in h else rep('"showtr","trwat"]', '"showtr","trwat","ctboth","showct"]')
rep('document.getElementById("t-trails").addEventListener("click",()=>setMode("trails"));',
    'document.getElementById("t-trails").addEventListener("click",()=>setMode("trails"));\ndocument.getElementById("t-cities").addEventListener("click",()=>setMode("cities"));')
rep('document.querySelectorAll(".trdate").forEach(e=>e.textContent=fmtD(TR.date));',
    'document.querySelectorAll(".trdate").forEach(e=>e.textContent=fmtD(TR.date));\ndocument.querySelectorAll(".ctdate").forEach(e=>e.textContent=fmtD(CT.date));')

CTJS = r'''
/* ---------- cities tab ---------- */
const CTW={}; CT.W.forEach(w=>{CTW[w[4]]=[w[1],w[2],w[3]]}); CT.L.forEach(x=>{if(x[19])CTW[x[12]]=[x[1],x[11],x[13]]});
const ctCity=ci=>{const c=CT.cities[ci];return c?`${c[0]}, ${c[1]}`:""};
const ctZ=(addr,city,st)=>"https://www.zillow.com/homes/"+encodeURIComponent(`${addr}, ${city}, ${st}`).replace(/%20/g,"-")+"_rb/";
const ctWaterTier=t=>t==="on"?"on the water":t==="near"?"near the water · MLS waterfront":"springhead";
function ctTrailTxt(ti,seg,dist){const t=TR.trails[ti]; if(!t)return esc(seg||"");
  const net=wtGood(t[0])?t[0]:(t[1].find(wtGood)||null), sg=wtGood(seg)?seg:(net||"an unnamed trail");
  const kinds=trTags(t).map(k=>TTN[k].toLowerCase()).join(", ");
  return `${wtDist(dist)} to ${esc(sg)} · ${net&&net!==sg?esc(net)+" network, ":""}${miTxt(t[2])} mi${kinds?" · "+kinds:""}`}
function ctFilter(){
  const q=document.getElementById("q").value.trim().toLowerCase(), s=sel.value, ty=document.getElementById("trtype").value,
    dmax=+document.getElementById("trdist").value, pmax=+document.getElementById("trprice").value, nw=document.getElementById("newonly").checked,
    both=document.getElementById("ctboth").checked;
  const tOK=ti=>!ty||(TR.trails[ti]&&trTags(TR.trails[ti]).includes(ty));
  const qOK=(ci,extra)=>{if(!q)return true;const c=CT.cities[ci];return (c[0]+" "+NAMES[c[1]]+" "+extra).toLowerCase().includes(q)||c[1].toLowerCase()===q};
  const Ls=CT.L.filter(x=>(!s||CT.cities[x[0]][1]===s||x[9]===s)&&x[11]<=dmax&&x[2]<=pmax&&(!nw||x[15])&&(!both||x[19])&&tOK(x[1])&&qOK(x[0],x[7]+" "+x[8]+" "+x[13]+" "+(TR.trails[x[1]]||[""])[0]));
  const Ws=CT.W.filter(w=>(!s||CT.cities[w[0]][1]===s)&&w[7]<=pmax&&(!nw||w[17])&&tOK(w[1])&&qOK(w[0],w[13]+" "+w[14]+" "+w[5]+" "+w[3]));
  return {q,s,both,Ls,Ws}}
function ctItem(x){
  const [ci,ti,price,beds,baths,sqft,ac,addr,city,st,dom,dist,path,seg,first,isNew,lat,lon,yr,wat,wt]=x;
  const facts=[beds!=null?beds+" bd":null,baths!=null?baths+" ba":null,sqft?sqft.toLocaleString()+" sq ft":null,ac?ac+" ac":null,yr?"built "+yr:null];
  const seen=first&&first!==CT.date?` · on our list since ${fmtD(first)}`:"";
  return `<li class="${wat?"both":""}${isNew?" is-new":""}"><span class="pr">${money(price)}${isNew?' <span class="newb">New</span>':""}</span><span class="ad">${esc(addr)}, ${esc(city)}<small>${facts.filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}${seen}</small></span><span><span class="tier tr" title="Straight-line distance from the house's map point">${dist} m to ${esc(wtGood(seg)?seg:"the trail")}</span> <a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">Redfin</a> <a href="${ctZ(addr,city,st)}" target="_blank" rel="noopener">Zillow</a></span>${wat?`<div class="xtra"><span><span class="tt wat">On the water</span>${esc(wat)} · ${ctWaterTier(wt)}</span><span><span class="tt">Bike trail</span>${ctTrailTxt(ti,seg,dist)}</span></div>`:""}</li>`}
function ctWItem(w){
  const [ci,ti,dist,seg,path,wat,wt,price,ty,beds,baths,sqft,ac,addr,city,st,dom,isNew]=w;
  const facts=ty==="h"?[beds!=null?beds+" bd":null,baths!=null?baths+" ba":null,sqft?sqft.toLocaleString()+" sq ft":null,ac?ac+" ac":null]:["Land",ac?ac+" ac":null];
  return `<li class="both${isNew?" is-new":""}"><span class="pr">${money(price)}${isNew?' <span class="newb">New</span>':""}</span><span class="ad">${esc(addr)}, ${esc(city)}<small>${facts.filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}</small></span><span><a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">Redfin</a> <a href="${ctZ(addr,city,st)}" target="_blank" rel="noopener">Zillow</a></span><div class="xtra"><span><span class="tt wat">On the water</span>${esc(wat)} · ${ctWaterTier(wt)}</span><span><span class="tt">Bike trail</span>${ctTrailTxt(ti,seg,dist)}</span></div></li>`}
function renderCities(){
  const F=ctFilter(); let html="";
  const BH=F.Ls.filter(x=>x[19]), seenP=new Set(BH.map(x=>x[12])), BW=F.Ws.filter(w=>!seenP.has(w[4]));
  const nb=BH.length+BW.length;
  if(nb){
    const byC=new Map(); BH.forEach(x=>{if(!byC.has(x[0]))byC.set(x[0],{h:[],w:[]});byC.get(x[0]).h.push(x)}); BW.forEach(w=>{if(!byC.has(w[0]))byC.set(w[0],{h:[],w:[]});byC.get(w[0]).w.push(w)});
    html+=`<article class="state both"><div class="shead"><h2>Water and trail access</h2><span class="count">${nb} listing${nb===1?"":"s"} · ${byC.size} cit${byC.size===1?"y":"ies"}</span></div><ol>`;
    [...byC.entries()].sort((a,b)=>CT.cities[b[0]][2]-CT.cities[a[0]][2]).forEach(([ci,g])=>{
      html+=`<li class="row"><span class="rk ct">${g.h.length+g.w.length}</span><div class="nm">${esc(ctCity(ci))}<small>${CT.cities[ci][2].toLocaleString()} people</small></div><span></span><ul class="lsts" style="grid-column:2/-1">${[...g.h.sort((a,b)=>a[11]-b[11]).map(ctItem),...g.w.sort((a,b)=>a[2]-b[2]).map(ctWItem)].join("")}</ul></li>`});
    html+="</ol></article>";
  }
  if(!F.both){
    const byC=new Map(); F.Ls.forEach(x=>{if(!byC.has(x[0]))byC.set(x[0],new Map());const m=byC.get(x[0]);if(!m.has(x[1]))m.set(x[1],[]);m.get(x[1]).push(x)});
    [...byC.entries()].sort((a,b)=>[...b[1].values()].reduce((s,L)=>s+L.length,0)-[...a[1].values()].reduce((s,L)=>s+L.length,0)).forEach(([ci,m])=>{
      const c=CT.cities[ci], tot=[...m.values()].reduce((a,L)=>a+L.length,0), nn=[...m.values()].reduce((a,L)=>a+L.filter(x=>x[15]).length,0), nw=[...m.values()].reduce((a,L)=>a+L.filter(x=>x[19]).length,0);
      html+=`<article class="state"><div class="shead"><h2>${esc(c[0])}<span class="ab">${c[1]}</span></h2><span class="count">${tot} house${tot===1?"":"s"} · ${m.size} trail${m.size===1?"":"s"}${nw?` · ${nw} on the water`:""}${nn&&!document.getElementById("newonly").checked?` · ${nn} new`:""}</span></div><ol>`;
      [...m.entries()].sort((a,b)=>b[1].length-a[1].length).forEach(([ti,L])=>{const t=TR.trails[ti]||["Trail",[],0,null,"u","",{},[],[0,0,0,0]];
        const tags=trTags(t).map(k=>`<span class="tt">${TTN[k]}</span>`).join(""), nm=wtGood(t[0])?t[0]:(t[1].find(wtGood)||"Unnamed trail network");
        const n2=L.filter(x=>x[15]).length;
        html+=`<li class="row"><span class="rk tr">${miTxt(t[2])} mi</span><div class="nm">${esc(nm)}<small>${tags}${miTxt(t[2])} mi of trail${t[3]?` · ${miTxt(t[3])} mi end to end`:""}${t[1].filter(wtGood).length?` · also ${t[1].filter(wtGood).slice(0,3).map(esc).join(", ")}`:""}</small></div><span></span>
          <details class="lst"${document.getElementById("newonly").checked||(F.s&&m.size<=2)?" open":""}><summary>${L.length} house${L.length===1?"":"s"} ${n2?`<span class="cnt new">${n2} new</span>`:""}</summary><ul class="lsts">${L.sort((a,b)=>a[11]-b[11]).map(ctItem).join("")}</ul></details>
          <div class="links"><a href="${trMapUrl(t[8])}" target="_blank" rel="noopener">Trail map (CyclOSM)</a></div></li>`});
      html+="</ol></article>"});
  }
  document.getElementById("list").innerHTML=html||`<p class="empty">${F.both?"No city listings with both water and trail access match those filters.":"No city houses near a trail match those filters."}</p>`;
}
function ctPopup(x){
  const [ci,ti,price,beds,baths,sqft,ac,addr,city,st,dom,dist,path,seg,first,isNew,lat,lon,yr,wat,wt]=x;
  const size=[beds!=null?beds+" bd":null,baths!=null?baths+" ba":null,sqft?sqft.toLocaleString()+" sq ft":null,ac?ac+" ac":null];
  return `<div class="pp-price">${money(price)}${isNew?' <span class="newb">New</span>':""}</div>
    <div class="pp-sub">${size.filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}</div>
    <div>${esc(addr)}, ${esc(city)}, ${st}</div>
    <div class="pp-water"><span class="tt ct">City</span>${esc(ctCity(ci))}</div>
    <div class="pp-water"><span class="tt">Bike trail</span>${ctTrailTxt(ti,seg,dist)}</div>
    ${wat?`<div class="pp-water"><span class="tt wat">On the water</span>${esc(wat)}</div>`:""}
    <div class="pp-links"><a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">View listing on Redfin</a><a class="alt" href="${ctZ(addr,city,st)}" target="_blank" rel="noopener">Find on Zillow</a></div>`;
}
'''
rep("/* ---------- map tab ---------- */", CTJS + "\n/* ---------- map tab ---------- */")

# water + trail helpers: on the map, with city houses switched on, city water listings near trails count too
rep_between("/* ---------- water + trails ---------- */", "function wtFacts(", "WT.w[path]", "wtGet(path)")
rep("const wtNear=(path,d)=>{const w=wtGet(path);", "const wtGet=path=>WT.w[path]||(mode===\"map\"&&document.getElementById(\"showct\").checked?CTW[path]:null)||null;\nconst wtNear=(path,d)=>{const w=wtGet(path);")

# ---- map layer ----
rep("  m.addLayer(MAPV.waters); m.addLayer(MAPV.cluster); m.addLayer(MAPV.heads); m.addLayer(MAPV.trl);",
    "  MAPV.ct=L.markerClusterGroup({showCoverageOnHover:false,maxClusterRadius:42,spiderfyOnMaxZoom:true,chunkedLoading:true,\n"
    "    iconCreateFunction:c=>{const n=c.getChildCount(), s=n<10?30:n<50?36:44; return L.divIcon({html:`<div class=\"mc ctc\" style=\"width:${s}px;height:${s}px\">${n}</div>`,className:\"\",iconSize:[s,s]})}});\n"
    "  m.addLayer(MAPV.waters); m.addLayer(MAPV.cluster); m.addLayer(MAPV.heads); m.addLayer(MAPV.trl); m.addLayer(MAPV.ct);")
rep("  const shownStates=new Set(L0.map(o=>o.st));",
    """  MAPV.ct.clearLayers(); let nC=0;
  if(document.getElementById("showct").checked&&pt!=="l"){const cc=tok("--city"), tg=tok("--trail");
    const CL=CT.L.filter(x=>{const c=CT.cities[x[0]];if((s&&x[9]!==s&&c[1]!==s)||(nw&&!x[15])||(WTD()&&!x[19]))return false;
      if(q&&!(c[0]+" "+x[7]+" "+x[8]+" "+x[13]+" "+NAMES[c[1]]).toLowerCase().includes(q)&&c[1].toLowerCase()!==q)return false;return true});
    nC=CL.length;
    MAPV.ct.addLayers(CL.map(x=>L.circleMarker([x[16],x[17]],{radius:x[19]?8:7,color:x[19]?tg:surf,weight:x[19]?3:1.5,fillColor:cc,fillOpacity:.95}).bindPopup(()=>ctPopup(x),{maxWidth:300})));
    if(s)CL.forEach(x=>{const b=STBOX[s]=STBOX[s]||[90,180,-90,-180];b[0]=Math.min(b[0],x[16]);b[1]=Math.min(b[1],x[17]);b[2]=Math.max(b[2],x[16]);b[3]=Math.max(b[3],x[17])});
  }
  const shownStates=new Set(L0.map(o=>o.st));""")
rep('+(nT?` · ${nT.toLocaleString()} house${nT===1?"":"s"} near bike trails`:"");', '+(nT?` · ${nT.toLocaleString()} house${nT===1?"":"s"} near bike trails`:"")+(nC?` · ${nC.toLocaleString()} city house${nC===1?"":"s"} near bike trails`:"");')
rep("if(WTD()&&!L0.length&&!nH){", "if(WTD()&&!L0.length&&!nH&&!nC){")
open(page, "w").write(h)
print("cities tab added")
