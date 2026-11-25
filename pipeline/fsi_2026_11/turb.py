"""Summarise turbidity at Water Quality Portal stations within 600 m of each candidate's vents (NTU/FNU, 2000 on)."""
import csv, json, math, statistics, collections
import re
key = lambda c: re.sub(r"\W+", "_", c["lead"][2])
C = json.load(open("cands.json"))
def dist(a, b, c, d): return math.hypot((a - c) * 111.2, (b - d) * 111.2 * math.cos(math.radians(a))) * 1000
def q(v, p):
    v = sorted(v); k = (len(v) - 1) * p; f = math.floor(k); return v[f] + (v[min(f + 1, len(v) - 1)] - v[f]) * (k - f)
out = []
for i, c in enumerate(C):
    st = {}
    for r in csv.DictReader(open(f"cache/wqp/Station_{key(c)}.csv", encoding="utf-8-sig")):
        try: la, lo = float(r["LatitudeMeasure"]), float(r["LongitudeMeasure"])
        except: continue
        d = min(dist(la, lo, v[0], v[1]) for v in c["vents"])
        if d <= 600: st[r["MonitoringLocationIdentifier"]] = (r["MonitoringLocationName"], r["MonitoringLocationTypeName"], round(d))
    vals, yrs, sites = [], set(), set()
    for r in csv.DictReader(open(f"cache/wqp/Result_{key(c)}.csv", encoding="utf-8-sig")):
        if r["MonitoringLocationIdentifier"] not in st: continue
        u = (r.get("ResultMeasure/MeasureUnitCode") or "").upper()
        if u and not any(x in u for x in ("NTU", "FNU", "JTU", "NTRU")): continue
        try: v = float(r["ResultMeasureValue"])
        except: continue
        if v < 0 or v > 500: continue
        vals.append(v); yrs.add(r["ActivityStartDate"][:4]); sites.add(r["MonitoringLocationIdentifier"])
    s = None
    if vals: s = dict(m=round(statistics.median(vals), 2), a=round(q(vals, .25), 2), b=round(q(vals, .75), 2), n=len(vals), yrs=len(yrs), y0=min(yrs), y1=max(yrs), sites=len(sites))
    out.append({"name": c["lead"][2], "turb": s, "stations": list(st.values())[:6]})
    print(f"{c['lead'][2]:45} {s}")
json.dump(out, open("turb.json", "w"), indent=0)
