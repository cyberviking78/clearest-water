"""Restore the full-screen map styles (and the .row .nop rule) inside the page's own stylesheet.
They used to sit in the page's <head> style, which the artifact publish replaces, so the Nov 15, 2026 refresh dropped them and
full screen broke (map in half the screen, Filters / Legend panels stuck open). Idempotent.
Usage: restore_css.py page.html"""
import sys
CSS = r"""/* full-screen map (kept in the page's own stylesheet, so republishing can't drop it) */
.mxbtn{font:inherit;font-size:13px;line-height:1.2;padding:6px 12px;border:1px solid var(--rule);border-radius:8px;background:var(--surface);color:var(--ink);cursor:pointer}
.mxbtn:hover{border-color:var(--muted)} .mxbtn[aria-expanded="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
#mapmax{font-weight:600}
.mxbar,#mxfilt{display:none}
.mxleg{display:grid;gap:10px}
#mapwrap.max{position:fixed;inset:0;z-index:1000;margin:0;gap:0;background:var(--bg);display:flex;flex-direction:column;
  padding:env(safe-area-inset-top,0px) env(safe-area-inset-right,0px) env(safe-area-inset-bottom,0px) env(safe-area-inset-left,0px)}
#mapwrap.max .mxbar{display:flex;align-items:center;gap:8px;padding:8px 10px;border-bottom:1px solid var(--rule);flex:none}
#mapwrap.max .mxsp{flex:1} #mapwrap.max .privnote{display:none}
#mapwrap.max #mapmax{display:none}
#mapwrap.max .mxleg,#mapwrap.max #mxfilt{display:none;position:absolute;left:8px;right:8px;top:var(--mxtop,52px);z-index:1002;max-height:min(70vh,560px);overflow:auto;
  background:var(--bg);border:1px solid var(--rule);border-radius:10px;padding:12px 14px;box-shadow:0 8px 28px rgba(0,0,0,.28)}
@media (min-width:900px){#mapwrap.max .mxleg,#mapwrap.max #mxfilt{right:auto;width:560px}}
#mapwrap.max.leg .mxleg,#mapwrap.max.filt #mxfilt{display:grid}
#mxfilt .controls{position:static;border:0;padding:0;background:none}
#mapwrap.max #leafmap{flex:1 1 auto;height:auto;min-height:0;border:0;border-radius:0}
html.mapmax,html.mapmax body{overflow:hidden}
.leaflet-control.mxctl a{font-size:17px;font-weight:700;line-height:30px;text-align:center;text-decoration:none;cursor:pointer}

.row .nop{grid-column:2/-1;font-size:12px;color:var(--muted);margin-top:2px}
"""
p = sys.argv[1]; h = open(p).read()
if "#mapwrap.max{" in h: print("full-screen styles already present"); sys.exit()
k = h.index("<style>\n", h.index("</style>", h.index("fonts from Fontsource")))
h = h[:k + 8] + CSS + h[k + 8:]
open(p, "w").write(h); print("full-screen styles restored")
