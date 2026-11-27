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
for name, urls in [("WR29", ["https://share.mo.gov/nr/mgs/MGSData/Books/Water%20Resources/Springs%20of%20Missouri/WR29revised.pdf",
                               "http://share.mo.gov/nr/mgs/MGSData/Books/Water%20Resources/Springs%20of%20Missouri/WR29revised.pdf"]),
                ]:
    try:
        ok = False
        for u in urls:
            r = curl(u, f"out/books/{name}.pdf"); log.append(f"{name} {u}: {r}")
            if os.path.exists(f"out/books/{name}.pdf") and open(f"out/books/{name}.pdf", "rb").read(5) == b"%PDF-": ok = True; break
        if not ok: continue
        n = int(subprocess.run(["pdfinfo", f"out/books/{name}.pdf"], capture_output=True, text=True).stdout.split("Pages:")[1].split()[0])
        pages = []
        for p in range(1, n + 1):
            pages.append(subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), f"out/books/{name}.pdf", "-"], capture_output=True, text=True).stdout)
        json.dump(pages, open(f"out/books/{name}_pages.json", "w"))
        im = subprocess.run(["pdfimages", "-list", f"out/books/{name}.pdf"], capture_output=True, text=True).stdout
        open(f"out/books/{name}_images.txt", "w").write(im)
        log.append(f"{name}: {n} pages, {sum(len(p) for p in pages)} chars, {im.count(chr(10))} image rows, {os.path.getsize(f'out/books/{name}.pdf')} bytes")
        os.remove(f"out/books/{name}.pdf") if os.path.getsize(f"out/books/{name}.pdf") > 90e6 else None
    except Exception as e: log.append(f"{name}: {e}")
pts = json.load(open("ci/mo_pts.json")); com = {}
import re
GEN = {"spring", "springs", "big", "blue", "cave", "cold", "mill", "the", "upper", "lower", "little", "rise", "of"}
for gid, nm, lat, lon, mag in pts:
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "format": "json", "generator": "geosearch",
        "ggscoord": f"{lat}|{lon}", "ggsradius": 600, "ggslimit": 200, "ggsnamespace": 6, "prop": "imageinfo|coordinates",
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
# Wikidata: springs in Missouri with an image
q = """SELECT ?item ?itemLabel ?coord ?image WHERE { ?item wdt:P31/wdt:P279* wd:Q124714; wdt:P131* wd:Q1581; wdt:P625 ?coord.
 OPTIONAL { ?item wdt:P18 ?image } SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }"""
try:
    d = json.loads(get("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"})))
    json.dump(d["results"]["bindings"], open("out/wikidata.json", "w")); log.append(f"wikidata: {len(d['results']['bindings'])} springs")
except Exception as e: log.append(f"wikidata: {e}")
json.dump(com, open("out/commons.json", "w")); log.append(f"commons: {len(com)} of {len(pts)} springs have photos within 400 m")
open("out/log.txt", "w").write("\n".join(log)); print("\n".join(log))
