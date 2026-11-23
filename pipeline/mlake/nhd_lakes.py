"""Check every candidate mountain lake (lakes.json / lakes_geom.json from build_lakes.py, Census TIGER shapes) against the USGS
National Hydrography Dataset (NHD high resolution, The National Map, hydro.nationalmap.gov, Waterbody layer):
- kept only when at least half of it is covered by NHD lake/pond polygons that hold water all year (FCode 39000, 39004, 39009-39012),
  or by an NHD reservoir whose name says Lake (natural lakes raised by a small dam, e.g. Payette, Wallowa). This drops river
  channels the Census map coded as lake area (NHD maps them as stream/river), intermittent and dry ponds, marshes and stock tanks.
- named from NHD (USGS GNIS names) when the Census map has no name; a lake NHD names "... Reservoir", "Tank", "Pit" etc. is dropped.
- a shape check backs this up: a lake whose average width (2 x area / shoreline) is under 40 m and whose outline is long and thin
  (4 pi area / shoreline^2 under 0.03) is a channel, not a lake.
Reads lakes_tiger.json / lakes_geom_tiger.json (build_lakes.py), writes lakes_nhd.json / lakes_geom_nhd.json (the checked lakes, TIGER outlines) for clarity.py. NHD responses are
cached in nhd_cache/. Usage: nhd_lakes.py"""
import json, os, re, math, time, urllib.request, urllib.parse, sys
from concurrent.futures import ThreadPoolExecutor
import shapely, pyproj
from shapely.geometry import shape, mapping, box
from shapely.ops import transform
HERE = os.path.dirname(os.path.abspath(__file__))
LK = json.load(open(HERE + "/lakes_tiger.json")); GE = [shape(g) for g in json.load(open(HERE + "/lakes_geom_tiger.json"))]
C = HERE + "/nhd_cache"; os.makedirs(C, exist_ok=True)
URL = "https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/12/query"
PERENNIAL = {39000, 39004, 39009, 39010, 39011, 39012}
BADN = re.compile(r"reservoir|\bres\b|tank|\bpit\b|pond number|tailing|sewage|settling|evaporat|lagoon|hatchery|treatment|waste|gravel", re.I)
# tiles of 0.2 x 0.2 degrees holding candidate lakes
T = 0.2; tiles = {}
for i, g in enumerate(GE):
    b = g.bounds; tiles.setdefault((math.floor(b[0] / T), math.floor(b[1] / T)), []).append(i)
print(len(tiles), "tiles to check", flush=True)
def query(w, s, e, n, depth=0):
    """NHD lakes, ponds and reservoirs in a box; a box the server can't answer in time is split into quarters."""
    feats, off = [], 0
    while True:
        q = dict(where="ftype in (390,436) and areasqkm >= 0.002", geometry=f"{w},{s},{e},{n}", geometryType="esriGeometryEnvelope", inSR=4326,
                 spatialRel="esriSpatialRelIntersects", outFields="gnis_name,ftype,fcode,areasqkm", returnGeometry="true", outSR=4326,
                 maxAllowableOffset=0.00005, geometryPrecision=6, resultOffset=off, resultRecordCount=500, f="geojson")
        d = None
        for a in range(3):
            try:
                d = json.load(urllib.request.urlopen(URL + "?" + urllib.parse.urlencode(q), timeout=120)); break
            except Exception as ex:
                time.sleep(4 * (a + 1))
        if d is None:
            if depth >= 4: raise RuntimeError(f"NHD box {w},{s},{e},{n} failed")
            mx, my = (w + e) / 2, (s + n) / 2
            out = {}
            for bb in ((w, s, mx, my), (mx, s, e, my), (w, my, mx, n), (mx, my, e, n)):
                for f in query(*bb, depth + 1): out[json.dumps(f, sort_keys=True)] = f      # a lake on a quarter line comes back twice
            return list(out.values())
        fs = d.get("features", []); feats += fs
        if len(fs) < 500 and not d.get("properties", {}).get("exceededTransferLimit"): break
        off += len(fs)
    return feats
def fetch(key):
    f = f"{C}/{key[0]}_{key[1]}.json"
    if os.path.exists(f): return json.load(open(f))
    ids = tiles[key]; w, s, e, n = shapely.union_all([GE[i].envelope for i in ids]).bounds
    feats = query(w, s, e, n)
    json.dump(feats, open(f, "w"), separators=(",", ":")); return feats
with ThreadPoolExecutor(4) as ex: res = dict(zip(tiles, ex.map(fetch, list(tiles))))
keep, geoms, why = [], [], {"river shape": 0, "not a year-round lake in NHD": 0, "NHD reservoir/tank name": 0}
for key, ids in tiles.items():
    nf = []
    for f in res[key]:
        if not f.get("geometry"): continue
        p = {k.lower(): v for k, v in f["properties"].items()}; ft, fc, nm = p.get("ftype"), p.get("fcode"), (p.get("gnis_name") or "").strip()
        ok = (ft == 390 and fc in PERENNIAL) or (ft == 436 and re.search(r"\blake\b", nm, re.I) and not re.search(r"reservoir", nm, re.I))
        try: g = shape(f["geometry"]).buffer(0)
        except Exception: continue
        nf.append((g, ok, nm, 1 if ft == 436 or fc in (39010, 39012) else 0))   # reservoir: NHD type reservoir, or a lake whose level is a dam's normal pool or spillway
    tree = shapely.STRtree([t[0] for t in nf]) if nf else None
    for i in ids:
        g = GE[i]; l = list(LK[i])
        la, lo = l[5], l[6]
        pr = pyproj.Transformer.from_crs(4326, pyproj.CRS.from_proj4(f"+proj=aeqd +lat_0={la} +lon_0={lo} +datum=WGS84 +units=m"), always_xy=True).transform
        gm = transform(pr, g); A, P = gm.area, gm.length
        if P and 2 * A / P < 40 and 4 * math.pi * A / P ** 2 < 0.03: why["river shape"] += 1; continue
        cov, best, bft = 0.0, None, None
        if tree is not None:
            for j in tree.query(g):
                h, ok, nm, rv = nf[j]
                if not ok: continue
                try: ov = g.intersection(h).area
                except Exception: continue
                cov += ov
                if bft is None or ov > bft[0]: bft = (ov, rv)
                if nm and (best is None or ov > best[0]): best = (ov, nm)
        if cov < 0.5 * g.area: why["not a year-round lake in NHD"] += 1; continue
        if best and BADN.search(best[1]): why["NHD reservoir/tank name"] += 1; continue
        if best: l[0] = best[1]          # the full official (GNIS) name: "Priest Lake", not the Census abbreviation "Priest Lk"
        l = l[:8] + [1 if bft and bft[1] else 0]     # index 8: 1 when NHD maps it as a reservoir (a dammed or dam-raised lake)
        keep.append(l); geoms.append(g)
print(f"kept {len(keep)} of {len(LK)}; dropped {why}; named {sum(1 for l in keep if l[0])}", flush=True)
# ---- one entry per lake: the Census map cuts big lakes into pieces (county lines, bays); join touching pieces with the same name
grp = {}
for i, l in enumerate(keep):
    if l[0]: grp.setdefault(l[0].lower(), []).append(i)   # (Lake Tahoe spans two states, so the state is not part of the key)
gone = set()
for nm, ids in grp.items():
    if len(ids) < 2: continue
    buf = [geoms[i].buffer(0.004) for i in ids]          # about 400 m: the Census map also leaves slivers of a lake detached from it
    par = list(range(len(ids)))
    def root(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for a in range(len(ids)):
        for c in range(a + 1, len(ids)):
            if buf[a].intersects(buf[c]): par[root(a)] = root(c)
    comp = {}
    for a in range(len(ids)): comp.setdefault(root(a), []).append(ids[a])
    for mem in comp.values():
        if len(mem) < 2: continue
        big = max(mem, key=lambda i: keep[i][3]); g = shapely.union_all([geoms[i] for i in mem]); p = g.representative_point()
        keep[big] = [keep[big][0], keep[big][1], keep[big][2], round(sum(keep[i][3] for i in mem), 1), min(keep[i][4] for i in mem),
                     round(p.y, 5), round(p.x, 5), keep[big][7], max(keep[i][8] for i in mem)]
        geoms[big] = g; gone |= set(mem) - {big}
keep = [l for i, l in enumerate(keep) if i not in gone]; geoms = [g for i, g in enumerate(geoms) if i not in gone]
print("joined pieces:", len(gone), "->", len(keep), "lakes", flush=True)
# ---- Chad's clarity cut-off (Nov 12, 2026): a lake the Lakes tab measures at under 15 ft of clarity everywhere is left out
P = json.load(open(os.path.dirname(HERE) + "/props.json")); meas = {}
for st, ws in P.items():
    if not isinstance(ws, list) or len(st) != 2: continue
    for w in ws:
        m = re.match(r"([\d.]+) ft", str(w.get("v", "")))
        if w.get("t") == "lake" and m: meas.setdefault((re.sub(r"\s+", " ", w["n"].lower()), w.get("st") or st), []).append(float(m.group(1)))
def ms(l): return [v for (n, st), vs in meas.items() if n == l[0].lower() and (st == l[1] or n == "lake tahoe" or n == "bear lake" and l[1] in ("ID", "UT")) for v in vs]
murky = [i for i, l in enumerate(keep) if l[0] and ms(l) and max(ms(l)) < 15]
print("under 15 ft of measured clarity, left out:", sorted(set(keep[i][0] + " " + keep[i][1] for i in murky)), flush=True)
keep = [l for i, l in enumerate(keep) if i not in set(murky)]; geoms = [g for i, g in enumerate(geoms) if i not in set(murky)]
from collections import Counter
print(dict(sorted(Counter(l[1] for l in keep).items())))
json.dump(keep, open(HERE + "/lakes_nhd.json", "w"), separators=(",", ":"))
json.dump([mapping(g) for g in geoms], open(HERE + "/lakes_geom_nhd.json", "w"), separators=(",", ":"))
