"""Houses within 400 m of a named segment of a qualifying trail, outside cities over 200k -> matches.json"""
import glob, io, json, os, collections
import numpy as np, pandas as pd, shapely
from shapely.geometry import shape
from pyproj import Transformer
ROOT = os.path.dirname(os.path.abspath(__file__))
COLS = dict(type=2, addr=3, city=4, st=5, zip=6, price=7, beds=8, baths=9, sqft=11, lot=12, year=13, dom=14, url=20, lat=25, lon=26)
T = {"L48": Transformer.from_crs(4326, 5070, always_xy=True), "AK": Transformer.from_crs(4326, 3338, always_xy=True),
     "HI": Transformer.from_crs(4326, 26904, always_xy=True)}
OFF = {"L48": 0.0, "AK": 1e8, "HI": 2e8}
def region(lon, lat):
    if lat > 50.5 and lon < -129: return "AK"
    if lon < -154 and lat < 23: return "HI"
    return "L48"
def proj_xy(lon, lat):
    r = region(lon[0], lat[0]); x, y = T[r].transform(lon, lat)
    return np.asarray(x) + OFF[r], np.asarray(y)

# listings
rows = {}
for f in glob.glob(os.path.join(ROOT, "rf", "*.csv")):
    try: d = pd.read_csv(f, low_memory=False)
    except Exception: continue
    if d.empty: continue
    d = d[d.iloc[:, 3].notna() & d.iloc[:, 7].notna()]
    d = pd.DataFrame({k: d.iloc[:, v].values for k, v in COLS.items()})
    for r in d.itertuples(index=False):
        if pd.isna(r.lat) or pd.isna(r.lon) or not str(r.type).startswith("Single Family"): continue
        if not 100000 <= r.price <= 750000: continue
        rows.setdefault(r.url, r)
print(len(rows), "houses in search boxes", flush=True)
R = list(rows.values())
lon = np.array([r.lon for r in R], float); lat = np.array([r.lat for r in R], float)

# drop houses inside cities over 200k
big = [shape(c["geom"]) for c in json.load(open(os.path.join(ROOT, "bigcities.json")))]
ct = shapely.STRtree(big)
pts = shapely.points(lon, lat)
inside = np.zeros(len(R), bool)
pi, gi = ct.query(pts, predicate="within")
inside[pi] = True
print(int(inside.sum()), "inside big-city limits", flush=True)

# trail segments, projected
segs, meta = [], []
for f in sorted(glob.glob(os.path.join(ROOT, "geom", "g*.json"))):
    for tid, L in json.load(open(f)).items():
        for name, c in L:
            c = np.array(c)
            x, y = proj_xy(c[:, 0], c[:, 1])
            segs.append(shapely.linestrings(np.column_stack([x, y]))); meta.append((int(tid), name))
tree = shapely.STRtree(segs)
P = []
for i in range(len(R)):
    x, y = proj_xy(lon[i:i + 1], lat[i:i + 1]); P.append(shapely.Point(x[0], y[0]))
P = np.array(P)
pi, si = tree.query(P, predicate="dwithin", distance=400)
best = {}
for a, s in zip(pi, si):
    if inside[a]: continue
    d = shapely.distance(P[a], segs[s])
    if a not in best or d < best[a][0]: best[a] = (d, s)
out = []
for a, (d, s) in best.items():
    r = R[a]; tid, name = meta[s]
    acres = r.lot / 43560 if pd.notna(r.lot) and r.lot > 0 else None
    out.append(dict(url=r.url, tid=tid, seg=name, dist=round(d), price=int(r.price), beds=None if pd.isna(r.beds) else float(r.beds),
                    baths=None if pd.isna(r.baths) else float(r.baths), sqft=None if pd.isna(r.sqft) else int(r.sqft),
                    acres=None if acres is None else round(acres, 2), year=None if pd.isna(r.year) else int(r.year),
                    addr=str(r.addr), city=str(r.city), st=str(r.st), dom=None if pd.isna(r.dom) else int(r.dom),
                    lat=round(float(r.lat), 5), lon=round(float(r.lon), 5)))
json.dump(out, open(os.path.join(ROOT, "matches.json"), "w"))
print(len(out), "houses within 400 m of a trail;", collections.Counter(o["st"] for o in out).most_common(12), flush=True)
