"""Put the Great Lakes shorelines on the page (Lakes tab rows, Property list) and teach every place that labels a water to say
"Great Lakes shoreline". Idempotent. Usage: page_edit3.py <page.html> <extra3.json> [patch_page.py]"""
import json, sys
page, ex = sys.argv[1], json.load(open(sys.argv[2]))
h = open(page).read()
def obj(name):
    i = h.find("const " + name + "="); o, end = json.JSONDecoder().raw_decode(h[i + len("const " + name + "="):]); return o, i, i + len("const " + name + "=") + end
def put(name, val):
    global h
    o, a, b = obj(name); h = h[:a] + "const " + name + "=" + json.dumps(val, separators=(",", ":"), ensure_ascii=False) + h[b:]
def rep(old, new, txt=None):
    global h
    t = h if txt is None else txt
    assert t.count(old) == 1, (t.count(old), old[:100])
    t = t.replace(old, new)
    if txt is None: h = t
    return t
LK, _, _ = obj("LK"); PR, _, _ = obj("PR")
if any(r.get("gl") for v in LK.values() for r in v["rows"]):
    print("already applied"); sys.exit()
for st, rows in ex["tab"].items(): LK.setdefault(st, {"q": 0, "rows": []})["rows"] += rows
for st, rows in ex["PR"].items(): PR.setdefault(st, []).extend(rows)
put("LK", LK); put("PR", PR)
# Lakes tab
rep('''  const nx=rows.filter(r=>r.x).length; let sep=0;''', '''  const nx=rows.filter(r=>r.x&&!r.gl).length; let sep="";''')
rep('''  shown.forEach(r=>{const rank=rows.indexOf(r)+1; const notes=[];
    if(r.x&&!sep){sep=1;h+=`<li class="xsep">Also clearer than 20 ft</li>`}''',
'''  shown.forEach(r=>{const rank=rows.indexOf(r)+1; const notes=[]; const g=r.x?(r.g||"x"):"";
    if(g&&g!==sep){sep=g;h+=`<li class="xsep">${g==="gl"?"Great Lakes shoreline":"Also clearer than 20 ft"}</li>`}
    if(r.gl){h+=`<li class="row"><span class="rk">·</span><div class="nm">${esc(r.n)}<small>${esc(r.note)} · <a href="${esc(r.src)}" target="_blank" rel="noopener">${esc(r.srcn)}</a></small></div><div class="val"><b>~${r.ft}</b> <span class="u">ft</span><span class="sub">${r.m} m · open water</span></div></li>`;return}''')
rep('''const nX=Object.values(m==="lakes"?LK:RV).reduce((a,v)=>a+v.rows.filter(r=>r.x&&!r.nm).length,0),''',
    '''const nX=Object.values(m==="lakes"?LK:RV).reduce((a,v)=>a+v.rows.filter(r=>r.x&&!r.nm&&!r.gl).length,0), nG=Object.values(LK).reduce((a,v)=>a+v.rows.filter(r=>r.gl).length,0),''')
rep('''${m==="rivers"&&nM?`<span class="chip"><b>${nM}</b> known clear, not measured</span>`:""}''',
    '''${m==="rivers"&&nM?`<span class="chip"><b>${nM}</b> known clear, not measured</span>`:""}${m==="lakes"&&nG?`<span class="chip"><b>${nG}</b> Great Lakes shorelines</span>`:""}''')
rep('''followed by every other lake in the state that averages clearer than 20 ft.''',
    '''followed by every other lake in the state that averages clearer than 20 ft, then the state's Great Lakes shoreline, with open-lake clarity from published surveys (water near shore is often less clear).''')
# Property list (also in the page patcher, which regenerates this code on every refresh)
P_REPS = [
    ('''<span class="rk type">${r[0]==="l"?"Lake":"River"}</span>''', '''<span class="rk type">${r[0]==="l"?"Lake":r[0]==="g"?"Great Lake":"River"}</span>'''),
    ('''<small>${r[2]?`#${r[2]} ${r[0]==="l"?"clearest lake":"clearest river"} · ${esc(r[3])}`:"Known for clear water · not measured"}${cty?` · ${esc(cty)} ${k==="LA"?"Parish":"Co."}`:""}''',
     '''<small>${r[0]==="g"?`Great Lakes shoreline · ${esc(r[3])} · only listings on the lake`:r[2]?`#${r[2]} ${r[0]==="l"?"clearest lake":"clearest river"} · ${esc(r[3])}`:"Known for clear water · not measured"}${cty?` · ${r[0]==="g"&&r[5].length>3?r[5].length+" counties":esc(cty)+" "+(k==="LA"?"Parish":"Co.")}`:""}'''),
    ('''<div class="links"><a href="${zUrl(r[4],"waterfront")}" target="_blank" rel="noopener">Zillow waterfront</a><a class="alt" href="${zUrl(r[4],null)}" target="_blank" rel="noopener">Zillow all</a>${lw}</div></li>`});''',
     '''${r[0]==="g"?(r[5].length>3?"":`<div class="links">${lw}</div>`):`<div class="links"><a href="${zUrl(r[4],"waterfront")}" target="_blank" rel="noopener">Zillow waterfront</a><a class="alt" href="${zUrl(r[4],null)}" target="_blank" rel="noopener">Zillow all</a>${lw}</div>`}</li>`});'''),
]
for o, n in P_REPS: rep(o, n)
# water labels in map popups, tooltips and the map's place search
rep('''t:r[0]==="l"?"lake":"river",st:k,rank:r[2]}''', '''t:r[0]==="l"?"lake":r[0]==="g"?"gl":"river",st:k,rank:r[2]}''')
rep('''(${w.rank?`#${w.rank} `:"clear, unmeasured "}${w.t}${w.t==="lake"||w.t==="river"?" in "+esc(NAMES[w.st]):""}''',
    '''(${w.t==="gl"?"Great Lakes shoreline in "+esc(NAMES[w.st]):`${w.rank?`#${w.rank} `:"clear, unmeasured "}${w.t}${w.t==="lake"||w.t==="river"?" in "+esc(NAMES[w.st]):""}`}''')
rep('''<br>${w.rank?`#${w.rank} `:"Known clear, not measured · "}${w.t}${w.t==="lake"||w.t==="river"?" in "+esc(NAMES[w.st]):""}`''',
    '''<br>${w.t==="gl"?"Great Lakes shoreline in "+esc(NAMES[w.st]):`${w.rank?`#${w.rank} `:"Known clear, not measured · "}${w.t}${w.t==="lake"||w.t==="river"?" in "+esc(NAMES[w.st]):""}`}`''')
rep('''`${r[1]} · ${r[2]?`#${r[2]} `:"known clear "}${r[0]==="l"?"lake":"river"} in ${NAMES[k]} · ${r[3]}`''',
    '''`${r[1]} · ${r[0]==="g"?"Great Lakes shoreline":`${r[2]?`#${r[2]} `:"known clear "}${r[0]==="l"?"lake":"river"}`} in ${NAMES[k]} · ${r[3]}`''')
for a, b in [('MI:"Excludes Lake Michigan and Lake Superior."', 'MI:"The Great Lakes aren\'t in the ranking; their shorelines are listed above."'), ('WI:"Excludes Lake Michigan and Lake Superior."', 'WI:"The Great Lakes aren\'t in the ranking; their shorelines are listed above."'), ('MN:"Excludes Lake Superior."', 'MN:"Lake Superior isn\'t in the ranking; its shoreline is listed above."')]: rep(a, b)
open(page, "w").write(h)
if len(sys.argv) > 3:
    pp = open(sys.argv[3]).read()
    if 'r[0]==="g"?"Great Lake"' not in pp:
        for o, n in P_REPS: pp = rep(o, n, pp)
        open(sys.argv[3], "w").write(pp); print("patch_page.py updated")
print("page: +", sum(len(v) for v in ex["tab"].values()), "lake rows; property list +", sum(len(v) for v in ex["PR"].values()))
