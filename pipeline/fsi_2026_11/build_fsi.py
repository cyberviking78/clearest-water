"""Add the clear-blue Florida springs found through the Florida Springs Institute that the Springs tab didn't have (Nov 25, 2026).
Candidates (cands.py): springs whose field-survey description reads clear and blue (looks.py), farther than 1.5 km from every
Florida spring already ranked, vents within 1.5 km of each other combined. Dropped when the Water Quality Portal's turbidity
at stations within 600 m of the vents has a median over 2 NTU (Natural Bridge Rise, Sandbag Spring). Springs with no
turbidity record are kept on the strength of the survey description and say so.
Each new spring gets a props.json "FS" entry (searched by run.py like every other spring), a traced run in shore/FS.json
(trace.py), a shape in map/st/FL.json, and an FSB row on the page (written by page_edit_fsi.py).
Idempotent: entries already added (props "added" == TAG) are replaced, not duplicated.
Usage: build_fsi.py   (run from anywhere; writes props.json, shore/FS.json, map/st/FL.json, fsi_2026_11/fsb.json)"""
import json, os, re, sys, urllib.parse
import numpy as np
from shapely.geometry import shape
HERE = os.path.dirname(os.path.abspath(__file__)); PL = os.path.dirname(HERE); REPO = os.path.dirname(PL)
TAG = "2026-11-25"
C = json.load(open(HERE + "/cands.json")); T = json.load(open(HERE + "/turb.json")); RUNS = json.load(open(HERE + "/runs.json"))
assert len(C) == len(T) == len(RUNS) and all(c["lead"][2] == t["name"] for c, t in zip(C, T))
P = json.load(open(PL + "/props.json")); SHORE = json.load(open(PL + "/shore/FS.json"))
FS = P["FS"]
keep = [i for i, e in enumerate(FS) if e.get("added") != TAG]
assert keep == list(range(len(keep))), "added entries must sit at the end of FS"
base = len(keep); del FS[base:]
for k in [k for k in SHORE if int(k.rsplit("_", 1)[1]) >= base]: del SHORE[k]
tmpl = json.loads(urllib.parse.unquote(FS[0]["z"].split("=", 1)[1]))
def zurl(b, wf):
    q = json.loads(json.dumps(tmpl)); q["mapBounds"] = {"west": b[0], "east": b[2], "south": b[1], "north": b[3]}
    if not wf: q["filterState"].pop("att", None)
    return "https://www.zillow.com/homes/for_sale/?searchQueryState=" + urllib.parse.quote(json.dumps(q, separators=(",", ":")))
def clean(n, cty):
    m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*(#\s*\w+)?$", n)
    core, par = (m.group(1), m.group(2)) if m else (n, "")
    core = re.sub(r"\s*#\s*\w+$", "", core).strip()
    if re.fullmatch(r"[A-Z][a-z]{2}\d{5,}", core): return "Unnamed spring"
    if par and par.lower() != cty.lower(): core += f" ({par})"
    return core
FSB, added = [], []
for c, t, run in zip(C, T, RUNS):
    s = t["turb"]
    if s and s["m"] > 2: print("dropped, median", s["m"], "NTU:", c["lead"][2]); continue
    lead = c["lead"]; cty = lead[3]; name = clean(lead[2], cty)
    g = shape(run["geom"]); w, so, e, n = g.bounds
    w, so, e, n = w - .012, so - .011, e + .012, n + .011
    if e - w < .057: cx = (w + e) / 2; w, e = cx - .0285, cx + .0285
    if n - so < .049: cy = (so + n) / 2; so, n = cy - .0245, cy + .0245
    bb = [round(w, 4), round(so, 4), round(e, 4), round(n, 4)]
    wi = len(FS)
    lwp = f"florida-land-for-sale/{cty.lower().replace(' ', '-')}-county/waterfront-property/price-100000-750000"
    FS.append({"t": "spring", "n": name, "rk": None, "v": f"{s['m']} NTU" if s else "clear blue (field survey)", "c": cty,
               "z": zurl(bb, True), "za": zurl(bb, False), "lw": [[cty, "https://www.landwatch.com/" + lwp]],
               "lat": lead[0], "lon": lead[1], "dot": [lead[0], lead[1]], "added": TAG, "src": "fsi", "mag": lead[4]})
    SHORE[f"FS_{wi}"] = {"geom": run["geom"], "method": "run traced"}
    runs = ", ".join(x for x in run["flows"] if x.lower() not in name.lower())[:80]
    FSB.append([wi, name, cty, s["m"] if s else None, s["a"] if s else None, s["b"] if s else None, s["n"] if s else 0, s["yrs"] if s else 0,
                int(s["y0"]) if s else None, int(s["y1"]) if s else None, s["sites"] if s else 0, runs, bb, lwp, 0, "run traced", "FL", "FS",
                [lead[0], lead[1]], lead[4], len(c["vents"])])
    added.append(name)
json.dump(P, open(PL + "/props.json", "w"))
json.dump(SHORE, open(PL + "/shore/FS.json", "w"), separators=(",", ":"))
# FSB: magnitude first, then turbidity (no record last)
FSB.sort(key=lambda r: (r[19], r[3] if r[3] is not None else 9))
json.dump(FSB, open(HERE + "/fsb.json", "w"), ensure_ascii=False, separators=(",", ":"))
# map shapes, same encoding as mapbuild/build_map.py
def enc(coords, scale=1e5):
    a = np.round(np.asarray(coords, dtype=float)[:, :2] * scale).astype(np.int64)
    if len(a) < 2: return None
    d = np.vstack([a[:1], np.diff(a, axis=0)]); k = np.ones(len(d), bool); k[1:] = np.any(d[1:] != 0, axis=1); d = d[k]
    return d.ravel().tolist() if len(d) >= 2 else None
def polys_of(g):
    if g.geom_type == "Polygon": return [[list(g.exterior.coords)] + [list(i.coords) for i in g.interiors]]
    if g.geom_type in ("MultiPolygon", "GeometryCollection"): return [p for x in g.geoms for p in polys_of(x)]
    return []
def plines_of(g):
    if g.geom_type == "LineString": return [list(g.coords)]
    if g.geom_type in ("MultiLineString", "GeometryCollection"): return [c for x in g.geoms for c in plines_of(x)]
    return []
def encpoly(g, scale):
    out = []
    for rings in polys_of(g):
        er = [e for e in (enc(r, scale) for r in rings) if e]
        if er: out.append(er)
    return out
MF = REPO + "/map/st/FL.json"; D = json.load(open(MF))
D["wt"] = [r for r in D["wt"] if not (r[0] == "FS" and r[1] >= base)]
for r in FSB:
    g = shape(SHORE[f"FS_{r[0]}"]["geom"]).simplify(0.00002)
    D["wt"].append(["FS", r[0], "s", r[1], encpoly(g, 1e5), [e for e in (enc(c, 1e5) for c in plines_of(g)) if e]])
json.dump(D, open(MF, "w"), separators=(",", ":"), ensure_ascii=False)
print(len(added), "springs added at FS index", base, "on:", ", ".join(added))
