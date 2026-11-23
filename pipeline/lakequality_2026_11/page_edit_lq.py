"""Put the LakeQuality pass on the page (out/extra.json from build_lq.py): Lakes-tab rows under their own divider with a link to
each lake's LakeQuality page, Property-list rows (PR, index-aligned with props.json), the method note and the source credit.
Idempotent.  Usage: page_edit_lq.py <page.html> <extra.json>"""
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
    if new in h: return
    assert h.count(old) == 1, (h.count(old), old[:90]); h = h.replace(old, new)
LK, _, _ = obj("LK"); PR, _, _ = obj("PR")
if not any(r.get("g") == "lq" for v in LK.values() for r in v["rows"]):
    for st, rows in ex["LK"].items():
        R = LK.setdefault(st, {"q": 0, "rows": []})["rows"]
        i = next((j for j, r in enumerate(R) if r.get("g") == "gl"), len(R)); R[i:i] = rows
    for st, rows in ex["PR"].items(): PR.setdefault(st, []).extend(rows)
    put("LK", LK); put("PR", PR)
rep('''{gl:"Great Lakes shoreline",x15:"Also 15 to 20 ft"}[g]''', '''{gl:"Great Lakes shoreline",x15:"Also 15 to 20 ft",lq:"Also 15 ft or clearer · found through LakeQuality, thinner records"}[g]''')
rep('''${r.s>1?` · ${r.s} sites`:""}${recent}</small>''', '''${r.s>1?` · ${r.s} sites`:""}${recent}${r.lq?` · <a href="https://lakequality.org${esc(r.lq)}" target="_blank" rel="noopener">LakeQuality</a>`:""}</small>''')
h = h.replace('if(r.lim)notes.push(r.g==="lq"?"Thinner record than the main list: fewer than 20 readings or 5 years.":"Limited record: fewer than 20 readings or 5 years.");', 'if(r.lim)notes.push("Limited record: fewer than 20 readings or 5 years.");')   # earlier draft
rep('''if(r.lim)notes.push("Limited record: fewer than 20 readings or 5 years.");''', '''if(r.lim&&r.g!=="lq")notes.push("Limited record: fewer than 20 readings or 5 years.");''')
rep('''followed by every other lake in the state that averages 15 ft or clearer (those clearer than 20 ft first), then the state's Great Lakes shoreline''',
    '''followed by every other lake in the state that averages 15 ft or clearer (those clearer than 20 ft first), then lakes with thinner records that LakeQuality.org flagged and our own check confirms at 15 ft or clearer, then the state's Great Lakes shoreline''')
rep('''<p>Some agencies label stations with codes only. Those stations took the name of the nearest named station or USGS lake site within 1.5 km on the same watershed, and rows that rely mostly on this carry a note.</p>''',
    '''<p>Some agencies label stations with codes only. Those stations took the name of the nearest named station or USGS lake site within 1.5 km on the same watershed, and rows that rely mostly on this carry a note.</p>
  <p>Lakes under "found through LakeQuality" came from the clearest-lake rankings that <a href="https://lakequality.org" target="_blank" rel="noopener">LakeQuality.org</a> publishes for 24 states. We used those rankings only as a list of lakes to check: each lake it ranks at 15 ft or clearer that wasn't already here was looked up in the same Water Quality Portal, using the stations in its county named for it, and kept only if our own numbers put both its average (computed as above) and the median of all its readings at 15 ft or more, from at least 6 readings or readings in 3 different years. That is a lighter bar than the main list's 20 readings over 5 years, so these rows say so. Lakes that LakeQuality rates from satellite estimates alone (all four of its Colorado picks), values the portal doesn't bear out, and lakes inside national parks were left out. Its rankings cover AL, AR, CO, FL, GA, IA, IL, KS, MI, MN, MO, MT, NC, ND, NE, NM, NY, OK, TX, UT, VA, VT, WI and WY.</p>''')
open(page, "w").write(h)
print("LK rows +", sum(len(v) for v in ex["LK"].values()), "; PR rows +", sum(len(v) for v in ex["PR"].values()))
h = open(page).read()
rep('''const SRC=[
''', '''const SRC=[
 ["LakeQuality.org (ColdPress LLC), clearest-lake rankings by state: used as a checklist of lakes to verify against the Water Quality Portal","https://lakequality.org/ranking/clearest"],
''')
open(page, "w").write(h)
