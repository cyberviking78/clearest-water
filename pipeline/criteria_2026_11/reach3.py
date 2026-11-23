"""Clear stretches of rivers whose whole-river median misses the 2 NTU line.
Station-level turbidity (Water Quality Portal, stream sites, 2016+; plus USGS continuous sensors in TX, ID, WY sampled weekly)
is grouped by river name (from the station name) and by distance (stations within 15 km chain into one stretch). A stretch
qualifies when its median is at or under 3 NTU (was under 2 before Nov 12) on 24+ samples over 3+ years, and the river isn't already on that state's list.
Each river contributes its clearest qualifying stretch, named after the nearest town. -> out/reaches.json"""
import csv, io, json, os, re, sys, collections, statistics, math, urllib.request, time
import numpy as np
HERE = "/home/claude/live/crit"; C = "/home/claude/live/reach/cache"; os.makedirs(HERE + "/out", exist_ok=True)   # same station data as reach.py
h = open("/home/claude/live/page.work.html").read()
def obj(name):
    i = h.find("const " + name + "="); o, _ = json.JSONDecoder().raw_decode(h[i + len("const " + name + "="):]); return o
RV, FSD = obj("RV"), obj("FSD")
UNITS = {"NTU", "FNU", "NTRU", "FTU", "FNRU", "FBU", "FAU", "NTMU"}
RIVERY = re.compile(r"\b(river|riv|rv|r|fork|fk|rio)\b", re.I)
SEP = re.compile(r"\s+(?:at|near|nr|abv|above|blw|below|bl|ab|bel|upstream|downstream|us|ds|u/s|d/s|off|east of|west of|north of|south of|from|in|on|@|by|between|btw|\d.*)\b|[,(@\-–#:;]|\s+\d", re.I)
TOK = {"frk": "fork", "fk": "fork", "rv": "river", "riv": "river", "ri": "river", "r": "river", "crk": "creek", "cr": "creek", "br": "branch", "mf": "middle fork", "nf": "north fork", "sf": "south fork", "ef": "east fork", "wf": "west fork"}
DIR = {"n": "north", "s": "south", "e": "east", "w": "west", "m": "middle"}
def canon(w):
    t = re.sub(r"[^a-z0-9 ']", " ", (w or "").lower()).split()
    t = [TOK.get(x, x) for x in t]
    if t and t[0] in DIR: t[0] = DIR[t[0]]
    return " ".join(" ".join(t).split())
STOP = set("road rd street st ave avenue drive dr hwy highway route bridge br at nr near mouth above below ab bl abv blw upper lower mid reach gauge gage gaging site station sta headwaters headwater confluence culvert xing the of and us sr fm cr ih sh ozar inlet outlet dam ds us wwtp cty county co park walking intersection".split())
DIRW = {"north", "south", "east", "west", "middle", "little", "big", "upper", "lower", "northwest", "northeast", "southwest", "southeast"}
BAD = {"creek", "brook", "bk", "trib", "tributary", "ditch", "canal", "drain", "wasteway", "ww", "outfall", "effluent", "wwtp", "lateral", "slough", "spring", "springs", "pond", "lake", "reservoir", "res", "estuary", "bay", "harbor", "inlet", "stream", "strm"}
FIX = {"bitteroot": "bitterroot"}
def river_name(n):
    n = re.sub(r"\bS\.\s?R\.?", " SR ", n or "", flags=re.I)
    t = [FIX.get(x, x) for x in canon(n).split()]
    if not t or any(x in BAD and not (x == "lake" and i + 1 < len(t) and t[i + 1] == "fork") for i, x in enumerate(t)): return None
    if "river" in t:
        i = t.index("river"); j = i
        while j > 0 and i - j < 3 and t[j - 1].replace("'", "").isalpha() and t[j - 1] not in STOP and t[j - 1] not in ("creek", "brook", "run"): j -= 1
        # "fork of new river": keep "of" inside fork names
        if j > 1 and t[j - 1] == "of" and t[j - 2] == "fork": j -= 2
        while j > 0 and i - j < 5 and t[j - 1] in DIRW | {"fork"}: j -= 1
        if j > 0 and t[j - 1] in ("st", "saint", "ste"): j -= 1
        name = t[j:i + 1]
        if name and name[0] == "rio": name = name[:-1]
    elif "fork" in t:
        i = t.index("fork"); j = i
        while j > 0 and i - j < 2 and t[j - 1].replace("'", "").isalpha() and t[j - 1] not in STOP: j -= 1
        name = t[j:i + 1]
        if any(x in ("creek", "brook", "run", "ck", "crk", "branch") for x in t[i + 1:i + 4]): return None
        if i + 1 < len(t) and t[i + 1].isalpha() and len(t[i + 1]) >= 3 and t[i + 1] not in STOP and t[i + 1] not in ("creek", "brook", "run", "ck", "crk"):
            name = name + [t[i + 1], "river"]
        elif i + 1 < len(t) and t[i + 1] in ("creek", "brook", "run", "ck", "crk"): return None
    else:
        return None
    core = [x for x in name if x not in DIRW | {"fork", "river", "of", "st", "saint", "ste", "rio"}]
    if not core or any(x in ("creek", "brook", "ck", "crk", "trib", "tributary", "ditch", "canal", "drain") for x in name): return None
    cap = lambda x: x if x in ("de", "la", "del", "of", "the") else "St." if x in ("st", "saint") else ("Mc" + x[2:].capitalize() if x.startswith("mc") and len(x) > 3 else x.capitalize())
    return " ".join(cap(x) for x in name)
def norm(n): return canon(re.sub(r"\s*\(.*\)", "", n or "")).replace("'", "")
listed = collections.defaultdict(set)
for st, v in RV.items():
    for r in v["rows"]: listed[st].add(norm(r["n"]))
for r in FSD["rivers"]: listed[r[13]].add(norm(r[1]))

# stations
ST = {}
for f in os.listdir(C):
    if not f.startswith("st_"): continue
    st = f[3:5]
    for r in csv.DictReader(io.StringIO(open(f"{C}/{f}", encoding="utf-8", errors="replace").read())):
        try: ST[r["MonitoringLocationIdentifier"]] = (st, r["MonitoringLocationName"], float(r["LatitudeMeasure"]), float(r["LongitudeMeasure"]))
        except Exception: pass
# samples
S = collections.defaultdict(list)
for f in os.listdir(C):
    if not f.startswith("res_"): continue
    for r in csv.DictReader(io.StringIO(open(f"{C}/{f}", encoding="utf-8", errors="replace").read())):
        sid = r["MonitoringLocationIdentifier"]
        if sid not in ST: continue
        u = (r.get("ResultMeasure/MeasureUnitCode") or "").upper().replace(" ", "")
        v = r.get("ResultMeasureValue") or ""
        if re.search(r"not detected|below", (r.get("ResultDetectionConditionText") or ""), re.I): val = 0.5
        else:
            try: val = float(v)
            except Exception: continue
            if u not in UNITS or val < 0 or val > 5000: continue
        y = (r.get("ActivityStartDate") or "")[:4]
        S[sid].append((val, y))
# USGS continuous sensors (daily means, one per week)
def get(u):
    for a in range(4):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read())
        except Exception as e: print("retry", e, flush=True); time.sleep(10 * (a + 1))
    return {}
ucache = C + "/usgs.json"
if os.path.exists(ucache): U = json.load(open(ucache))
else:
    U = {}
    for st, name in (("TX", "Texas"), ("ID", "Idaho"), ("WY", "Wyoming")):
        d = get(f"https://api.waterdata.usgs.gov/ogcapi/v0/collections/time-series-metadata/items?f=json&parameter_code=63680&state_name={name}&computation_identifier=Mean&computation_period_identifier=Daily&limit=500")
        for ft in d.get("features", []):
            p = ft["properties"]
            if (p.get("end") or "") < "2017": continue
            loc = p["monitoring_location_id"]
            m = get(f"https://api.waterdata.usgs.gov/ogcapi/v0/collections/monitoring-locations/items/{loc}?f=json")
            vals = get(f"https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items?f=json&time_series_id={ft['id']}&time=2016-01-01T00:00:00Z/2026-12-31T00:00:00Z&limit=50000")
            xs = [(f2["properties"]["time"][:10], float(f2["properties"]["value"])) for f2 in vals.get("features", []) if f2["properties"].get("value") not in (None, "")]
            if not xs: continue
            c = ft["geometry"]["coordinates"]
            U[loc] = dict(st=st, name=(m.get("properties") or {}).get("monitoring_location_name", loc), lat=c[1], lon=c[0], xs=sorted(xs))
            print("usgs", st, U[loc]["name"], len(xs), flush=True)
    json.dump(U, open(ucache, "w"))
for loc, u in U.items():
    ST.setdefault(loc, (u["st"], u["name"], u["lat"], u["lon"]))
    seen_w = set()
    for d, v in u["xs"]:
        wk = d[:4] + "-" + str(int(d[5:7]) * 5 // 1 + int(d[8:10]) // 7)
        if wk in seen_w: continue
        seen_w.add(wk); S[loc].append((v, d[:4]))
# places for naming
places = []
import zipfile
with zipfile.ZipFile("/home/claude/geo_src/gaz_place.zip") as zf:
    t = zf.read(zf.namelist()[0]).decode("latin-1")
for r in csv.DictReader(io.StringIO(t), delimiter="\t"):
    r = {k.strip(): v.strip() for k, v in r.items()}
    places.append((r["USPS"], re.sub(r" (city|town|village|borough|CDP|municipality)$", "", r["NAME"]), float(r["INTPTLAT"]), float(r["INTPTLONG"])))
PL = collections.defaultdict(list)
for p in places: PL[p[0]].append(p)
def nearest_place(st, lat, lon):
    best = min(PL[st], key=lambda p: (p[2] - lat) ** 2 + ((p[3] - lon) * math.cos(math.radians(lat))) ** 2)
    return best[1]
def km(a, b): return math.hypot((a[0] - b[0]) * 111, (a[1] - b[1]) * 111 * math.cos(math.radians(a[0])))
# group by state + river name, then chain stations within 15 km
G = collections.defaultdict(list)
for sid, (st, nm, lat, lon) in ST.items():
    rn = river_name(nm)
    if rn and S.get(sid): G[(st, rn)].append((sid, lat, lon))
out = []
for (st, rn), sts in G.items():
    if norm(rn) in listed[st] or any(norm(rn).endswith(" " + x) for x in listed[st]): continue
    n = len(sts); parent = list(range(n))
    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if km(sts[i][1:], sts[j][1:]) <= 15: parent[find(i)] = find(j)
    cl = collections.defaultdict(list)
    for i in range(n): cl[find(i)].append(sts[i])
    best = None
    for members in cl.values():
        vals = [v for sid, _, _ in members for v, y in S[sid]]
        yrs = {y for sid, _, _ in members for v, y in S[sid] if y}
        if len(vals) < 24 or len(yrs) < 3: continue
        med = statistics.median(vals)
        if med > 3: continue     # Nov 12: the property cut-off is 3 NTU
        if best is None or med < best["m"]:
            q = np.percentile(vals, [25, 75])
            top = max(members, key=lambda m: len(S[m[0]]))
            lat = sum(m[1] for m in members) / len(members); lon = sum(m[2] for m in members) / len(members)
            best = dict(st=st, river=rn, m=round(med, 2), p25=round(float(q[0]), 2), p75=round(float(q[1]), 2), k=len(vals), s=len(members),
                        y=f"{min(yrs)}–{max(yrs)}", site=ST[top[0]][1], lat=lat, lon=lon, pts=[[m[1], m[2]] for m in members],
                        usgs=any(m[0] in U for m in members))
    if best:
        best["n"] = f"{rn} (near {nearest_place(st, best['lat'], best['lon'])})"
        out.append(best)
def core(rn): return " ".join(x for x in canon(rn).replace("'", "").split() if x not in DIRW | {"fork", "of", "river", "st", "saint"})
bestc = {}
for r in out:
    k = (r["st"], core(r["river"]))
    if k not in bestc or r["m"] < bestc[k]["m"]: bestc[k] = r
out = sorted(bestc.values(), key=lambda r: (r["st"], r["m"]))
json.dump(out, open(HERE + "/out/reaches3.json", "w"), ensure_ascii=False)
print("REACHES", len(out), collections.Counter(r["st"] for r in out).most_common(30), flush=True)
for r in out:
    if r["st"] in ("TX", "ID", "WY"): print(" ", r["st"], r["n"], r["m"], r["k"], r["y"], "|", r["site"])
