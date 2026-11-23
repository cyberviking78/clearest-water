"""Build the web-site copy of the page for GitHub Pages (cyberviking78/clearest-water): the same page as the claude.ai
artifact, with live street, topo and satellite basemaps under the map's own layers. Outside claude.ai nothing blocks the
basemap images, so this copy works in any browser, phone included.
Writes <out>/index.html only; the map data (map/counties-10m.json, map/nat.json, map/st/, map/hy/) is copied into the
repository once and never changes. Search engines are asked not to list the site (robots meta tag and robots.txt).
Usage: python3 make_site.py <page.html> <repo dir>"""
import sys, os
src, repo = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
tmp = os.path.join(repo, ".index.tmp")
sys.argv = ["make_private.py", src, tmp]
exec(open(os.path.join(here, "make_private.py")).read(), {"__name__": "make_private"})
h = open(tmp).read(); os.remove(tmp)
h = h.replace(" (Private)</title>", "</title>", 1)
old = ("<b>Private copy.</b> Street, topo and satellite maps load from OpenStreetMap, USGS and Esri, so this version opens only for you. "
       "The shareable page has the same layers on a plain map.")
assert old in h
h = h.replace(old, "Street, topo and satellite maps from OpenStreetMap, USGS and Esri: use the switcher in the map's top-right corner. "
                   "Listings refresh on the 1st and 15th of each month.")
HEAD = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="strict-origin-when-cross-origin">'
        '<style>body{margin:0}[hidden]{display:none!important}</style></head><body>')
h = HEAD + h + "</body></html>"
open(os.path.join(repo, "index.html"), "w").write(h)
open(os.path.join(repo, "robots.txt"), "w").write("User-agent: *\nDisallow: /\n")
open(os.path.join(repo, ".nojekyll"), "w").write("")
print("site page written", os.path.join(repo, "index.html"), os.path.getsize(os.path.join(repo, "index.html")) // 1024 // 1024, "MB")
