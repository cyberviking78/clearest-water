"""Old-growth forest sites and the areas to shade on the map (Nov 12, 2026).
Sites: the Old-Growth Forest Network's 370 dedicated forests (their Google My Maps export, ogfn.json: name, state, county,
description, coordinates), plus large public old-growth landscapes from Wikipedia's List of old-growth forests that the network
doesn't cover (national parks, wilderness areas, wildlife refuges, state parks; Tongass for Alaska).
Area for each site, in order of preference:
  1. the official boundary of the park, wilderness, refuge or preserve it is in (National Map govunits; Census TIGER area
     landmarks), when every distinctive word of its name appears in the site's name and the boundary isn't vastly bigger than the forest (<= 20,000 acres, or the
     stated old growth is at least a fifth of it);
  2. otherwise a circle at the network's coordinates sized to the stated acreage (at least 150 m), marked approximate.
Writes out/sites.json and out/geom.json"""
import json, math, re, os, collections
import shapely, shapefile
from shapely.geometry import shape, Point, mapping
from shapely.ops import transform
import pyproj
HERE = os.path.dirname(os.path.abspath(__file__)); os.makedirs(HERE + "/out", exist_ok=True)
G = "/home/claude/geo_src"
h = open("/home/claude/live/page.work.html").read()
_i = h.find("const NAMES={"); NAMES = dict(re.findall(r'([A-Z]{2}):"([^"]+)"', h[_i:h.find("}", _i)]))
ABBR = {v.lower(): k for k, v in NAMES.items()}; ABBR["pennsylania"] = "PA"
FIPS = {}
for r in shapefile.Reader(G + "/county500k.zip").iterRecords(): FIPS[r["STUSPS"]] = r["STATEFP"]
ACRE = 4046.86
def utm_for(lon, lat):
    return pyproj.Transformer.from_crs(4326, pyproj.CRS.from_proj4(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m"), always_xy=True)
def circle(lon, lat, acres):
    r = max(150, math.sqrt(max(acres or 0, 1) * ACRE / math.pi))
    f = utm_for(lon, lat); inv = pyproj.Transformer.from_crs(f.target_crs, 4326, always_xy=True)
    return transform(inv.transform, Point(0, 0).buffer(r, 32))
def acres_of(g):
    c = g.centroid; f = utm_for(c.x, c.y); return transform(f.transform, g).area / ACRE
# ---- boundaries
GOV = {}
for k in ("np", "nm", "wild", "fws", "nf"):
    for f in json.load(open(f"{HERE}/gov/{k}.geojson"))["features"]:
        n = f["properties"]["name"]
        if not n or not f.get("geometry"): continue
        GOV.setdefault((k, n), []).append(shape(f["geometry"]).buffer(0))
GOV = {k: shapely.union_all(v) for k, v in GOV.items()}
ALM = collections.defaultdict(list)    # state -> [(name, geom)]
def alm(st):
    if st in ALM or st not in FIPS: return ALM.get(st, [])
    f = f"{G}/arealm/{FIPS[st]}.zip"
    if os.path.exists(f):
        for r in shapefile.Reader(f).iterShapeRecords():
            n = r.record["FULLNAME"]
            if n and r.record["MTFCC"] in ("K2180", "K2181", "K2182", "K2183", "K2184", "K2185", "K2186", "K2187", "K2188", "K2189", "K2190", "K2540", "K2561"):
                try: ALM[st].append((n, shape(r.shape.__geo_interface__).buffer(0)))
                except Exception: pass
    return ALM[st]
STOPW = {"the", "of", "and", "at", "in", "state", "park", "forest", "national", "natural", "area", "nature", "preserve", "trail", "woods",
         "reserve", "county", "wildlife", "management", "memorial", "scenic", "old", "growth", "grove", "creek", "river", "mountain", "lake",
         "sp", "st", "pk", "for", "nat", "np", "a", "wilderness", "conservation", "sanctuary", "center", "recreation", "regional", "city", "co",
         "natl", "national", "mnmt", "monument", "historical", "historic", "memorial", "meml", "landmark", "unit", "inc", "areas"}
ABR = {"st": "state", "pk": "park", "sp": "state park", "for": "forest", "mtn": "mountain", "nat": "natural", "pres": "preserve", "cr": "creek", "res": "reservation"}
def toks(s):
    w = re.sub(r"[^a-z0-9 ]", " ", (s or "").lower().replace("'", "")).split()
    w = " ".join(ABR.get(x, x) for x in w).split()
    return w
def sig(s): return {x for x in toks(s) if x not in STOPW and len(x) > 2}
def best_boundary(name, st, pt, acres):
    """A boundary that holds (or nearly holds) the point and whose name shares a distinctive word with the site's name."""
    cands = []
    S = sig(name)
    for (k, n), g in GOV.items():
        if k == "nf": continue
        if g.distance(pt) > 0.004: continue
        if sig(n) and sig(n) <= S: cands.append((n, g))          # every distinctive word of the boundary's name is in the site's name
    for n, g in alm(st):
        if g.distance(pt) > 0.004: continue
        if sig(n) and sig(n) <= S: cands.append((n, g))
    out = []
    for n, g in cands:
        a = acres_of(g)
        if a <= 20000 or (acres and acres >= 0.2 * a): out.append((a, n, g))
    return min(out, key=lambda x: x[0]) if out else None
def parse_acres(desc):
    m = re.search(r"([\d,]+(?:\.\d+)?)[- ]acres? of (?:old[- ]growth|ancient|virgin|primary)", desc, re.I) or \
        re.search(r"(?:approximately|about|roughly|some|over|nearly|more than)\s+([\d,]+(?:\.\d+)?)[- ]acres?", desc, re.I) or \
        re.search(r"([\d,]+(?:\.\d+)?)[- ]acres?", desc, re.I)
    try: return float(m.group(1).replace(",", "")) if m else None
    except ValueError: return None
sites = []; geoms = []
for d in json.load(open(HERE + "/ogfn.json")):
    st = ABBR.get(d["State"].strip().lower(), d["State"].strip().upper())
    if st not in NAMES: print("state?", d["State"], d["name"]); continue
    desc = re.sub(r"\s+", " ", d.get("Description", "")).strip()
    acres = parse_acres(desc)
    future = bool(re.search(r"not (?:yet )?old[- ]growth|future old[- ]growth", desc, re.I))
    pt = Point(d["lon"], d["lat"])
    b = best_boundary(d["name"], st, pt, acres)
    if b: g, kind, bname = b[2], "boundary", b[1]
    else: g, kind, bname = circle(d["lon"], d["lat"], acres), "approx", None
    sites.append(dict(n=d["name"].strip(), st=st, cty=d.get("County", "").strip(), ac=acres, fut=future, src="ogfn", page=d.get("Forest Detail Page", ""),
                      web=d.get("Website", ""), desc=desc[:420], lat=round(d["lat"], 5), lon=round(d["lon"], 5), kind=kind, bname=bname))
    geoms.append(g)
# ---- landscapes from Wikipedia's list that the network doesn't hold
WIKI = "https://en.wikipedia.org/wiki/List_of_old-growth_forests"
LAND = [  # (name, state, old-growth acres per the list, boundary layer, boundary name)
    ("Tongass National Forest", "AK", 5400000, "nf", "Tongass National Forest"),
    ("Olympic National Park", "WA", 366000, "np", "Olympic National Park"), ("Mount Rainier National Park", "WA", 91000, "np", "Mount Rainier National Park"),
    ("North Cascades National Park", "WA", 236000, "np", "North Cascades National Park"),
    ("Redwood National Park", "CA", 38982, "np", "Redwood National Park"), ("Yosemite National Park", "CA", 225510, "np", "Yosemite National Park"),
    ("Sequoia National Park", "CA", 202430, "np", "Sequoia National Park"), ("Kings Canyon National Park", "CA", 202430, "np", "Kings Canyon National Park"),
    ("Lassen Volcanic National Park", "CA", 27130, "np", "Lassen Volcanic National Park"), ("Muir Woods National Monument", "CA", 240, "nm", "Muir Woods National Monument"),
    ("Crater Lake National Park", "OR", 50000, "np", "Crater Lake National Park"),
    ("Great Smoky Mountains National Park", "TN", 187000, "np", "Great Smoky Mountains National Park"),
    ("Congaree National Park", "SC", 11000, "np", "Congaree National Park"), ("Hot Springs National Park", "AR", 320, "np", "Hot Springs National Park"),
    ("Big Cypress National Preserve", "FL", 158000, "np", "Big Cypress National Preserve"), ("Apostle Islands National Lakeshore", "WI", 1500, "np", "Apostle Islands National Lakeshore"),
    ("Sipsey Wilderness", "AL", None, "wild", "Sipsey Wilderness"), ("Sylvania Wilderness", "MI", 15000, "wild", "Sylvania Wilderness"),
    ("Boundary Waters Canoe Area Wilderness", "MN", 401000, "wild", "Boundary Waters Canoe Area Wilderness"),
    ("Ellicott Rock Wilderness", "SC", 1000, "wild", "Ellicott Rock Wilderness"), ("Great Gulf Wilderness", "NH", None, "wild", "Great Gulf Wilderness"),
    ("Allegheny Islands Wilderness", "PA", 156, "wild", "Allegheny Islands Wilderness"),
    ("Dale Bumpers White River National Wildlife Refuge", "AR", 973, "fws", "Dale Bumpers White River National Wildlife Refuge"),
    ("Overflow National Wildlife Refuge", "AR", 230, "fws", "Overflow National Wildlife Refuge"), ("Cypress Creek National Wildlife Refuge", "IL", 500, "fws", "Cypress Creek National Wildlife Refuge"),
]
for n, st, ac, k, bn in LAND:
    g = GOV.get((k, bn))
    if g is None: print("no boundary", n); continue
    if any(s["st"] == st and s["kind"] == "boundary" and s["bname"] == bn for s in sites): continue
    c = g.representative_point()
    sites.append(dict(n=n, st=st, cty="", ac=ac, fut=False, src="wiki", page=WIKI, web="", desc="", lat=round(c.y, 5), lon=round(c.x, 5), kind="boundary", bname=bn))
    geoms.append(g)
# a landscape the network already covers with a boundary of about the same area is dropped (e.g. Redwood, Congaree, Sylvania)
keep = []
for i, (s_, g) in enumerate(zip(sites, geoms)):
    if s_["src"] == "wiki" and any(o["src"] == "ogfn" and o["kind"] == "boundary" and og.intersects(g) and
                                    og.intersection(g).area > 0.5 * min(og.area, g.area) and og.area > 0.3 * g.area
                                    for o, og in zip(sites, geoms)):
        print("landscape already in the network:", s_["n"]); continue
    keep.append(i)
sites = [sites[i] for i in keep]; geoms = [geoms[i] for i in keep]
json.dump(sites, open(HERE + "/out/sites.json", "w"), ensure_ascii=False)
json.dump([mapping(g) for g in geoms], open(HERE + "/out/geom.json", "w"))
c = collections.Counter(s["kind"] for s in sites)
print(len(sites), "sites;", dict(c), "; network", sum(1 for s in sites if s["src"] == "ogfn"), "; landscapes", sum(1 for s in sites if s["src"] == "wiki"))
for s in sites[:400]:
    if s["kind"] == "boundary" and s["src"] == "ogfn": print("  ", s["st"], s["n"], "->", s["bname"])
