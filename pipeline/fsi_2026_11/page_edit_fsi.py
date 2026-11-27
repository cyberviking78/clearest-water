"""Put the Florida Springs Institute pass on the page (Nov 25, 2026). Idempotent.
- const FSI: every spring on the Institute's map [lat, lon, name, county, magnitude (4 = 4th or smaller), look, photo, report, words]
  (look from looks.py: "blue", "clear", "tint" or ""; photo/report paths are relative to FSIU unless they start with http).
- const FSB: the clear-blue springs added by build_fsi.py, same row layout as FSD.springs plus [19] magnitude, [20] vents.
- Each Florida spring and springhead is matched to the Institute's spring at runtime (fsiFind: same first name word within 1.5 km,
  else the nearest within 300 m; among matches, one with a rating, then one with a photo, then the nearest), so the matching
  survives every listings refresh.
- Springs tab: look badge, survey words, photo and water-quality report on each Florida spring; an "Also clear and blue" section
  for FSB; Springheads tab: the same on Florida springheads; map: look in spring tooltips and springhead popups.
- A "Spring look" menu on the Springs, Springheads and Map tabs: clear blue only / clear or blue / has a photo (Florida only).
renderSprings lives in the block patch_page.py rewrites on every refresh, so the same edits are made to patch_page.py's RENDER.
Usage: page_edit_fsi.py <page.html> [patch_page.py]"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
page = sys.argv[1]; pp = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(HERE), "patch_page.py")
h = open(page).read()
PRE = "https://floridaspringsinstitute.org/wp-content/uploads/"
FSI = [[r[0], r[1], r[2], r[3], r[4], r[5], r[6][len(PRE):] if r[6].startswith(PRE) else r[6], r[7][len(PRE):] if r[7].startswith(PRE) else r[7],
        r[8] if (r[5] or r[6]) else ""] for r in json.load(open(HERE + "/fsi.json"))]
FSB = json.load(open(HERE + "/fsb.json"))
J = lambda o: json.dumps(o, separators=(",", ":"), ensure_ascii=False)
data = "const FSI=" + J(FSI) + ";\nconst FSB=" + J(FSB) + ";\n"
if "const FSI=" in h:     # already on the page (later fixes build on these edits): refresh the data only
    h = re.sub(r"const FSI=\[.*?\];\nconst FSB=\[.*?\];\n", lambda m: data, h, count=1, flags=re.S)
    open(page, "w").write(h); print("FSI/FSB data refreshed"); sys.exit()
else:
    assert h.count("const SRC=[") == 1; h = h.replace("const SRC=[", data + "const SRC=[")

def rep(old, new, text=None):
    global h
    t = h if text is None else text
    if new in t: return t
    assert t.count(old) == 1, (t.count(old), old[:100])
    t = t.replace(old, new)
    if text is None: h = t
    return t

# ---------- renderSprings (also in patch_page.py RENDER) ----------
RS = [
 ('const S=FSD.springs.map((r,i)=>[r,i+1]).filter(([r])=>hitS(r)&&keep(r[17],r[0]));',
  'const S=FSD.springs.map((r,i)=>[r,i+1]).filter(([r])=>hitS(r)&&keep(r[17],r[0])&&fsiOKs(r));'),
 ('''${n} readings · ${yrs} years, ${y0}–${y1}${sites>1?` · ${sites} sites`:""}</small></div>${val(m,a,b)}
      ${block(g,wi)}''',
  '''${n} readings · ${yrs} years, ${y0}–${y1}${sites>1?` · ${sites} sites`:""}</small></div>${val(m,a,b)}
      ${fsiBox(fsiRow(r))}${block(g,wi)}'''),
 ('''  if(!S.length)h+=`<li class="row"><span></span><div class="nm"><small>No springs match.</small></div></li>`;
''',
  '''  if(!S.length)h+=`<li class="row"><span></span><div class="nm"><small>No springs match.</small></div></li>`;
  const B=(typeof FSB!=="undefined"?FSB:[]).filter(r=>hitS(r)&&keep(r[17],r[0])&&fsiOKs(r));
  if(B.length){h+=`</ol></article><article class="state nat"><div class="shead"><h2>Also clear and blue · Florida field surveys</h2><span class="count">${B.length} of ${FSB.length}</span></div><p class="fsinote">Florida springs the state's field surveys describe as clear and blue that aren't in the ranking above, most because they have fewer than 6 turbidity readings. Found through the Florida Springs Institute; sorted by size.</p><ol>`;
    B.forEach(r=>{const [wi,name,cty,m,a,b,n,yrs,y0,y1,sites,runs,bb,lwp,ploc,meth,st,g,ll,mag,nv]=r;
      h+=`<li class="row"><span class="rk mg" title="Magnitude ${mag}">M${mag}</span><div class="nm">${esc(name)}<span class="st-tag">${st}</span><small>${esc(cty)} Co., ${esc(NAMES[st])} · magnitude ${mag}${nv>1?` · ${nv} vents`:""} · ${runs?`flows into ${esc(runs)} · `:""}${n?`${n} turbidity reading${n>1?"s":""}, ${y0===y1?y0:`${y0}–${y1}`}`:"no turbidity readings on record"}</small></div>${m!=null?val(m,a,b):`<div class="val"><span class="sub">no turbidity record</span></div>`}
      ${fsiBox(fsiRow(r))}${block(g,wi)}<div class="links"><a href="${zUrl(zb(bb),"waterfront")}" target="_blank" rel="noopener">Zillow waterfront</a><a class="alt" href="${zUrl(zb(bb),null)}" target="_blank" rel="noopener">Zillow all</a><a class="alt" href="${LW+esc(lwp)}" target="_blank" rel="noopener">LandWatch: ${esc(cty)}</a></div></li>`})}
'''),
]
for old, new in RS: rep(old, new)
P = open(pp).read()
for old, new in RS: P = rep(old, new, P)
open(pp, "w").write(P)

# ---------- helpers ----------
JS = r'''/* ---------- Florida Springs Institute: how each Florida spring looks (pipeline/fsi_2026_11) ---------- */
const FSIU="https://floridaspringsinstitute.org/wp-content/uploads/";
const FSIL={blue:["Clear blue","fl-blue"],clear:["Clear","fl-clear"],tint:["Tannic or murky","fl-tint"]};
const FSISTOP=new Set(["spring","springs","main","head","the","upper","lower","rise","seep","sink","vent","boil","run","complex","group","of","st","saint"]);
const FSIC=new Map();
function fsiTok(n){const w=(String(n||"").toLowerCase().replace(/\(.*?\)|#\s*\w+|\d+/g," ").match(/[a-z]+/g)||[]).filter(x=>!FSISTOP.has(x));return w[0]||""}
function fsiFind(lat,lon,name){
  if(lat==null||lon==null||typeof FSI==="undefined")return null;
  const key=lat.toFixed(5)+","+lon.toFixed(5)+","+name; if(FSIC.has(key))return FSIC.get(key);
  const t=fsiTok(name), cl=Math.cos(lat*Math.PI/180); let best=null, bs=null;
  for(const r of FSI){const d=Math.hypot((r[0]-lat)*111200,(r[1]-lon)*111200*cl); if(d>1500)continue;
    const nm=!!t&&fsiTok(r[2])===t; if(!nm&&d>300)continue;
    const s=[nm?0:1,r[5]?0:1,r[6]?0:1,d]; if(!bs||s[0]<bs[0]||(s[0]===bs[0]&&(s[1]<bs[1]||(s[1]===bs[1]&&(s[2]<bs[2]||(s[2]===bs[2]&&s[3]<bs[3]))))))bs=s,best=r}
  FSIC.set(key,best); return best}
function fsiRow(r){if(r[16]!=="FL")return null; const d=r[18]||[(r[12][1]+r[12][3])/2,(r[12][0]+r[12][2])/2]; return fsiFind(d[0],d[1],r[1])}
function fsiHead(hd){return hd[1]==="FL"?fsiFind(hd[8],hd[9],hd[0]):null}
function fsiWant(){const e=document.getElementById("fsilook");return e?e.value:""}
function fsiPass(f){const v=fsiWant(); if(!v)return true; if(!f)return false;
  return v==="blue"?f[5]==="blue":v==="clear"?(f[5]==="blue"||f[5]==="clear"):v==="photo"?!!f[6]:true}
const fsiOKs=r=>!fsiWant()||fsiPass(fsiRow(r)), fsiOKh=hd=>!fsiWant()||fsiPass(fsiHead(hd));
const fsiUrl=p=>p?(/^https?:/.test(p)?p:FSIU+p):"";
function fsiBadge(f){const l=f&&FSIL[f[5]]; return l?`<span class="fl ${l[1]}">${l[0]}</span>`:""}
function fsiBox(f){if(!f||!(f[5]||f[6]||f[7]))return "";
  const img=fsiUrl(f[6]), pdf=fsiUrl(f[7]);
  return `<div class="fsi">${img?`<a class="fsi-ph" href="${esc(img)}" target="_blank" rel="noopener"><img src="${esc(img)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.parentNode.remove()"></a>`:""}<div>${fsiBadge(f)||`<span class="fl">Look not described</span>`} <span class="fsi-src">Florida Springs Institute${f[2]?`: ${esc(f[2])}`:""}</span>${f[8]?`<q>${esc(f[8])}</q>`:""}<span class="fsi-l">${img?`<a href="${esc(img)}" target="_blank" rel="noopener">Photo</a>`:""}${pdf?`<a href="${esc(pdf)}" target="_blank" rel="noopener">Water-quality report</a>`:""}</span></div></div>`}
function fsiPop(f){if(!f||!(f[5]||f[6]))return "";const img=fsiUrl(f[6]);
  return `<div class="pp-sub">${fsiBadge(f)||"Florida Springs Institute"}${f[8]?` <i>${esc(f[8].length>160?f[8].slice(0,157)+"…":f[8])}</i>`:""}${img?` <a href="${esc(img)}" target="_blank" rel="noopener">Photo</a>`:""}</div>`}
function fsiWord(f){const l=f&&FSIL[f[5]];return l?" · "+l[0].toLowerCase():""}
'''
rep("/* ---------- map tab ---------- */", JS + "/* ---------- map tab ---------- */")

CSS = '''
/* Florida Springs Institute look ratings */
.fl{display:inline-block;font-size:11.5px;font-weight:700;letter-spacing:.02em;border-radius:4px;padding:1px 7px;background:var(--rule);color:var(--ink);white-space:nowrap}
.fl.fl-blue{background:color-mix(in srgb,#1e88e5 20%,var(--surface));color:color-mix(in srgb,#1565c0 75%,var(--ink))}
.fl.fl-clear{background:color-mix(in srgb,#26a69a 20%,var(--surface));color:color-mix(in srgb,#00796b 75%,var(--ink))}
.fl.fl-tint{background:color-mix(in srgb,#a1662f 20%,var(--surface));color:color-mix(in srgb,#7a4a1e 75%,var(--ink))}
.fsi{grid-column:2/-1;display:flex;gap:10px;align-items:flex-start;font-size:12.5px;color:var(--muted);margin:6px 0 2px}
.fsi-ph{flex:none;line-height:0}.fsi-ph img{width:96px;height:64px;object-fit:cover;border-radius:6px;border:1px solid var(--rule)}
.fsi q{display:block;margin-top:3px;font-style:italic;quotes:"“" "”"}
.fsi-src{font-size:11.5px}
.fsi-l{display:flex;gap:12px;margin-top:3px}.fsi-l a{color:var(--lake);font-weight:600}
.fsinote{font-size:13px;color:var(--muted);margin:4px 0 10px}
'''
rep("/* springheads */", CSS.strip("\n") + "\n/* springheads */")

# ---------- control ----------
rep('<label class="toggle" data-mode="property springs" hidden><input id="haslist" type="checkbox"> Only waters with listings</label>',
    '<label class="toggle" data-mode="property springs" hidden><input id="haslist" type="checkbox"> Only waters with listings</label>\n'
    '  <select id="fsilook" aria-label="Spring look" data-mode="springs heads map" hidden><option value="">Spring look: any</option><option value="blue">Clear blue springs only (Florida)</option><option value="clear">Clear or blue springs (Florida)</option><option value="photo">Springs with a photo (Florida)</option></select>')
rep('"octype","ocprice","showoc"]', '"octype","ocprice","showoc","fsilook"]')

# ---------- Springheads tab ----------
rep("const headOK=hd=>(!s||hd[1]===s)&&hd[3]<=mx&&(!rc||recentOK(hd));", "const headOK=hd=>(!s||hd[1]===s)&&hd[3]<=mx&&(!rc||recentOK(hd))&&fsiOKh(hd);")
rep('''${pub?" · on public land":""}</small></div><span></span>
    ${body||""}''', '''${pub?" · on public land":""}</small></div><span></span>
    ${fsiBox(fsiHead(hd))}${body||""}''')
rep('''near the vent</span>`:""}</div>
    ${wtPop(path)}''', '''near the vent</span>`:""}</div>${fsiPop(fsiHead(hd))}
    ${wtPop(path)}''')

# ---------- listings on springs: name the new springs, show the look ----------
rep('''  FSD.springs.forEach((r,i)=>{(W[r[17]]=W[r[17]]||{})[r[0]]={n:r[1],t:"spring",st:r[16],rank:i+1}});''',
    '''  FSD.springs.forEach((r,i)=>{(W[r[17]]=W[r[17]]||{})[r[0]]={n:r[1],t:"spring",st:r[16],rank:i+1,fr:r}});
  (typeof FSB!=="undefined"?FSB:[]).forEach(r=>{(W[r[17]]=W[r[17]]||{})[r[0]]={n:r[1],t:"spring",st:r[16],rank:0,fsb:1,fr:r}});''')
rep('''${w.rank?`#${w.rank} `:"clear, unmeasured "}${w.t}''', '''${w.rank?`#${w.rank} `:w.fsb?"clear blue ":"clear, unmeasured "}${w.t}''')
rep('''${w.dist!=null?`, ${w.dist} m from shore`:""})</span>`).join("<br>");''',
    '''${w.dist!=null?`, ${w.dist} m from shore`:""}${w.fr?fsiWord(fsiRow(w.fr)):""})</span>`).join("<br>");''')

# ---------- map ----------
rep('''`${w.rank?`#${w.rank} `:"Known clear, not measured · "}${w.t}''', '''`${w.rank?`#${w.rank} `:w.fsb?"Clear blue by field survey · ":"Known clear, not measured · "}${w.t}''')
rep('''    FSD.springs.forEach((r,i)=>{if(s&&s!==r[16])return;const b=r[12],d=r[18];add(d?d[0]:(b[1]+b[3])/2,d?d[1]:(b[0]+b[2])/2,`${r[1]} · #${i+1} spring · ${r[3]} NTU`)});''',
    '''    FSD.springs.forEach((r,i)=>{if(s&&s!==r[16])return;if(!fsiOKs(r))return;const b=r[12],d=r[18];add(d?d[0]:(b[1]+b[3])/2,d?d[1]:(b[0]+b[2])/2,`${r[1]} · #${i+1} spring · ${r[3]} NTU${fsiWord(fsiRow(r))}`)});
    (typeof FSB!=="undefined"?FSB:[]).forEach(r=>{if(s&&s!==r[16])return;if(!fsiOKs(r))return;add(r[18][0],r[18][1],`${r[1]} · clear blue spring (field survey)${r[3]!=null?` · ${r[3]} NTU`:""}`)});''')
rep('''      if((s&&hd[1]!==s)||(pt&&x[3]!==pt)||(nw&&!x[15])||!wtOK(x[12]))return;''',
    '''      if((s&&hd[1]!==s)||(pt&&x[3]!==pt)||(nw&&!x[15])||!wtOK(x[12])||!fsiOKh(hd))return;''')
rep('''${l.options.q!=null?`; last measured at about ${geoCfs(l.options.q)} cfs`:""}</div><div class="pp-links"></div>`,{maxWidth:300});''',
    '''${l.options.q!=null?`; last measured at about ${geoCfs(l.options.q)} cfs`:""}</div>${fsiPop(fsiFind(l.getLatLng().lat,l.getLatLng().lng,l.options.nm))}<div class="pp-links"></div>`,{maxWidth:300});''')

# ---------- facts, notes, source ----------
rep('''<span class="chip"><b>${FSD.rivers.length}</b> spring-fed rivers</span>''',
    '''<span class="chip"><b>${FSD.rivers.length}</b> spring-fed rivers</span><span class="chip"><b>${FSB.length}</b> more clear-blue Florida springs</span>''')
NOTE = ('''  <p><b>How each Florida spring looks.</b> Turbidity alone can't tell a sapphire-blue spring from a tea-coloured one: tannic water can still test very clear. '''
        '''The <a href="https://floridaspringsinstitute.org/springs-map-2-0/" target="_blank" rel="noopener">Florida Springs Institute's springs map</a> carries the Florida Geological Survey's field description of 1,011 Florida springs, with a photo for 441 and a water-quality report for 158. '''
        '''Each description was read for what it says about the spring's own water (not the river it runs into): <b>Clear blue</b> when it's called blue, bluish, blue-green or turquoise; <b>Clear</b> when it's called clear but not blue; '''
        '''<b>Tannic or murky</b> when it's called tannic, tea-coloured, dark, brown, murky, turbid or cloudy (only "slightly" murky water that's also called clear counts as clear). '''
        '''A description is one visit, often 2001–2003; a spring can look different after heavy rain or when its river floods it, so use the photo to judge. '''
        '''Florida springs and springheads show the rating, the survey's words, the photo and the report link, and the <b>Spring look</b> menu narrows the list to clear blue springs, clear or blue springs, or springs with a photo. Springs in other states have no rating, so the menu shows Florida only.</p>\n'''
        '''  <p><b>Also clear and blue</b> lists 19 Florida springs the surveys describe as clear and blue that weren't in the ranking, most because they have fewer than 6 turbidity readings. Two more were left out because the Water Quality Portal's turbidity within 600 m of the vents has a median over 2 NTU (Natural Bridge Rise and Sandbag Spring); those with no turbidity record are kept on the strength of the survey and say so. Their runs were traced 5 km downstream like the others, and their listings come with the regular refresh.</p>\n''')
rep('''the runs and the rivers they feed are where private frontage is.</p>\n</section>''',
    '''the runs and the rivers they feed are where private frontage is.</p>\n''' + NOTE + '''</section>''')
SRCL = ' ["Florida Springs Institute: Interactive Florida Springs Map (Florida Geological Survey spring descriptions, photos, water-quality reports)","https://floridaspringsinstitute.org/springs-map-2-0/"],\n'
if "springs-map-2-0/\"]" not in h:
    i = h.index("const SRC=[") + len("const SRC=["); nl = h.index("\n", i - 1)
    h = h[:i] + "\n" + SRCL.rstrip("\n") + h[i:] if h[i] != "\n" else h[:i + 1] + SRCL + h[i + 1:]
open(page, "w").write(h); print("page updated", len(h) // 1024, "KB")
