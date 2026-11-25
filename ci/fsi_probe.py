"""One-off: read the Florida Springs Institute's springs map (ArcGIS) and save its springs layer."""
import json, urllib.request, urllib.parse, re, os
os.makedirs("out", exist_ok=True)
def get(u, raw=False):
    r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60)
    b = r.read(); return (r.geturl(), b) if raw else json.loads(b)
log = []
final, body = get("https://arcg.is/HTyrO", raw=True); log.append("short link -> " + final)
q = urllib.parse.parse_qs(urllib.parse.urlparse(final).query)
appid = (q.get("appid") or q.get("id") or [None])[0]
if not appid:
    m = re.search(r"/([0-9a-f]{32})", final); appid = m and m.group(1)
log.append("app id " + str(appid))
item = get(f"https://www.arcgis.com/sharing/rest/content/items/{appid}?f=json")
data = get(f"https://www.arcgis.com/sharing/rest/content/items/{appid}/data?f=json")
json.dump({"item": item, "data": data}, open("out/app.json", "w"), indent=1)
s = json.dumps(data); maps = set(re.findall(r'"(?:webmap|itemId|id)"\s*:\s*"([0-9a-f]{32})"', s))
log.append("candidate maps " + ", ".join(maps))
layers = []
for mid in maps:
    try:
        it = get(f"https://www.arcgis.com/sharing/rest/content/items/{mid}?f=json")
        if it.get("type") != "Web Map": continue
        wm = get(f"https://www.arcgis.com/sharing/rest/content/items/{mid}/data?f=json")
        json.dump(wm, open(f"out/webmap_{mid}.json", "w"), indent=1)
        def walk(ls):
            for l in ls:
                if l.get("url"): layers.append((l.get("title"), l["url"]))
                walk(l.get("layers") or [])
        walk(wm.get("operationalLayers", []))
    except Exception as e: log.append(f"map {mid}: {e}")
for title, url in layers:
    log.append(f"layer {title}: {url}")
    try:
        meta = get(url + "?f=json")
        sub = [url] if "fields" in meta else [f"{url}/{l['id']}" for l in meta.get("layers", [])]
        for u in sub:
            m2 = get(u + "?f=json"); name = re.sub(r"\W+", "_", m2.get("name", "x"))
            feats, off = [], 0
            while True:
                r = get(u + "/query?" + urllib.parse.urlencode({"where": "1=1", "outFields": "*", "outSR": 4326, "f": "json",
                        "resultOffset": off, "resultRecordCount": 1000, "returnGeometry": "true"}))
                feats += r.get("features", []); off += 1000
                if not r.get("exceededTransferLimit") or not r.get("features"): break
            json.dump({"meta": m2, "features": feats}, open(f"out/layer_{name}.json", "w"))
            log.append(f"  {name}: {len(feats)} features, fields: " + ", ".join(f["name"] for f in m2.get("fields", [])))
            att = m2.get("hasAttachments")
            if att and feats:
                oid = m2.get("objectIdField") or "OBJECTID"
                ids = [str(f["attributes"][oid]) for f in feats]; n = 0; rows = {}
                for i in range(0, len(ids), 200):
                    r = get(u + "/queryAttachments?" + urllib.parse.urlencode({"objectIds": ",".join(ids[i:i+200]), "f": "json"}))
                    for g in r.get("attachmentGroups", []): rows[g["parentObjectId"]] = [a.get("name") for a in g.get("attachmentInfos", [])]
                json.dump(rows, open(f"out/attach_{name}.json", "w")); log.append(f"  attachments on {len(rows)} features")
    except Exception as e: log.append(f"  error {e}")
open("out/log.txt", "w").write("\n".join(log)); print("\n".join(log))
