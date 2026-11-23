"""Oceanfront listings (added Nov 23, 2026): houses and land priced $100,000 to $750,000 with direct frontage on the open Atlantic
(Maine to Florida) or Pacific (California, Oregon, Washington) where the water in front is clear.
Coast: coast.json from build_coast.py (Census TIGER coastline cut into ~1 km pieces; open ocean only: bay, sound and inlet shores
and the backs of barrier islands are left out). Clarity: kd.json from kd_coast.py (NOAA VIIRS satellite Kd490 in front of each
piece). A piece counts as clear when its Kd490 is KD_MAX or less; the page shows it as an estimated Secchi depth, SECCHI_K / Kd490.
Redfin (map-data feed) is searched with its waterfront filter in grid cells around the clear pieces. A listing is kept when the
agent marked it waterfront AND its map point sits within reach of a clear open-ocean piece: 90 m (the Census coastline sits at the
water's edge, and beaches are wide) plus the side of a square of the lot's size (at most 250 m; 120 m for a house and 150 m for land
when no lot size is given), AND no bay or sound shore is closer. Units in a building (an address with # or "unit" and no lot of its
own), boat slips and timeshare weeks are left out.
Writes ocean/oc.json, seen_oc.json, meta_oc.json and refreshes the page's OC data through oc_tab.py.
Usage: run_ocean.py [page.html]      (SHARD / PULL_ONLY: see shard.py)"""
import csv, io, json, math, os, re, sys, time, datetime
from concurrent.futures import ThreadPoolExecutor
import numpy as np, shapely, pyproj
from shapely.geometry import LineString, Point, box
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
import rfjson, shard
page = sys.argv[1] if len(sys.argv) > 1 else None
TODAY = datetime.date.today().isoformat()
KD_MAX = 0.37          # m^-1: about 15 ft of estimated visibility (1.7 / 0.37 = 4.6 m), the same bar as the Lakes tab
SECCHI_K = 1.7         # Secchi depth ~ 1.7 / Kd (Poole-Atkins); a rough guide for a satellite estimate
C = json.load(open(HERE + "/coast.json")); KD = {int(k): v for k, v in json.load(open(HERE + "/kd.json")).items()}
CLR = [r for r in C if KD.get(r[0]) is not None and KD[r[0]] <= KD_MAX]
print(len(CLR), "clear open-ocean pieces of", len(C), flush=True)
# ---- search cells: 300 m around the clear pieces, gridded
DX, DY = 0.15, 0.12
zone = {}
for r in CLR:
    g = LineString(r[6]).buffer(0.003, 4)
    for cx in range(math.floor(g.bounds[0] / DX), math.floor(g.bounds[2] / DX) + 1):
        for cy in range(math.floor(g.bounds[1] / DY), math.floor(g.bounds[3] / DY) + 1):
            c = box(cx * DX, cy * DY, (cx + 1) * DX, (cy + 1) * DY)
            if c.intersects(g): zone.setdefault((cx, cy), []).append(c.intersection(g))
cells = []
for (cx, cy), parts in sorted(zone.items()):
    w, s_, e, n = shapely.union_all(parts).bounds
    cells.append((f"{cx}_{cy}", [round(w, 4), round(s_, 4), round(e, 4), round(n, 4)]))
print(len(cells), "search cells", flush=True)
CSVD = os.environ.get("OC_CSV") or HERE + "/csv"; os.makedirs(CSVD, exist_ok=True)
def url(b):
    w, s_, e, n = b; poly = f"{w}+{s_},{e}+{s_},{e}+{n},{w}+{n},{w}+{s_}"
    return ("https://www.redfin.com/stingray/api/gis-csv?al=1&min_price=100000&max_price=750000&num_homes=350"
            f"&ord=redfin-recommended-asc&page_number=1&poly={poly}&sf=1,2,3,5,6,7&status=9&uipt=1,5&v=8&wf=true")
def fetch(b, depth=0):
    t = rfjson.fetch_csv(url(b))
    if t.count("\n") >= 351 and depth < 4:
        w, s_, e, n = b; mx, my = (w + e) / 2, (s_ + n) / 2
        parts = [fetch(q, depth + 1) for q in ([w, s_, mx, my], [mx, s_, e, my], [w, my, mx, n], [mx, my, e, n])]
        t = parts[0] + "".join(p.split("\n", 1)[1] if "\n" in p else "" for p in parts[1:])
    return t
def get(c):
    k, b = c; f = f"{CSVD}/{k}_{abs(hash(tuple(b))) % 10**8}.csv"
    if os.path.exists(f): return open(f).read()
    for a in range(4):
        try:
            t = fetch(b); open(f, "w").write(t); time.sleep(1.5); return t
        except Exception as ex:
            if "Invalid arguments" in str(ex): print("skipped cell", k, b, flush=True); return ""
            print("retry", k, ex, flush=True); time.sleep(10 * (a + 1))
    raise RuntimeError(f"cell {k} failed")
if shard.pull_only(): cells = shard.take(cells)
with ThreadPoolExecutor(4) as ex: texts = list(ex.map(get, cells))
if shard.pull_only(): print("PULL ONLY: searches saved", flush=True); sys.exit(0)
# ---- on the open-ocean shore?
T = pyproj.Transformer.from_crs(4326, 5070, always_xy=True)
def proj(coords):
    x, y = T.transform([c[0] for c in coords], [c[1] for c in coords]); return LineString(list(zip(x, y)))
ALL = json.load(open(HERE + "/coast_all.json"))
CI = {r[0]: i for i, r in enumerate(CLR)}
clear_lines = [proj(r[6]) for r in CLR]; ctree = shapely.STRtree(clear_lines)
bay_lines = [proj(r[6]) for r in ALL if r[7] < 90]; btree = shapely.STRtree(bay_lines)
rows = {}
for t in texts:
    if not t: continue
    for r in csv.DictReader(io.StringIO(t)):
        try: price = int(float(r["PRICE"])); lat = float(r["LATITUDE"]); lon = float(r["LONGITUDE"])
        except Exception: continue
        if not 100000 <= price <= 750000: continue
        rows.setdefault(r["URL"], r)
print(len(rows), "waterfront-marked listings in the cells", flush=True)
seenp = HERE + "/seen_oc.json"; seen = json.load(open(seenp)) if os.path.exists(seenp) else {}
metap = HERE + "/meta_oc.json"; meta = json.load(open(metap)) if os.path.exists(metap) else {}
prev = meta.get("date") if meta.get("date") != TODAY else meta.get("prev")
first_run = not seen
def num(v, f=float):
    try: return f(float(v))
    except Exception: return None
L = []
for u, r in rows.items():
    lat, lon = float(r["LATITUDE"]), float(r["LONGITUDE"]); x, y = T.transform(lon, lat); p = Point(x, y)
    i = int(ctree.nearest(p)); d = clear_lines[i].distance(p)
    land = str(r["PROPERTY TYPE"]).startswith("Vacant")
    lot = num(r["LOT SIZE"])
    allow = min(250.0, 90.0 + math.sqrt(lot * 0.092903)) if lot and lot > 0 else (150.0 if land else 120.0)
    if d > allow: continue
    addr = str(r["ADDRESS"])
    if (re.search(r"#|\bunit\b|\bapt\b", addr, re.I) and not (lot and lot >= 2000)) or re.search(r"\b(slip|seg|segment|week|interval|timeshare|share)\b", addr, re.I):
        continue          # condo, co-op or hotel units, boat slips and timeshare weeks
    j = btree.query(p, predicate="dwithin", distance=d)
    if len(j) and min(bay_lines[k].distance(p) for k in j) < d - 1: continue      # a bay or sound shore is closer
    path = u.replace("https://www.redfin.com", "")
    first = seen.get(u, [TODAY])[0]; is_new = (not first_run) and u not in seen; seen[u] = [first, TODAY]
    acres = round(lot / 43560, 2) if lot else None
    L.append([i, int(r["PRICE"]), "l" if land else "h", num(r["BEDS"]), num(r["BATHS"]), num(r["SQUARE FEET"], int), acres,
              r["ADDRESS"], r["CITY"], r["STATE OR PROVINCE"], num(r["DAYS ON MARKET"], int), int(round(d)), path, first, is_new,
              round(lat, 5), round(lon, 5), num(r["YEAR BUILT"], int)])
L.sort(key=lambda x: (x[9], -x[0], x[1]))
def enc(coords):
    out = []; px = py = 0
    for x, y in coords:
        x, y = round(x * 1e4), round(y * 1e4)
        if (x, y) == (px, py) and out: continue
        out += [x - px, y - py]; px, py = x, y
    return out
OC = dict(date=TODAY, prev=prev, first=first_run, kdmax=KD_MAX, k=SECCHI_K,
          P=[[r[1], KD[r[0]], enc(r[6])] for r in CLR], L=L,
          km={st: sum(1 for r in CLR if r[1] == st) for st in sorted({r[1] for r in C})},
          kmall={st: sum(1 for r in C if r[1] == st) for st in sorted({r[1] for r in C})})
json.dump(OC, open(HERE + "/oc.json", "w"), separators=(",", ":"), ensure_ascii=False)
json.dump(seen, open(seenp, "w"), separators=(",", ":"))
cur = {x[12] for x in L}; prev_paths = set(meta.get("paths", []))
json.dump(dict(date=TODAY, prev=prev, n=len(L), new=sum(1 for x in L if x[14]), gone=len(prev_paths - cur) if prev_paths else 0,
               paths=sorted(cur)), open(metap, "w"), separators=(",", ":"))
from collections import Counter
print(f"OC DONE {TODAY}: {len(L)} oceanfront listings ({sum(1 for x in L if x[2]=='h')} houses, {sum(1 for x in L if x[2]=='l')} land) on "
      f"{len(CLR)} km of clear open coast; {sum(1 for x in L if x[14])} new since {prev}; by state {dict(Counter(x[9] for x in L))}", flush=True)
if page:
    import subprocess
    subprocess.run([sys.executable, HERE + "/oc_tab.py", page, HERE + "/oc.json"], check=True)
