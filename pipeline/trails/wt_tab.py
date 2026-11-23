"""One-time page edits for the water + trail highlight (idempotent: exits if already applied).
Adds the "near a bike trail" filter on the Property, Springs, Springheads and Map tabs, trail lines on listings and popups,
a green ring on the map for listings within 1 mile of a major bike trail, and "also on the water" on the Trails tab.
The data (const WT) comes from water_trails.py. The Property/Springs listing code is rebuilt monthly by patch_page.py,
whose template calls wtOK() and wtLine() defined here. Usage: wt_tab.py page.html"""
import re, sys
page = sys.argv[1]
h = open(page).read()
if 'id="wtd"' in h:
    print("water+trail edits already present"); sys.exit()

def rep(old, new, count=1):
    global h
    assert h.count(old) == count, f"{h.count(old)}x: {old[:110]}"
    h = h.replace(old, new)

def rep_in(fn_start, old, new):
    """replace the first `old` after the start of function `fn_start`"""
    global h
    i = h.index(fn_start); j = h.index(old, i)
    h = h[:j] + new + h[j + len(old):]

# ---- CSS ----
rep(".mc.trc{background:color-mix(in srgb,var(--trail) 85%,transparent)}",
    ".mc.trc{background:color-mix(in srgb,var(--trail) 85%,transparent)}\n"
    ".lg i.wt{background:var(--surface);border:2.5px solid var(--trail);box-shadow:none}\n"
    ".tt.wat{color:var(--lake);background:var(--lake-soft)}\n"
    ".chip.trc{border-color:color-mix(in srgb,var(--trail) 45%,var(--rule))}\n.chip.trc b{color:var(--trail)}")

# ---- controls ----
rep('<select id="ptype" aria-label="Property type" data-mode="property springs heads map" hidden><option value="">Houses and land</option><option value="h">Houses only</option><option value="l">Land only</option></select>',
    '<select id="ptype" aria-label="Property type" data-mode="property springs heads map" hidden><option value="">Houses and land</option><option value="h">Houses only</option><option value="l">Land only</option></select>'
    '<select id="wtd" aria-label="Distance to a major bike trail" data-mode="property springs heads map" hidden><option value="">Bike trail: any distance</option>'
    '<option value="400">Bike trail within ¼ mile</option><option value="800">Bike trail within ½ mile</option><option value="1609">Bike trail within 1 mile</option></select>\n'
    '  <label class="toggle" data-mode="property springs heads map" hidden><input id="wtboth" type="checkbox"> <b>Only listings near both water and a major bike trail</b></label>')
rep('<label class="toggle" data-mode="trails" hidden><input id="trall" type="checkbox"> Also list trails with no houses for sale</label>',
    '<label class="toggle" data-mode="trails" hidden><input id="trall" type="checkbox"> Also list trails with no houses for sale</label>\n'
    '  <label class="toggle" data-mode="trails" hidden><input id="trwat" type="checkbox"> Only houses that are also on the water</label>')
rep('<span class="lg"><i class="tr"></i>House near a bike trail</span>',
    '<span class="lg"><i class="tr"></i>House near a bike trail</span><span class="lg"><i class="wt"></i>Green ring: water listing within 1 mile of a major bike trail</span>')

# ---- explanation ----
SECTION = """<section class="extra" data-mode="property springs heads" hidden>
  <h2>Water and bike trails</h2>
  <p>Listings within a mile of a major bike trail carry a <span class="tt">Bike trail</span> line with the distance and the trail's name, length and type. Use the <i>distance to a bike trail</i> menu to keep only those within a quarter, half or full mile. The trails are the same networks as on the Trails tab: gravel rail-trails, mountain bike trail systems and paved multi-use paths with 20 or more miles of trail, or 10 or more miles end to end. Distances run in a straight line from the listing's map point to the nearest named segment, so the actual walk or ride may be longer. Listings inside cities of more than 200,000 people don't get a trail line, matching the Trails tab.</p>
</section>

<section class="extra" data-mode="map" hidden>"""
rep('<section class="extra" data-mode="map" hidden>', SECTION)

# ---- Springheads tab (code inserted once by sh_tab.py) ----
rep("return headOK(hd)&&x[2]<=mp&&(!pt||x[3]===pt)&&(!nw||x[15])&&", "return headOK(hd)&&x[2]<=mp&&(!pt||x[3]===pt)&&(!nw||x[15])&&wtOK(x[12])&&")
rep("  if(gcd)xs.push(`Groundwater district:", "  if(WT.w[path])xs.push(wtSpan(path));\n  if(gcd)xs.push(`Groundwater district:")

# ---- Trails tab (code inserted once by tr_tab.py) ----
rep("&&x[10]<=dmax&&x[1]<=pmax&&(!nw||x[14])&&", "&&x[10]<=dmax&&x[1]<=pmax&&(!nw||x[14])&&(!document.getElementById(\"trwat\").checked||WT.t[x[11]])&&")
rep('<a href="${z}" target="_blank" rel="noopener">Zillow</a></span></li>`}\nfunction trailRow(',
    '<a href="${z}" target="_blank" rel="noopener">Zillow</a></span>${WT.t[path]?`<div class="xtra"><span><span class="tt wat">Also on the water</span>${esc(WT.t[path][0])}</span></div>`:""}</li>`}\nfunction trailRow(')

# ---- map popups and markers ----
rep_in("function popupHtml(o){", '<div class="pp-links">', '${wtPop(path)}<div class="pp-links">')
rep_in("function shPopup(x){", '<div class="pp-links">', '${wtPop(path)}<div class="pp-links">')
rep_in("function trPopup(x){", '<div class="pp-links">', '${WT.t[path]?`<div class="pp-water"><span class="tt wat">Also on the water</span>${esc(WT.t[path][0])}</div>`:""}<div class="pp-links">')
rep("(near||o.x[1]===0)&&", "(near||o.x[1]===0)&&wtOK(o.x[12])&&")
rep('const on=tok("--lake"), nr=tok("--warn"), surf=tok("--surface");', 'const on=tok("--lake"), nr=tok("--warn"), surf=tok("--surface"), trc=tok("--trail");')
rep('return L.circleMarker([o.x[16],o.x[17]],{radius:7,color:land?c:surf,weight:land?2.5:1.5,fillColor:c,fillOpacity:land?.18:.95})',
    'const tw=wtNear(o.x[12],1609); return L.circleMarker([o.x[16],o.x[17]],{radius:tw?8:7,color:tw?trc:(land?c:surf),weight:tw?3:(land?2.5:1.5),fillColor:c,fillOpacity:land?.18:.95})')
rep("if((s&&hd[1]!==s)||(pt&&x[3]!==pt)||(nw&&!x[15]))return;", "if((s&&hd[1]!==s)||(pt&&x[3]!==pt)||(nw&&!x[15])||!wtOK(x[12]))return;")
rep("L.circleMarker([x[16],x[17]],{radius:8,color:land?sp:surf,weight:land?2.5:1.5,fillColor:sp,fillOpacity:land?.2:.95})",
    "L.circleMarker([x[16],x[17]],{radius:8,color:wtNear(x[12],1609)?tok(\"--trail\"):(land?sp:surf),weight:wtNear(x[12],1609)?3:(land?2.5:1.5),fillColor:sp,fillOpacity:land?.2:.95})")
rep("const TL=TR.L.filter(x=>{if((s&&x[8]!==s)||(nw&&!x[14]))return false;", "const TL=TR.L.filter(x=>{if((s&&x[8]!==s)||(nw&&!x[14])||(WTD()&&!WT.t[x[11]]))return false;")

rep('  if(s&&STBOX[s]){const b=STBOX[s];m.fitBounds(',
    '  if(WTD()&&!L0.length&&!nH){const d=WTD(), n=new Set([...Object.values(LS).flatMap(v=>v.map(x=>x[12])),...SH.L.map(x=>x[12])].filter(p=>wtNear(p,d))).size;\n'
    '    document.getElementById("mapcount").textContent=`No water listings within ${d===400?"¼ mile":d===800?"½ mile":"1 mile"} of a major bike trail${s?" in "+NAMES[s]:""}`+(s&&n?` · ${n} nationwide; set the state menu to All states to see them`:"");}\n'
    '  if(s&&STBOX[s]){const b=STBOX[s];m.fitBounds(')

rep('sw=document.getElementById("showwat").checked;', 'sw=document.getElementById("showwat").checked&&!document.getElementById("wtboth").checked;')

# ---- listeners ----
rep('"trtype","trdist","trprice","trall","showtr"]', '"trtype","trdist","trprice","trall","showtr","trwat"]')

JS = r'''
/* ---------- water + trails ---------- */
const WTD=()=>{const e=document.getElementById("wtd"), b=document.getElementById("wtboth");return (e&&+e.value)||(b&&b.checked?1609:0)};
const wtNear=(path,d)=>{const w=WT.w[path];return !!w&&w[1]<=d};
const wtOK=path=>{const d=WTD();return !d||wtNear(path,d)};
const wtGood=n=>!!n&&!/^(n\/?a|none|null|unnamed|unknown|trail)$/i.test(String(n).trim());
const wtDist=m=>m<400?`${m} m`:`${m.toLocaleString()} m (${(m/1609.344).toFixed(1)} mi)`;
function wtText(path){const w=WT.w[path]; if(!w)return""; const t=TR.trails[w[0]]; if(!t)return"";
  const net=wtGood(t[0])?t[0]:(t[1].find(wtGood)||null), seg=wtGood(w[2])?w[2]:(net||"an unnamed trail");
  const kinds=trTags(t).map(k=>TTN[k].toLowerCase()).join(", ");
  return `${wtDist(w[1])} to ${esc(seg)} · ${net&&net!==seg?esc(net)+" network, ":""}${miTxt(t[2])} mi${kinds?" · "+kinds:""}`}
const wtSpan=path=>`<span><span class="tt">Bike trail</span>${wtText(path)}</span>`;
const wtLine=path=>WT.w[path]?`<div class="xtra">${wtSpan(path)}</div>`:"";
const wtPop=path=>WT.w[path]?`<div class="pp-water"><span class="tt">Bike trail</span>${wtText(path)}</div>`:"";
function wtFacts(m){
  const d=WTD()||1609, dl=d===400?"¼ mile":d===800?"½ mile":"1 mile";
  const cnt=paths=>new Set(paths.filter(p=>wtNear(p,d))).size;
  let n=null, txt="";
  if(m==="property")n=cnt(Object.entries(LS).filter(([k])=>k!=="FS"&&k!=="SP").flatMap(([k,v])=>v.map(x=>x[12])));
  else if(m==="springs")n=cnt([...(LS.FS||[]),...(LS.SP||[])].map(x=>x[12]));
  else if(m==="heads")n=cnt(SH.L.map(x=>x[12]));
  else if(m==="map")n=cnt([...Object.values(LS).flatMap(v=>v.map(x=>x[12])),...SH.L.map(x=>x[12])]);
  if(n!=null)txt=`<span class="chip trc"><b>${n}</b> within ${dl} of a major bike trail</span>`;
  if(m==="trails"){const k=TR.L.filter(x=>WT.t[x[11]]).length; if(k)txt=`<span class="chip"><b>${k}</b> also on the water</span>`}
  if(txt)document.getElementById("facts").insertAdjacentHTML("beforeend",txt);
}
setMode=(f=>function(m){f(m);wtFacts(m)})(setMode);
document.getElementById("wtd").addEventListener("change",()=>setMode(mode));
document.getElementById("wtboth").addEventListener("change",()=>setMode(mode));
'''
rep('document.querySelectorAll(".rundate").forEach(e=>e.textContent=fmtD(e.textContent));', JS + 'document.querySelectorAll(".rundate").forEach(e=>e.textContent=fmtD(e.textContent));')
open(page, "w").write(h)
print("water+trail edits applied")
