"""Accuracy pass for the map (Nov 12, 2026).
1. River shapes: a river's shape is every stretch of that name inside its search box, and some boxes held two different rivers of
   the same name (Connecticut has several Mill Rivers). Keep only the connected stretches that the river's own monitoring
   stations sit on (within 1.5 km); if none do, keep the stretch nearest them. Search cells are rebuilt for the kept shape.
2. Water dots: the map used the centre of each water's search box, which for long rivers and widened lakes can land on dry land
   miles away. Each dot now sits on the water: a lake's dot at its monitoring station when that is in the lake, otherwise at the
   lake's visual centre; a river's dot on the channel next to its stations; a spring's at its vent; a Great Lakes shoreline's on
   the shore facing the open lake.
Usage: dots.py <page.html>   (edits pipeline/props.json and pipeline/shore/*.json in place, and the page's PR and FSD)"""
import json, math, os, re, sys, collections
import shapely
from shapely.geometry import shape, mapping, box, Point
from shapely.ops import polylabel
LIVE = "/home/claude/live"; HERE = os.path.dirname(os.path.abspath(__file__))
page = sys.argv[1]; h = open(page).read()
src = open(HERE + "/newwaters15.py").read()
src = src[:src.index("from concurrent.futures")].replace('os.path.dirname(os.path.abspath(__file__))', repr(HERE))
src = src.replace('h = open(LIVE + "/page.work.html").read()', 'h = open(%r).read()' % page)
exec(src)        # station lookups (stations, river_pts), TIGER helpers, the page's data
def obj(name):
    i = h.find("const " + name + "="); o, end = json.JSONDecoder().raw_decode(h[i + len("const " + name + "="):]); return o, i, i + len("const " + name + "=") + end
PR, _, _ = obj("PR"); FSD, _, _ = obj("FSD"); RV, _, _ = obj("RV")
site_of = {(k, r["n"]): r.get("site") for k, v in RV.items() for r in v["rows"]}
for r in FSD["rivers"]: site_of.setdefault((r[13], r[1]), None)
P = json.load(open(LIVE + "/pipeline/props.json"))
SH = {st: json.load(open(f"{LIVE}/pipeline/shore/{st}.json")) for st in P}
KM = lambda lat: 111 * math.cos(math.radians(lat))
DX, DY = 0.15, 0.12
def cells_for(G):
    zone = G.buffer(0.015); out = []
    for cx in range(math.floor(zone.bounds[0] / DX), math.floor(zone.bounds[2] / DX) + 1):
        for cy in range(math.floor(zone.bounds[1] / DY), math.floor(zone.bounds[3] / DY) + 1):
            b = box(cx * DX, cy * DY, (cx + 1) * DX, (cy + 1) * DY)
            if not b.intersects(zone): continue
            c = list(b.intersection(zone).bounds)
            if c[2] - c[0] < 0.01: m = (c[0] + c[2]) / 2; c[0], c[2] = m - 0.005, m + 0.005
            if c[3] - c[1] < 0.01: m = (c[1] + c[3]) / 2; c[1], c[3] = m - 0.005, m + 0.005
            out.append([round(c[0], 4), round(c[2], 4), round(c[1], 4), round(c[3], 4)])
    return out
def parts(G):
    """connected pieces of a river shape (lines and any river-area polygons touching them)"""
    gs = list(getattr(G, "geoms", [G]))
    flat = []
    for g in gs: flat += list(getattr(g, "geoms", [g]))
    blobs = shapely.union_all([g.buffer(0.0004) for g in flat])
    out = []
    for b in getattr(blobs, "geoms", [blobs]):
        out.append(shapely.union_all([g for g in flat if g.intersects(b)]))
    return out
fixed = []; nofix = []
for st, L in P.items():
    for i, e in enumerate(L):
        key = f"{st}_{i}"; s = SH[st].get(key)
        if not s or not s.get("geom") or e["t"] != "river" or e.get("added", "") in ("2026-11-10b", "2026-11-12"): continue   # stretches and curated reaches are already cut to their own extent
        G = shape(s["geom"])
        name = re.sub(r"\s*\(.*\)", "", e["n"]); stt = e.get("st", st) if st in ("FS", "SP") else st
        try: pts = river_pts(stt, name, site_of.get((st, e["n"])) or site_of.get((stt, e["n"])))
        except Exception: pts = []
        if not pts: pts = [(e["lat"], e["lon"])]
        PT = shapely.MultiPoint([(x, y) for y, x in pts])
        ps = parts(G)
        if len(ps) < 2: continue
        near = [p for p in ps if p.distance(PT) * KM(e["lat"]) <= 1.5]
        if not near: continue                      # stations not on any piece: leave the shape alone
        keep = list(near)                          # then take back pieces of the same river split by a dam, lake or gap (within 2 km)
        while True:
            K = shapely.union_all(keep)
            more = [p for p in ps if p not in keep and p.distance(K) * KM(e["lat"]) <= 2]
            if not more: break
            keep += more
        if len(keep) == len(ps): continue
        G2 = shapely.union_all(keep)
        drop_km = sum(p.length for p in ps if p not in keep) * KM(e["lat"])
        if drop_km < 1: continue
        s["geom"] = mapping(G2.simplify(0.0001)); s["method"] = (s.get("method") or "") + " · kept the stretches its stations are on"
        if e.get("boxes"): e["boxes"] = [e["boxes"][0]] + cells_for(G2)
        fixed.append((st, e["n"], round(drop_km), len(ps), len(keep)))
print("river shapes trimmed to their own stretches:", len(fixed))
for f in fixed: print("  ", f)

# ---- dots on the water
ne = {f["properties"]["name"][5:]: shape(f["geometry"]) for f in json.load(open("/home/claude/geo_src/ne_10m_lakes.geojson"))["features"]
      if f["properties"].get("name") in ("Lake Superior", "Lake Michigan", "Lake Huron", "Lake Erie", "Lake Ontario")}
def dot(st, i, e):
    s = SH[st].get(f"{st}_{i}"); g = s and s.get("geom")
    p0 = Point(e["lon"], e["lat"]) if e.get("lat") is not None else None
    if not g: return [e["lat"], e["lon"]] if p0 else None
    G = shape(g)
    if e.get("gl"):
        lake = re.match(r"Lake (\w+)", e["n"]).group(1)
        q = shapely.ops.nearest_points(G, ne[lake].centroid)[0]
    elif e["t"] == "lake":
        polys = [x for x in getattr(G, "geoms", [G]) if x.geom_type == "Polygon"]
        if p0 is not None and G.contains(p0): q = p0
        elif polys:
            part = min(polys, key=lambda x: x.distance(p0)) if p0 is not None else max(polys, key=lambda x: x.area)
            q = polylabel(part, tolerance=0.0002)
        else: q = shapely.ops.nearest_points(G, p0)[0] if p0 is not None else G.representative_point()
    elif e["t"] == "spring" and p0 is not None and G.distance(p0) * KM(e["lat"]) < 0.3: q = p0
    else:
        stt = e.get("st", st) if st in ("FS", "SP") else st; name = re.sub(r"\s*\(.*\)", "", e["n"])
        try: pts = river_pts(stt, name, site_of.get((st, e["n"])) or site_of.get((stt, e["n"]))) if e["t"] == "river" and e.get("added", "") not in ("2026-11-10b", "2026-11-12") else []
        except Exception: pts = []
        if pts:
            ys = sorted(p[0] for p in pts); xs = sorted(p[1] for p in pts)
            ref = Point(xs[len(xs) // 2], ys[len(ys) // 2])
        else: ref = p0 if p0 is not None else G.representative_point()
        q = shapely.ops.nearest_points(G, ref)[0]
    return [round(q.y, 5), round(q.x, 5)]
moved = []
for st, L in P.items():
    for i, e in enumerate(L):
        d = dot(st, i, e)
        if d is None: continue
        if st not in ("FS", "SP") and st in PR and i < len(PR[st]):
            r = PR[st][i]; b = r[4]; old = ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2)
            while len(r) < 7: r.append(None)
            r[6] = d
            moved.append((math.hypot((old[0] - d[0]) * 111, (old[1] - d[1]) * KM(d[0])), st, e["n"]))
        e["dot"] = d
for r in FSD["springs"]:
    e = P[r[17]][r[0]]
    while len(r) < 19: r.append(None)
    r[18] = e.get("dot")
for r in FSD["rivers"]:
    e = P[r[14]][r[0]]
    while len(r) < 16: r.append(None)
    r[15] = e.get("dot")
moved.sort(reverse=True)
print("dots moved more than 2 km:", sum(1 for m in moved if m[0] > 2), "of", len(moved), "; largest:", [(round(a, 1), b, c) for a, b, c in moved[:12]])
json.dump(P, open(LIVE + "/pipeline/props.json", "w"), ensure_ascii=False)
for st, d in SH.items(): json.dump(d, open(f"{LIVE}/pipeline/shore/{st}.json", "w"), separators=(",", ":"))
def put(name, val):
    global h
    o, a, b = obj(name); h = h[:a] + "const " + name + "=" + json.dumps(val, separators=(",", ":"), ensure_ascii=False) + h[b:]
put("PR", PR); put("FSD", FSD)
def rep(old, new):
    global h
    if new in h: return
    assert h.count(old) == 1, (h.count(old), old[:80]); h = h.replace(old, new)
rep('''PR[k].forEach(r=>{const b=r[4];add((b[0]+b[1])/2,(b[2]+b[3])/2,''', '''PR[k].forEach(r=>{const b=r[4],d=r[6];add(d?d[0]:(b[0]+b[1])/2,d?d[1]:(b[2]+b[3])/2,''')
rep('''FSD.springs.forEach((r,i)=>{if(s&&s!==r[16])return;const b=r[12];add((b[1]+b[3])/2,(b[0]+b[2])/2,''', '''FSD.springs.forEach((r,i)=>{if(s&&s!==r[16])return;const b=r[12],d=r[18];add(d?d[0]:(b[1]+b[3])/2,d?d[1]:(b[0]+b[2])/2,''')
rep('''FSD.rivers.forEach((r,i)=>{if(s&&s!==r[13])return;const b=r[11];add((b[1]+b[3])/2,(b[0]+b[2])/2,''', '''FSD.rivers.forEach((r,i)=>{if(s&&s!==r[13])return;const b=r[11],d=r[15];add(d?d[0]:(b[1]+b[3])/2,d?d[1]:(b[0]+b[2])/2,''')
open(page, "w").write(h)
print("page updated")
