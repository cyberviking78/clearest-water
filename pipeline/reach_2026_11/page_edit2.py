"""Put the clear river stretches and the known-clear (not measured) waters on the page, and teach every place that shows a
water's rank to handle "not measured". Idempotent. Usage: page_edit2.py <page.html> <extra2.json> [patch_page.py]"""
import json, re, sys
page, ex = sys.argv[1], json.load(open(sys.argv[2]))
h = open(page).read()
def obj(name):
    i = h.find("const " + name + "="); o, end = json.JSONDecoder().raw_decode(h[i + len("const " + name + "="):]); return o, i, i + len("const " + name + "=") + end
def put(name, val):
    global h
    o, a, b = obj(name); h = h[:a] + "const " + name + "=" + json.dumps(val, separators=(",", ":"), ensure_ascii=False) + h[b:]
def rep(old, new, count=1):
    global h
    assert h.count(old) == count, (h.count(old), old[:90]); h = h.replace(old, new)
RV, _, _ = obj("RV"); PR, _, _ = obj("PR")
if any(r.get("g") in ("reach", "nm") for v in RV.values() for r in v["rows"]):
    print("already applied"); sys.exit()
for st, rows in ex["tab"].items():
    RV.setdefault(st, {"q": 0, "rows": []})["rows"] += rows
for st, rows in ex["PR"].items(): PR.setdefault(st, []).extend(rows)
put("RV", RV); put("PR", PR)
# Rivers tab: a divider for each kind of extra row; not-measured rows show their source instead of numbers
rep('''  const nx=rows.filter(r=>r.x).length; let sep=0;
  let h=`<article class="state"><div class="shead"><h2>${esc(NAMES[k])}<span class="ab">${k}</span></h2>${pill(st,nx?`5 ranked + ${nx} more`:"5 ranked")}</div><ol>`;
  shown.forEach(r=>{const rank=rows.indexOf(r)+1; const notes=rNotes(r.m,r.b,r.px);
    if(r.x&&!sep){sep=1;h+=`<li class="xsep">Also under 2 NTU</li>`}''',
'''  const nx=rows.filter(r=>r.x).length; let sep="";
  const XS={x:"Also under 2 NTU",reach:"Clear stretches of other rivers",nm:"Known for clear water · not measured"};
  let h=`<article class="state"><div class="shead"><h2>${esc(NAMES[k])}<span class="ab">${k}</span></h2>${pill(st,nx?`5 ranked + ${nx} more`:"5 ranked")}</div><ol>`;
  shown.forEach(r=>{const rank=rows.indexOf(r)+1; const notes=r.nm?[]:rNotes(r.m,r.b,r.px); const g=r.x?(r.g||"x"):"";
    if(g&&g!==sep){sep=g;h+=`<li class="xsep">${XS[g]}</li>`}
    if(r.nm){h+=`<li class="row"><span class="rk">·</span><div class="nm">${esc(r.n)}<small>${esc(r.note)} · <a href="${esc(r.src)}" target="_blank" rel="noopener">${esc(r.srcn)}</a></small></div><div class="val"><b>—</b><span class="sub">not measured</span></div></li>`;return}''')
rep('''const nX=Object.values(m==="lakes"?LK:RV).reduce((a,v)=>a+v.rows.filter(r=>r.x).length,0);''',
    '''const nX=Object.values(m==="lakes"?LK:RV).reduce((a,v)=>a+v.rows.filter(r=>r.x&&!r.nm).length,0), nM=Object.values(RV).reduce((a,v)=>a+v.rows.filter(r=>r.nm).length,0);''')
rep('''<span class="chip"><b>${nX}</b> more ${m==="lakes"?"lakes clearer than 20 ft":"rivers under 2 NTU"}</span>''',
    '''<span class="chip"><b>${nX}</b> more ${m==="lakes"?"lakes clearer than 20 ft":"rivers or river stretches under 2 NTU"}</span>${m==="rivers"&&nM?`<span class="chip"><b>${nM}</b> known clear, not measured</span>`:""}''')
rep('Every other river in the state with a median under 2 NTU follows the top five.',
    'Every other river in the state with a median under 2 NTU follows the top five, then the clearest monitored stretch of rivers whose whole-length median is higher (judged on the stations along that stretch), then a few rivers well known for clear water that have no turbidity record, marked as not measured.')
# 1.96 should not read as "2.0" on a list of waters under 2
rep('const nt=r=>r.b>=50?"&lt; RL":(r.m<1?r.m.toFixed(2):', 'const nt=r=>r.b>=50?"&lt; RL":(r.m<1||(r.m>=1.95&&r.m<2)?r.m.toFixed(2):')
rep('.xsep{list-style:none;display:block;margin:10px 0 2px;padding:6px 0 4px;', '.row .nm small a{color:var(--lake)}.xsep{list-style:none;display:block;margin:10px 0 2px;padding:6px 10px 4px;')
# ranks that can be missing
PROP_OLD = '''<small>#${r[2]} ${r[0]==="l"?"clearest lake":"clearest river"} · ${esc(r[3])}'''
PROP_NEW = '''<small>${r[2]?`#${r[2]} ${r[0]==="l"?"clearest lake":"clearest river"} · ${esc(r[3])}`:"Known for clear water · not measured"}'''
rep(PROP_OLD, PROP_NEW)
rep('''(#${w.rank} ${w.t}${w.t==="lake"||w.t==="river"?" in "+esc(NAMES[w.st]):""}''', '''(${w.rank?`#${w.rank} `:"clear, unmeasured "}${w.t}${w.t==="lake"||w.t==="river"?" in "+esc(NAMES[w.st]):""}''')
rep('''<br>#${w.rank} ${w.t}${w.t==="lake"||w.t==="river"?" in "+esc(NAMES[w.st]):""}`''', '''<br>${w.rank?`#${w.rank} `:"Known clear, not measured · "}${w.t}${w.t==="lake"||w.t==="river"?" in "+esc(NAMES[w.st]):""}`''')
rep('''`${r[1]} · #${r[2]} ${r[0]==="l"?"lake":"river"} in ${NAMES[k]} · ${r[3]}`''', '''`${r[1]} · ${r[2]?`#${r[2]} `:"known clear "}${r[0]==="l"?"lake":"river"} in ${NAMES[k]} · ${r[3]}`''')
open(page, "w").write(h)
if len(sys.argv) > 3:   # the monthly page patcher regenerates the Property list code, so it needs the same change
    pp = open(sys.argv[3]).read()
    if PROP_OLD in pp: open(sys.argv[3], "w").write(pp.replace(PROP_OLD, PROP_NEW)); print("patch_page.py updated")
print("page: +", sum(len(v) for v in ex["tab"].values()), "river rows; property list +", sum(len(v) for v in ex["PR"].values()))
