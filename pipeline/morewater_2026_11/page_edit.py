"""Put the extra waters on the page: Lakes and Rivers tab rows (after each state's top 5, under a divider), the Property tab's
water list (PR), the tab introductions and counts. Idempotent. Usage: page_edit.py <page.html> <extra.json>"""
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
    assert h.count(old) == count, (h.count(old), old[:80]); h = h.replace(old, new)
LK, _, _ = obj("LK"); RV, _, _ = obj("RV"); PR, _, _ = obj("PR")
if any(r.get("x") for v in LK.values() for r in v["rows"]) or any(r.get("x") for v in RV.values() for r in v["rows"]):
    print("extra waters already on the page"); sys.exit()
nl = nr = 0
for st, t in ex["tab"].items():
    if t["l"]:
        LK.setdefault(st, {"q": 0, "rows": []})["rows"] += t["l"]; nl += len(t["l"])
    if t["r"]:
        RV.setdefault(st, {"q": 0, "rows": []})["rows"] += t["r"]; nr += len(t["r"])
for st, rows in ex["PR"].items():
    PR.setdefault(st, []).extend(rows)
put("LK", LK); put("RV", RV); put("PR", PR)

# divider before the extra rows, and a header pill that counts them
rep('''  let h=`<article class="state"><div class="shead"><h2>${esc(NAMES[k])}<span class="ab">${k}</span></h2>${pill(st,"5 ranked")}</div><ol>`;
  shown.forEach(r=>{const rank=rows.indexOf(r)+1; const notes=[];''',
    '''  const nx=rows.filter(r=>r.x).length; let sep=0;
  let h=`<article class="state"><div class="shead"><h2>${esc(NAMES[k])}<span class="ab">${k}</span></h2>${pill(st,nx?`5 ranked + ${nx} more`:"5 ranked")}</div><ol>`;
  shown.forEach(r=>{const rank=rows.indexOf(r)+1; const notes=[];
    if(r.x&&!sep){sep=1;h+=`<li class="xsep">Also clearer than 20 ft</li>`}''')
rep('''  let h=`<article class="state"><div class="shead"><h2>${esc(NAMES[k])}<span class="ab">${k}</span></h2>${pill(st,"5 ranked")}</div><ol>`;
  shown.forEach(r=>{const rank=rows.indexOf(r)+1; const notes=rNotes(r.m,r.b,r.px);''',
    '''  const nx=rows.filter(r=>r.x).length; let sep=0;
  let h=`<article class="state"><div class="shead"><h2>${esc(NAMES[k])}<span class="ab">${k}</span></h2>${pill(st,nx?`5 ranked + ${nx} more`:"5 ranked")}</div><ol>`;
  shown.forEach(r=>{const rank=rows.indexOf(r)+1; const notes=rNotes(r.m,r.b,r.px);
    if(r.x&&!sep){sep=1;h+=`<li class="xsep">Also under 2 NTU</li>`}''')
rep("\n/* leaflet */\n", """
li.xsep{list-style:none;display:block;margin:10px 0 2px;padding:6px 0 4px;border-top:1px dashed var(--rule);font-size:12px;font-weight:650;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
\n/* leaflet */\n""")
# lstat/rstat: a full state stays "full" when extra rows are present (they all meet the threshold)
rep('''document.getElementById("facts").innerHTML=`<span class="chip"><b>${c.full}</b> states with five ranked ${w}</span>''',
    '''const nX=Object.values(m==="lakes"?LK:RV).reduce((a,v)=>a+v.rows.filter(r=>r.x).length,0);
  document.getElementById("facts").innerHTML=`<span class="chip"><b>${c.full}</b> states with five ranked ${w}</span><span class="chip"><b>${nX}</b> more ${m==="lakes"?"lakes clearer than 20 ft":"rivers under 2 NTU"}</span>''')
rep('lakes:"The five clearest lakes in each state, ranked by long-term average Secchi depth: how far down a black-and-white disk stays visible.',
    'lakes:"The five clearest lakes in each state, ranked by long-term average Secchi depth: how far down a black-and-white disk stays visible, followed by every other lake in the state that averages clearer than 20 ft.')
rep('rivers:"The five clearest rivers in each state, ranked by median turbidity: how much suspended sediment and algae scatter light, in nephelometric turbidity units (NTU). Lower is clearer.',
    'rivers:"The five clearest rivers in each state, ranked by median turbidity: how much suspended sediment and algae scatter light, in nephelometric turbidity units (NTU). Lower is clearer. Every other river in the state with a median under 2 NTU follows the top five.')
open(page, "w").write(h)
print("page: +", nl, "lakes, +", nr, "rivers on the tabs; property list +", sum(len(v) for v in ex["PR"].values()), "waters")
