"""One-time build of the close-up water layer: ponds, lakes, rivers and creeks from US Census TIGER 2024 (AREAWATER and
LINEARWATER, which carry the National Hydrography Dataset's features), for the 1,654 counties within reach of a
qualifying trail, a ranked water or a springhead. Only features within about 1.5 km of a trail, ranked water or springhead
are kept, so the files stay small. Writes ../map/hy/<ST>.json, loaded by the page when zoomed in close."""
import json, glob, os, sys, collections, multiprocessing as mp
import numpy as np, shapely, shapefile
from shapely.geometry import shape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
P = "/home/claude/live/pipeline"; G = "/home/claude/geo_src"; OUT = "/home/claude/live/map/hy"
os.makedirs(OUT, exist_ok=True)
FIPS = {r.record["STATEFP"]: r.record["STUSPS"] for r in shapefile.Reader(G + "/state500k.zip").iterShapeRecords()}

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
def lines_of(g):
    t = g.geom_type
    if t == "LineString": return [list(g.coords)]
    if t in ("MultiLineString", "GeometryCollection"): return [c for x in g.geoms for c in lines_of(x)]
    return []

MASK = None
def build_mask():
    gs = []
    for f in glob.glob(P + "/trails/geom/g*.json"):
        for tid, Lg in json.load(open(f)).items():
            for n, c in Lg:
                if len(c) > 1: gs.append(shapely.LineString(c).simplify(0.001))
    for f in glob.glob(P + "/shore/*.json"):
        for k, v in json.load(open(f)).items():
            if v.get("geom"): gs.append(shape(v["geom"]).simplify(0.001))
    for h in json.load(open(P + "/heads/heads.json")): gs.append(shapely.Point(h["lon"], h["lat"]))
    return shapely.buffer(np.array(gs, dtype=object), 0.015, quad_segs=4)

def init(m):
    global TREE; TREE = shapely.STRtree(m)
def near(geoms):
    if not geoms: return np.zeros(0, bool)
    a, b = TREE.query(np.array(geoms, dtype=object), predicate="intersects")
    ok = np.zeros(len(geoms), bool); ok[np.unique(a)] = True; return ok

def county(c):
    out = dict(a=[], l=[])
    try:
        r = shapefile.Reader(f"{G}/aw/{c}.zip"); recs = []
        for sr in r.iterShapeRecords():
            if sr.record["AWATER"] < 1500: continue
            recs.append((sr.record["FULLNAME"] or "", shape(sr.shape.__geo_interface__)))
        ok = near([g for _, g in recs])
        for (n, g), k in zip(recs, ok):
            if not k: continue
            ps = []
            for p in polys_of(g.simplify(0.00004)):
                rs = [e for e in (enc(x) for x in p) if e]
                if rs: ps.append(rs)
            if ps: out["a"].append([n, ps])
    except Exception as e: print("aw", c, e, flush=True)
    try:
        r = shapefile.Reader(f"{G}/lw/{c}.zip"); recs = []
        for sr in r.iterShapeRecords():
            if sr.record["MTFCC"] not in ("H3010", "H3013", "H3020", "H1100"): continue
            recs.append((sr.record["FULLNAME"] or "", sr.record["MTFCC"], shape(sr.shape.__geo_interface__)))
        ok = near([g for _, _, g in recs])
        for (n, mt, g), k in zip(recs, ok):
            if not k: continue
            for x in lines_of(g.simplify(0.00004)):
                e = enc(x)
                if e: out["l"].append([n, 1 if mt == "H3020" else 0, e])
    except Exception as e: print("lw", c, e, flush=True)
    return c, out

if __name__ == "__main__":
    coi = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "coi.json")))
    m = build_mask(); print("mask", len(m), flush=True)
    D = collections.defaultdict(lambda: dict(a=[], l=[]))
    with mp.Pool(8, initializer=init, initargs=(m,)) as pool:
        for i, (c, o) in enumerate(pool.imap_unordered(county, coi, chunksize=4)):
            s = FIPS[c[:2]]; D[s]["a"] += o["a"]; D[s]["l"] += o["l"]
            if i % 200 == 0: print(i, flush=True)
    tot = 0
    for s, d in D.items():
        b = json.dumps(d, separators=(",", ":"), ensure_ascii=False); open(f"{OUT}/{s}.json", "w").write(b); tot += len(b)
    print("hydro", tot // 1024 // 1024, "MB;", sorted(((os.path.getsize(f"{OUT}/{s}.json") // 1024, s) for s in D), reverse=True)[:10], flush=True)
