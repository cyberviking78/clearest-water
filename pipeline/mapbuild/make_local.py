"""Build the stand-alone copy of the page: one .html file to open in a browser, with street, topo and satellite basemaps.
Artifact pages can't load images from other websites (the claude.ai viewer blocks them), so the basemaps only work when the
page is opened straight from a file. Everything the map needs is packed into the file: county outlines, the national layer
and every state's detail. The close-up creek-and-pond layer is left out (the street and topo maps already draw water).
Usage: python3 make_local.py <page.html> <map dir> <out.html>"""
import sys, os, json, re
src, mapdir, dst = sys.argv[1:4]
here = os.path.dirname(os.path.abspath(__file__))
sys.argv = ["make_private.py", src, dst + ".tmp"]
exec(open(os.path.join(here, "make_private.py")).read(), {"__name__": "make_private"})
h = open(dst + ".tmp").read(); os.remove(dst + ".tmp")
h = h.replace(" (Private)</title>", " (with satellite maps)</title>", 1)
h = h.replace("<b>Private copy.</b> Street, topo and satellite maps load from OpenStreetMap, USGS and Esri, so this version opens only for you. The shareable page has the same layers on a plain map.",
              "<b>Copy with street, topo and satellite maps.</b> Use the switcher in the map's top-right corner. The street, topo and satellite images load from OpenStreetMap, USGS and Esri, so you need an internet connection. Listings are as of the date this file was made; the shared page has the latest.")
def blob(path):
    t = open(path).read()
    json.loads(t)                                   # validate
    return t.replace("</", "<\\/")
parts = ['<script type="application/json" id="geo-map/counties-10m.json">' + blob(os.path.join(mapdir, "counties-10m.json")) + "</script>",
         '<script type="application/json" id="geo-map/nat.json">' + blob(os.path.join(mapdir, "nat.json")) + "</script>"]
for f in sorted(os.listdir(os.path.join(mapdir, "st"))):
    parts.append(f'<script type="application/json" id="geo-map/st/{f}">' + blob(os.path.join(mapdir, "st", f)) + "</script>")
SHIM = """<script>
/* file copy: answer the page's map-data requests from the data packed into this file */
(function(){const real=window.fetch?window.fetch.bind(window):null;
  window.fetch=function(u,o){if(typeof u==="string"&&u.indexOf("map/")===0){const e=document.getElementById("geo-"+u);
    if(!e)return Promise.resolve({ok:false,status:404,json:()=>Promise.reject(new Error("not packed"))});
    return Promise.resolve({ok:true,status:200,json:()=>Promise.resolve(JSON.parse(e.textContent))})}
    return real?real(u,o):Promise.reject(new Error("no fetch"))};})();
</script>"""
# data blocks and the shim go before the page's first script so they exist when the map asks for them
i = h.index("<script>")
h = h[:i] + "\n".join(parts) + "\n" + SHIM + "\n" + h[i:]
if not h.lstrip().lower().startswith("<!doctype"):
    h = ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
         '<style>body{margin:0}[hidden]{display:none!important}</style></head><body>' + h + "</body></html>")
open(dst, "w").write(h)
print("file copy written", dst, os.path.getsize(dst) // 1024 // 1024, "MB")
