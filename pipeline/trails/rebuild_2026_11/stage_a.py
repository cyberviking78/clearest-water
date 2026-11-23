"""Trail network rebuild, stage A: load the second Overture pull and USGS, keep unnamed cycleways and bike-legal footways,
give unnamed Overture lines the name of a USGS trail that runs along them, build the network and find the components
that could qualify but are not already one of the 1,760 existing trails. -> stage_a.pkl"""
import glob, json, os, pickle, re, sys, time, collections
import numpy as np, pyarrow.parquet as pq, pyarrow.compute as pc, shapely
from shapely.geometry import LineString
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
sys.path.insert(0, "/home/claude/live/pipeline/trails")
import build_trails as B           # reuse the original rules: names, bike access, projection
HERE = os.path.dirname(os.path.abspath(__file__)); TR = "/home/claude/live/pipeline/trails"; MI = 1609.344
t0 = time.time()
segs = []   # (src, id, name, cls, surf, wkb, footway)
for f in sorted(glob.glob(os.path.join(HERE, "raw", "ov_*.parquet"))):
    t = pq.read_table(f)
    if not t.num_rows: continue
    names = pc.struct_field(t["names"], "primary").to_pylist()
    cls = t["class"].to_pylist(); sub = t["subclass"].to_pylist(); surf = t["road_surface"].to_pylist()
    acc = t["access_restrictions"].to_pylist(); geo = t["geometry"].to_pylist(); ids = t["id"].to_pylist()
    for i in range(t.num_rows):
        c, n = cls[i], names[i]
        b = B.bike_ok(acc[i], c)
        if b is False or b == "motor": continue
        if c == "footway":
            if b is not True or sub[i] in ("sidewalk", "crosswalk", "traffic_island"): continue
        elif c != "cycleway" and b is not True: continue
        if c == "cycleway" and sub[i] == "cycle_crossing": n = n or ""
        if not B.good_name(n): n = ""
        s = B.SURF.get(surf[i][0]["value"], "U") if surf[i] else "U"
        segs.append(("o", ids[i], n, c, s, geo[i]))
print("overture", len(segs), round(time.time() - t0), "s", flush=True)
G = list(shapely.from_wkb([s[5] for s in segs]))
U = json.load(open(os.path.join(HERE, "raw", "usgs.json")))
ug, ua = [], []
for a, paths in U:
    n = a.get("name") or a.get("namealternate")
    if not B.good_name(n) or a.get("ohvover50inches") in ("Y", "Yes"): continue
    for p in paths:
        if len(p) >= 2: ug.append(LineString(p)); ua.append(a)
def proj(geoms):
    out = []
    for g in geoms:
        c = shapely.get_coordinates(g); r = B.region(c[0, 0], c[0, 1])
        x, y = B.T[r].transform(c[:, 0], c[:, 1]); out.append(LineString(np.column_stack([np.asarray(x) + B.OFF[r], y])))
    return out
PO = proj(G); PU = proj(ug)
print("projected", round(time.time() - t0), "s", flush=True)
names = [s[2] for s in segs]
tree = shapely.STRtree(PO)
keepu = []; renamed = 0
for j, g in enumerate(PU):
    pts = shapely.line_interpolate_point(g, np.linspace(0, 1, 6), normalized=True)
    pi, si = tree.query(pts, predicate="dwithin", distance=25)
    if len(set(pi)) / 6 >= 0.7:
        nm = (ua[j].get("name") or ua[j].get("namealternate")).strip()
        for s in set(si.tolist()):
            if not names[s]: names[s] = nm; renamed += 1
    else:
        keepu.append(j)
print("usgs kept", len(keepu), "of", len(PU), "; named", renamed, "unnamed Overture lines from USGS", round(time.time() - t0), "s", flush=True)
recs = [(s[0], s[1], names[i], s[3], s[4]) for i, s in enumerate(segs)]
for j in keepu:
    a = ua[j]; ts = (a.get("trailsurface") or "").lower()
    s = "P" if re.search(r"asphalt|concrete|paved|boardwalk", ts) else "G" if re.search(r"gravel|aggregate|crushed|limestone|cinder", ts) else "D" if re.search(r"native|dirt|soil|natural|rock", ts) else "U"
    recs.append(("u", str(a.get("objectid")), (a.get("name") or a.get("namealternate")).strip(), "usgs", s))
    PO.append(PU[j]); G.append(ug[j])
pickle.dump(dict(recs=recs, G=shapely.to_wkb(np.array(G, dtype=object)), PO=shapely.to_wkb(np.array(PO, dtype=object))), open(os.path.join(HERE, "segs.pkl"), "wb"))
print("STAGE A DONE", len(recs), "segments", round(time.time() - t0), "s", flush=True)
