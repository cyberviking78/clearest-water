"""Add the new waters' shapes to the map's state files (map/st/<ST>.json "wt"), same encoding as mapbuild/build_map.py."""
import json, os, sys
import numpy as np, shapely
from shapely.geometry import shape
MAP = "/home/claude/live/map"; OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
P = json.load(open(OUT + "/props.json"))
def enc(coords, scale=1e5):
    a = np.round(np.asarray(coords, dtype=float)[:, :2] * scale).astype(np.int64)
    if len(a) < 2: return None
    d = np.vstack([a[:1], np.diff(a, axis=0)]); keep = np.ones(len(d), bool); keep[1:] = np.any(d[1:] != 0, axis=1); d = d[keep]
    return d.ravel().tolist() if len(d) >= 2 else None
def polys_of(g):
    t = g.geom_type
    if t == "Polygon": return [[list(g.exterior.coords)] + [list(i.coords) for i in g.interiors]]
    if t in ("MultiPolygon", "GeometryCollection"): return [p for x in g.geoms for p in polys_of(x)]
    return []
def plines_of(g):
    t = g.geom_type
    if t == "LineString": return [list(g.coords)]
    if t in ("MultiLineString", "GeometryCollection"): return [c for x in g.geoms for c in plines_of(x)]
    return []
changed = []
for f in sorted(os.listdir(OUT + "/shore")):
    st = f[:-5]
    if not os.path.exists(f"{MAP}/st/{st}.json"): continue          # FS/SP springs live in their own groups
    S = json.load(open(f"{OUT}/shore/{st}.json")); D = json.load(open(f"{MAP}/st/{st}.json"))
    have = {(r[0], r[1]) for r in D.get("wt", [])}; n = 0
    for k, v in S.items():
        grp, i = k.rsplit("_", 1); i = int(i)
        if not P[st][i].get("added") or P[st][i].get("gl") or not v.get("geom"): continue   # Great Lakes: the basemap shows them
        if (grp, i) in have:
            if "kept the" not in (v.get("method") or ""): continue
            D["wt"] = [r for r in D["wt"] if (r[0], r[1]) != (grp, i)]        # shape was trimmed: redraw it
        g = shape(v["geom"]).simplify(0.00002); e = P[st][i]
        polys = [[r for r in (enc(x) for x in p) if r] for p in polys_of(g)]
        D.setdefault("wt", []).append([grp, i, "l" if e["t"] == "lake" else "r", e["n"], [p for p in polys if p], [x for x in (enc(c) for c in plines_of(g)) if x]]); n += 1
    if n:
        json.dump(D, open(f"{MAP}/st/{st}.json", "w"), separators=(",", ":"), ensure_ascii=False); changed.append(st)
json.dump(changed, open(OUT + "/map_changed.json", "w"))
print("map water shapes added in", len(changed), "states:", changed)
