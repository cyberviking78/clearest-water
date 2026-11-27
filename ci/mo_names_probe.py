"""One-off: Wikimedia Commons photos of named Missouri springs that carry no map position (searched by name and county)."""
import json, os, re, time, urllib.parse, urllib.request, urllib.error
os.makedirs("out", exist_ok=True)
UA = "ClearestWater/1.0 (https://github.com/cyberviking78/clearest-water; springs research) python-urllib"
def get(u):
    for t in range(6):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=120).read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and t < 5: time.sleep(int(e.headers.get("Retry-After") or 0) or 10 * (t + 1)); continue
            raise
Q = json.load(open("ci/mo_names.json")); out = {}; log = []
for i, name, county in Q:
    q = f'intitle:"{name}" Missouri'
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrsearch": q,
        "gsrnamespace": 6, "gsrlimit": 30, "prop": "imageinfo|categories", "cllimit": 50, "iiprop": "url|extmetadata", "iiurlwidth": 640})
    try:
        d = get(u); rows = []
        for p in ((d.get("query") or {}).get("pages") or {}).values():
            ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata") or {}
            rows.append({"title": p.get("title"), "thumb": ii.get("thumburl"), "page": ii.get("descriptionurl"),
                         "cats": [c["title"] for c in p.get("categories", [])],
                         "license": (md.get("LicenseShortName") or {}).get("value"),
                         "artist": re.sub("<[^>]+>", "", (md.get("Artist") or {}).get("value") or "")[:120],
                         "desc": re.sub("<[^>]+>", "", (md.get("ImageDescription") or {}).get("value") or "")[:400]})
        if rows: out[f"{i}|{name}|{county}"] = rows
    except Exception as e: log.append(f"{name}: {e}")
    time.sleep(1.0)
json.dump(out, open("out/commons_names.json", "w")); log.append(f"{len(out)} of {len(Q)} names have candidate files")
open("out/log.txt", "w").write("\n".join(log)); print("\n".join(log[-3:]))
