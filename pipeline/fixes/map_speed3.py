"""Map speed, part 3 (Nov 23, 2026): the full-screen map on a high-resolution screen.
The map's lines (trails, roads, waters, the 400 m band...) are painted on about eight see-through drawing layers stacked on top
of each other. Each one was 80% wider and taller than the map itself (so a drag didn't show blank edges), and on a screen
that scales by 1.5 (a 4K monitor at 150%) the mapping library doubles every layer again. In full screen on a 2560 x 1440
display that made each layer about 9,200 x 5,000 pixels (46 million pixels, ~185 MB of graphics memory) and the browser
had to move and repaint several of them on every drag and zoom, which is why full screen lagged and the small map didn't.
Now the extra margin shrinks as the map gets bigger (the small map keeps its wide margin; full screen uses 10%), and each
layer is drawn at the screen's real sharpness (1.5, not 2), capped at about 9 million pixels per layer.
Idempotent. Usage: map_speed3.py page.html"""
import sys
page = sys.argv[1]; h = open(page).read()
if "_cwFix" in h:
    print("canvas sizing already fixed"); sys.exit()
OLD = "function geoInit(m){\n"
assert h.count(OLD) == 1, h.count(OLD)
NEW = OLD + (
    "  if(!L.Canvas.prototype._cwFix){L.Canvas.prototype._cwFix=1;\n"
    "    // size each drawing layer for the map's real size and the screen's real sharpness (see pipeline/fixes/map_speed3.py)\n"
    "    L.Canvas.prototype._update=function(){if(this._map._animatingZoom&&this._bounds)return;\n"
    "      if(this._padBase==null)this._padBase=this.options.padding; const ms=this._map.getSize(), a=Math.max(1,ms.x*ms.y);\n"
    "      this.options.padding=Math.max(.1,Math.min(this._padBase,(Math.sqrt(5.2e6/a)-1)/2));\n"
    "      L.Renderer.prototype._update.call(this);\n"
    "      const b=this._bounds,c=this._container,s=b.getSize(),r=Math.max(1,Math.min(window.devicePixelRatio||1,Math.sqrt(9e6/Math.max(1,s.x*s.y))));\n"
    "      L.DomUtil.setPosition(c,b.min); c.width=Math.round(r*s.x); c.height=Math.round(r*s.y); c.style.width=s.x+\"px\"; c.style.height=s.y+\"px\";\n"
    "      this._ctx.scale(c.width/s.x,c.height/s.y); this._ctx.translate(-b.min.x,-b.min.y); this.fire(\"update\")}}\n")
h = h.replace(OLD, NEW)
open(page, "w").write(h); print("canvas sizing fixed")
