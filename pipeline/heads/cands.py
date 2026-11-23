"""Listings near springhead vents -> cands.json"""
import json, glob, io, math, os
import pandas as pd
COLS = dict(type=2, addr=3, city=4, st=5, zip=6, price=7, beds=8, baths=9, sqft=11, lot=12, year=13, dom=14, url=20, lat=25, lon=26)
h = json.load(open("heads.json")); boxes = json.load(open("boxes.json"))
import collections
grid = collections.defaultdict(list)
for i, x in enumerate(h):
    for lon, lat in x["pts"]: grid[(int(lat // 0.02), int(lon // 0.02))].append((i, lon, lat))
rows = {}
for f in glob.glob("rf*/*.csv"):
    i = int(os.path.basename(f)[:-4])
    try: d = pd.read_csv(f)
    except Exception: continue
    if d.empty: continue
    d = d[d.iloc[:, 3].notna() & d.iloc[:, 7].notna()]
    d = pd.DataFrame({k: d.iloc[:, v].values for k, v in COLS.items()})
    for r in d.itertuples(index=False):
        if pd.isna(r.lat): continue
        rows.setdefault(r.url, (r, None))
out = []
for url, (r, ids) in rows.items():
    acres = r.lot / 43560 if pd.notna(r.lot) and r.lot > 0 else None
    rad = math.sqrt(acres * 4046.86 / math.pi) if acres else 60
    kx = 111320 * math.cos(math.radians(r.lat))
    best = None
    gy, gx = int(r.lat // 0.02), int(r.lon // 0.02)
    for i, lon, lat in [p for a in (-1, 0, 1) for b in (-1, 0, 1) for p in grid.get((gy + a, gx + b), [])]:
        if True:
            dist = math.hypot((lon - r.lon) * kx, (lat - r.lat) * 110540)
            # vents within the lot's equivalent radius x2 (lots are rarely circles) + 150 m, or 400 m
            if dist <= max(2 * rad + 150, 400) and (best is None or dist < best[1]): best = (i, dist, lon, lat)
    if best:
        out.append(dict(url=url, addr=r.addr, city=r.city, st=r.st, zip=None if pd.isna(r.zip) else str(r.zip), price=int(r.price), type=r.type,
                        beds=None if pd.isna(r.beds) else float(r.beds), baths=None if pd.isna(r.baths) else float(r.baths), sqft=None if pd.isna(r.sqft) else int(r.sqft),
                        acres=None if acres is None else round(acres, 2), dom=None if pd.isna(r.dom) else int(r.dom), lat=r.lat, lon=r.lon,
                        head=best[0], dist=round(best[1]), vlon=best[2], vlat=best[3], rad=round(rad)))
json.dump(out, open("cands.json", "w"))
import collections
print(len(rows), "listings in boxes;", len(out), "candidates", collections.Counter(c["st"] for c in out).most_common(25))
