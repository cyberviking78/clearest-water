"""Old-growth acreage: private land and homes for sale, 25+ acres, $100,000-$750,000, within 5 miles of an old-growth forest.
Reads og/sites.json and og/geom.json (built once by build_sites.py; see README). For each state the search area is every forest
buffered by 5 miles; it is covered with grid cells (0.25 x 0.2 degrees, 0.5 x 0.4 in Alaska) and each cell is searched on
Redfin's map-data feed (houses and land, Redfin's minimum lot size filter at 25 acres). Each listing is matched to the nearest
forest edge: 0 borders it or sits inside (within 400 m; includes private inholdings), 1 within a mile, 2 within 5 miles.
Usage: run_og.py page.html   (env OG_CSV=<dir> builds from saved searches instead of fetching)
Each listing also gets creek and pond flags (wildflags.py, Census TIGER water).
Writes og/og.json, og/seen_og.json, og/meta_og.json and refreshes the page's OG data."""
import csv, io, json, math, os, sys, time, datetime, re, urllib.parse
from concurrent.futures import ThreadPoolExecutor
import shapely, pyproj
from shapely.geometry import shape, box, Point, mapping
from shapely.ops import transform
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import rfjson, wildflags
import shard
page = sys.argv[1] if len(sys.argv) > 1 else None
S = json.load(open(HERE + "/sites.json")); GE = [shape(g) for g in json.load(open(HERE + "/geom.json"))]
MI5 = 8047; ACRE = 4046.86; TODAY = datetime.date.today().isoformat()
def aeqd(lon, lat): return pyproj.Transformer.from_crs(4326, pyproj.CRS.from_proj4(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m"), always_xy=True)
def buffered(g, m):
    c = g.centroid; f = aeqd(c.x, c.y); inv = pyproj.Transformer.from_crs(f.target_crs, 4326, always_xy=True)
    return transform(inv.transform, transform(f.transform, g).buffer(m, 6))
# ---- search cells per state
zones = {}
for s, g in zip(S, GE):     # big boundaries (Tongass has thousands of islands) are simplified harder before buffering; the 5-mile zone only picks search cells
    if g.area >= 1:              # national-forest scale: a coarse degree buffer (over-covers slightly; distances are checked exactly below)
        zones.setdefault(s["st"], []).append(shapely.union_all([p.simplify(0.01).buffer(0.13, 3) for p in g.geoms if p.area > 2e-4] if hasattr(g, "geoms") else [g.simplify(0.01).buffer(0.13, 3)]))
        continue
    tol = 0.0005 if g.area < 0.05 else 0.003
    zones.setdefault(s["st"], []).append(buffered(g.simplify(tol), MI5))
cells = []
for st, zs in zones.items():
    Z = shapely.union_all(zs); dx, dy = (0.5, 0.4) if st == "AK" else (0.25, 0.2)
    for cx in range(math.floor(Z.bounds[0] / dx), math.floor(Z.bounds[2] / dx) + 1):
        for cy in range(math.floor(Z.bounds[1] / dy), math.floor(Z.bounds[3] / dy) + 1):
            b = box(cx * dx, cy * dy, (cx + 1) * dx, (cy + 1) * dy)
            if b.intersects(Z):
                w, s_, e, n = b.intersection(Z).bounds
                if e - w < 0.01: m = (w + e) / 2; w, e = m - 0.005, m + 0.005      # Redfin refuses a sliver polygon
                if n - s_ < 0.01: m = (s_ + n) / 2; s_, n = m - 0.005, m + 0.005
                cells.append((st, len(cells), [round(w, 4), round(s_, 4), round(e, 4), round(n, 4)]))
print(len(cells), "search cells in", len(zones), "states", flush=True)
CSVD = os.environ.get("OG_CSV") or HERE + "/csv"; os.makedirs(CSVD, exist_ok=True)
def url(b):
    w, s_, e, n = b; poly = f"{w}+{s_},{e}+{s_},{e}+{n},{w}+{n},{w}+{s_}"
    return ("https://www.redfin.com/stingray/api/gis-csv?al=1&min_price=100000&max_price=750000&num_homes=350&min_parcel_size=1089000"
            f"&ord=redfin-recommended-asc&page_number=1&poly={poly}&sf=1,2,3,5,6,7&status=9&uipt=1,5&v=8")
def get(c):
    st, i, b = c; f = f"{CSVD}/{st}_{i}.csv"
    if os.path.exists(f): return open(f).read()
    for a in range(4):
        try:
            t = rfjson.fetch_csv(url(b))
            if t.count("\n") >= 351:      # a full page: split the cell in four
                w, s_, e, n = b; mx, my = (w + e) / 2, (s_ + n) / 2; t = None
                parts = [rfjson.fetch_csv(url(q)) for q in ([w, s_, mx, my], [mx, s_, e, my], [w, my, mx, n], [mx, my, e, n])]
                t = parts[0] + "".join(p.split("\n", 1)[1] for p in parts[1:])
            open(f, "w").write(t); time.sleep(0.6); return t
        except Exception as ex:
            if "Invalid arguments" in str(ex): print("skipped cell", st, i, b, flush=True); return ""
            print("retry", st, i, ex, flush=True); time.sleep(5 * (a + 1))
    raise RuntimeError(f"cell {st}_{i} failed")
if shard.pull_only(): cells = shard.take(cells)          # one slice of the searches (parallel GitHub jobs)
with ThreadPoolExecutor(4) as ex: texts = list(ex.map(get, cells))
if shard.pull_only(): print('PULL ONLY: searches saved', flush=True); sys.exit(0)
# ---- match listings to forests
GD = [shapely.MultiPolygon([p for p in g.simplify(0.002).geoms if p.geom_type == "Polygon" and p.area > 2e-5]) if g.area >= 1 else g for g in GE]   # Tongass: distance to a lighter outline
tree = shapely.STRtree(GD)
seenp = HERE + "/seen_og.json"; seen = json.load(open(seenp)) if os.path.exists(seenp) else {}
metap = HERE + "/meta_og.json"; meta = json.load(open(metap)) if os.path.exists(metap) else {}
prev = meta.get("date") if meta.get("date") != TODAY else meta.get("prev")
first_run = not seen
rows = {}
for t in texts:
    for r in csv.DictReader(io.StringIO(t or "")):
        try: lat, lon = float(r["LATITUDE"]), float(r["LONGITUDE"]); price = int(float(r["PRICE"]))
        except Exception: continue
        lot = float(r["LOT SIZE"] or 0) / 43560
        if lot < 25 or not (100000 <= price <= 750000): continue
        typ = "l" if r["PROPERTY TYPE"] == "Vacant Land" else "h"
        if price / lot < 300 or (typ == "h" and lot > 1000): continue   # a subdivision's or common area's acreage on a town lot (e.g. 13,068 acres for a $320k house)
        path = r["URL"].replace("https://www.redfin.com", "")
        if path in rows: continue
        p = Point(lon, lat); f = aeqd(lon, lat); P0 = Point(0, 0)
        best = None
        for gi in tree.query(p.buffer(0.12)):
            d = transform(f.transform, GD[gi]).distance(P0)
            if d <= MI5 and (best is None or d < best[1]): best = (int(gi), d)
        if not best: continue
        typ = "l" if r["PROPERTY TYPE"] == "Vacant Land" else "h"
        num = lambda k: (float(r[k]) if r[k] not in ("", None) else None)
        first = seen.get(path) or TODAY; seen[path] = first
        rows[path] = [best[0], price, typ, num("BEDS"), num("BATHS"), int(num("SQUARE FEET") or 0) or None, round(lot, 1), r["ADDRESS"], r["CITY"],
                      r["STATE OR PROVINCE"], int(num("DAYS ON MARKET")) if r["DAYS ON MARKET"] not in ("", None) else None, int(round(best[1])), path,
                      first, (not first_run) and (first > (prev or "")), round(lat, 5), round(lon, 5), int(num("YEAR BUILT") or 0) or None]
L = sorted(rows.values(), key=lambda x: (x[0], x[11]))
for x, fl in zip(L, wildflags.flags([(x[15], x[16], x[6]) for x in L])): x += list(fl)   # 18: creek on the lot (name or ""), 19: pond acres
gone = len([k for k in seen if k not in rows and seen[k] < TODAY]) if not first_run else 0
seen = {k: v for k, v in seen.items() if k in rows}
json.dump(seen, open(seenp, "w"))
json.dump(dict(date=TODAY, prev=prev, n=len(L)), open(metap, "w"))
# ---- forests for the page (areas encoded like the map files: delta integers at 1e5)
def enc(coords):
    pts = [(round(x * 1e4), round(y * 1e4)) for x, y in coords]; out = []; px = py = 0
    for x, y in pts:
        if (x, y) == (px, py) and out: continue
        out += [x - px, y - py]; px, py = x, y
    return out
def rings(g):
    out = []
    for poly in getattr(g, "geoms", [g]):
        if poly.geom_type != "Polygon": continue
        a = poly.area
        if a < (2e-5 if g.area > 1 else 1e-7): continue
        out.append(enc(poly.exterior.coords))
    return out
SITES = []
for i, (s, g) in enumerate(zip(S, GE)):
    if s["kind"] == "boundary":
        tol = 0.0003 if g.area < 0.01 else 0.001 if g.area < 0.2 else 0.004
        area = rings(g.simplify(tol, preserve_topology=True))
    else: area = None
    SITES.append([s["n"], s["st"], s["cty"], s["ac"], 1 if s["fut"] else 0, s["src"], s["page"], s["web"], s["lat"], s["lon"],
                  s["kind"], s.get("bname"), area, round(math.sqrt(max(s["ac"] or 0, 1) * ACRE / math.pi)) if s["kind"] == "approx" else None, s["desc"]])
OG = dict(date=TODAY, prev=prev, first=first_run, S=SITES, L=L)
json.dump(OG, open(HERE + "/og.json", "w"), separators=(",", ":"), ensure_ascii=False)
n50 = sum(1 for x in L if x[6] >= 50); nb = sum(1 for x in L if x[11] <= 400); nn = sum(1 for x in L if x[14])
print(f"OG DONE {TODAY}: {len(L)} listings of 25+ acres near {len(set(x[0] for x in L))} of {len(S)} old-growth forests; {n50} of 50+ acres; "
      f"{nb} bordering or inside; {nn} new since {prev}; {gone} gone; size {os.path.getsize(HERE + '/og.json') // 1024} KB", flush=True)
if page:
    import subprocess
    subprocess.run([sys.executable, HERE + "/og_tab.py", page, HERE + "/og.json"], check=True)
