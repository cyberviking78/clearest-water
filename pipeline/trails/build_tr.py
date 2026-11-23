"""Assemble the Trails tab data (TR) from trails.json + matches.json; mark listings first seen this run as new.
Usage: build_tr.py <date>   -> tr.json, seen_trails.json, meta_trails.json"""
import glob, json, os, sys, datetime, collections
import numpy as np, shapely
from shapely.geometry import shape
ROOT = os.path.dirname(os.path.abspath(__file__))
TODAY = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
T = json.load(open(os.path.join(ROOT, "trails.json")))
M = json.load(open(os.path.join(ROOT, "matches.json")))
seen_p = os.path.join(ROOT, "seen_trails.json"); meta_p = os.path.join(ROOT, "meta_trails.json")
seen = json.load(open(seen_p)) if os.path.exists(seen_p) else {}
meta = json.load(open(meta_p)) if os.path.exists(meta_p) else {}
baseline = not seen
prev = meta.get("prev") if meta.get("date") == TODAY else meta.get("date")
prev_urls = set(meta.get("urls", []))

# states each trail passes through (cached in trails.json after the first run)
if any("states" not in t for t in T):
    S = [(s["st"], shape(s["geom"])) for s in json.load(open(os.path.join(ROOT, "states.json")))]
    tree = shapely.STRtree([g for _, g in S])
    for f in glob.glob(os.path.join(ROOT, "geom", "g*.json")):
        for tid, L in json.load(open(f)).items():
            pts = np.vstack([np.array(c)[:: max(1, len(c) // 4)] for _, c in L])
            hit = collections.Counter()
            for a, b in zip(*tree.query(shapely.points(pts), predicate="within")): hit[S[b][0]] += 1
            if not hit:
                for p in pts[:: max(1, len(pts) // 5)]: hit[S[int(tree.nearest(shapely.Point(p)))][0]] += 1
            T[int(tid)]["states"] = [k for k, _ in hit.most_common()]
    json.dump(T, open(os.path.join(ROOT, "trails.json"), "w"), separators=(",", ":"))

L = []
for m in sorted(M, key=lambda m: (m["tid"], m["dist"])):
    url = m["url"]; first = seen.get(url, [TODAY])[0]
    is_new = (not baseline) and url not in seen
    seen[url] = [first, TODAY]
    L.append([m["tid"], m["price"], m["beds"], m["baths"], m["sqft"], m["acres"], m["addr"], m["city"], m["st"], m["dom"], m["dist"],
              url.replace("https://www.redfin.com", ""), m["seg"], first, is_new, m["lat"], m["lon"], m["year"]])
# trail rows: [name, also, miles, end-to-end miles, main type, tags, shares, states, bbox]
TRL = [[t["name"], t["also"][:4], t["mi"], t["route_mi"], t["type"], "".join(t["tags"]), t["share"], t["states"], t["bbox"]] for t in T]
cur = {x[11] for x in L}
TR = dict(date=TODAY, prev=None if baseline else prev, trails=TRL, L=L)
json.dump(TR, open(os.path.join(ROOT, "tr.json"), "w"), separators=(",", ":"), ensure_ascii=False)
json.dump(seen, open(seen_p, "w"), separators=(",", ":"))
gone = len(prev_urls - {"https://www.redfin.com" + u for u in cur}) if prev_urls else 0
json.dump(dict(date=TODAY, prev=TR["prev"], n=len(L), new=sum(1 for x in L if x[14]), gone=gone,
               urls=sorted("https://www.redfin.com" + u for u in cur)), open(meta_p, "w"), separators=(",", ":"))
print("TR", len(TRL), "trails,", len({x[0] for x in L}), "with listings,", len(L), "listings,", sum(1 for x in L if x[14]), "new,", gone, "gone; size",
      len(json.dumps(TR, separators=(",", ":"))) // 1024, "KB")
