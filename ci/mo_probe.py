"""One-off: Springs of Missouri books (text by page) and Wikimedia Commons photos near Missouri springs."""
import json, os, subprocess, urllib.parse, urllib.request, time
os.makedirs("out/books", exist_ok=True)
def get(u, out=None):
    r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "ClearestWater/1.0 (github.com/cyberviking78/clearest-water)"}), timeout=180)
    b = r.read()
    if out: open(out, "wb").write(b)
    return b
log = []
for name, u in [("WR29", "https://share.mo.gov/nr/mgs/MGSData/Books/Water%20Resources/Springs%20of%20Missouri/WR29revised.pdf"),
                ("V029", "https://share.mo.gov/nr/mgs/MGSData/Books/Volumes/The%20Large%20Springs%20of%20Missouri/V-029.pdf")]:
    try:
        get(u, f"out/books/{name}.pdf"); n = int(subprocess.run(["pdfinfo", f"out/books/{name}.pdf"], capture_output=True, text=True).stdout.split("Pages:")[1].split()[0])
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
for gid, nm, lat, lon, mag in pts:
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "format": "json", "generator": "geosearch",
        "ggscoord": f"{lat}|{lon}", "ggsradius": 400, "ggslimit": 20, "ggsnamespace": 6, "prop": "imageinfo|coordinates",
        "iiprop": "url|extmetadata|size", "iiurlwidth": 640})
    try:
        d = json.loads(get(u)); ps = (d.get("query") or {}).get("pages") or {}
        rows = []
        for p in ps.values():
            ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata") or {}
            c = (p.get("coordinates") or [{}])[0]
            rows.append({"title": p.get("title"), "thumb": ii.get("thumburl"), "page": ii.get("descriptionurl"), "lat": c.get("lat"), "lon": c.get("lon"),
                         "license": (md.get("LicenseShortName") or {}).get("value"), "artist": (md.get("Artist") or {}).get("value"),
                         "desc": ((md.get("ImageDescription") or {}).get("value") or "")[:300]})
        if rows: com[f"{gid}|{nm}"] = rows
    except Exception as e: log.append(f"commons {nm}: {e}")
    time.sleep(0.15)
json.dump(com, open("out/commons.json", "w")); log.append(f"commons: {len(com)} of {len(pts)} springs have photos within 400 m")
open("out/log.txt", "w").write("\n".join(log)); print("\n".join(log))
