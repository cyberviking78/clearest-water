"""Spring runs for the new springs, the same way as the Springs tab's other springs ("run traced"): the NHD flowline nearest
the vents (within 400 m) followed downstream for about 5 km, plus NHD waterbody and area polygons (spring pools, the river
it runs into) within 150 m of a vent, clipped to 5 km of the vents. A vent with nothing mapped near it gets a 60 m pool circle.
Source: USGS National Hydrography Dataset, hydro.nationalmap.gov (large scale). Writes cache/nhd/<i>.json and runs.json."""
import json, os, subprocess, urllib.parse, math
import shapely
from shapely.geometry import shape, LineString, Point, mapping, Polygon
from shapely.ops import linemerge
C = json.load(open("cands.json")); os.makedirs("cache/nhd", exist_ok=True)
U = "https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/{}/query?"
def q(layer, bb):
    f = f"cache/nhd/{layer}_{bb}.json"
    if not os.path.exists(f) or os.path.getsize(f) < 50:
        url = U.format(layer) + urllib.parse.urlencode({"where": "1=1", "geometry": bb, "geometryType": "esriGeometryEnvelope", "inSR": 4326, "outSR": 4326,
              "spatialRel": "esriSpatialRelIntersects", "outFields": "gnis_name,fcode,ftype,flowdir", "returnGeometry": "true", "f": "json"})
        subprocess.run(["curl", "-s", "-m", "200", "-o", f, url])
    return json.load(open(f)).get("features", [])
M = lambda lat: (111200.0, 111200.0 * math.cos(math.radians(lat)))   # metres per degree (lat, lon)
out = []
for i, c in enumerate(C):
    vents = [(v[1], v[0]) for v in c["vents"]]; lat0 = vents[0][1]; my, mx = M(lat0)
    lo = [v[0] for v in vents]; la = [v[1] for v in vents]
    bb = f"{min(lo)-.06:.3f},{min(la)-.05:.3f},{max(lo)+.06:.3f},{max(la)+.05:.3f}"
    fl = [f for f in q(6, bb) if f.get("geometry", {}).get("paths")]
    lines = []
    for f in fl:
        for p in f["geometry"]["paths"]: lines.append((f["attributes"], [tuple(x[:2]) for x in p]))
    def dm(a, b): return math.hypot((a[0] - b[0]) * mx, (a[1] - b[1]) * my)
    starts = {}
    for j, (_, p) in enumerate(lines): starts.setdefault((round(p[0][0], 6), round(p[0][1], 6)), []).append(j)
    run, used = [], set()
    for v in vents:
        best = None
        for j, (_, p) in enumerate(lines):
            d = LineString(p).distance(Point(v)) * mx
            if d <= 400 and (best is None or d < best[0]): best = (d, j)
        if not best: continue
        j = best[1]; L = 0.0
        # start at the point of the line nearest the vent
        p = lines[j][1]; k = min(range(len(p)), key=lambda t: dm(p[t], v)); seg = p[k:]
        while True:
            if j in used: break
            used.add(j)
            for a, b in zip(seg, seg[1:]):
                if L >= 5000: break
                run.append((a, b)); L += dm(a, b)
            if L >= 5000: break
            end = lines[j][1][-1]; nx = [t for t in starts.get((round(end[0], 6), round(end[1], 6)), []) if t not in used]
            if not nx: break
            j = nx[0]; seg = lines[j][1]
    geoms = []
    if run:
        ml = linemerge([LineString([a, b]) for a, b in run])
        geoms += list(ml.geoms) if hasattr(ml, "geoms") else [ml]
    near = shapely.union_all([Point(v).buffer(150 / mx) for v in vents])
    reach = shapely.union_all([Point(v).buffer(5000 / mx) for v in vents])
    runbuf = shapely.union_all([g.buffer(30 / mx) for g in geoms]) if geoms else near
    for layer in (12, 9):
        for f in q(layer, bb):
            try: g = shape({"type": "Polygon", "coordinates": f["geometry"]["rings"]}).buffer(0)
            except Exception: continue
            if g.is_empty: continue
            if g.intersects(near) or (layer == 9 and g.intersects(runbuf)):
                geoms.append(g.intersection(reach))
    for v in vents:
        if not any(g.distance(Point(v)) * mx < 120 for g in geoms): geoms.append(Point(v).buffer(60 / mx, 8))
    G = shapely.GeometryCollection([g.simplify(0.00002) for g in geoms if not g.is_empty])
    names = []
    for j in sorted(used, key=lambda t: list(used).index(t)):
        n = lines[j][0].get("gnis_name") or ""
        if n and n not in names: names.append(n)
    out.append({"geom": mapping(G), "method": "run traced", "flows": names})
    print(f"{i:2} {c['lead'][2]:42} run {sum(dm(a,b) for a,b in run)/1000:4.1f} km, {len(geoms)} parts, {names[:3]}", flush=True)
json.dump(out, open("runs.json", "w"))
