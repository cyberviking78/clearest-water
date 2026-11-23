"""Wild Lakes (replaces the Mountain Lakes list, Nov 19, 2026): clear, unspoiled lakes and ponds of 1+ acre in the western states and
in TN, WV, NC, ME, VT and NH, at any elevation.
Sources: Census TIGER 2024 area water (lake/pond and reservoir outlines, by county); LimnoSat-US (Topp et al. 2020, Zenodo 4139695:
Landsat colour of 56,792 US lakes, 1984-2020; lake_color.json from limnosat_color.py: median summer dominant wavelength 2013-2020,
matched to a lake through its HydroLakes deepest point); NLCD 2021 land cover (USGS/MRLC, www.mrlc.gov WCS, 30 m); PRISM 800 m
elevation (shown, not used); the Lakes tab's Secchi measurements (Chad's 15 ft cut-off).
A lake is kept when
  - the 2021 land cover shows it as open water (at least 40% of its area): drops dried-up and seasonal ponds and stale map outlines;
  - it is not a river channel (long and thin), not named as a river, creek, ditch, tailings, sewage or similar pond, not measured on
    the Lakes tab at under 15 ft, and not wholly inside a national park or wilderness area (nothing for sale there);
  - and EITHER its satellite colour is blue (summer dominant wavelength 505 nm or less, about the bluest third of US lakes: Crater
    472, Tahoe 478, Sebago 484, Flathead 486, Summersville 495, Fontana 498, Watauga 503; murky Utah Lake 549, Upper Klamath 553,
    Erie 560), OR, for lakes without a colour record (mostly ponds under 25 acres), its shore is wild: within 200 m of the water at
    least 75% forest, shrub, grassland, wetland or bare rock, at most 5% developed land and at most 10% farmland.
clarity_wild.py then drops every lake of 100+ acres measured at under 15 ft (Water Quality Portal Secchi readings since 2000) and
blue lakes with under 40% natural shore (subdivision and town lakes).
Writes lakes_tiger.json / lakes_geom_tiger.json style output for run_lakes.py: lakes.json [[name, st, county fips, acres, elev_m, lat,
lon, 0, 0, measured clarity ft or null, colour nm or null, wild shore % or null, setting code]] and lakes_geom.json.
Cache: nlcd_blocks/ (per 0.5-degree block results). Usage: build_wild.py"""
import json, os, re, math, io, zipfile, time, urllib.request, urllib.parse, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np, shapefile, shapely, pyproj, rasterio
from rasterio.features import geometry_mask
from rasterio.io import MemoryFile
from shapely.geometry import shape, mapping, box, Point
from shapely.ops import transform
G = "/home/claude/geo_src"; HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
STATES = set("WA OR CA ID MT WY NV UT CO AZ NM TN WV NC ME VT NH".split())
RIVER = re.compile(r"\b(river|riv|creek|crk|cr|fork|frk|slough|ditch|canal|channel|brook|br|run|branch|wash|bayou|inlet|outlet|cove|bay|harbor|hbr|sound)\b", re.I)
BAD = re.compile(r"tailing|sewage|settling|evaporat|lagoon|hatchery|stock ?pond|treatment|waste|slurry|leach|\bpit\b|quarry|retention|detention|sediment|effluent|cooling|ash pond|mine", re.I)
dem = np.fromfile(G + "/prism/dem800.bil", dtype="<i4").reshape(3105, 7025)
X0, Y0, D = -125.016666666666, 49.933333665556, 0.00833333333
TO5070 = pyproj.Transformer.from_crs(4326, 5070, always_xy=True).transform
# ---- candidates from the Census water maps
cty = [(r["STATEFP"] + r["COUNTYFP"], r["STUSPS"]) for r in shapefile.Reader(G + "/county500k.zip").iterRecords() if r["STUSPS"] in STATES]
gov = []
for k in ("np", "wild"):
    for f in json.load(open(f"/home/claude/live/og/gov/{k}.geojson"))["features"]:
        if f.get("geometry"): gov.append(shape(f["geometry"]).buffer(0))
GOV = shapely.union_all(gov); shapely.prepare(GOV)
cand = []   # [name, st, fips, geom]
for fips, st in cty:
    f = f"{G}/aw/{fips}.zip"
    if not os.path.exists(f): print("missing", fips); continue
    for sr in shapefile.Reader(f).iterShapeRecords():
        r = sr.record
        if r["MTFCC"] not in ("H2030", "H2040"): continue
        if (r["ALAND"] + r["AWATER"]) / 4046.86 < 1: continue
        name = (r["FULLNAME"] or "").strip()
        if name and (RIVER.search(name) or BAD.search(name)): continue
        try: g = shape(sr.shape.__geo_interface__).buffer(0)
        except Exception: continue
        if g.is_empty: continue
        cand.append([name, st, fips, g])
print(len(cand), "candidate outlines", flush=True)
# join touching pieces of one named lake (the Census map cuts lakes at county lines)
grp = {}
for i, c in enumerate(cand):
    if c[0]: grp.setdefault(c[0].lower(), []).append(i)
gone = set()
for nm, ids in grp.items():
    if len(ids) < 2: continue
    tr = shapely.STRtree([cand[i][3].buffer(0.004) for i in ids]); par = list(range(len(ids)))
    def root(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for a in range(len(ids)):
        for c in tr.query(cand[ids[a]][3].buffer(0.004)):
            if c != a: par[root(a)] = root(int(c))
    comp = {}
    for a in range(len(ids)): comp.setdefault(root(a), []).append(ids[a])
    for mem in comp.values():
        if len(mem) < 2: continue
        big = max(mem, key=lambda i: cand[i][3].area); cand[big][3] = shapely.union_all([cand[i][3] for i in mem]); gone |= set(mem) - {big}
cand = [c for i, c in enumerate(cand) if i not in gone]
print(len(cand), "lakes after joining pieces", flush=True)
# ---- shape, park/wilderness
keep = []
for c in cand:
    g = c[3]; p = g.representative_point()
    gm = transform(TO5070, g); A, P = gm.area, gm.length
    if A < 4046.86 * 0.9: continue
    if P and 2 * A / P < 40 and 4 * math.pi * A / P ** 2 < 0.03: continue          # a river channel
    if GOV.contains(p) and GOV.contains(g.buffer(-0.0005) if g.area > 1e-6 else g): continue
    keep.append(c + [A / 4046.86, p.y, p.x, gm])
cand = keep; print(len(cand), "after shape and park checks", flush=True)
# ---- satellite colour through HydroLakes deepest points
COL = json.load(open(HERE + "/lake_color.json")); tree = shapely.STRtree([c[3] for c in cand]); colour = {}
sf = shapefile.Reader(HERE + "/src/HydroLakes_DP")
for sr in sf.iterShapeRecords():
    hid = int(sr.record["Hylak_id"]); v = COL.get(str(hid))
    if not v or v[1] < 5: continue
    x, y = sr.shape.points[0]; pt = Point(x, y)
    for j in tree.query(pt, predicate="intersects"):
        j = int(j)      # HydroLakes numbers lakes from the largest down: when two fall in one outline, the lake itself has the lower number
        if j not in colour or hid < colour[j][2]: colour[j] = v + [hid]
print(len(colour), "lakes with a satellite colour", flush=True)
# ---- land cover in 0.5-degree blocks
C = HERE + "/nlcd_blocks"; os.makedirs(C, exist_ok=True)
blocks = {}
for i, c in enumerate(cand): blocks.setdefault((math.floor(c[6] / 0.5), math.floor(c[5] / 0.5)), []).append(i)
NATURAL = np.isin(np.arange(256), [12, 31, 41, 42, 43, 51, 52, 71, 72, 90, 95])
DEV = np.isin(np.arange(256), [21, 22, 23, 24]); AG = np.isin(np.arange(256), [81, 82]); WAT = np.arange(256) == 11
def nlcd(xmin, ymin, xmax, ymax):
    q = [("service", "WCS"), ("version", "2.0.1"), ("request", "GetCoverage"), ("coverageId", "mrlc_download__NLCD_2021_Land_Cover_L48"),
         ("subset", f"X({int(xmin)},{int(xmax)})"), ("subset", f"Y({int(ymin)},{int(ymax)})"), ("format", "image/geotiff")]
    for a in range(5):
        try: return urllib.request.urlopen("https://www.mrlc.gov/geoserver/ows?" + urllib.parse.urlencode(q), timeout=300).read()
        except Exception as ex: err = ex; time.sleep(5 * (a + 1))
    raise RuntimeError(f"NLCD failed: {err}")
def block(key):
    f = f"{C}/{key[0]}_{key[1]}.json"
    if os.path.exists(f): return json.load(open(f))
    ids = blocks[key]
    gs = [cand[i][7] for i in ids]
    xmin, ymin, xmax, ymax = shapely.union_all([g.envelope for g in gs]).bounds
    out = {}
    with MemoryFile(nlcd(xmin - 300, ymin - 300, xmax + 300, ymax + 300)) as mf, mf.open() as r:
        a = r.read(1); T = r.transform
        for i, g in zip(ids, gs):
            ring = g.buffer(200).difference(g)
            win = rasterio.windows.from_bounds(*ring.bounds, transform=T).round_offsets().round_lengths()
            r0, c0 = max(int(win.row_off), 0), max(int(win.col_off), 0)
            sub = a[r0:r0 + int(win.height), c0:c0 + int(win.width)]
            if sub.size == 0: continue
            st = rasterio.windows.transform(rasterio.windows.Window(c0, r0, sub.shape[1], sub.shape[0]), T)
            inside = ~geometry_mask([mapping(g)], sub.shape, st, all_touched=False)
            rin = ~geometry_mask([mapping(ring)], sub.shape, st, all_touched=False)
            w = sub[inside]; rr = sub[rin]
            if rr.size == 0: continue
            out[str(i)] = [round(float(WAT[w].mean()), 2) if w.size else None, round(float(NATURAL[rr].mean()), 2),
                           round(float(DEV[rr].mean()), 2), round(float(AG[rr].mean()), 2)]
    json.dump(out, open(f, "w")); return out
keys = sorted(blocks); print(len(keys), "land-cover blocks", flush=True)
LC = {}; done = 0
with ThreadPoolExecutor(4) as ex:
    for res in ex.map(block, keys):
        LC.update(res); done += 1
        if done % 100 == 0: print(done, "blocks", flush=True)
# ---- Chad's 15 ft clarity cut-off from the Lakes tab
P = json.load(open(ROOT + "/props.json")); meas = {}
for st, ws in P.items():
    if not isinstance(ws, list) or len(st) != 2: continue
    for w in ws:
        m = re.match(r"([\d.]+) ft", str(w.get("v", "")))
        if w.get("t") == "lake" and m: meas.setdefault((re.sub(r"\s+", " ", w["n"].lower()), w.get("st") or st), []).append(float(m.group(1)))
def full(n): return re.sub(r"\bLk\b", "Lake", re.sub(r"\bPd\b", "Pond", n))
# ---- decide
lakes, geoms, why = [], [], {"not open water in 2021": 0, "murky colour": 0, "shore not wild": 0, "measured under 15 ft": 0, "no land cover": 0}
for i, c in enumerate(cand):
    name, st, fips, g, acres, la, lo, gm = c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7]
    lc = LC.get(str(i))
    if not lc: why["no land cover"] += 1; continue
    wat, nat, dev, ag = lc
    if wat is not None and wat < 0.4 and acres >= 2: why["not open water in 2021"] += 1; continue
    if wat is not None and wat < 0.2: why["not open water in 2021"] += 1; continue
    nm = full(name); ms = meas.get((nm.lower(), st))
    if ms and max(ms) < 15: why["measured under 15 ft"] += 1; continue
    col = colour.get(i)
    if col:
        if col[0] > 505: why["murky colour"] += 1; continue
        how = "colour"
    else:
        if nat < 0.75 or dev > 0.05 or ag > 0.10: why["shore not wild"] += 1; continue
        how = "shore"
    b = g.bounds; r0, r1 = int((Y0 - b[3]) / D), int(math.ceil((Y0 - b[1]) / D)); c0, c1 = int((b[0] - X0) / D), int(math.ceil((b[2] - X0) / D))
    win = dem[max(r0, 0):r1 + 1, max(c0, 0):c1 + 1]; win = win[win > -9000]
    el = int(win.min()) if win.size else 0
    lakes.append([nm, st, fips, round(acres, 1), el, round(la, 5), round(lo, 5), 0, 0, round(max(ms), 1) if ms else None,
                  col[0] if col else None, round(nat * 100), how])
    geoms.append(mapping(g.simplify(0.00003)))
print("left out:", why, flush=True)
from collections import Counter
print("KEPT", len(lakes), "lakes:", dict(sorted(Counter(l[1] for l in lakes).items())), "| by colour", sum(1 for l in lakes if l[12] == "colour"),
      "| by wild shore", sum(1 for l in lakes if l[12] == "shore"), "| named", sum(1 for l in lakes if l[0]), flush=True)
json.dump(lakes, open(HERE + "/lakes.json", "w"), separators=(",", ":"))
json.dump(geoms, open(HERE + "/lakes_geom.json", "w"), separators=(",", ":"))
print("sizes MB", os.path.getsize(HERE + "/lakes.json") // 2**20, os.path.getsize(HERE + "/lakes_geom.json") // 2**20)
