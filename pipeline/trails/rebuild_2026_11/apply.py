"""Merge the new trails into the pipeline and the map (existing trails, ids and listings untouched).
1. pipeline/trails/trails.json += trails_new.json; geometry -> pipeline/trails/geom/g2.json (g3... if large)
2. rebuild pipeline/trails/boxes.json and pipeline/cities/boxes.json (Redfin search cells) from all trail geometry
3. pipeline/trails/tr.json "trails" list gets the new rows (houses along them arrive with the next refresh)
4. map/nat.json and map/st/<ST>.json get the new trail lines"""
import json, os, sys, subprocess, collections
import numpy as np, shapely, shapefile
from shapely.geometry import shape
HERE = os.path.dirname(os.path.abspath(__file__)); P = "/home/claude/live/pipeline"; TR = P + "/trails"; MAP = "/home/claude/live/map"
old = json.load(open(TR + "/trails.json")); new = json.load(open(HERE + "/trails_new.json")); geom = json.load(open(HERE + "/geom_new.json"))
assert new[0]["id"] == len(old) and all("states" in t for t in old)
json.dump(old + new, open(TR + "/trails.json", "w"), separators=(",", ":"))
k, chunk, size = 2, {}, 0
for tid in sorted(geom, key=int):
    s = len(json.dumps(geom[tid], separators=(",", ":")))
    if size + s > 12_000_000 and chunk:
        json.dump(chunk, open(f"{TR}/geom/g{k}.json", "w"), separators=(",", ":")); k += 1; chunk, size = {}, 0
    chunk[tid] = geom[tid]; size += s
json.dump(chunk, open(f"{TR}/geom/g{k}.json", "w"), separators=(",", ":"))
print("trails", len(old), "->", len(old) + len(new), "; geometry files g2..g%d" % k, flush=True)
b0 = len(json.load(open(TR + "/boxes.json"))); c0 = len(json.load(open(P + "/cities/boxes.json")))
subprocess.run([sys.executable, "-W", "ignore", "make_boxes.py"], cwd=TR, check=True)
subprocess.run([sys.executable, "-W", "ignore", "make_city_boxes.py"], cwd=P + "/cities", check=True)
print("search cells: trails", b0, "->", len(json.load(open(TR + "/boxes.json"))), "; cities", c0, "->", len(json.load(open(P + "/cities/boxes.json"))), flush=True)
T = json.load(open(TR + "/tr.json"))
assert len(T["trails"]) == len(old)
T["trails"] += [[t["name"], t["also"][:4], t["mi"], t["route_mi"], t["type"], "".join(t["tags"]), t["share"], t["states"], t["bbox"]] for t in new]
json.dump(T, open(TR + "/tr.json", "w"), separators=(",", ":"), ensure_ascii=False)
# map layers: same encoding as mapbuild/build_map.py
def enc(coords, scale):
    a = np.round(np.asarray(coords, dtype=float)[:, :2] * scale).astype(np.int64)
    if len(a) < 2: return None
    d = np.vstack([a[:1], np.diff(a, axis=0)]); keep = np.ones(len(d), bool); keep[1:] = np.any(d[1:] != 0, axis=1); d = d[keep]
    return d.ravel().tolist() if len(d) >= 2 else None
ST = {}
for r in shapefile.Reader("/home/claude/geo_src/state500k.zip").iterShapeRecords():
    if r.record["STUSPS"] not in ("PR", "VI", "GU", "MP", "AS"): ST[r.record["STUSPS"]] = shape(r.shape.__geo_interface__)
codes = sorted(ST); stree = shapely.STRtree([ST[s] for s in codes])
NAT = json.load(open(MAP + "/nat.json")); D = {}
byid = {t["id"]: t for t in new}; added = collections.Counter()
for tid, segs in geom.items():
    t = byid[int(tid)]; ty = t["type"]
    for name, c in segs:
        if len(c) < 2: continue
        g = shapely.LineString(c)
        gn = g.simplify(0.0012)
        if gn.length > 0.002:
            e = enc(gn.coords, 1e4)
            if e: NAT["tr"].append([int(tid), ty, e])
        e = enc(g.simplify(0.00003).coords, 1e5)
        if not e: continue
        for i in stree.query(g, predicate="intersects"):
            s = codes[i]
            if s not in D: D[s] = json.load(open(f"{MAP}/st/{s}.json"))
            D[s].setdefault("tr", []).append([int(tid), ty, name if name != t["name"] else 0, e]); added[s] += 1
json.dump(NAT, open(MAP + "/nat.json", "w"), separators=(",", ":"), ensure_ascii=False)
for s, d in D.items(): json.dump(d, open(f"{MAP}/st/{s}.json", "w"), separators=(",", ":"), ensure_ascii=False)
json.dump(sorted(D), open(HERE + "/changed_states.json", "w"))
print("map: nat.json", os.path.getsize(MAP + "/nat.json") // 1024, "KB; states changed", len(D), dict(added.most_common(8)), flush=True)
print("APPLY DONE")
