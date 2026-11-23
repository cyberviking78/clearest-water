"""Wild Lakes: houses and land for sale, $100,000-$750,000, on the shore of a clear, unspoiled lake or pond in the western states or
TN, WV, NC, ME, VT and NH, named or not (lakes.json / lakes_geom.json, built once by build_wild.py: blue satellite colour or a wild,
undeveloped shore; at any elevation). Lakes are covered with grid cells (0.15 x 0.12 degrees, cut to 400 m around the lakes) searched on Redfin's map-data
feed. A listing counts as on the lake when the lake's shore is within the lot's reach of its map point (the side of a square of
the lot's area plus 30 m, at most 570 m; land without a lot size 120 m, a house 60 m) -- the same test as the Property tab (tier 0); tier 1 "near the lake" when the shore is within 250 m beyond that.
Lakes the Census map leaves unnamed get their USGS GNIS name where there is one (cached in gnis.json); a lake GNIS names as a
"... Reservoir" is dropped.
Usage: run_wild.py page.html   (env ML_CSV=<dir> builds from saved searches)
Writes wild/ml.json, wild/seen_wl.json, wild/meta_wl.json and refreshes the page's ML data (mlake/ml_tab.py)."""
import csv, io, json, math, os, re, sys, time, datetime
from concurrent.futures import ThreadPoolExecutor
import shapely, pyproj
from shapely.geometry import shape, box, Point
from shapely.ops import transform
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
import rfjson
import shard
page = sys.argv[1] if len(sys.argv) > 1 else None
TODAY = datetime.date.today().isoformat()
LK = json.load(open(HERE + "/lakes.json"))
GJ = json.load(open(HERE + "/lakes_geom.json")) if os.path.exists(HERE + "/lakes_geom.json") else \
     json.load(open(HERE + "/lakes_geom_1.json")) + json.load(open(HERE + "/lakes_geom_2.json"))     # published in two halves (16 MB file limit)
GE = [shape(g) for g in GJ]; assert len(GE) == len(LK)
# ---- cells: 400 m around every lake, gridded
DX, DY = 0.3, 0.24          # searched areas split into quarters wherever Redfin returns a full page
zone = {}
for g in GE:
    b = g.buffer(0.004, 4)
    for cx in range(math.floor(b.bounds[0] / DX), math.floor(b.bounds[2] / DX) + 1):
        for cy in range(math.floor(b.bounds[1] / DY), math.floor(b.bounds[3] / DY) + 1):
            c = box(cx * DX, cy * DY, (cx + 1) * DX, (cy + 1) * DY)
            if c.intersects(b): zone.setdefault((cx, cy), []).append(c.intersection(b))
cells = []
for (cx, cy), parts in sorted(zone.items()):
    w, s_, e, n = shapely.union_all(parts).bounds
    if e - w < 0.01: m = (w + e) / 2; w, e = m - 0.005, m + 0.005
    if n - s_ < 0.01: m = (s_ + n) / 2; s_, n = m - 0.005, m + 0.005
    cells.append((f"{cx}_{cy}", [round(w, 4), round(s_, 4), round(e, 4), round(n, 4)]))
print(len(cells), "search cells around", len(LK), "lakes", flush=True)
CSVD = os.environ.get("ML_CSV") or HERE + "/csv"; os.makedirs(CSVD, exist_ok=True)
def url(b):
    w, s_, e, n = b; poly = f"{w}+{s_},{e}+{s_},{e}+{n},{w}+{n},{w}+{s_}"
    return ("https://www.redfin.com/stingray/api/gis-csv?al=1&min_price=100000&num_homes=350"
            f"&ord=redfin-recommended-asc&page_number=1&poly={poly}&sf=1,2,3,5,6,7&status=9&uipt=1,5&v=8")
def fetch(b, depth=0):
    t = rfjson.fetch_csv(url(b))
    if t.count("\n") >= 351 and depth < 6:
        w, s_, e, n = b; mx, my = (w + e) / 2, (s_ + n) / 2
        parts = [fetch(q, depth + 1) for q in ([w, s_, mx, my], [mx, s_, e, my], [w, my, mx, n], [mx, my, e, n])]
        t = parts[0] + "".join(p.split("\n", 1)[1] if "\n" in p else "" for p in parts[1:])
    return t
def get(c):
    k, b = c; f = f"{CSVD}/{k}_{abs(hash(tuple(b))) % 10**8}_nc.csv"      # the box is part of the name, so a changed lake list re-searches the cell
    if os.path.exists(f): return open(f).read()
    for a in range(4):
        try:
            t = fetch(b); open(f, "w").write(t); time.sleep(0.6); return t
        except Exception as ex:
            if "Invalid arguments" in str(ex): print("skipped cell", k, b, flush=True); return ""
            print("retry", k, ex, flush=True); time.sleep(5 * (a + 1))
    raise RuntimeError(f"cell {k} failed")
if shard.pull_only(): cells = shard.take(cells)          # one slice of the searches (parallel GitHub jobs)
with ThreadPoolExecutor(4) as ex: texts = list(ex.map(get, cells))
if shard.pull_only(): print('PULL ONLY: searches saved', flush=True); sys.exit(0)
# ---- on the shore?
tree = shapely.STRtree(GE)
seenp, metap = HERE + "/seen_wl.json", HERE + "/meta_wl.json"
seen = json.load(open(seenp)) if os.path.exists(seenp) else {}; meta = json.load(open(metap)) if os.path.exists(metap) else {}
prev = meta.get("date") if meta.get("date") != TODAY else meta.get("prev"); first_run = not seen
rows = {}
for t in texts:
    for r in csv.DictReader(io.StringIO(t or "")):
        try: lat, lon = float(r["LATITUDE"]), float(r["LONGITUDE"]); price = int(float(r["PRICE"]))
        except Exception: continue
        if price < 100000: continue          # no upper limit in the search: listings over $750,000 are counted separately (ML "H")
        path = r["URL"].replace("https://www.redfin.com", "")
        if path in rows: continue
        typ = "l" if r["PROPERTY TYPE"] == "Vacant Land" else "h"
        lot = float(r["LOT SIZE"] or 0)
        if lot > 0 and typ == "h" and lot / 43560 > 1000: lot = 0          # a subdivision's acreage on a town lot
        reach = min(570.0, 30.0 + math.sqrt(lot * 0.092903)) if lot > 0 else (120.0 if typ == "l" else 60.0)
        p = Point(lon, lat)
        f = pyproj.Transformer.from_crs(4326, pyproj.CRS.from_proj4(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m"), always_xy=True)
        best = None
        for gi in tree.query(p.buffer(0.009)):
            d = transform(f.transform, GE[gi]).distance(Point(0, 0))
            if d <= reach + 250 and (best is None or d < best[1] or (d == best[1] and LK[gi][3] > LK[best[0]][3])): best = (int(gi), d)
        if not best: continue
        tier = 0 if best[1] <= reach else 1           # 1: near the lake, the shore within 250 m beyond the lot's reach
        num = lambda k: (float(r[k]) if r[k] not in ("", None) else None)
        first = seen.get(path) or TODAY; seen[path] = first
        rows[path] = [best[0], price, typ, num("BEDS"), num("BATHS"), int(num("SQUARE FEET") or 0) or None, round(lot / 43560, 2) if lot else None,
                      r["ADDRESS"], r["CITY"], r["STATE OR PROVINCE"], int(num("DAYS ON MARKET")) if r["DAYS ON MARKET"] not in ("", None) else None,
                      int(round(best[1])), path, first, (not first_run) and (first > (prev or "")), round(lat, 5), round(lon, 5), int(num("YEAR BUILT") or 0) or None, tier]
ALL = sorted(rows.values(), key=lambda x: (x[0], x[18], x[11]))
L = [x for x in ALL if x[1] <= 750000]; HI = [x for x in ALL if x[1] > 750000]
for x in HI: seen.pop(x[12], None)
gone = len([k for k in seen if k not in rows and seen[k] < TODAY]) if not first_run else 0
seen = {k: v for k, v in seen.items() if k in rows}
json.dump(seen, open(seenp, "w")); json.dump(dict(date=TODAY, prev=prev, n=len(L)), open(metap, "w"))
# lakes with listings, renumbered, with their shapes (delta-encoded lon/lat at 1e5) for the map
def enc(coords):
    out = []; px = py = 0
    for x, y in coords:
        x, y = round(x * 1e5), round(y * 1e5)
        if (x, y) == (px, py) and out: continue
        out += [x - px, y - py]; px, py = x, y
    return out
# names for unnamed lakes from the USGS Geographic Names (GNIS) on The National Map; lakes GNIS calls a "... Reservoir" are dropped
import urllib.request, urllib.parse
gp = HERE + "/gnis.json"; GN = json.load(open(gp)) if os.path.exists(gp) else {}
def gnis(o):
    k = f"{LK[o][5]},{LK[o][6]}"          # keyed by the lake's position, so a rebuilt lake list can't mix up names
    if k in GN: return GN[k]
    g = GE[o]; w, s_, e, n = g.bounds; out = None
    q = urllib.parse.urlencode(dict(geometry=f"{w},{s_},{e},{n}", geometryType="esriGeometryEnvelope", inSR=4326, spatialRel="esriSpatialRelIntersects",
                                    outFields="gaz_name,gaz_featureclass", returnGeometry="true", outSR=4326, f="json"))
    try:
        d = json.load(urllib.request.urlopen("https://carto.nationalmap.gov/arcgis/rest/services/geonames/MapServer/7/query?" + q, timeout=60))
        c = [(f["attributes"]["gaz_name"], f["attributes"]["gaz_featureclass"]) for f in d.get("features", [])
             if f["attributes"]["gaz_featureclass"] in ("Lake", "Reservoir") and g.buffer(max(0.0015, 0.1 * math.sqrt(g.area))).contains(Point(f["geometry"]["x"], f["geometry"]["y"]))]
        c.sort(key=lambda t: t[1] != "Lake")
        out = list(c[0]) if c else ["", ""]
    except Exception as ex:
        print("GNIS lookup failed", o, ex, flush=True); return None
    GN[k] = out; return out
drop = set()
for o in sorted(set(x[0] for x in L)):
    if LK[o][0]: continue
    r = gnis(o)
    if not r: continue
    if r[0] and re.search(r"reservoir", r[0], re.I): drop.add(o)
    elif r[0]: LK[o][0] = r[0]
json.dump(GN, open(gp, "w"), separators=(",", ":"), ensure_ascii=False)
if drop: print("dropped GNIS reservoirs:", [GN[f"{LK[o][5]},{LK[o][6]}"][0] for o in drop], flush=True)
L = [x for x in L if x[0] not in drop]
HI = [x for x in HI if x[0] not in drop]
for x in HI: o = x[0]; x[0] = [LK[o][0], LK[o][1], LK[o][3], round(LK[o][4] * 3.28084)]   # lake name, state, acres, elevation ft
used = sorted(set(x[0] for x in L)); ren = {o: i for i, o in enumerate(used)}
LKS = []
for o in used:
    n, st, fips, ac, el, la, lo = LK[o][:7]; g = GE[o].simplify(0.0001)
    LKS.append([n, st, ac, round(el * 3.28084), la, lo, [enc(p.exterior.coords) for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon"],
                LK[o][9], LK[o][10], LK[o][11], LK[o][12]])  # 7: measured clarity ft or null; 8: satellite colour nm or null; 9: wild shore %; 10: "colour" or "shore"
for x in L: x[0] = ren[x[0]]
ML = dict(date=TODAY, prev=prev, first=first_run, nlakes=len(LK), K=LKS, L=L, H=HI)   # H: same rows, over $750,000 (not shown on the page)
json.dump(ML, open(HERE + "/ml.json", "w"), separators=(",", ":"), ensure_ascii=False)
nn = sum(1 for x in L if x[14])
print(f"ML DONE {TODAY}: {len(L)} listings ({sum(1 for x in L if x[18] == 0)} on the shore) at {len(used)} of {len(LK)} wild lakes ({sum(1 for k in LKS if not k[0])} unnamed); "
      f"{sum(1 for x in L if x[2] == 'h')} houses, {sum(1 for x in L if x[2] == 'l')} land; {nn} new since {prev}; {gone} gone", flush=True)
if page:
    import subprocess
    subprocess.run([sys.executable, ROOT + "/mlake/ml_tab.py", page, HERE + "/ml.json"], check=True)
