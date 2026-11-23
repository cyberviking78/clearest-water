"""USGS National Digital Trails segments that allow bicycles -> raw/usgs.json (same as pipeline/trails/usgs_pull.py)"""
import json, os, time, urllib.parse, urllib.request
U = "https://carto.nationalmap.gov/arcgis/rest/services/transportation/MapServer/37/query"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw", "usgs.json")
def get(q):
    for a in range(5):
        try: return json.load(urllib.request.urlopen(U, urllib.parse.urlencode(q).encode(), timeout=300))
        except Exception as e: print("retry", e, flush=True); time.sleep(20 * (a + 1))
    raise RuntimeError("USGS trails unreachable")
W = "bicycle IN ('Y','Yes')"
ids = sorted(get(dict(where=W, returnIdsOnly="true", f="json"))["objectIds"])
print(len(ids), "ids", flush=True)
out = []
for i in range(0, len(ids), 1000):
    r = get(dict(objectIds=",".join(map(str, ids[i:i + 1000])), outFields="objectid,name,namealternate,trailtype,trailsurface,lengthmiles,networklength,sourceoriginator,ebike,motorcycle,ohvover50inches",
                 returnGeometry="true", outSR=4326, maxAllowableOffset=0.0001, geometryPrecision=5, f="json"))
    for f in r.get("features", []):
        if f.get("geometry", {}).get("paths"): out.append([f["attributes"], f["geometry"]["paths"]])
    if i % 20000 == 0: print(i, len(out), flush=True)
json.dump(out, open(OUT, "w"))
print("USGS DONE", len(out), flush=True)
