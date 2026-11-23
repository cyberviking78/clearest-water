"""Map the clear river stretches (out/reaches.json) and the curated not-measured waters (curated.json) onto Census TIGER water
(USGS NHD names and shapes), and append them to props.json / shore/<ST>.json and the page's Rivers tab and Property list.
Writes out/props.json, out/shore/<ST>.json, out/extra2.json."""
import json, os, re, sys, collections, math, urllib.parse, urllib.request, time
import shapely, shapefile
from shapely.geometry import shape, mapping, box
HERE = os.path.dirname(os.path.abspath(__file__)); LIVE = "/home/claude/live"; G = "/home/claude/geo_src"; OUT = HERE + "/out"
os.makedirs(OUT + "/shore", exist_ok=True)
h = open(LIVE + "/page.work.html").read()
_i = h.find("const NAMES={"); NAMES = dict(re.findall(r'([A-Z]{2}):"([^"]+)"', h[_i:h.find("}", _i)]))
P = json.load(open(LIVE + "/pipeline/props.json"))
CT = collections.defaultdict(list)
for r in shapefile.Reader(G + "/county500k.zip").iterShapeRecords():
    CT[r.record["STUSPS"]].append((r.record["NAME"], shape(r.shape.__geo_interface__), r.record["GEOID"]))
CT_OLD = [(r.record["NAME"], shape(r.shape.__geo_interface__)) for r in shapefile.Reader(G + "/county2020.zip").iterShapeRecords() if r.record["STUSPS"] == "CT"]
ALLC = [(gid, g) for st in CT for a, g, gid in CT[st]]; ctree = shapely.STRtree([g for _, g in ALLC])
def counties_in(env): return [ALLC[i][0] for i in ctree.query(box(*env))]
def counties_of(st, geom):
    L = CT_OLD if st == "CT" else [(a, g) for a, g, gid in CT[st]]
    hit = sorted(((a, g.intersection(geom.buffer(0.002)).length + g.intersection(geom).area * 1000) for a, g in L if g.intersects(geom)), key=lambda x: -x[1])
    return [a for a, _ in hit[:3]] or [min(L, key=lambda t: t[1].distance(geom))[0]]
ABR = {"lake": "lk", "lakes": "lks", "river": "riv", "creek": "crk", "brook": "brk", "branch": "br", "stream": "strm", "reservoir": "res",
       "fork": "frk", "mountain": "mtn", "saint": "st", "mount": "mt", "fort": "ft", "east": "e", "west": "w", "north": "n", "south": "s", "springs": "spgs", "spring": "spg"}
def norm(n): return " ".join(ABR.get(w, w) for w in re.sub(r"[^a-z0-9 ]", "", (n or "").lower().replace("-", " ")).split())
_TC = {}
def get(url):
    for a in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read()
        except Exception as e:
            if "404" in str(e): return None
            time.sleep(5 * (a + 1))
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
def channel(names, env):
    E = box(*env); cs = counties_in(env)
    for nm in names:
        nn = norm(nm)
        lines = [g for c in cs for n2, g in tiger("lw", c) if n2 == nn and g.intersects(E)]
        areas = [g for c in cs for n2, g in tiger("aw", c) if n2 == nn and g.intersects(E)]
        if not lines and not areas: continue
        if not lines:     # wide rivers are only in AREAWATER
            geo = shapely.union_all(areas).intersection(E)
            if not geo.is_empty: return geo.simplify(0.0001), nm
            continue
        L = shapely.union_all(lines).intersection(E)
        geo = L
        if areas:
            A = shapely.union_all(areas).intersection(L.buffer(0.002))
            if not A.is_empty: geo = shapely.union_all([L, A])
        if not geo.is_empty: return geo.simplify(0.0001), nm
    return None, None
def zurl(b, att):
    fs = {"sort": {"value": "globalrelevanceex"}, "price": {"min": 100000, "max": 750000}, "tow": {"value": False}, "mf": {"value": False},
          "con": {"value": False}, "apa": {"value": False}, "apco": {"value": False}, "manu": {"value": False}}
    if att: fs["att"] = {"value": att}
    s = json.dumps({"pagination": {}, "isMapVisible": True, "isListVisible": True, "mapBounds": {"west": b[0], "east": b[1], "south": b[2], "north": b[3]}, "filterState": fs}, separators=(",", ":"))
    return "https://www.zillow.com/homes/for_sale/?searchQueryState=" + urllib.parse.quote(s, safe="")
def lwpath(st, cty):
    return f"{NAMES[st].lower().replace(' ', '-')}-land-for-sale/{cty.lower().replace(' ', '-').replace('.', '')}-{'parish' if st == 'LA' else 'county'}/waterfront-property/price-100000-750000"
DX, DY = 0.15, 0.12
def boxes_for(G_):
    w, s, e, n = G_.bounds; pad = 0.012
    zb = [round(w - pad, 4), round(e + pad, 4), round(s - pad, 4), round(n + pad, 4)]
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

R = json.load(open(OUT + "/reaches.json")); CU = json.load(open(HERE + "/curated.json"))
tab = collections.defaultdict(list); PR = collections.defaultdict(list); shore = collections.defaultdict(dict); misses = []
nriv = {st: sum(1 for e in L if e["t"] == "river") for st, L in P.items()}
# A measured stretch inside a curated reach of the same river takes the curated name and extent but keeps its measurements;
# curated waters with no measured stretch are listed as "not measured".
def inside(r, bb): return bb[0] <= r["lon"] <= bb[2] and bb[1] <= r["lat"] <= bb[3]
items = []; used = set()
for r in R:
    c = next((c for c in CU if c["st"] == r["st"] and norm(c["names"][0]) == norm(r["river"]) and inside(r, c["bbox"])), None)
    if c: used.add(c["n"]); r = dict(r, n=c["n"], cur=c)
    items.append(("reach", r))
items += [("nm", c) for c in CU if c["n"] not in used]
def full_len(names, env):
    """Total length (km) of the named channel in the counties around env -- screens out small streams."""
    cs = counties_in(box(*env).buffer(0.3).bounds); best = 0
    for nm in names:
        nn = norm(nm); L = [g for c in cs for n2, g in tiger("lw", c) if n2 == nn]
        A = [g for c in cs for n2, g in tiger("aw", c) if n2 == nn]
        km_ = (shapely.union_all(L).length if L else 0) + (shapely.union_all(A).length / 2 if A else 0)
        best = max(best, km_ * 95)
    return best
for kind, r in items:
    st = r["st"]
    if st not in P: continue
    if kind == "reach":
        names = [r["river"]] + ([r["river"][:-6]] if r["river"].endswith(" River") and " Fork " in r["river"] + " " else [])
        if r.get("cur"): names, env = r["cur"]["names"], r["cur"]["bbox"]
        else: env = shapely.MultiPoint([(x, y) for y, x in r["pts"]]).envelope.buffer(0.05).bounds
        if full_len(names, env) < 25:
            misses.append((st, r["n"], "short or unnamed in NHD")); continue
        geo, how = channel(names, env)
        if geo is None: misses.append((st, r["n"], "no channel")); continue
        row = dict(n=r["n"], m=r["m"], p25=r["p25"], p75=r["p75"], k=r["k"], s=r["s"], y=r["y"], b=0.0, px=0.0, site=r["site"], u="NTU", x=True, g="reach")
        v = ("0.0" if r["m"] < 0.05 else f"{r['m']:.2f}" if r["m"] < 1 or r["m"] >= 1.95 else f"{r['m']:.1f}") + " NTU"
    else:
        geo, how = channel(r["names"], r["bbox"])
        row = dict(n=r["n"], x=True, g="nm", nm=True, note=r["note"], src=r["src"], srcn=r["srcn"])
        v = "not measured"
    if geo is None:   # only curated waters get here: list them without a map shape or search
        misses.append((st, r["n"], "curated, no channel")); row["nogeo"] = True; tab[st].append(row); continue
    ctys = counties_of(st, geo)
    if kind == "reach": nriv[st] += 1; rk = nriv[st]
    else: rk = None
    zb, cells = boxes_for(geo)
    c = geo.representative_point()
    e = dict(t="river", n=r["n"], rk=rk, v=v, c=", ".join(ctys), z=zurl(zb, "waterfront"), za=zurl(zb, None),
             lw=[[a, "https://www.landwatch.com/" + lwpath(st, a)] for a in ctys], lat=round(c.y, 4), lon=round(c.x, 4), added="2026-11-10b")
    if cells: e["boxes"] = [zb] + cells
    P[st].append(e); i = len(P[st]) - 1
    shore[st][f"{st}_{i}"] = dict(name=r["n"], method="river channel" if kind == "reach" else "curated reach", matched=[how], geom=mapping(geo))
    tab[st].append(row)
    PR[st].append(["r", r["n"], rk, v, [zb[2], zb[3], zb[0], zb[1]], [[a, lwpath(st, a)] for a in ctys]])
    print(kind, st, r["n"], v, "boxes", 1 + len(cells or []), flush=True)
json.dump(P, open(OUT + "/props.json", "w"), ensure_ascii=False)
for st, d in shore.items():
    S = json.load(open(f"{LIVE}/pipeline/shore/{st}.json")); S.update(d)
    json.dump(S, open(f"{OUT}/shore/{st}.json", "w"), separators=(",", ":"))
json.dump(dict(tab=tab, PR=PR, misses=misses), open(OUT + "/extra2.json", "w"), ensure_ascii=False)
print("DONE", sum(len(v) for v in PR.values()), "searchable;", len(misses), "unmapped:", misses, flush=True)
