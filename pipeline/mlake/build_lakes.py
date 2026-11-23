"""Mountain lakes (Nov 13, 2026): every lake and pond in the western mountain states, named or not, high enough to be a montane,
subalpine or alpine lake. Source: Census TIGER/Line 2024 area water (MTFCC H2030 lake/pond, plus H2040 "reservoirs" named Lake, which are natural lakes raised by a small
dam such as Payette or Wallowa; other reservoirs, canals, treatment and other man-made basins left out) and the PRISM 800 m elevation grid. Lake elevation = the lowest grid cell touching the lake (the
basin floor; cell values are averages, so it can read a little high or low). Kept when the lake is at least 1 acre and sits no
more than 1,300 m below the regional treeline, taken as 3,500 m at 39 N falling 130 m per degree north (capped at 3,600 m),
350 m lower along the wetter Pacific ranges and the Sierra Nevada (west of 120.3 W, or west of 117.5 W south of 42 N). That puts the cut at about 2,000 m (6,700 ft) in central Colorado,
1,840 m around Lake Tahoe, 1,300 m (4,300 ft) in the Oregon Cascades, 850 m (2,800 ft) in the Washington Cascades and
1,000 m (3,200 ft) around Glacier. The land must also rise at least 350 m within about 4 km of the lake (mountains, not the
high plains or plateaus, where ponds are mostly stock ponds and prairie potholes). Names with reservoir, dam, tailings, sewage, settling, evaporation, lagoon, hatchery or stock are dropped.
Lakes lying wholly inside a national park or wilderness area (USGS National Map boundaries) are left out: no private land there.
Writes lakes_tiger.json (then nhd_lakes.py and clarity.py check it and write lakes.json): [[name or "", st, county fips, acres, elev_m, lat, lon, thresh_m], ...] and lakes_geom.json (one
simplified polygon per lake)."""
import json, os, re, math, numpy as np, shapefile, shapely
from shapely.geometry import shape, mapping
G = "/home/claude/geo_src"; OUT = os.path.dirname(os.path.abspath(__file__))
W = {"WA", "OR", "CA", "NV", "ID", "MT", "WY", "UT", "CO", "AZ", "NM"}
dem = np.fromfile(G + "/prism/dem800.bil", dtype="<i4").reshape(3105, 7025)
X0, Y0, D = -125.016666666666, 49.933333665556, 0.00833333333
def thresh(lat, lon):
    tl = min(3600, 3500 - 130 * (lat - 39)) - (350 if lon < -120.3 or (lat < 42 and lon < -117.5) else 0)   # wetter Pacific ranges and the Sierra
    return tl - 1300
RIVER = re.compile(r"\b(river|riv|creek|crk|cr|fork|frk|slough|ditch|canal|channel|brook|run|branch|wash)\b", re.I)
BAD = re.compile(r"reservoir|\bres\b|rsvr|\bdam\b|tailing|sewage|settling|evaporat|lagoon|hatchery|stock ?pond|treatment|waste|slurry|leach|pit\b", re.I)
cty = [(r["STATEFP"] + r["COUNTYFP"], r["STUSPS"]) for r in shapefile.Reader(G + "/county500k.zip").iterRecords() if r["STUSPS"] in W]
gov = []
for k in ("np", "wild"):
    for f in json.load(open(f"/home/claude/live/og/gov/{k}.geojson"))["features"]:
        if f.get("geometry"): gov.append(shape(f["geometry"]).buffer(0))
GOV = shapely.union_all(gov); shapely.prepare(GOV)
lakes, geoms = [], []
for fips, st in cty:
    f = f"{G}/aw/{fips}.zip"
    if not os.path.exists(f): print("missing", fips); continue
    for sr in shapefile.Reader(f).iterShapeRecords():
        r = sr.record
        name = (r["FULLNAME"] or "").strip()
        if r["MTFCC"] != "H2030" and not (r["MTFCC"] == "H2040" and re.search(r"\b(lk|lake)\b", name, re.I)): continue   # natural lakes raised by a small dam are often coded as reservoirs
        acres = (r["ALAND"] + r["AWATER"]) / 4046.86
        if acres < 1: continue
        name = (r["FULLNAME"] or "").strip()
        if name and (BAD.search(name) or RIVER.search(name)): continue
        try: g = shape(sr.shape.__geo_interface__).buffer(0)
        except Exception: continue
        if g.is_empty: continue
        b = g.bounds
        r0, r1 = int((Y0 - b[3]) / D), int(math.ceil((Y0 - b[1]) / D)); c0, c1 = int((b[0] - X0) / D), int(math.ceil((b[2] - X0) / D))
        if r1 < 0 or c1 < 0 or r0 >= 3105 or c0 >= 7025: continue
        win = dem[max(r0, 0):r1 + 1, max(c0, 0):c1 + 1]; win = win[win > -9000]
        if not win.size: continue
        elev = int(win.min())
        p = g.representative_point()
        th = thresh(p.y, p.x)
        nb = dem[max(r0 - 5, 0):r1 + 6, max(c0 - 5, 0):c1 + 6]; nb = nb[nb > -9000]    # the lake and about 4 km around it
        if elev >= th:
            if nb.max() - elev < 350: continue          # mountains, not high plains: at least 350 m of rise within about 4 km
        else:   # big-lake rule: a large lake in a deep mountain valley (Priest, Pend Oreille, Chelan, Crescent, Wallowa, Bear Lake)
            if acres < 50 or elev < max(th - 600, 300): continue      # and at least 300 m (1,000 ft) up: not the lowland lakes at the foot of the Cascades
            nb8 = dem[max(r0 - 10, 0):r1 + 11, max(c0 - 10, 0):c1 + 11]; nb8 = nb8[nb8 > -9000]
            if nb8.max() - elev < 600: continue        # at least 600 m of rise within about 8 km
        if GOV.contains(g): continue
        lakes.append([name, st, fips, round(acres, 1), elev, round(p.y, 5), round(p.x, 5), int(th)])
        geoms.append(g.simplify(0.00005))
print(len(lakes), "mountain lakes;", sum(1 for l in lakes if l[0]), "named;", {s: sum(1 for l in lakes if l[1] == s) for s in sorted(W)})
json.dump(lakes, open(OUT + "/lakes_tiger.json", "w"), separators=(",", ":"))
json.dump([mapping(g) for g in geoms], open(OUT + "/lakes_geom_tiger.json", "w"), separators=(",", ":"))
print("sizes KB", os.path.getsize(OUT + "/lakes_tiger.json") // 1024, os.path.getsize(OUT + "/lakes_geom_tiger.json") // 1024)
