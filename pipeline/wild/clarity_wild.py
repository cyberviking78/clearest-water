"""Measured water clarity for the Wild Lakes (run after build_wild.py). For every satellite-blue lake of 100 acres or more, Secchi-disk depths since 2000 are fetched from the Water Quality Portal (USGS, EPA and state monitoring,
waterqualitydata.us) and only readings taken at stations inside the lake (within about 300 m of its outline) are used.
Chad's clarity cut-off (Nov 12, 2026) applies: a lake whose median reading (2+ readings) is under 15 ft is left out. Lakes with no
readings stay in (most high lakes are never measured), so look at the water on the satellite view.
Adds index 9 to each lake in lakes.json: median clarity in feet (null when not measured). Cache: clarity_cache/.
Reads lakes.json (first run saves it as lakes_unmeasured.json and reads that afterwards), writes lakes.json / lakes_geom.json. Usage: clarity.py"""
import json, os, csv, io, time, math, statistics, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from shapely.geometry import shape, Point
HERE = os.path.dirname(os.path.abspath(__file__)); C = HERE + "/clarity_cache"; os.makedirs(C, exist_ok=True)
LK = json.load(open(HERE + "/lakes.json")); GJ = json.load(open(HERE + "/lakes_geom.json")); GE = [shape(g) for g in GJ]
if not os.path.exists(HERE + "/lakes_unmeasured.json"): json.dump(LK, open(HERE + "/lakes_unmeasured.json", "w")); json.dump(GJ, open(HERE + "/lakes_geom_unmeasured.json", "w"))
LK = json.load(open(HERE + "/lakes_unmeasured.json")); GJ = json.load(open(HERE + "/lakes_geom_unmeasured.json")); GE = [shape(g) for g in GJ]
W = "https://www.waterqualitydata.us/data/"
def get(kind, bb):
    q = urllib.parse.urlencode(dict(bBox=",".join(f"{v:.4f}" for v in bb), characteristicName="Depth, Secchi disk depth", startDateLo="01-01-2000", mimeType="csv",
                                    **({"dataProfile": "narrowResult"} if kind == "Result" else {})))
    for a in range(4):
        try: return list(csv.DictReader(io.StringIO(urllib.request.urlopen(W + kind + "/search?" + q, timeout=240).read().decode("utf-8", "replace"))))
        except Exception as ex: time.sleep(6 * (a + 1))
    return None
def clar(i):
    l = LK[i]; f = f"{C}/{l[5]}_{l[6]}.json"
    if os.path.exists(f): return json.load(open(f))
    g = GE[i]; bb = g.buffer(0.003).bounds
    st, rs = get("Station", bb), get("Result", bb)
    if st is None or rs is None: return None                   # not cached: tried again next run
    zone = g.buffer(0.003); inside = set()
    for s in st:
        try:
            if zone.contains(Point(float(s["LongitudeMeasure"]), float(s["LatitudeMeasure"]))): inside.add(s["MonitoringLocationIdentifier"])
        except Exception: pass
    ft = []
    for r in rs:
        if r["MonitoringLocationIdentifier"] not in inside: continue
        try: v = float(r["ResultMeasureValue"])
        except Exception: continue
        u = (r.get("ResultMeasure/MeasureUnitCode") or "").lower()
        v = v * 3.28084 if u in ("m", "meters") else v / 12 if u == "in" else v / 30.48 if u == "cm" else v if u in ("ft", "feet") else None
        if v is not None and 0 < v < 200: ft.append(v)
    out = dict(n=len(ft), med=round(statistics.median(ft), 1) if ft else None)
    json.dump(out, open(f, "w")); return out
todo = [i for i, l in enumerate(LK) if l[3] >= 100]     # every lake of 100+ acres
print(len(todo), "lakes to check for clarity readings", flush=True)
with ThreadPoolExecutor(4) as ex: res = dict(zip(todo, ex.map(clar, todo)))
keep, gk, out = [], [], {"murky": []}
MURKY = []
for i, l in enumerate(LK):
    r = res.get(i)
    if r and r["n"] >= 2 and r["med"] is not None and r["med"] < 15 and l[0]: MURKY.append((l[0], l[1], l[5], l[6], 0.5 if l[3] >= 1000 else 0.1))
def murky_piece(l):    # another piece of a measured-murky lake (the Census map cuts big lakes at county lines): same name and state within ~10 km (~50 km for a lake of 1,000+ acres)
    return any(l[0] == n and l[1] == s and abs(l[5] - la) < r and abs(l[6] - lo) < r * 1.3 for n, s, la, lo, r in MURKY)   # ~50 km for a big reservoir's arms
for i, l in enumerate(LK):
    if l[0] and murky_piece(l) and not (res.get(i) and res[i]["n"] >= 2 and res[i]["med"] is not None and res[i]["med"] >= 15):
        out["murky"].append(f"{l[0]} {l[1]} (another piece of a murky lake)"); continue
    if l[12] == "colour" and l[11] < 40: out.setdefault("blue but built-up shore", []).append(f"{l[0] or 'unnamed'} {l[1]}"); continue   # a blue lake in a subdivision or town (Silver Lakes, Helendale): under 40% natural shore
    r = res.get(i); med = r["med"] if r and r["n"] >= 2 else None
    if med is not None and med < 15: out["murky"].append(f"{l[0] or 'unnamed'} {l[1]} {med} ft"); continue
    l = list(l); l[9] = l[9] if l[9] is not None else med; keep.append(l); gk.append(GJ[i])
print("left out, under 15 ft:", len(out["murky"]), sorted(out["murky"]))
print("left out, blue but under 40% natural shore:", len(out.get("blue but built-up shore", [])), sorted(out.get("blue but built-up shore", []))[:40])
print("kept", len(keep), "lakes;", sum(1 for l in keep if l[9]), "with measured clarity")
json.dump(keep, open(HERE + "/lakes.json", "w"), separators=(",", ":")); json.dump(gk, open(HERE + "/lakes_geom.json", "w"), separators=(",", ":"))
