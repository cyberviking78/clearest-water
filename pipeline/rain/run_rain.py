"""Rainforest country: land and homes of 25+ acres, $100,000-$750,000, inside temperate rainforest country -- the misty, big-tree,
fern-and-wildflower forests (zones.geojson, built once by build_zones.py from PRISM rain, temperature and elevation normals):
Pacific and Appalachian rainforest (70+ in of rain a year), the coast redwood fog belt, the inland cedar-hemlock rainforest of
north Idaho and NW Montana, Appalachian cloud forest (spruce-fir highlands), the Downeast Maine fog coast, and Southeast Alaska.
Each zone is covered with grid cells (0.25 x 0.2 degrees, 0.5 x 0.4 in Alaska) searched on Redfin's map-data feed (houses and
land, Redfin's 25-acre minimum lot filter). A listing is kept when its map point is inside a zone. Each gets the zone, the
annual rain and elevation at its point (PRISM), the nearest old-growth forest within 10 miles, and creek and pond flags
(wildflags.py, from Census TIGER water maps).
Usage: run_rain.py page.html   (env RAIN_CSV=<dir> builds from saved searches)
Writes rain/rain.json, rain/seen_rain.json, rain/meta_rain.json and refreshes the page's RF data (rf_tab.py)."""
import csv, io, json, math, os, sys, time, datetime
from concurrent.futures import ThreadPoolExecutor
import numpy as np, shapely, pyproj
from shapely.geometry import shape, box, Point
from shapely.ops import transform
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
import rfjson, wildflags
import shard
page = sys.argv[1] if len(sys.argv) > 1 else None
TODAY = datetime.date.today().isoformat()
KINDS = ["core", "fog", "inland", "cloud", "maine", "alaska"]
Z = {f["properties"]["kind"]: shape(f["geometry"]) for f in json.load(open(HERE + "/zones.geojson"))["features"]}
for g in Z.values(): shapely.prepare(g)
RP = json.load(open(HERE + "/rainpts.json")); RP["idx"] = np.cumsum(RP["idx"]); RIDX = {int(i): k for k, i in enumerate(RP["idx"])}
X0, Y0, D = -125.016666666666, 49.933333665556, 0.00833333333
def rain_elev(lat, lon):
    r, c = int(round((Y0 - lat) / D)), int(round((lon - X0) / D))
    for rad in range(0, 4):
        best = None
        for dr in range(-rad, rad + 1):
            for dc in range(-rad, rad + 1):
                k = RIDX.get((r + dr) * 7025 + c + dc)
                if k is not None and (best is None or abs(dr) + abs(dc) < best[0]): best = (abs(dr) + abs(dc), k)
        if best: k = best[1]; return int(RP["ppt"][k]), int(RP["elev"][k])
    return None, None
# ---- cells
cells = []
for kind, g in Z.items():
    dx, dy = (0.5, 0.4) if kind == "alaska" else (0.25, 0.2)
    for cx in range(math.floor(g.bounds[0] / dx), math.floor(g.bounds[2] / dx) + 1):
        for cy in range(math.floor(g.bounds[1] / dy), math.floor(g.bounds[3] / dy) + 1):
            b = box(cx * dx, cy * dy, (cx + 1) * dx, (cy + 1) * dy)
            if not g.intersects(b): continue
            w, s_, e, n = g.intersection(b).bounds
            if e - w < 0.01: m = (w + e) / 2; w, e = m - 0.005, m + 0.005
            if n - s_ < 0.01: m = (s_ + n) / 2; s_, n = m - 0.005, m + 0.005
            cells.append((kind, len(cells), [round(w, 4), round(s_, 4), round(e, 4), round(n, 4)]))
print(len(cells), "search cells", flush=True)
CSVD = os.environ.get("RAIN_CSV") or HERE + "/csv"; os.makedirs(CSVD, exist_ok=True)
def url(b):
    w, s_, e, n = b; poly = f"{w}+{s_},{e}+{s_},{e}+{n},{w}+{n},{w}+{s_}"
    return ("https://www.redfin.com/stingray/api/gis-csv?al=1&min_price=100000&max_price=750000&num_homes=350&min_parcel_size=1089000"
            f"&ord=redfin-recommended-asc&page_number=1&poly={poly}&sf=1,2,3,5,6,7&status=9&uipt=1,5&v=8")
def fetch(b, depth=0):
    t = rfjson.fetch_csv(url(b))
    if t.count("\n") >= 351 and depth < 3:
        w, s_, e, n = b; mx, my = (w + e) / 2, (s_ + n) / 2
        parts = [fetch(q, depth + 1) for q in ([w, s_, mx, my], [mx, s_, e, my], [w, my, mx, n], [mx, my, e, n])]
        t = parts[0] + "".join(p.split("\n", 1)[1] if "\n" in p else "" for p in parts[1:])
    return t
def get(c):
    kind, i, b = c; f = f"{CSVD}/{kind}_{i}.csv"
    if os.path.exists(f): return open(f).read()
    for a in range(4):
        try:
            t = fetch(b); open(f, "w").write(t); time.sleep(0.6); return t
        except Exception as ex:
            if "Invalid arguments" in str(ex): print("skipped cell", kind, i, b, flush=True); return ""
            print("retry", kind, i, ex, flush=True); time.sleep(5 * (a + 1))
    raise RuntimeError(f"cell {kind}_{i} failed")
if shard.pull_only(): cells = shard.take(cells)          # one slice of the searches (parallel GitHub jobs)
with ThreadPoolExecutor(4) as ex: texts = list(ex.map(get, cells))
if shard.pull_only(): print('PULL ONLY: searches saved', flush=True); sys.exit(0)
# ---- listings in the zones
OGS = json.load(open(ROOT + "/og/sites.json")); OGG = [shape(g) for g in json.load(open(ROOT + "/og/geom.json"))]
OGD = [shapely.MultiPolygon([p for p in g.simplify(0.002).geoms if p.geom_type == "Polygon" and p.area > 2e-5]) if g.area >= 1 else g for g in OGG]
tree = shapely.STRtree(OGD)
def aeqd(lon, lat): return pyproj.Transformer.from_crs(4326, pyproj.CRS.from_proj4(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m"), always_xy=True)
seenp, metap = HERE + "/seen_rain.json", HERE + "/meta_rain.json"
seen = json.load(open(seenp)) if os.path.exists(seenp) else {}; meta = json.load(open(metap)) if os.path.exists(metap) else {}
prev = meta.get("date") if meta.get("date") != TODAY else meta.get("prev"); first_run = not seen
rows = {}
for t in texts:
    for r in csv.DictReader(io.StringIO(t or "")):
        try: lat, lon = float(r["LATITUDE"]), float(r["LONGITUDE"]); price = int(float(r["PRICE"]))
        except Exception: continue
        lot = float(r["LOT SIZE"] or 0) / 43560
        if lot < 25 or not (100000 <= price <= 750000): continue
        typ = "l" if r["PROPERTY TYPE"] == "Vacant Land" else "h"
        if price / lot < 300 or (typ == "h" and lot > 1000): continue      # a subdivision's acreage on a town lot
        path = r["URL"].replace("https://www.redfin.com", "")
        if path in rows: continue
        p = Point(lon, lat); kind = next((k for k in KINDS if k in Z and Z[k].contains(p)), None)
        if not kind: continue
        rain, elev = rain_elev(lat, lon) if kind != "alaska" else (None, None)
        f = aeqd(lon, lat); best = None
        for gi in tree.query(p.buffer(0.25)):
            d = transform(f.transform, OGD[gi]).distance(Point(0, 0))
            if d <= 16093 and (best is None or d < best[1]): best = (int(gi), int(round(d)))
        num = lambda k: (float(r[k]) if r[k] not in ("", None) else None)
        first = seen.get(path) or TODAY; seen[path] = first
        rows[path] = [KINDS.index(kind), price, typ, num("BEDS"), num("BATHS"), int(num("SQUARE FEET") or 0) or None, round(lot, 1), r["ADDRESS"],
                      r["CITY"], r["STATE OR PROVINCE"], int(num("DAYS ON MARKET")) if r["DAYS ON MARKET"] not in ("", None) else None, rain,
                      round(elev * 3.28084) if elev is not None else None, path, first, (not first_run) and (first > (prev or "")),
                      round(lat, 5), round(lon, 5), int(num("YEAR BUILT") or 0) or None, best[0] if best else None, best[1] if best else None, None, None]
L = sorted(rows.values(), key=lambda x: (x[9], -(x[11] or 0)))
# creek and pond flags (index 21: creek name or "" for an unnamed creek, 22: pond/lake acres) from the Census water maps
flags = wildflags.flags([(x[16], x[17], x[6]) for x in L])
for x, fl in zip(L, flags): x[21], x[22] = fl
gone = len([k for k in seen if k not in rows and seen[k] < TODAY]) if not first_run else 0
seen = {k: v for k, v in seen.items() if k in rows}
json.dump(seen, open(seenp, "w")); json.dump(dict(date=TODAY, prev=prev, n=len(L)), open(metap, "w"))
OGN = {x[19]: [OGS[x[19]]["n"], OGS[x[19]]["st"]] for x in L if x[19] is not None}
RF = dict(date=TODAY, prev=prev, first=first_run, kinds=KINDS, og=OGN, L=L)
json.dump(RF, open(HERE + "/rain.json", "w"), separators=(",", ":"), ensure_ascii=False)
from collections import Counter
nn = sum(1 for x in L if x[15]); n50 = sum(1 for x in L if x[6] >= 50)
print(f"RAIN DONE {TODAY}: {len(L)} listings of 25+ acres in rainforest country; {n50} of 50+ acres; {sum(1 for x in L if x[21] is not None)} with a creek, "
      f"{sum(1 for x in L if x[22])} with a pond; by zone {dict(Counter(KINDS[x[0]] for x in L))}; {nn} new since {prev}; {gone} gone", flush=True)
if page:
    import subprocess
    subprocess.run([sys.executable, HERE + "/rf_tab.py", page, HERE + "/rain.json", HERE + "/zones.geojson"], check=True)
