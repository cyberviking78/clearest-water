"""Mark unnamed bike-path segments that run along a road (sidepaths) using Census TIGER 2024 roads.
A segment is a sidepath when at least 60% of points sampled every ~40 m lie within 22 m of a public road. -> sidepaths.json"""
import json, os, pickle, sys, collections, multiprocessing as mp
import numpy as np, shapely, shapefile
from shapely.geometry import shape
from pyproj import Transformer
HERE = os.path.dirname(os.path.abspath(__file__)); RD = "/home/claude/geo_src/rd"
ROADS = {"S1100", "S1200", "S1400", "S1630", "S1640"}   # interstates, highways, local streets, ramps, service drives
TP = Transformer.from_crs(4326, 5070, always_xy=True)
def projl(g):
    c = shapely.get_coordinates(g); x, y = TP.transform(c[:, 0], c[:, 1]); return shapely.linestrings(np.column_stack([x, y]))
def init(segs):
    global SEG; SEG = segs
def county(args):
    c, ids = args
    try: r = shapefile.Reader(f"{RD}/{c}.zip")
    except Exception as e: return c, None
    rl = [projl(shape(s.shape.__geo_interface__)) for s in r.iterShapeRecords() if s.record["MTFCC"] in ROADS]
    if not rl: return c, {}
    tree = shapely.STRtree(rl); out = {}
    for i in ids:
        g = SEG[i]; n = max(4, int(shapely.length(g) / 40))
        pts = shapely.line_interpolate_point(g, np.linspace(0, 1, n), normalized=True)
        a, b = tree.query(pts, predicate="dwithin", distance=22)
        out[i] = len(set(a.tolist())) / n
    return c, out
if __name__ == "__main__":
    S = pickle.load(open(os.path.join(HERE, "segs.pkl"), "rb")); G = shapely.from_wkb(S["G"])
    plan = json.load(open(os.path.join(HERE, "sp_plan.json")))
    test = plan["test"]
    segs = {i: projl(G[i]) for i in test}
    cg = [(r.record["GEOID"], shape(r.shape.__geo_interface__)) for r in shapefile.Reader("/home/claude/geo_src/county500k.zip").iterShapeRecords()]
    tree = shapely.STRtree([g for _, g in cg])
    a, b = tree.query(np.array([G[i] for i in test], dtype=object), predicate="intersects")
    job = collections.defaultdict(list)
    for p, k in zip(a, b): job[cg[k][0]].append(test[p])
    frac = collections.defaultdict(float); miss = []
    with mp.Pool(8, initializer=init, initargs=(segs,)) as pool:
        for k, (c, out) in enumerate(pool.imap_unordered(county, sorted(job.items()), chunksize=2)):
            if out is None: miss.append(c); continue
            for i, f in out.items(): frac[i] = max(frac[i], f)
            if k % 100 == 0: print(k, flush=True)
    sp = sorted(i for i in test if frac.get(i, 0) >= 0.6)
    json.dump(sp, open(os.path.join(HERE, "sidepaths.json"), "w"))
    L = {i: shapely.length(segs[i]) for i in test}
    print("SIDEPATHS", len(sp), "of", len(test), "segments,", round(sum(L[i] for i in sp) / 1609), "of", round(sum(L.values()) / 1609), "miles; missing counties", miss, flush=True)
