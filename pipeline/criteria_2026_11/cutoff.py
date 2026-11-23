"""Property cut-off (Nov 12, 2026): no listings on rivers whose median is over 3 NTU or lakes averaging under 15 ft of Secchi
clarity, in any state. Those waters stay on the Lakes and Rivers tabs (marked) but get "skip": true in props.json, so run.py and
prefetch.py don't search them and the Property list leaves them out. Waters known for clear water but not measured stay in.
Great Lakes: Michigan's Lake Erie shore (western basin, about 4 ft) is skipped; Ohio's Lake Erie shore is cut back to the
central basin, east of Marblehead (the western basin averages about 4 ft). Springs and spring-fed rivers (Springs tab) unchanged.
Also: listings on the water first -- "Include near-the-water listings" now applies to the Property tab too and starts unchecked.
Idempotent. Usage: cutoff.py <page.html> [patch_page.py]"""
import json, math, re, sys
import shapely
from shapely.geometry import shape, mapping, box
LIVE = "/home/claude/live"
page = sys.argv[1]; h = open(page).read()
P = json.load(open(LIVE + "/pipeline/props.json"))
def why(e):
    v = e.get("v", "")
    if e.get("gl"):
        ft = float(re.search(r"([\d.]+) ft", v).group(1))
        return "under 15 ft" if ft < 15 else None
    m = re.match(r"([\d.]+) (ft|NTU)", v)
    if not m: return None                      # "not measured", "< RL"
    x = float(m.group(1))
    if m.group(2) == "NTU" and x > 3: return "over 3 NTU"
    if m.group(2) == "ft" and x < 15: return "under 15 ft"
    return None
DX, DY, ZB = 0.1, 0.08, 0.008
def gl_cells(line):
    zone = line.buffer(ZB); out = []
    for cx in range(math.floor(zone.bounds[0] / DX), math.floor(zone.bounds[2] / DX) + 1):
        for cy in range(math.floor(zone.bounds[1] / DY), math.floor(zone.bounds[3] / DY) + 1):
            b = box(cx * DX, cy * DY, (cx + 1) * DX, (cy + 1) * DY)
            if not b.intersects(zone): continue
            c = list(b.intersection(zone).bounds)
            if c[2] - c[0] < 0.01: m = (c[0] + c[2]) / 2; c[0], c[2] = m - 0.005, m + 0.005
            if c[3] - c[1] < 0.01: m = (c[1] + c[3]) / 2; c[1], c[3] = m - 0.005, m + 0.005
            out.append([round(c[0], 4), round(c[2], 4), round(c[1], 4), round(c[3], 4)])
    return out
skipped = {}
for st, L in P.items():
    if st in ("FS", "SP"): continue
    for i, e in enumerate(L):
        w = why(e)
        if w: e["skip"] = True; e["skipwhy"] = w; skipped[(st, i)] = w
        else: e.pop("skip", None); e.pop("skipwhy", None)
        if e.get("gl") and st == "OH" and "Erie" in e["n"] and not e.get("trimmed"):
            S = json.load(open(f"{LIVE}/pipeline/shore/OH.json")); s = S[f"OH_{i}"]
            G = shape(s["geom"]).intersection(box(-82.72, 40, -80, 43))
            s["geom"] = mapping(G); s["method"] += " · central basin only (east of Marblehead)"
            e["boxes"] = gl_cells(G); e["trimmed"] = True; e["v"] = "about 19 ft open lake"
            json.dump(S, open(f"{LIVE}/pipeline/shore/OH.json", "w"), separators=(",", ":"))
            print("OH Lake Erie shoreline trimmed to the central basin:", len(e["boxes"]), "cells")
json.dump(P, open(LIVE + "/pipeline/props.json", "w"), ensure_ascii=False)
print("waters with no property search:", len(skipped), {w: sum(1 for x in skipped.values() if x == w) for w in set(skipped.values())})

def obj(name):
    i = h.find("const " + name + "="); o, end = json.JSONDecoder().raw_decode(h[i + len("const " + name + "="):]); return o, i, i + len("const " + name + "=") + end
def put(name, val):
    global h
    o, a, b = obj(name); h = h[:a] + "const " + name + "=" + json.dumps(val, separators=(",", ":"), ensure_ascii=False) + h[b:]
def rep(old, new, txt=None):
    global h
    t = h if txt is None else txt
    if new in t: return t
    assert t.count(old) == 1, (t.count(old), old[:90]); t = t.replace(old, new)
    if txt is None: h = t
    return t
PR, _, _ = obj("PR"); LK, _, _ = obj("LK"); RV, _, _ = obj("RV")
for st, rows in PR.items():
    for i, r in enumerate(rows):
        while len(r) < 8: r.append(None)
        r[7] = skipped.get((st, i))
        if st == "OH" and r[0] == "g" and "Erie" in r[1]: r[3] = "about 19 ft open-lake clarity (central basin)"
nop = {(st, P[st][i]["n"]): w for (st, i), w in skipped.items()}
for D in (LK, RV):
    for st, v in D.items():
        for r in v["rows"]:
            w = nop.get((st, r["n"]))
            if w: r["nop"] = w
            else: r.pop("nop", None)
for v in LK.get("OH", {}).get("rows", []):
    if v.get("gl") and "Erie" in v["n"]:
        v["note"] = "Central-basin August average, 1968–2002. Only the shore east of Marblehead is searched: the western basin, toward Toledo, averages about 4 ft. " + v["note"].split(". ", 1)[1] if v["note"].startswith("Central") else v["note"]
put("PR", PR); put("LK", LK); put("RV", RV)
# tabs: say which waters get no property search
rep('''${r.ft.toFixed(1)}</b> <span class="u">ft</span><span class="sub">${r.m.toFixed(1)} m</span></div>${notes.length?''',
    '''${r.ft.toFixed(1)}</b> <span class="u">ft</span><span class="sub">${r.m.toFixed(1)} m</span></div>${r.nop?`<div class="nop">No property search · ${esc(r.nop)}</div>`:""}${notes.length?''')
rep('''<span class="u">NTU</span><span class="sub">IQR ${r.p25}–${r.p75}</span></div>${notes.length?''',
    '''<span class="u">NTU</span><span class="sub">IQR ${r.p25}–${r.p75}</span></div>${r.nop?`<div class="nop">No property search · ${esc(r.nop)}</div>`:""}${notes.length?''')
rep('''<div class="val"><b>~${r.ft}</b> <span class="u">ft</span><span class="sub">${r.m} m · open water</span></div></li>`;return}''',
    '''<div class="val"><b>~${r.ft}</b> <span class="u">ft</span><span class="sub">${r.m} m · open water</span></div>${r.nop?`<div class="nop">No property search · ${esc(r.nop)}</div>`:""}</li>`;return}''')
i = h.find("</style>");
if ".nop{" not in h: h = h[:i] + "\n.row .nop{grid-column:2/-1;font-size:12px;color:var(--muted);margin-top:2px}\n" + h[i:]
# Property list: leave out the skipped waters; near-the-water listings only when asked for
P_REPS = [
    ('''function listingsFor(k,wi,pt,nw){return (LS[k]||[]).filter(x=>x[0]===wi&&(!pt||x[3]===pt)&&(!nw||x[15])&&wtOK(x[12]))}''', '''const NEAR=()=>{const e=document.getElementById("incnear");return !e||e.checked};
function listingsFor(k,wi,pt,nw){return (LS[k]||[]).filter(x=>x[0]===wi&&(!pt||x[3]===pt)&&(!nw||x[15])&&wtOK(x[12])&&(NEAR()||x[1]!==1))}'''),
    ('''  keys.forEach(k=>{if(s&&s!==k)return; const rows=PR[k]||[];''', '''  keys.forEach(k=>{if(s&&s!==k)return; const rows=(PR[k]||[]).filter(r=>!r[7]);'''),
    ('''.map(r=>[r,rows.indexOf(r)]);''', '''.map(r=>[r,PR[k].indexOf(r)]);'''),
    ('''    const all=(LS[k]||[]).filter(x=>(!pt||x[3]===pt)&&(!nw||x[15])&&wtOK(x[12])),''', '''    const all=(LS[k]||[]).filter(x=>(!pt||x[3]===pt)&&(!nw||x[15])&&wtOK(x[12])&&(NEAR()||x[1]!==1)),'''),
]
for o, n in P_REPS: rep(o, n)
rep('''function listingsFor(k,wi,pt,nw){return (LS[k]||[]).filter(x=>x[0]===wi&&(!pt||x[3]===pt)&&(!nw||x[15])&&wtOK(x[12]))}''',
    '''const NEAR=()=>{const e=document.getElementById("incnear");return !e||e.checked};
function listingsFor(k,wi,pt,nw){return (LS[k]||[]).filter(x=>x[0]===wi&&(!pt||x[3]===pt)&&(!nw||x[15])&&wtOK(x[12])&&(NEAR()||x[1]!==1))}''')
rep('''<label class="toggle" data-mode="map" hidden><input id="incnear" type="checkbox" checked> Include near-the-water listings</label>''',
    '''<label class="toggle" data-mode="map property" hidden><input id="incnear" type="checkbox"> Include near-the-water listings (MLS waterfront, lot not touching the mapped shore)</label>''')
rep('''property:"Houses and land for sale on the shore of every lake and river on the state lists, priced $100,000 to $750,000, each checked against the real shoreline.''',
    '''property:"Houses and land for sale on the shore of every lake and river on the state lists, priced $100,000 to $750,000, each checked against the real shoreline. Only waters clear enough are searched: rivers at or under 3 NTU and lakes 15 ft or clearer, plus rivers known for clear water that have no record. Listings on the water show first; tick Include near-the-water listings for the rest.''')
open(page, "w").write(h)
if len(sys.argv) > 2:
    pp = open(sys.argv[2]).read()
    for o, n in P_REPS: pp = rep(o, n, pp)
    open(sys.argv[2], "w").write(pp); print("patch_page.py updated")
print("page updated")
