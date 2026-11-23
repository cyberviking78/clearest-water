"""Water + trail overlap. For every waterfront (Property, Springs) and springhead listing, the nearest named segment of a
qualifying bike trail (pipeline/trails) within 1 mile, skipping listings inside cities over 200k; and for every trail-side
house, the water it's on if it's also a water listing. Writes wt.json and injects `const WT=...;` into the page.
Usage: water_trails.py <page.html>   (run from pipeline/trails; needs shapely, pyproj, numpy)"""
import glob, json, os, re, sys
import numpy as np, shapely
from shapely.geometry import shape
from pyproj import Transformer
ROOT = os.path.dirname(os.path.abspath(__file__)); P = os.path.dirname(ROOT)
MAXD = 1609
T = {"L48": Transformer.from_crs(4326, 5070, always_xy=True), "AK": Transformer.from_crs(4326, 3338, always_xy=True),
     "HI": Transformer.from_crs(4326, 26904, always_xy=True)}
OFF = {"L48": 0.0, "AK": 1e8, "HI": 2e8}
def region(lon, lat):
    if lat > 50.5 and lon < -129: return "AK"
    if lon < -154 and lat < 23: return "HI"
    return "L48"
def pxy(lon, lat):
    r = region(lon[0], lat[0]); x, y = T[r].transform(lon, lat); return np.asarray(x) + OFF[r], np.asarray(y)

LS = json.load(open(os.path.join(P, "listings.json")))
props = json.load(open(os.path.join(P, "props.json")))
SH = json.load(open(os.path.join(P, "heads", "sh.json")))
TR = json.load(open(os.path.join(ROOT, "tr.json")))
pts = {}          # redfin path -> (lon, lat, water label)
for g, rows in LS.items():
    for x in rows:
        if x[16] is None: continue
        w = props[g][x[0]]; nm = w.get("n") or w.get("name") or "the water"
        tier = "on" if x[1] == 0 else "near"
        lab = [nm, tier, (w.get("st") if g in ("FS", "SP") else g) or g]
        if x[12] not in pts or (pts[x[12]][2][1] != "on" and tier == "on"): pts[x[12]] = (x[17], x[16], lab)
for x in SH["L"]:
    hd = SH["heads"][x[0]]
    pts.setdefault(x[12], (x[17], x[16], [hd[0] + f" (magnitude {hd[3]} spring)", "spring", hd[1]]))
paths = list(pts); lon = np.array([pts[p][0] for p in paths]); lat = np.array([pts[p][1] for p in paths])

big = [shape(c["geom"]) for c in json.load(open(os.path.join(ROOT, "bigcities.json")))]
inside = np.zeros(len(paths), bool)
pi, _ = shapely.STRtree(big).query(shapely.points(lon, lat), predicate="within"); inside[pi] = True

segs, meta = [], []
for f in sorted(glob.glob(os.path.join(ROOT, "geom", "g*.json"))):
    for tid, Lg in json.load(open(f)).items():
        for name, c in Lg:
            c = np.array(c); x, y = pxy(c[:, 0], c[:, 1])
            segs.append(shapely.linestrings(np.column_stack([x, y]))); meta.append((int(tid), name))
tree = shapely.STRtree(segs)
PP = np.array([shapely.Point(*[v[0] for v in pxy(lon[i:i + 1], lat[i:i + 1])]) for i in range(len(paths))])
a_, s_ = tree.query(PP, predicate="dwithin", distance=MAXD)
best = {}
for a, s in zip(a_, s_):
    if inside[a]: continue
    d = shapely.distance(PP[a], segs[s])
    if a not in best or d < best[a][0]: best[a] = (d, s)
W = {paths[a]: [meta[s][0], int(round(d)), meta[s][1]] for a, (d, s) in best.items()}
# trail-side houses (Trails tab) that are also water or springhead listings
TW = {x[11]: pts[x[11]][2] for x in TR["L"] if x[11] in pts}
WT = dict(w=W, t=TW, n_in_city=int(inside.sum()), n_pts=len(paths))
json.dump(WT, open(os.path.join(ROOT, "wt.json"), "w"), separators=(",", ":"), ensure_ascii=False)
if len(sys.argv) > 1:
    page = sys.argv[1]; h = open(page).read()
    data = "const WT=" + json.dumps(WT, separators=(",", ":"), ensure_ascii=False) + ";\n"
    if "const WT=" in h: h = re.sub(r"const WT=\{.*?\};\n", lambda m: data, h, count=1, flags=re.S)
    else: h = h.replace("const SRC=[", data + "const SRC=[", 1)
    open(page, "w").write(h)
c = lambda m: sum(1 for v in W.values() if v[1] <= m)
print(f"WT DONE: {len(paths)} water/springhead listings; within 400 m of a trail {c(400)}, 800 m {c(800)}, 1 mile {c(1609)};"
      f" {len(TW)} trail-side houses also on the water; {int(inside.sum())} inside big cities")
