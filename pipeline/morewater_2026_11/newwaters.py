"""Add every lake clearer than 20 ft and every river under 2 NTU (same quality bar as the state lists) beyond each state's top 5.
Sources: the page's national lists (NL lakes, NR rivers), USGS NHD (waterbody, flowline, area) for shapes, Water Quality Portal
station locations for rivers. Writes out/props.json, out/shore/<ST>.json, out/extra.json (tab rows and PR rows)."""
import json, os, re, sys, time, collections, urllib.parse, urllib.request, io, csv
import shapely, shapefile
from shapely.geometry import shape, mapping, box
HERE = os.path.dirname(os.path.abspath(__file__)); LIVE = "/home/claude/live"; OUT = os.path.join(HERE, "out")
os.makedirs(OUT + "/shore", exist_ok=True); os.makedirs(HERE + "/cache", exist_ok=True)
h = open(LIVE + "/page.work.html").read()
def obj(name):
    i = h.find("const " + name + "="); o, _ = json.JSONDecoder().raw_decode(h[i + len("const " + name + "="):]); return o
NL, NR, LK, RV, FSD = obj("NL"), obj("NR"), obj("LK"), obj("RV"), obj("FSD")
_i = h.find("const NAMES={"); NAMES = dict(re.findall(r'([A-Z]{2}):"([^"]+)"', h[_i:h.find("}", _i)]))
P = json.load(open(LIVE + "/pipeline/props.json"))
CT = collections.defaultdict(list); FIPS = {}
for r in shapefile.Reader("/home/claude/geo_src/county500k.zip").iterShapeRecords():
    CT[r.record["STUSPS"]].append((r.record["NAME"], r.record["NAMELSAD"], shape(r.shape.__geo_interface__), r.record["GEOID"]))
for r in shapefile.Reader("/home/claude/geo_src/county2020.zip").iterShapeRecords():   # Connecticut: use its 8 counties, not the 2022 planning regions
    if r.record["STUSPS"] == "CT": CT["CT_old"].append((r.record["NAME"], r.record["NAMELSAD"], shape(r.shape.__geo_interface__), r.record["GEOID"]))
def county_poly(st, name):
    n = (name or "").lower().replace(" county", "").replace(" parish", "").strip()
    for a, b, g, gid in CT[st]:
        if a.lower() == n or b.lower() == (name or "").lower(): return a, g, gid
    for a, b, g, gid in CT[st]:
        if a.lower().startswith(n[:6]) and n: return a, g, gid
    return None, None, None
def county_at(st, x, y):
    p = shapely.Point(x, y)
    if st == "CT": st = "CT_old"
    for a, b, g, gid in CT[st]:
        if g.contains(p): return a
    return min(CT[st], key=lambda t: t[2].distance(p))[0]

import hashlib
def get(url, data=None, tries=4):
    key = hashlib.md5((url + json.dumps(data, sort_keys=True)).encode()).hexdigest()
    cf = f"{HERE}/cache/q_{key}"
    if os.path.exists(cf): return open(cf, "rb").read()
    for a in range(tries):
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode() if data else None, headers={"User-Agent": "Mozilla/5.0 clearest-water"})
            b = urllib.request.urlopen(req, timeout=180).read(); open(cf, "wb").write(b); return b
        except Exception as e:
            print("  retry", a, str(e)[:100], flush=True); time.sleep(10 * (a + 1))
    return None
NHD = "https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/{}/query"
def nhd(layer, where, env):
    w, s, e, n = env
    b = get(NHD.format(layer), dict(where=where, geometry=f"{w},{s},{e},{n}", geometryType="esriGeometryEnvelope", inSR=4326, spatialRel="esriSpatialRelIntersects",
                                    outFields="GNIS_NAME,FTYPE", returnGeometry="true", outSR=4326, geometryPrecision=5, maxAllowableOffset=0.00005, f="geojson"))
    if not b: return []
    try: return [(f["properties"], shape(f["geometry"])) for f in json.loads(b).get("features", []) if f.get("geometry")]
    except Exception: return []
q = lambda s: s.replace("'", "''")

inLK = {(k, r["n"]) for k, v in LK.items() for r in v["rows"]}; inRV = {(k, r["n"]) for k, v in RV.items() for r in v["rows"]}
fsr = {(r[13], r[1].lower()) for r in FSD["rivers"]}
lakes = sorted([r for r in NL if r[3] > 20 and (r[1], r[0]) not in inLK and r[5] >= 20 and r[6] >= 5 and r[1] in P], key=lambda r: -r[3])
rivers = sorted([r for r in NR if r[2] < 2 and (r[1], r[0]) not in inRV and r[5] >= 24 and (r[8] - r[7] + 1) >= 3 and r[1] in P
                 and (r[1], r[0].lower()) not in fsr], key=lambda r: r[2])
print(len(lakes), "lakes,", len(rivers), "rivers qualify", flush=True)

STN = {}
SFIPS = {"AL":"01","AK":"02","AZ":"04","AR":"05","CA":"06","CO":"08","CT":"09","DE":"10","FL":"12","GA":"13","HI":"15","ID":"16","IL":"17","IN":"18","IA":"19","KS":"20","KY":"21","LA":"22","ME":"23","MD":"24","MA":"25","MI":"26","MN":"27","MS":"28","MO":"29","MT":"30","NE":"31","NV":"32","NH":"33","NJ":"34","NM":"35","NY":"36","NC":"37","ND":"38","OH":"39","OK":"40","OR":"41","PA":"42","RI":"44","SC":"45","SD":"46","TN":"47","TX":"48","UT":"49","VT":"50","VA":"51","WA":"53","WV":"54","WI":"55","WY":"56"}
def stations(st):
    if st in STN: return STN[st]
    f = f"{HERE}/cache/st_{st}.csv"
    if not os.path.exists(f):
        b = get(f"https://www.waterqualitydata.us/data/Station/search?statecode=US:{SFIPS[st]}&siteType=Stream&characteristicName=Turbidity&startDateLo=01-01-2016&mimeType=csv&zip=no")
        open(f, "wb").write(b or b"")
    rows = []
    for r in csv.DictReader(io.StringIO(open(f, encoding="utf-8", errors="replace").read())):
        try: rows.append((r["MonitoringLocationName"] or "", float(r["LatitudeMeasure"]), float(r["LongitudeMeasure"])))
        except Exception: pass
    STN[st] = rows; return rows
MOD = r"(little|north|south|east|west|middle|upper|lower|fork|branch|old|new)\s+$"
def river_pts(st, name, site):
    S = stations(st); nl = name.lower()
    exact = [(y, x) for n, y, x in S if n.strip().lower() == (site or "").strip().lower()]
    pts = []
    for n, y, x in S:
        s = n.lower(); i = s.find(nl)
        if i < 0: continue
        if re.search(MOD, s[:i]): continue
        pts.append((y, x))
    if exact:
        cy = sum(p[0] for p in exact) / len(exact); cx = sum(p[1] for p in exact) / len(exact)
        pts = [p for p in pts if abs(p[0] - cy) < 0.35 and abs(p[1] - cx) < 0.45] or exact
    elif pts:
        cy = sorted(p[0] for p in pts)[len(pts) // 2]; cx = sorted(p[1] for p in pts)[len(pts) // 2]
        pts = [p for p in pts if abs(p[0] - cy) < 0.35 and abs(p[1] - cx) < 0.45]
    return pts


# ---- US Census TIGER 2024 water (names and shapes come from the USGS National Hydrography Dataset)
G = "/home/claude/geo_src"
ABR = {"lake": "lk", "lakes": "lks", "river": "riv", "creek": "crk", "brook": "brk", "branch": "br", "stream": "strm", "reservoir": "res",
       "fork": "frk", "mountain": "mtn", "saint": "st", "mount": "mt", "fort": "ft", "east": "e", "west": "w", "north": "n", "south": "s", "springs": "spgs", "spring": "spg"}
def norm(n): return " ".join(ABR.get(w, w) for w in re.sub(r"[^a-z0-9 ]", "", (n or "").lower().replace("-", " ")).split())
_TC = {}
def tiger(kind, gid):
    k = (kind, gid)
    if k in _TC: return _TC[k]
    f = f"{G}/{kind}/{gid}.zip"
    if not os.path.exists(f) or os.path.getsize(f) < 1000:
        b = get(f"https://www2.census.gov/geo/tiger/TIGER2024/{'AREAWATER' if kind == 'aw' else 'LINEARWATER'}/tl_2024_{gid}_{'areawater' if kind == 'aw' else 'linearwater'}.zip")
        if b and len(b) > 1000: open(f, "wb").write(b)
    out = []
    try:
        for r in shapefile.Reader(f).iterShapeRecords():
            if r.record["FULLNAME"]: out.append((norm(r.record["FULLNAME"]), shape(r.shape.__geo_interface__)))
    except Exception: pass
    _TC[k] = out; return out
ALLC = [(gid, g) for st in CT for a, b, g, gid in CT[st]]
ctree = shapely.STRtree([g for _, g in ALLC])
def counties_in(env): return [ALLC[i][0] for i in ctree.query(box(*env))]

def zurl(b, att):
    fs = {"sort": {"value": "globalrelevanceex"}, "price": {"min": 100000, "max": 750000}, "tow": {"value": False}, "mf": {"value": False},
          "con": {"value": False}, "apa": {"value": False}, "apco": {"value": False}, "manu": {"value": False}}
    if att: fs["att"] = {"value": att}
    s = json.dumps({"pagination": {}, "isMapVisible": True, "isListVisible": True, "mapBounds": {"west": b[0], "east": b[1], "south": b[2], "north": b[3]}, "filterState": fs}, separators=(",", ":"))
    return "https://www.zillow.com/homes/for_sale/?searchQueryState=" + urllib.parse.quote(s, safe="")
def lwpath(st, cty):
    return f"{NAMES[st].lower().replace(' ', '-')}-land-for-sale/{cty.lower().replace(' ', '-').replace('.', '')}-{'parish' if st == 'LA' else 'county'}/waterfront-property/price-100000-750000"
def sbox(g, minw=0.05, minh=0.04, pad=0.012, cap=0.8):
    w, s, e, n = g.bounds; w -= pad; e += pad; s -= pad; n += pad
    cx, cy = (w + e) / 2, (s + n) / 2
    if e - w < minw: w, e = cx - minw / 2, cx + minw / 2
    if n - s < minh: s, n = cy - minh / 2, cy + minh / 2
    if e - w > cap: w, e = cx - cap / 2, cx + cap / 2
    if n - s > cap: s, n = cy - cap / 2, cy + cap / 2
    return [round(w, 4), round(e, 4), round(s, 4), round(n, 4)]

from concurrent.futures import ThreadPoolExecutor
def variants(n):
    v = [n]
    m = re.match(r"(?i)lake (.+)", n)
    if m: v.append(m.group(1) + " Lake")
    m = re.match(r"(?i)(.+) lake$", n)
    if m: v.append("Lake " + m.group(1))
    m = re.match(r"(?i)(.+) pond$", n)
    if m: v.append(m.group(1) + " Lake")
    return v
for st_ in {r[1] for r in rivers}: stations(st_)
added = collections.defaultdict(list); tabrows = collections.defaultdict(lambda: {"l": [], "r": []}); misses = []

for r in lakes:
    name, st, cty, ft, m, k, yrs, y0, y1, px = r[:10]
    tabrows[st]["l"].append(dict(n=name, c=cty, ft=ft, m=m, rft=None, k=k, yrs=yrs, y=f"{y0}–{y1}", s=1, px=px, lim=False, x=True))
    cn, cg, gid = county_poly(st, cty)
    if cg is None: misses.append((st, name, "county")); continue
    geo = None; how = None
    for v in variants(name):
        fs = [g for nm, g in tiger("aw", gid) if nm == norm(v)]
        if not fs:   # lakes that straddle a county line
            for g2 in counties_in(cg.buffer(0.02).bounds):
                if g2 != gid: fs += [g for nm, g in tiger("aw", g2) if nm == norm(v) and g.intersects(cg.buffer(0.02))]
        if fs:
            geo = shapely.union_all(fs); how = v
            w_, s_, e_, n_ = geo.bounds
            if len(fs) > 1 and (e_ - w_ > 0.1 or n_ - s_ > 0.1):
                big = max(fs, key=lambda g: g.area); geo = shapely.union_all([g for g in fs if g.distance(big) < 0.002])
            break
    if geo is None: misses.append((st, name, "no NHD shape")); continue
    geo = geo.simplify(0.0001)
    c = geo.representative_point()
    added[st].append(dict(t="lake", n=name, v=f"{ft:.1f} ft", c=cn, geom=geo, box=sbox(geo), matched=[how], method="name", lat=round(c.y, 4), lon=round(c.x, 4), val=ft))
    print("lake", st, name, "ok", flush=True)
for r in rivers:
    name, st, med, p25, p75, k, s, y0, y1, b, px, site = r[:12]
    tabrows[st]["r"].append(dict(n=name, m=med, p25=p25, p75=p75, k=k, s=s, y=f"{y0}–{y1}", b=float(b), px=float(px), site=site, u="NTU", x=True))
    pts = river_pts(st, name, site)
    if not pts: misses.append((st, name, "no station")); continue
    pb = shapely.MultiPoint([(x, y) for y, x in pts]); env = pb.envelope.buffer(0.03).bounds
    cs = counties_in(env); nn = norm(name); E = box(*env)
    lines = [g for c in cs for nm, g in tiger("lw", c) if nm == nn and g.intersects(E)]
    if not lines: misses.append((st, name, "no channel")); continue
    L = shapely.union_all(lines).intersection(E)
    areas = [g for c in cs for nm, g in tiger("aw", c) if nm == nn and g.intersects(E)]
    geo = L
    if areas:
        A = shapely.union_all(areas).intersection(L.buffer(0.002))
        if not A.is_empty: geo = shapely.union_all([L, A])
    geo = geo.simplify(0.0001)
    if geo.is_empty: misses.append((st, name, "empty")); continue
    c = pb.centroid
    added[st].append(dict(t="river", n=name, v=(f"{med:.2f}" if med < 1 else f"{med:.1f}") + " NTU", c=county_at(st, c.x, c.y), geom=geo,
                          box=sbox(shapely.union_all([geo.envelope, pb.envelope])), matched=[name], method="river channel", lat=round(c.y, 4), lon=round(c.x, 4), val=med))
    print("river", st, name, "ok", len(pts), "stations", flush=True)

# write props / shore / page rows (new waters appended after the existing ones, so existing indexes don't move)
PR_ADD = {}; shore_new = collections.defaultdict(dict)
for st, L in added.items():
    base = len(P[st]); nl = sum(1 for e in P[st] if e["t"] == "lake"); nr = sum(1 for e in P[st] if e["t"] == "river")
    L.sort(key=lambda a: (a["t"] != "lake", -a["val"] if a["t"] == "lake" else a["val"]))
    rows = []
    for a in L:
        if a["t"] == "lake": nl += 1; rk = nl
        else: nr += 1; rk = nr
        w, e, s, n = a["box"]; lw = lwpath(st, a["c"])
        P[st].append(dict(t=a["t"], n=a["n"], rk=rk, v=a["v"], c=a["c"], z=zurl(a["box"], "waterfront"), za=zurl(a["box"], None),
                          lw=[[a["c"], "https://www.landwatch.com/" + lw]], lat=a["lat"], lon=a["lon"], added="2026-11-10"))
        i = len(P[st]) - 1
        shore_new[st][f"{st}_{i}"] = dict(name=a["n"], method=a["method"], matched=a["matched"], geom=mapping(a["geom"]))
        rows.append(["l" if a["t"] == "lake" else "r", a["n"], rk, a["v"], [s, n, w, e], [[a["c"], lw]]])
    PR_ADD[st] = rows
json.dump(P, open(OUT + "/props.json", "w"), ensure_ascii=False)
for st, d in shore_new.items():
    S = json.load(open(f"{LIVE}/pipeline/shore/{st}.json")); S.update(d)
    json.dump(S, open(f"{OUT}/shore/{st}.json", "w"), separators=(",", ":"))
json.dump(dict(PR=PR_ADD, tab={k: v for k, v in tabrows.items()}, misses=misses), open(OUT + "/extra.json", "w"), ensure_ascii=False)
print("DONE: searchable", sum(len(v) for v in added.values()), "of", len(lakes) + len(rivers), "; misses", len(misses), collections.Counter(m[2] for m in misses), flush=True)
