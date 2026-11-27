"""One-off: Springs of Missouri books (text by page) and Wikimedia Commons photos near Missouri springs."""
import json, os, subprocess, urllib.parse, urllib.request, urllib.error, time
os.makedirs("out/books", exist_ok=True)
UA = "ClearestWater/1.0 (https://github.com/cyberviking78/clearest-water; springs research) python-urllib"
BROWSER = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
def get(u, out=None, ua=UA):
    for t in range(6):
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": ua, "Accept": "*/*"}), timeout=300); b = r.read(); break
        except urllib.error.HTTPError as e:
            if e.code == 429 and t < 5: time.sleep(int(e.headers.get("Retry-After") or 0) or 10 * (t + 1)); continue
            raise
    if out: open(out, "wb").write(b)
    return b
def curl(u, out):
    p = subprocess.run(["curl", "-sSL", "--http1.1", "--retry", "3", "--retry-all-errors", "-m", "600", "-A", BROWSER, "-o", out, "-w", "%{http_code}", u], capture_output=True, text=True)
    return p.stdout + " " + p.stderr.strip()
log = []
pts = json.load(open("ci/mo_pts.json")); com = {}
import re
GEN = {"spring", "springs", "big", "blue", "cave", "cold", "mill", "the", "upper", "lower", "little", "rise", "of"}
for gid, nm, lat, lon, mag in pts:
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "format": "json", "generator": "geosearch",
        "ggscoord": f"{lat}|{lon}", "ggsradius": 450, "ggslimit": 200, "ggsnamespace": 6, "prop": "imageinfo|coordinates",
        "iiprop": "url|extmetadata|size", "iiurlwidth": 640})
    try:
        d = json.loads(get(u)); ps = (d.get("query") or {}).get("pages") or {}
        toks = [w for w in re.findall(r"[a-z]+", nm.lower()) if w not in GEN]
        rows = []
        for p in ps.values():
            t = p.get("title", ""); tl = t.lower()
            if "iss0" in tl or "view of earth" in tl: continue
            if not ("spring" in tl or any(w in tl for w in toks)): continue
            ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata") or {}
            c = (p.get("coordinates") or [{}])[0]
            rows.append({"title": t, "thumb": ii.get("thumburl"), "page": ii.get("descriptionurl"), "lat": c.get("lat"), "lon": c.get("lon"),
                         "license": (md.get("LicenseShortName") or {}).get("value"), "artist": re.sub("<[^>]+>", "", (md.get("Artist") or {}).get("value") or "")[:120],
                         "desc": re.sub("<[^>]+>", "", (md.get("ImageDescription") or {}).get("value") or "")[:300]})
        if rows: com[f"{gid}|{nm}"] = rows
    except Exception as e: log.append(f"commons {nm}: {e}")
    time.sleep(1.0)
json.dump(com, open("out/commons.json", "w")); log.append(f"commons: {len(com)} of {len(pts)} springs have photos within 400 m")
open("out/log.txt", "w").write("\n".join(log)); print("\n".join(log))
