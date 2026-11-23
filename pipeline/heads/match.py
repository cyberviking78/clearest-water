"""Decide whether each candidate listing's lot holds the spring vent; attach permits. -> matches.json"""
import json, math, re, sys
from shapely.geometry import Point
from shapely.ops import transform
import warnings; warnings.filterwarnings('ignore')
import parcels, permits
h = json.load(open("heads.json")); C = json.load(open("cands.json"))
cache = {}
def P(st, lon, lat, tol=0, county=None):
    k = (st, round(lon, 6), round(lat, 6), tol)
    if k not in cache:
        try: cache[k] = parcels.parcels_at(st, lon, lat, tol, county)
        except Exception as e: print("parcel error", st, e, flush=True); cache[k] = "err"
    return cache[k]
def norm_owner(o): return re.sub(r"[^A-Z]", "", (o or "").upper())[:18]
GOV = re.compile(r"(?i)\b(TIITF|STATE LANDS?|W M D|WATER MGMT|WATER MANA|U S GOVERNMENT|STATE PARK|NATIONAL FOREST|FOREST SERVICE|BUREAU OF|STATE OF|UNITED STATES|USA\b|U S A|COUNTY|CITY OF|TOWN OF|BOARD OF TRUSTEES|TRUSTEES OF THE INTERNAL|WATER MANAGEMENT|DISTRICT|PARKS|NATIONAL PARK|DEPARTMENT|DEPT|COMMISSION|UNIVERSITY)")
out = []
for c in C:
    s = h[c["head"]]; st = c["st"]
    kx = 111320 * math.cos(math.radians(c["vlat"]))
    proj = lambda x, y, z=None: ((x - c["vlon"]) * kx, (y - c["vlat"]) * 110540)
    vent = Point(0, 0)
    res = dict(c, tier=None, how=None); vgov = None
    L = P(st, c["lon"], c["lat"], 0, s.get("county"))
    if L == "err": continue
    if L is None:          # no public parcel layer: estimate from lot size
        r = max(c["rad"], 40)
        if c["dist"] <= r: res.update(tier=3, how="estimate")
    else:
        if not L: L = P(st, c["lon"], c["lat"], 25, s.get("county")) or []
        if L == "err": continue
        if not L or all(GOV.search(a["owner"] or "") for g, a in L):
            # listing's map point isn't on a private parcel (road, park, unmapped): fall back to the lot-size estimate
            if c["dist"] <= max(c["rad"], 40):
                res.update(tier=3, how="estimate", note="the listing's map point isn't on a private parcel, so this is estimated from lot size")
                out.append(res); print(st, c["city"], c["price"], "tier 3 (fallback)", s["name"], "mag", s["mag"], flush=True)
            continue
        dl = min(transform(proj, g).distance(vent) for g, a in L)
        V = P(st, c["vlon"], c["vlat"], 0, s.get("county"))
        V = [] if V == "err" else V
        vids = {a["id"] for g, a in V}; lids = {a["id"] for g, a in L}
        vgov = any(GOV.search(a["owner"] or "") for g, a in V)
        same_owner = any(norm_owner(a["owner"]) and norm_owner(a["owner"]) == norm_owner(b["owner"]) for g, a in V for g2, b in L)
        if vids & lids: res.update(tier=0, how="parcel", gap=0)
        elif not V and dl <= 30: res.update(tier=1, how="parcel", gap=round(dl), note="vent in unparceled water at the lot's edge")
        elif V and same_owner and not vgov: res.update(tier=2, how="parcel", gap=round(dl))
        elif V and dl <= 30 and not vgov: res.update(tier=1, how="parcel", gap=round(dl), note="vent mapped within 30 m of the lot line")
        if res["tier"] is not None:
            pa = sum(transform(proj, g).area for g, a in L) / 4046.86
            if c["acres"] and pa > 2.5 * c["acres"] + 1:     # listing is a piece of a larger parcel
                res.update(tier=4 if c["dist"] <= 2 * c["rad"] else None, note="the parcel is larger than the acreage for sale; the vent may or may not be in the piece being sold")
        if res["tier"] is not None:
            res["parcel_acres"] = round(sum(transform(proj, g).area for g, a in L) / 4046.86, 2)
            res["parcel_ids"] = [a["id"] for g, a in L]
    if res["tier"] is None: continue
    res["vent_owner_gov"] = vgov
    out.append(res)
    print(st, c["city"], c["price"], "tier", res["tier"], s["name"], "mag", s["mag"], flush=True)
# permits / rights near the vent of each matched spring
for r in out:
    if r["st"] == "FL":
        r["permits"] = permits.fl_permits(r["vlon"], r["vlat"], 400)
    elif r["st"] == "TX":
        rights, gcd = permits.tx_rights(r["vlon"], r["vlat"], 800); r["permits"] = rights; r["gcd"] = gcd
json.dump(out, open("matches.json", "w"), default=str)
import collections
print(len(out), "matches", collections.Counter((r["st"], r["tier"]) for r in out))
