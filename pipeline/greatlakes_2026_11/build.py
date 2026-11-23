"""Great Lakes shoreline for the property search: one water per (state, Great Lake) -- 13 in all.
Shoreline = the edge of Census TIGER 2024 AREAWATER polygons named for the lake (plus the bays joined to it, e.g. Green Bay,
Saginaw Bay, Grand Traverse Bay, and large joined pieces TIGER labels otherwise) in every county on that lake, kept where it meets land (within ~250 m of the county outline).
Search cells: 0.1 deg lon x 0.08 deg lat grid, clipped to the shoreline buffered ~800 m (only listings on the lake are kept).
Writes out/gl.json: {ST: [{lake, geom, boxes, counties, bbox}]}"""
import json, math, os, re, sys, collections, urllib.request, time
import shapely, shapefile
from shapely.geometry import shape, mapping, box
G = "/home/claude/geo_src"; OUT = os.path.dirname(os.path.abspath(__file__)) + "/out"; os.makedirs(OUT, exist_ok=True)
LAKES = {"Superior": ["MN", "WI", "MI"], "Michigan": ["WI", "IL", "IN", "MI"], "Huron": ["MI"], "Erie": ["MI", "OH", "PA", "NY"], "Ontario": ["NY"]}
ne = {f["properties"]["name"][5:]: shape(f["geometry"]) for f in json.load(open(G + "/ne_10m_lakes.geojson"))["features"]
      if f["properties"].get("name") in ("Lake " + k for k in LAKES)}
CT = [(r.record["STUSPS"], r.record["NAME"], r.record["GEOID"], shape(r.shape.__geo_interface__)) for r in shapefile.Reader(G + "/county500k.zip").iterShapeRecords()]
def get(url):
    for a in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read()
        except Exception as e:
            if "404" in str(e): return None
            time.sleep(5 * (a + 1))
def aw(gid):
    f = f"{G}/aw/{gid}.zip"
    if not os.path.exists(f) or os.path.getsize(f) < 1000:
        b = get(f"https://www2.census.gov/geo/tiger/TIGER2024/AREAWATER/tl_2024_{gid}_areawater.zip")
        if b: open(f, "wb").write(b)
    return [(r.record["FULLNAME"] or "", r.record["MTFCC"], shape(r.shape.__geo_interface__)) for r in shapefile.Reader(f).iterShapeRecords()]
DX, DY, ZB = 0.1, 0.08, 0.008
def cells_for(line):
    zone = line.buffer(ZB); out = []
    for cx in range(math.floor(zone.bounds[0] / DX), math.floor(zone.bounds[2] / DX) + 1):
        for cy in range(math.floor(zone.bounds[1] / DY), math.floor(zone.bounds[3] / DY) + 1):
            b = box(cx * DX, cy * DY, (cx + 1) * DX, (cy + 1) * DY)
            if not b.intersects(zone): continue
            c = list(b.intersection(zone).bounds)
            if c[2] - c[0] < 0.01: m = (c[0] + c[2]) / 2; c[0], c[2] = m - 0.005, m + 0.005
            if c[3] - c[1] < 0.01: m = (c[1] + c[3]) / 2; c[1], c[3] = m - 0.005, m + 0.005
            out.append([round(c[0], 4), round(c[2], 4), round(c[1], 4), round(c[3], 4)])
    return out
res = collections.defaultdict(list)
for lake, states in LAKES.items():
    for st in states:
        cs = [(n, gid, g) for s, n, gid, g in CT if s == st and g.distance(ne[lake]) < 0.04]
        polys, others = [], []
        for n, gid, g in cs:
            for nm, mt, p in aw(gid):
                if nm == "Lk " + lake: polys.append(p)
                elif mt == "H2051" or (re.search(r"\bBay\b", nm) and p.area > 5e-5) or (mt == "H2030" and p.area > 2e-3 and not re.search(r"\b(Lk|Lake|Res|Reservoir|Pond)\b", nm)): others.append(p)   # large mislabeled pieces too
        if not polys: print("NO WATER", st, lake); continue
        W = shapely.union_all(polys)
        for _ in range(4):      # bays joined to the lake, and bays joined to those
            add = [p for p in others if p.distance(W) < 0.0005 and not W.contains(p)]
            if not add: break
            W = shapely.union_all([W] + add); others = [p for p in others if p not in add]
        land = shapely.union_all([g for n, gid, g in cs])
        shore = W.boundary.intersection(land.buffer(0.0025))
        shore = shapely.line_merge(shapely.union_all([l for l in getattr(shore, "geoms", [shore]) if l.length > 0.001])).simplify(0.00005)
        ctys = sorted({n for n, gid, g in cs if g.buffer(0.003).intersects(shore)})
        cells = cells_for(shore)
        km = shore.length * 111 * math.cos(math.radians(shore.centroid.y))
        res[st].append(dict(lake=lake, geom=mapping(shore), boxes=cells, counties=ctys, bbox=[round(x, 4) for x in shore.bounds], km=round(km)))
        print(st, lake, f"{km:.0f} km shore,", len(cells), "cells,", len(ctys), "counties", flush=True)
json.dump(res, open(OUT + "/gl.json", "w"))
print("TOTAL cells", sum(len(e["boxes"]) for v in res.values() for e in v))
