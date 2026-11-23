"""City counterpart of the Trails tab. Single-family houses $100k-750k inside the limits of a city over 200k and within
400 m of a named segment of a qualifying trail; plus water and springhead listings inside those cities within 1 mile of a
trail (the water + trail overlap the main highlight skips in cities). -> matches.json"""
import glob, json, os, re, collections
import numpy as np, pandas as pd, shapely
from shapely.geometry import shape
from pyproj import Transformer
ROOT = os.path.dirname(os.path.abspath(__file__)); P = os.path.dirname(ROOT); TRD = os.path.join(P, "trails")
COLS = dict(type=2, addr=3, city=4, st=5, zip=6, price=7, beds=8, baths=9, sqft=11, lot=12, year=13, dom=14, url=20, lat=25, lon=26)
T = {"L48": Transformer.from_crs(4326, 5070, always_xy=True), "AK": Transformer.from_crs(4326, 3338, always_xy=True),
     "HI": Transformer.from_crs(4326, 26904, always_xy=True)}
OFF = {"L48": 0.0, "AK": 1e8, "HI": 2e8}
def region(lon, lat):
    if lat > 50.5 and lon < -129: return "AK"
    if lon < -154 and lat < 23: return "HI"
    return "L48"
def pxy(lon, lat):
    r = region(lon[0], lat[0]); x, y = T[r].transform(lon, lat); return np.asarray(x) + OFF[r], np.asarray(y)
def ppoint(lon, lat):
    x, y = pxy(np.array([lon]), np.array([lat])); return shapely.Point(x[0], y[0])

CITIES = json.load(open(os.path.join(TRD, "bigcities.json")))
big = [shape(c["geom"]) for c in CITIES]
ctree = shapely.STRtree(big)
def city_of(lon, lat):
    hit = ctree.query(shapely.Point(lon, lat), predicate="within")
    return int(hit[0]) if len(hit) else None

segs, meta = [], []
for f in sorted(glob.glob(os.path.join(TRD, "geom", "g*.json"))):
    for tid, Lg in json.load(open(f)).items():
        for name, c in Lg:
            c = np.array(c); x, y = pxy(c[:, 0], c[:, 1])
            segs.append(shapely.linestrings(np.column_stack([x, y]))); meta.append((int(tid), name))
stree = shapely.STRtree(segs)
def nearest(lon, lat, maxd):
    p = ppoint(lon, lat)
    idx = stree.query(p, predicate="dwithin", distance=maxd)
    if not len(idx): return None
    d = shapely.distance(p, np.array(segs)[idx]); k = int(np.argmin(d))
    return meta[idx[k]][0], int(round(float(d[k]))), meta[idx[k]][1]

# water and springhead listings (path -> water label), from the other tabs
LS = json.load(open(os.path.join(P, "listings.json"))); props = json.load(open(os.path.join(P, "props.json")))
SH = json.load(open(os.path.join(P, "heads", "sh.json")))
water = {}
for g, rows in LS.items():
    for x in rows:
        if x[16] is None: continue
        w = props[g][x[0]]; st = (w.get("st") if g in ("FS", "SP") else g) or g
        lab = dict(water=w.get("n") or "the water", tier="on" if x[1] == 0 else "near", st=st, price=x[2], type=x[3], beds=x[4], baths=x[5],
                   sqft=x[6], acres=x[7], addr=x[8], city=x[9], dom=x[10], new=bool(x[15]), lat=x[16], lon=x[17])
        if x[12] not in water or (water[x[12]]["tier"] != "on" and lab["tier"] == "on"): water[x[12]] = lab
for x in SH["L"]:
    hd = SH["heads"][x[0]]
    water.setdefault(x[12], dict(water=f"{hd[0]} (magnitude {hd[3]} spring)", tier="spring", st=hd[1], price=x[2], type=x[3], beds=x[4], baths=x[5],
                                 sqft=x[6], acres=x[7], addr=x[8], city=x[9], dom=x[10], new=bool(x[15]), lat=x[16], lon=x[17]))

# city houses near trails
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
houses = []
for url, r in rows.items():
    ci = city_of(float(r.lon), float(r.lat))
    if ci is None: continue
    n = nearest(float(r.lon), float(r.lat), 400)
    if not n: continue
    path = url.replace("https://www.redfin.com", "")
    acres = r.lot / 43560 if pd.notna(r.lot) and r.lot > 0 else None
    houses.append(dict(url=url, ci=ci, tid=n[0], dist=n[1], seg=n[2], price=int(r.price), beds=None if pd.isna(r.beds) else float(r.beds),
                       baths=None if pd.isna(r.baths) else float(r.baths), sqft=None if pd.isna(r.sqft) else int(r.sqft),
                       acres=None if acres is None else round(acres, 2), year=None if pd.isna(r.year) else int(r.year),
                       addr=str(r.addr), city=str(r.city), st=str(r.st), dom=None if pd.isna(r.dom) else int(r.dom),
                       lat=round(float(r.lat), 5), lon=round(float(r.lon), 5), water=water.get(path, {}).get("water"),
                       wtier=water.get(path, {}).get("tier")))
# water and springhead listings inside big cities within 1 mile of a trail
wt = []
for path, w in water.items():
    if w["lat"] is None: continue
    ci = city_of(w["lon"], w["lat"])
    if ci is None: continue
    n = nearest(w["lon"], w["lat"], 1609)
    if not n: continue
    wt.append(dict(w, path=path, ci=ci, tid=n[0], dist=n[1], seg=n[2]))
json.dump(dict(houses=houses, water=wt), open(os.path.join(ROOT, "matches.json"), "w"))
print(len(houses), "city houses within 400 m of a trail,", sum(1 for h in houses if h["water"]), "also water listings;",
      len(wt), "water/springhead listings in cities within 1 mile of a trail;",
      collections.Counter(CITIES[h["ci"]]["name"] for h in houses).most_common(10), flush=True)
