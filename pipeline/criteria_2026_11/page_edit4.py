"""Put the second pass of extra waters (lakes 15-20 ft "x15", rivers 2-3 NTU "x3"; out/extra.json from newwaters15.py) on the
page: Lakes/Rivers tab rows under their own dividers, the Property list, counts and introductions. Idempotent.
Usage: page_edit4.py <page.html> <extra.json>"""
import json, sys
page, ex = sys.argv[1], json.load(open(sys.argv[2]))
h = open(page).read()
def obj(name):
    i = h.find("const " + name + "="); o, end = json.JSONDecoder().raw_decode(h[i + len("const " + name + "="):]); return o, i, i + len("const " + name + "=") + end
def put(name, val):
    global h
    o, a, b = obj(name); h = h[:a] + "const " + name + "=" + json.dumps(val, separators=(",", ":"), ensure_ascii=False) + h[b:]
def rep(old, new):
    global h
    assert h.count(old) == 1, (h.count(old), old[:90]); h = h.replace(old, new)
LK, _, _ = obj("LK"); RV, _, _ = obj("RV"); PR, _, _ = obj("PR")
if any(r.get("g") in ("x15", "x3") for v in list(LK.values()) + list(RV.values()) for r in v["rows"]): print("already applied"); sys.exit()
def insert_before(rows, new, groups):
    i = next((j for j, r in enumerate(rows) if r.get("g") in groups), len(rows))
    rows[i:i] = new
for st, t in ex["tab"].items():
    if t["l"]: insert_before(LK.setdefault(st, {"q": 0, "rows": []})["rows"], t["l"], {"gl"})
    if t["r"]: insert_before(RV.setdefault(st, {"q": 0, "rows": []})["rows"], t["r"], {"reach", "nm"})
for st, rows in ex["PR"].items(): PR.setdefault(st, []).extend(rows)
put("LK", LK); put("RV", RV); put("PR", PR)
rep('''if(g&&g!==sep){sep=g;h+=`<li class="xsep">${g==="gl"?"Great Lakes shoreline":"Also clearer than 20 ft"}</li>`}''',
    '''if(g&&g!==sep){sep=g;h+=`<li class="xsep">${{gl:"Great Lakes shoreline",x15:"Also 15 to 20 ft"}[g]||"Also clearer than 20 ft"}</li>`}''')
rep('''const XS={x:"Also under 2 NTU",reach:"Clear stretches of other rivers",nm:"Known for clear water · not measured"};''',
    '''const XS={x:"Also under 2 NTU",x3:"Also 2 to 3 NTU",reach:"Clear stretches of other rivers",nm:"Known for clear water · not measured"};''')
rep('''more ${m==="lakes"?"lakes clearer than 20 ft":"rivers or river stretches under 2 NTU"}''', '''more ${m==="lakes"?"lakes clearer than 15 ft":"rivers or river stretches at or under 3 NTU"}''')
rep('followed by every other lake in the state that averages clearer than 20 ft, then',
    'followed by every other lake in the state that averages 15 ft or clearer (those clearer than 20 ft first), then')
rep('Every other river in the state with a median under 2 NTU follows the top five, then the clearest monitored stretch',
    'Every other river in the state with a median at or under 3 NTU follows the top five (those under 2 NTU first), then the clearest monitored stretch')
open(page, "w").write(h)
print("page: +", sum(len(t["l"]) for t in ex["tab"].values()), "lakes, +", sum(len(t["r"]) for t in ex["tab"].values()), "rivers; property list +", sum(len(v) for v in ex["PR"].values()))
