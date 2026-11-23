"""LakeQuality pass (Nov 20, 2026).
LakeQuality.org (ColdPress LLC) publishes clearest-lake rankings for 24 states, built from the EPA/USGS Water Quality Portal plus
satellite estimates. We used its 24 state ranking pages only as a checklist of lakes to look at: every lake it ranks at 15 ft or
clearer that we did not already search was checked against the Water Quality Portal ourselves (Secchi depth readings since 2000
at stations in that county whose names match the lake), and our own numbers decide.
Kept when: the lake's average (each year's median reading, averaged across years, as on the main list, after dropping
readings over 148 ft or more than 3 times the lake's median) AND the median of all its readings are both 15 ft or more, and the record has at least 6 readings or readings in at
least 3 different years. Dropped: no portal readings (satellite-only values: all four Colorado lakes), duplicates of waters we
already search (Lake Denton, Lake Tulane, Big Twin, Lake Alva, Lake Inez, Strawberry, Flaming Gorge), stations inside national
parks or recreation areas with no private shore (Yellowstone, Jackson Lake/Grand Teton, Lake Powell), and values the portal
does not bear out (Adams Lake WI 100 ft, Meade Lake KS 53 ft, Loch Lomond IL, Lake Sapphire MI...).
Also fixed: 43 lakes that were already on the Lakes tab at 15 ft or clearer but had no property search because their map shape
was never found (Chancellor Lake, Smoky Lake, Little McDonald, Lake Elligo, Big Hurst...). Shapes now come from Census TIGER
area water, by name near the lake's monitoring stations, or the water body the stations sit in.
Inputs: scratch lq_wqp.json (match.py output), the page (LK, PR), props.json, shore/*.json, county500k.zip.
Writes out/props.json, out/shore/<ST>.json, out/extra.json (PR rows, LK rows), out/report.json."""
import json, os, re, sys, math, csv, io, collections, subprocess, urllib.parse, statistics
import shapely, shapefile
from shapely.geometry import shape, mapping, box, Point
from shapely.ops import polylabel
csv.field_size_limit(10**9)
HERE = os.path.dirname(os.path.abspath(__file__)); LIVE = "/home/claude/live"; OUT = HERE + "/out"
S = sys.argv[1]; page = sys.argv[2]
os.makedirs(OUT + "/shore", exist_ok=True); os.makedirs(HERE + "/cache/aw", exist_ok=True)
h = open(page).read()
def obj(name):
    i = h.find("const " + name + "="); o, _ = json.JSONDecoder().raw_decode(h[i + len("const " + name + "="):]); return o
LK, PR = obj("LK"), obj("PR")
_i = h.find("const NAMES={"); NAMES = dict(re.findall(r'([A-Z]{2}):"([^"]+)"', h[_i:h.find("}", _i)]))
P = json.load(open(LIVE + "/pipeline/props.json"))
CTY = json.load(open(S + "/cty.json"))
CT = collections.defaultdict(list)
for r in shapefile.Reader("/home/claude/geo_src/county500k.zip").iterShapeRecords():
    CT[r.record["STUSPS"]].append((r.record["NAME"], shape(r.shape.__geo_interface__), r.record["GEOID"]))
ALLC = [(gid, g, st, a) for st in CT for a, g, gid in CT[st]]; ctree = shapely.STRtree([x[1] for x in ALLC])
def gid_of(st, cty): return "".join(CTY[f"{st}|{cty.lower()}"])
def county_at(x, y):
    p = Point(x, y)
    for i in ctree.query(p):
        if ALLC[i][1].contains(p): return ALLC[i][3]
    return None

ABR = {"lake": "lk", "reservoir": "res", "pond": "pd", "saint": "st", "mount": "mt", "east": "e", "west": "w", "north": "n", "south": "s"}
def norm(n): return " ".join(ABR.get(w, w) for w in re.sub(r"[^a-z0-9 ]", "", (n or "").lower().replace("-", " ")).split())
def variants(n):
    n = re.sub(r"\s*\(.*?\)", "", n).strip(); v = [n]
    m = re.match(r"(?i)lake (.+)", n)
    if m: v += [m.group(1) + " Lake", m.group(1)]
    m = re.match(r"(?i)(.+) (lake|reservoir|pond)$", n)
    if m: v += ["Lake " + m.group(1), m.group(1), m.group(1) + " Reservoir", m.group(1) + " Pond", m.group(1) + " Lake"]
    if not re.search(r"(?i)\b(lake|reservoir|pond)\b", n): v += [n + " Lake", "Lake " + n]
    return list(dict.fromkeys(v))
_AW = {}
def aw(gid):
    if gid in _AW: return _AW[gid]
    f = f"{HERE}/cache/aw/{gid}.zip"
    if not os.path.exists(f) or os.path.getsize(f) < 1000:
        subprocess.run(["curl", "-s", "-m", "300", "-o", f, f"https://www2.census.gov/geo/tiger/TIGER2024/AREAWATER/tl_2024_{gid}_areawater.zip"])
    out = []
    try:
        for r in shapefile.Reader(f).iterShapeRecords():
            if not (r.record["MTFCC"].startswith("H2") or r.record["MTFCC"] == "H3010") or r.record["MTFCC"] == "H2041": continue
            try: g = shape(r.shape.__geo_interface__).buffer(0)
            except Exception: continue
            out.append(((r.record["FULLNAME"] or "").strip(), g, r.record["MTFCC"]))
    except Exception as ex: print("aw fail", gid, ex)
    _AW[gid] = out; return out
def polys_near(gid, env):
    E = box(*env); ids = {gid} | {ALLC[i][0] for i in ctree.query(E)}
    return [(nm, g, x, m) for x in ids for nm, g, m in aw(x) if g.intersects(E)]

# ---------- A: lakes found through LakeQuality, checked against the portal
skipnames = {"FL|Highlands-Denton Lake", "FL|Highlands-Tulane Lake", "MI|Twin Lake", "MT|Lake Alva Mid-Lake Deep", "MT|Lake Inez South Hole",
             "UT|Strawberry Mid Res Lake", "UT|Flaming Gorge-Green River Lake"}
inLK = {(k, r["n"]): r for k, v in LK.items() for r in v["rows"] if not r.get("gl")}
onLK = {"FL|Clay-Sheelar Lake": "Sheelar Lake", "MI|Chancellor Lake": "Chancellor Lake", "MI|Smoky Lake": "Smoky Lake",
        "MN|Little Mcdonald Lake": "Little McDonald Lake", "VT|Lake Elligo": "Lake Elligo", "VT|Harveys Lake": "Harveys Lake",
        "WI|Big Hurst Lake": "Big Hurst Lake", "NY|Eaton Reservoir": "Lake Eaton", "MN|Holland Lake": "Holland Lake"}
DISP = {"FL|Jackson-Silver Lake": "Silver Lake", "FL|Clay-Deer Lake": "Deer Lake", "FL|Putnam-Barco Lake": "Barco Lake",
        "FL|Miami-Dade-E Lake": "Lake E (Kendall)", "FL|Clc Lake": None, "MN|St James Pit Lake": "St. James Pit Lake", "MN|Miner'S Pit West Lake": "Miner's Pit West",
        "MT|Mcgilvray Lake": "McGilvray Lake", "WY|Lake Desmet Lpd": "Lake DeSmet", "WI|Buskey Bay Lake": "Buskey Bay", "WI|Bardon Lake": "Bardon Lake"}
cand = {f"{c[0]}|{c[1]}": c for c in json.load(open(S + "/lq_missing15.json"))}
A, report = [], []
for r in json.load(open(S + "/lq_wqp.json")):
    key = f"{r['st']}|{r['n']}"; why = None
    if key in skipnames: why = "already searched"
    elif key in onLK: why = "already on the Lakes tab (search added below)"
    elif not r["k"]: why = "no portal readings"
    elif r["k"] < 6 and r["yrs"] < 3: why = f"too few readings ({r['k']} in {r['yrs']} yr)"
    elif r["yavg"] < 15 or r["med"] < 15: why = f"portal average {r['yavg']} ft, median {r['med']} ft"
    report.append(dict(st=r["st"], n=r["n"], lq=r["lq"], k=r["k"], yrs=r["yrs"], avg=r["avg"], med=r["med"], yavg=r["yavg"], kept=why is None, why=why))
    if why: continue
    pts = [(float(s[2]), float(s[3])) for s in r["stations"]]
    # per-lake stats again (avg, metres, years) from match output
    A.append(dict(st=r["st"], key=key, n=DISP.get(key, r["n"]), raw=r["n"], cty=r["cty"], ft=r["yavg"], med=r["med"], k=r["k"], yrs=r["yrs"],
                  y=f"{r['y0']}–{r['y1']}", s=len({(round(a, 3), round(b, 3)) for a, b in pts}), pts=pts, href=cand[key][5]))
for skey in ["UT|Strawberry Marina Lake", "UT|Strawberry Reservoir Narrows T", "UT|Strawberry Reservoir Indian Creek Bay T", "UT|Strawberry Reservoir Strawberry Bay T",
             "UT|Strawberry Reservoir Bryants Fk T", "WY|West Thumb Lake", "WY|Yellowstone Lake", "WY|Moran Bay Lake", "WY|Inlet Arizona Island Lake",
             "WY|Leeks Marina North Lake", "UT|Lake Powell Off Davis Gulch"]:
    c = cand[skey]; report.append(dict(st=c[0], n=c[1], lq=c[3], kept=False, why="Strawberry Reservoir station (already searched)" if "Strawberry" in skey else "national park or recreation area station"))

# ---------- B: Lakes-tab lakes at 15 ft or clearer with no property search yet
prn = {st: {e["n"] for e in L} for st, L in P.items()}
B = []
for (st, n), r in inLK.items():
    if r["ft"] < 15 or n in prn.get(st, set()) or (st, n) in (("MI", "Twin Lake"), ("MI", "Chancellor (Blue) Lake")): continue
    B.append(dict(st=st, n=n, cty=r["c"], ft=r["ft"]))
def stations_for(st, cty, n):
    gid = gid_of(st, cty.split(",")[0].strip()); f = f"{S}/wqp/Station_{gid}.csv"
    if not os.path.exists(f):
        q = urllib.parse.quote
        subprocess.run(["curl", "-s", "-m", "300", "-o", f, f"https://www.waterqualitydata.us/data/Station/search?statecode=US:{int(gid[:2])}&countycode=US:{int(gid[:2])}:{gid[2:]}"
                        f"&characteristicName={q('Depth, Secchi disk depth')}&siteType={q('Lake, Reservoir, Impoundment')}&mimeType=csv"])
    STOP = {"lake", "reservoir", "res", "lk", "pond", "the", "of"}; QUAL = {"little", "big", "upper", "lower", "north", "south", "west", "east", "middle", "long", "great"}
    words = [w for w in re.sub(r"[^a-z0-9 ]", " ", re.sub(r"\(.*?\)", "", n.lower())).split() if w not in STOP]
    pts = []
    for row in csv.DictReader(open(f, encoding="utf-8", errors="replace")):
        nm = re.sub(r"[^a-z0-9 ]", " ", row["MonitoringLocationName"].lower())
        if all(re.search(r"\b" + w + r"\b", nm) for w in words) and not any(re.search(r"\b" + q_ + r"\b", nm) for q_ in QUAL - set(words)):
            try: pts.append((float(row["LatitudeMeasure"]), float(row["LongitudeMeasure"])))
            except Exception: pass
    if len(pts) > 2:   # drop stray stations far from the rest (another lake of the same name)
        my = statistics.median(p[0] for p in pts); mx = statistics.median(p[1] for p in pts)
        pts = [p for p in pts if abs(p[0] - my) < 0.05 and abs(p[1] - mx) < 0.07]
    return pts
for b in B: b["pts"] = stations_for(b["st"], b["cty"], b["n"])

# ---------- shapes
def find_shape(st, cty, names, pts):
    gid = gid_of(st, cty.split(",")[0].strip())
    cg = next(g for a, g, x in CT[st] if x == gid)
    if pts:
        MP = shapely.MultiPoint([(x, y) for y, x in pts]); env = MP.buffer(0.06).bounds
    else: MP = None; env = cg.bounds
    cands = polys_near(gid, env)
    nv = {norm(v) for v in names}
    named = [(nm, g) for nm, g, _, m in cands if m != "H3010" and norm(nm) in nv and (MP is None or g.distance(MP) < 0.03)]
    hit = [(nm, g) for nm, g, _, m in cands if MP is not None and g.distance(MP) < 0.0015 and (m != "H3010" or g.area > 1e-4)]
    if named and hit and min(t[1].distance(MP) for t in named) > 0.0015: named = []   # stations sit in another water body: trust them
    how = None
    if named:
        ref = min(named, key=lambda t: t[1].distance(MP)) if MP is not None else max(named, key=lambda t: t[1].area)
        pieces = [ref]; grow = True
        while grow:
            grow = False; U = shapely.union_all([p[1] for p in pieces])
            for t in named:
                if t not in pieces and t[1].distance(U) < 0.002: pieces.append(t); grow = True
        how = ("name", ref[0])
    elif hit:
        ref = max(hit, key=lambda t: (sum(1 for y, x in pts if t[1].distance(Point(x, y)) < 0.0015), t[1].area))
        pieces = [ref] + ([(t[0], t[1]) for t in cands if t[0] and t[0] == ref[0] and t[1] is not ref[1] and t[1].distance(ref[1]) < 0.002] if ref[0] else [])
        how = ("station", ref[0])
    elif MP is not None:      # not in TIGER: USGS NHD high-resolution waterbody the stations sit in
        c = MP.centroid
        b = subprocess.run(["curl", "-s", "-m", "200", f"https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/12/query?geometry={c.x},{c.y}&geometryType=esriGeometryPoint&inSR=4326"
                            f"&spatialRel=esriSpatialRelIntersects&distance=150&units=esriSRUnit_Meter&outFields=GNIS_NAME&returnGeometry=true&outSR=4326&f=geojson"], capture_output=True, text=True).stdout
        try: fs = [(f["properties"].get("GNIS_NAME") or "", shape(f["geometry"]).buffer(0)) for f in json.loads(b)["features"] if f.get("geometry")]
        except Exception: fs = []
        if not fs: return None, None, None
        ref = min(fs, key=lambda t: t[1].distance(MP)); pieces = [ref]; how = ("NHD", ref[0])
    else: return None, None, None
    G = shapely.union_all([p[1] for p in pieces])
    if (st, names[0]) in CLIP: G = G.intersection(MP.buffer(0.025))       # one TIGER polygon spans a chain of connected lakes
    G = G.simplify(0.0001)
    return G, how, (G.distance(MP) * 111000 if MP is not None else None)
CLIP = {('WI', 'Long Interlaken Lake'), ('WI', 'Flambeau Lake')}
def acres(G): return G.area * (111320 * math.cos(math.radians(G.centroid.y))) * 110540 / 4046.86
DX, DY = 0.15, 0.12
def boxes_for(G_):
    w, s, e, n = G_.bounds; pad = 0.012
    zb = [round(w - pad, 4), round(e + pad, 4), round(s - pad, 4), round(n + pad, 4)]
    cx, cy = (w + e) / 2, (s + n) / 2
    if zb[1] - zb[0] < 0.05: zb[0], zb[1] = round(cx - 0.025, 4), round(cx + 0.025, 4)
    if zb[3] - zb[2] < 0.04: zb[2], zb[3] = round(cy - 0.02, 4), round(cy + 0.02, 4)
    if e - w < 0.3 and n - s < 0.3: return zb, None
    zone = G_.buffer(0.015); cells = []
    for cx in range(math.floor(zone.bounds[0] / DX), math.floor(zone.bounds[2] / DX) + 1):
        for cy in range(math.floor(zone.bounds[1] / DY), math.floor(zone.bounds[3] / DY) + 1):
            b = box(cx * DX, cy * DY, (cx + 1) * DX, (cy + 1) * DY)
            if b.intersects(zone):
                c = list(b.intersection(zone).bounds)
                if c[2] - c[0] < 0.01: m = (c[0] + c[2]) / 2; c[0], c[2] = m - 0.005, m + 0.005
                if c[3] - c[1] < 0.01: m = (c[1] + c[3]) / 2; c[1], c[3] = m - 0.005, m + 0.005
                cells.append([round(c[0], 4), round(c[2], 4), round(c[1], 4), round(c[3], 4)])
    return zb, cells
def zurl(b, att):
    fs = {"sort": {"value": "globalrelevanceex"}, "price": {"min": 100000, "max": 750000}, "tow": {"value": False}, "mf": {"value": False},
          "con": {"value": False}, "apa": {"value": False}, "apco": {"value": False}, "manu": {"value": False}}
    if att: fs["att"] = {"value": att}
    s_ = json.dumps({"pagination": {}, "isMapVisible": True, "isListVisible": True, "mapBounds": {"west": b[0], "east": b[1], "south": b[2], "north": b[3]}, "filterState": fs}, separators=(",", ":"))
    return "https://www.zillow.com/homes/for_sale/?searchQueryState=" + urllib.parse.quote(s_, safe="")
def lwpath(st, cty):
    return f"{NAMES[st].lower().replace(' ', '-')}-land-for-sale/{cty.lower().replace(' ', '-').replace('.', '')}-{'parish' if st == 'LA' else 'county'}/waterfront-property/price-100000-750000"
def dot_of(G, pts):
    if pts:
        y = statistics.median(p[0] for p in pts); x = statistics.median(p[1] for p in pts); p0 = Point(x, y)
        if G.contains(p0): return [round(y, 5), round(x, 5)]
        inside = [Point(b, a) for a, b in pts if G.contains(Point(b, a))]
        if inside: return [round(inside[0].y, 5), round(inside[0].x, 5)]
    polys = [x for x in getattr(G, "geoms", [G]) if x.geom_type == "Polygon"]
    part = max(polys, key=lambda x: x.area); q = polylabel(part, tolerance=0.0002)
    return [round(q.y, 5), round(q.x, 5)]

added = collections.defaultdict(list); misses = []
NOP = {"FL|Clay-Deer Lake": "no map outline of this lake was found", "MT|Big Therriault Lake": "the lake lies in Kootenai National Forest (Ten Lakes Scenic Area)"}
LK_ADD = collections.defaultdict(list)
def lkrow(a, **kw): return dict(n=a["n"], c=a["cty"], ft=a["ft"], m=round(a["ft"] / 3.28084, 1), rft=None, k=a["k"], yrs=a["yrs"], y=a["y"], s=a["s"],
                                px=0, lim=a["k"] < 20 or a["yrs"] < 5, x=True, g="lq", lq=a["href"], **kw)
for kind, L in (("A", A), ("B", B)):
    for a in L:
        if kind == "A" and a["key"] in NOP: LK_ADD[a["st"]].append(lkrow(a, nop=NOP[a["key"]])); print("NOP", a["n"]); continue
        names = (variants(a["n"]) if a["n"] else []) + (variants(re.sub(r"^[A-Za-z.-]+-", "", a["raw"])) if kind == "A" else [])
        G, how, dist = find_shape(a["st"], a["cty"], names, a["pts"])
        if G is None: misses.append((kind, a["st"], a["n"], len(a["pts"]))); print("MISS", kind, a["st"], a["n"], len(a["pts"]), flush=True); continue
        if a["n"] is None: a["n"] = re.sub(r"\bLk\b", "Lake", how[1]) if how[1] else a["raw"]
        a.update(G=G, how=how, ac=round(acres(G)), dist=round(dist) if dist is not None else None)
        print(kind, a["st"], f"{a['n'][:28]:28}", a["cty"][:12], "ac", a["ac"], how, "dist", a["dist"], "pts", len(a["pts"]), flush=True)
        added[a["st"]].append((kind, a))
json.dump(dict(A=[{k: v for k, v in a.items() if k != "G"} for a in A], B=[{k: v for k, v in b.items() if k != "G"} for b in B], misses=misses, report=report),
          open(OUT + "/report.json", "w"), ensure_ascii=False, indent=0, default=str)

PR_ADD = {}; shore_new = collections.defaultdict(dict)
for st, L in added.items():
    nl = sum(1 for e in P[st] if e["t"] == "lake")
    L.sort(key=lambda t: -t[1]["ft"]); rows = []
    for kind, a in L:
        nl += 1; G = a["G"]
        zb, cells = boxes_for(G); d = dot_of(G, a["pts"])
        ctys = sorted({county_at(x, y) for x, y in [(G.representative_point().x, G.representative_point().y)] + [(b[0], b[2]) for b in [zb]] if county_at(x, y)} | {a["cty"].split(",")[0].strip()})
        ctys = [c for c in ctys if any(c == n for n, g, x in CT[st])] or [a["cty"]]
        v = f"{a['ft']:.1f} ft"
        e = dict(t="lake", n=a["n"], rk=nl, v=v, c=", ".join(ctys), z=zurl(zb, "waterfront"), za=zurl(zb, None),
                 lw=[[c, "https://www.landwatch.com/" + lwpath(st, c)] for c in ctys], lat=d[0], lon=d[1], dot=d, added="2026-11-20")
        if cells: e["boxes"] = [zb] + cells
        if kind == "A": e["lq"] = a["href"]
        P[st].append(e); i = len(P[st]) - 1
        shore_new[st][f"{st}_{i}"] = dict(name=a["n"], method=("USGS NHD waterbody" if a["how"][0] == "NHD" else "TIGER area water by " + a["how"][0]), matched=[a["how"][1]], geom=mapping(G))
        rows.append(["l", a["n"], nl, v, [zb[2], zb[3], zb[0], zb[1]], [[c, lwpath(st, c)] for c in ctys], d, None])
        if kind == "A":
            LK_ADD[st].append(lkrow(a))
    PR_ADD[st] = rows
for st in LK_ADD: LK_ADD[st].sort(key=lambda r: -r["ft"])
json.dump(P, open(OUT + "/props.json", "w"), ensure_ascii=False)
for st, d in shore_new.items():
    Sh = json.load(open(f"{LIVE}/pipeline/shore/{st}.json")); Sh.update(d)
    json.dump(Sh, open(f"{OUT}/shore/{st}.json", "w"), separators=(",", ":"))
json.dump(dict(PR=PR_ADD, LK=LK_ADD), open(OUT + "/extra.json", "w"), ensure_ascii=False)
print("DONE A", sum(1 for L in added.values() for k, a in L if k == "A"), "of", len(A), "; B", sum(1 for L in added.values() for k, a in L if k == "B"), "of", len(B), "; misses", misses)
