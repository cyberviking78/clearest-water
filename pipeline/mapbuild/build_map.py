"""One-time build of the detailed map layers (the geography does not change month to month; listings do).
Writes ../map/nat.json (national view) and ../map/st/<ST>.json (state detail, loaded when zoomed in).
Lines and rings are stored as delta-encoded integers (degrees x SCALE) to keep the files small; the page decodes them.

Sources: trail geometry (pipeline/trails/geom), ranked-water shapes (pipeline/shore), springheads (pipeline/heads/heads.json),
city limits (pipeline/trails/bigcities.json), Natural Earth 10m rivers and lakes, US Census TIGER 2024 primary and
secondary roads, Census cartographic state outlines, Census 2023 population estimates with Gazetteer coordinates."""
import json, glob, os, csv, io, zipfile, collections
import numpy as np, shapely, shapefile
from shapely.geometry import shape, mapping
P = "/home/claude/live/pipeline"; G = "/home/claude/geo_src"; OUT = "/home/claude/live/map"
os.makedirs(OUT + "/st", exist_ok=True)
FIPS = {}
# ---- states
sf = shapefile.Reader(G + "/state500k.zip")
ST = {}
for r in sf.iterShapeRecords():
    s = r.record["STUSPS"]
    if s in ("PR", "VI", "GU", "MP", "AS"): continue
    ST[s] = shape(r.shape.__geo_interface__); FIPS[r.record["STATEFP"]] = s
codes = sorted(ST); sgeo = [ST[s] for s in codes]; stree = shapely.STRtree(sgeo)
def states_of(g):
    return [codes[i] for i in stree.query(g, predicate="intersects")]
D = {s: collections.defaultdict(list) for s in codes}
NAT = collections.defaultdict(list)

def enc(coords, scale):
    a = np.round(np.asarray(coords, dtype=float)[:, :2] * scale).astype(np.int64)
    if len(a) < 2: return None
    d = np.vstack([a[:1], np.diff(a, axis=0)])
    keep = np.ones(len(d), bool); keep[1:] = np.any(d[1:] != 0, axis=1)   # drop repeated points
    d = d[keep]
    if len(d) < 2: return None
    return d.ravel().tolist()
def lines_of(g):
    if g.is_empty: return []
    t = g.geom_type
    if t == "LineString": return [list(g.coords)]
    if t == "MultiLineString": return [list(x.coords) for x in g.geoms]
    if t == "Polygon": return [list(g.exterior.coords)] + [list(i.coords) for i in g.interiors]
    if t in ("MultiPolygon", "GeometryCollection"): return [c for x in g.geoms for c in lines_of(x)]
    return []
def polys_of(g):
    """[[ring, hole, ...], ...] for polygon parts; [] otherwise"""
    t = g.geom_type
    if t == "Polygon": return [[list(g.exterior.coords)] + [list(i.coords) for i in g.interiors]]
    if t in ("MultiPolygon", "GeometryCollection"): return [p for x in g.geoms for p in polys_of(x)]
    return []
def plines_of(g):
    t = g.geom_type
    if t == "LineString": return [list(g.coords)]
    if t == "MultiLineString": return [list(x.coords) for x in g.geoms]
    if t == "GeometryCollection": return [c for x in g.geoms for c in plines_of(x)]
    return []
def encpoly(g, scale):
    out = []
    for p in polys_of(g):
        rs = [enc(r, scale) for r in p]
        if rs[0]: out.append([r for r in rs if r])
    return out

import pickle
CACHE = "/home/claude/live/mapbuild/stage1.pkl"
if os.path.exists(CACHE):
    D, NAT = pickle.load(open(CACHE, "rb")); D = {k: collections.defaultdict(list, v) for k, v in D.items()}; NAT = collections.defaultdict(list, NAT)
    SKIP1 = True
else: SKIP1 = False
# ---- trails
TR = {t["id"]: t for t in json.load(open(P + "/trails/trails.json"))}
ntr = 0
for f in ([] if SKIP1 else sorted(glob.glob(P + "/trails/geom/g*.json"))):
    for tid, Lg in json.load(open(f)).items():
        tid = int(tid); ty = TR[tid]["type"]
        for name, c in Lg:
            if len(c) < 2: continue
            g = shapely.LineString(c)
            gn = g.simplify(0.0012)
            if gn.length > 0.002:
                e = enc(gn.coords, 1e4)
                if e: NAT["tr"].append([tid, ty, e])
            gd = g.simplify(0.00003)
            e = enc(gd.coords, 1e5)
            if not e: continue
            for s in states_of(g):
                D[s]["tr"].append([tid, ty, name if name and name != TR[tid]["name"] else 0, e]); ntr += 1
print("trail segments", len(NAT["tr"]), "national,", ntr, "state", flush=True)

# ---- ranked waters (exact shapes the listings were matched against)
props = json.load(open(P + "/props.json"))
for f in ([] if SKIP1 else sorted(glob.glob(P + "/shore/*.json"))):
    for k, v in json.load(open(f)).items():
        if not v.get("geom"): continue
        grp, i = k.rsplit("_", 1); i = int(i)
        pr = props[grp][i]
        st = pr.get("st") if grp in ("FS", "SP") else grp
        g = shape(v["geom"]).simplify(0.00002)
        kind = "s" if grp == "FS" else "f" if grp == "SP" else ("l" if pr.get("t") == "lake" else "r")
        rec = [grp, i, kind, pr.get("n") or "", encpoly(g, 1e5), [e for e in (enc(c, 1e5) for c in plines_of(g)) if e]]
        for s in ([st] if st in D else states_of(g)):
            D[s]["wt"].append(rec)
print("ranked water shapes", sum(len(D[s]["wt"]) for s in D), flush=True)

if not SKIP1: pickle.dump(({k: dict(v) for k, v in D.items()}, dict(NAT)), open(CACHE, "wb"))
# ---- springheads (every magnitude 1-4 vent, not only those with listings)
for h in json.load(open(P + "/heads/heads.json")):
    if h["st"] in D:
        D[h["st"]]["hd"].append([h["name"], h["mag"], round(h["lat"], 5), round(h["lon"], 5), h.get("q")])

# ---- city limits
for c in json.load(open(P + "/trails/bigcities.json")):
    g = shape(c["geom"]).simplify(0.0002)
    for s in states_of(g):
        D[s]["cl"].append([c["name"], encpoly(g, 1e5)])

# ---- Natural Earth rivers and lakes (context; the county-level water layer adds detail when zoomed in)
us = shapely.union_all([g.simplify(0.01) for g in sgeo]).buffer(0.05)
for fn, kind in (("ne_10m_rivers_north_america", "rv"), ("ne_10m_rivers_lake_centerlines", "rv"), ("ne_10m_lakes_north_america", "lk"), ("ne_10m_lakes", "lk")):
    seen = set()
    for ft in json.load(open(f"{G}/{fn}.geojson"))["features"]:
        if not ft.get("geometry"): continue
        g = shape(ft["geometry"])
        if g.is_empty or not g.intersects(us): continue
        pr = ft["properties"]; nm = pr.get("name") or ""; sr = pr.get("scalerank") or 12
        key = (nm, round(g.centroid.x, 2), round(g.centroid.y, 2))
        if key in seen: continue
        seen.add(key)
        if kind == "rv":
            if sr <= 7:
                for c in lines_of(g.simplify(0.004)):
                    e = enc(c, 1e4)
                    if e: NAT["rv"].append([nm, sr, e])
            gs = g.simplify(0.0006)
            for s in states_of(g):
                for c in lines_of(gs.intersection(ST[s].buffer(0.02))):
                    e = enc(c, 1e5)
                    if e: D[s]["rv"].append([nm, sr, e])
        else:
            if sr <= 6 or g.area > 0.05:
                NAT["lk"].append([nm, encpoly(g.simplify(0.004), 1e4)])
            gs = g.simplify(0.0004)
            for s in states_of(g):
                D[s]["lk"].append([nm, encpoly(gs, 1e5)])
print("NE water done", flush=True)

# ---- roads: interstates and US highways nationally; primary + secondary per state
RT = {"I": "i", "U": "u", "S": "s"}
r = shapefile.Reader(G + "/primaryroads.zip")
byname = collections.defaultdict(list)
for sr_ in r.iterShapeRecords():
    if sr_.record["RTTYP"] not in ("I", "U"): continue
    byname[(sr_.record["FULLNAME"], sr_.record["RTTYP"])].append(shape(sr_.shape.__geo_interface__))
for (nm, rt), gs in byname.items():
    g = shapely.line_merge(shapely.union_all(gs)).simplify(0.003)
    for c in lines_of(g):
        e = enc(c, 1e4)
        if e and (rt == "I"): NAT["rd"].append([nm, "i", e])
for z in sorted(glob.glob(G + "/psr/*.zip")):
    s = FIPS.get(os.path.basename(z)[:2])
    if not s: continue
    rr = shapefile.Reader(z)
    byn = collections.defaultdict(list)
    for sr_ in rr.iterShapeRecords():
        rt = sr_.record["RTTYP"]
        if rt not in RT: continue
        byn[(sr_.record["FULLNAME"], RT[rt])].append(shape(sr_.shape.__geo_interface__))
    for (nm, rt), gs in byn.items():
        g = shapely.line_merge(shapely.union_all(gs)).simplify(0.00025)
        for c in lines_of(g):
            e = enc(c, 1e5)
            if e: D[s]["rd"].append([nm, rt, e])
print("roads done", flush=True)

# ---- places (incorporated places with 2023 population, Gazetteer label points)
gz = {}
with zipfile.ZipFile(G + "/gaz_place.zip") as zf:
    txt = zf.read(zf.namelist()[0]).decode("latin-1")
for row in csv.DictReader(io.StringIO(txt), delimiter="\t"):
    row = {k.strip(): v.strip() for k, v in row.items()}
    gz[row["GEOID"]] = (float(row["INTPTLAT"]), float(row["INTPTLONG"]))
import re
for row in csv.DictReader(open(G + "/subest.csv", encoding="latin-1")):
    if row["SUMLEV"] != "162": continue
    s = FIPS.get(row["STATE"]); ll = gz.get(row["STATE"] + row["PLACE"])
    if not s or not ll: continue
    pop = int(row["POPESTIMATE2023"])
    nm = re.sub(r" (city|town|village|borough|municipality|CDP|city and borough|consolidated government.*|metropolitan government.*|unified government.*|metro government.*|urban county)( \(balance\))?$", "", row["NAME"])
    if pop >= 15000: NAT["pl"].append([nm, s, round(ll[0], 4), round(ll[1], 4), pop])
    if pop >= 300: D[s]["pl"].append([nm, round(ll[0], 4), round(ll[1], 4), pop])
for s in D: D[s]["pl"].sort(key=lambda x: -x[3])
NAT["pl"].sort(key=lambda x: -x[4])

# ---- write
NAT["sb"] = {s: [round(v, 3) for v in ST[s].bounds] for s in codes}
json.dump(NAT, open(OUT + "/nat.json", "w"), separators=(",", ":"), ensure_ascii=False)
tot = 0
for s in codes:
    D[s]["v"] = 1
    b = json.dumps(D[s], separators=(",", ":"), ensure_ascii=False)
    open(f"{OUT}/st/{s}.json", "w").write(b); tot += len(b)
print("nat.json", os.path.getsize(OUT + "/nat.json") // 1024, "KB; states", tot // 1024 // 1024, "MB;",
      sorted(((os.path.getsize(f"{OUT}/st/{s}.json") // 1024, s) for s in codes), reverse=True)[:8])
for k in ("tr", "wt", "rd", "rv", "lk", "pl", "cl", "hd"):
    print(k, sum(len(json.dumps(D[s][k], separators=(",", ":"))) for s in codes) // 1024, "KB")
