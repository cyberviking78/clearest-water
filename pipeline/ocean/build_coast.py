"""Oceanfront (Nov 23, 2026), step 1: the open-ocean coast of the Atlantic (Maine to Florida) and Pacific (California, Oregon,
Washington) states, cut into ~1 km pieces.
Census TIGER 2024 coastline (tl_2024_us_coastline: NAME Atlantic / Pacific) also runs around bays and sounds (Chesapeake, Long
Island Sound, Puget Sound, Biscayne Bay...). Chad wants open ocean only, so each piece is kept only when the sea in front of it is
open: from a point just offshore, rays every 5 degrees must run 40 km without touching land over an arc of at least 90 degrees
(land: Census state outlines 1:500k, plus Natural Earth 10m land for Canada, Mexico, the Bahamas and islands). Bay and sound
shores, inlets and the backs of barrier islands fail this; the beach side of a barrier island passes.
Inputs (src/): tl_2024_us_coastline.zip, cb_2024_us_state_500k.zip, ne_10m_land.{shp,shx,dbf}.  Output: coast.json
[[id, state, lon0, lat0, lon1, lat1, [[lon, lat], ...], open arc degrees, bearing of the open sea]] for the kept pieces, and coast_all.json (every piece,
same layout, open or not: run_ocean.py uses it to tell a beach from a bay shore)."""
import json, math, os, sys
import numpy as np, shapefile, shapely
from shapely.geometry import shape, Point, LineString
from shapely.ops import substring
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = sys.argv[1] if len(sys.argv) > 1 else HERE + "/src"
ATL = {"ME", "NH", "MA", "RI", "CT", "NY", "NJ", "DE", "MD", "VA", "NC", "SC", "GA", "FL"}; PAC = {"CA", "OR", "WA"}
STA = []
for sr in shapefile.Reader(SRC + "/cb_2024_us_state_500k.zip").iterShapeRecords():
    STA.append((sr.record["STUSPS"], shape(sr.shape.__geo_interface__)))
land = [g for s, g in STA]
for sr in shapefile.Reader(SRC + "/ne_10m_land").iterShapes():
    g = shape(sr.__geo_interface__)
    if g.bounds[1] < 0: continue          # Antarctica's outline wraps the globe and would cover the ocean
    if g.intersects(shapely.box(-140, 15, -55, 60)): land.append(g.intersection(shapely.box(-140, 15, -55, 60)))
LAND = shapely.union_all([g.buffer(0) for g in land]); shapely.prepare(LAND)
stree = shapely.STRtree([g for s, g in STA])
def state_of(p):
    i = stree.nearest(p); return STA[i][0]
lines = []
for sr in shapefile.Reader(SRC + "/tl_2024_us_coastline.zip").iterShapeRecords():
    if sr.record["NAME"] not in ("Atlantic", "Pacific"): continue
    g = shape(sr.shape.__geo_interface__)
    for part in getattr(g, "geoms", [g]):
        x, y = part.coords[0]
        if x < -126 or y < 24.3 or x > -66: continue          # Alaska, Hawaii, Puerto Rico left out
        lines.append(part)
print(len(lines), "coastline lines", flush=True)
KM = 1 / 111.0
DIRS = np.radians(np.arange(0, 360, 5))
def open_arc(lon, lat):
    """largest run of 5-degree rays that reach 40 km over water from just offshore, and the bearing at its middle (the way the
    open sea lies)"""
    k = math.cos(math.radians(lat))
    rays = []
    for a in DIRS:
        dx, dy = math.sin(a) / k, math.cos(a)
        rays.append(LineString([(lon + dx * 0.3 * KM, lat + dy * 0.3 * KM), (lon + dx * 40 * KM, lat + dy * 40 * KM)]))
    ok = ~shapely.intersects(np.array(rays, dtype=object), LAND)
    if ok.all(): return 360, 0
    best, run, end = 0, 0, 0
    for j, v in enumerate(np.concatenate([ok, ok])):
        run = run + 1 if v else 0
        if run > best: best, end = run, j
    best = min(best, 72)
    return best * 5, int(((end - (best - 1) / 2) % 72) * 5)
pieces = []
for ln in lines:
    L = ln.length; n = max(1, round(L / (1.0 * KM)))
    for j in range(n):
        seg = substring(ln, L * j / n, L * (j + 1) / n)
        if seg.length == 0 or seg.geom_type != "LineString": continue
        m = seg.interpolate(0.5, normalized=True)
        pieces.append((seg, m))
print(len(pieces), "pieces of about 1 km", flush=True)
out, allp = [], []
for i, (seg, m) in enumerate(pieces):
    st = state_of(m)
    if st not in ATL | PAC: continue
    arc, brg = open_arc(m.x, m.y)
    if st == "WA" and m.y > 48.0 and m.x > -124.6: arc = 0     # Strait of Juan de Fuca: wide enough to pass the ray test, but not open ocean
    c = [[round(x, 5), round(y, 5)] for x, y in seg.simplify(0.00005).coords]
    rec = [len(allp), st, c[0][0], c[0][1], c[-1][0], c[-1][1], c, arc, brg]
    allp.append(rec)
    if arc >= 90: out.append(rec)
    if i % 1000 == 0: print(i, "of", len(pieces), flush=True)
json.dump(out, open(HERE + "/coast.json", "w"), separators=(",", ":"))
json.dump(allp, open(HERE + "/coast_all.json", "w"), separators=(",", ":"))
from collections import Counter
print("KEPT", len(out), "of", len(allp), "km;", dict(sorted(Counter(r[1] for r in out).items())))
