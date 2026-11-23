"""Lighter map drawing (Nov 23, 2026). The Oceanfront layer added 4,808 one-kilometre coast pieces as separate lines, and the Wild
Lakes layer draws ~360 detailed lake outlines; the map redraws every shape on each zoom, so it had become sluggish.
  - clear open-ocean coast: drawn from OC.M (each state's coast joined into long, simplified lines: ~17 layers instead of 4,808);
  - wild-lake outlines: only from zoom 8 in (they're smaller than a pixel further out; the listing markers show where they are).
oc_tab.py builds new pages the same way; this patch updates a page that already has the tab. Idempotent. Usage: map_speed.py page.html"""
import sys
page = sys.argv[1]; h = open(page).read()
def rep(old, new):
    global h
    if new in h: return
    assert h.count(old) == 1, (h.count(old), old[:100]); h = h.replace(old, new)
rep('''    if(!MAPV.ocP)MAPV.ocP=OC.P.map(p=>[p[0],geoDec(p[2],1e4)]);
    MAPV.ocP.forEach(([st,ll])=>{if(!s||st===s)L.polyline(ll,{color:ol,weight:4,opacity:.85,interactive:false}).addTo(MAPV.ocA)});''',
    '''    if(!MAPV.ocP)MAPV.ocP=OC.M?OC.M.map(([st,ls])=>[st,ls.map(e=>geoDec(e,1e4))]):OC.P.map(p=>[p[0],[geoDec(p[2],1e4)]]);
    MAPV.ocP.forEach(([st,ll])=>{if(!s||st===s)L.polyline(ll,{color:ol,weight:4,opacity:.85,interactive:false}).addTo(MAPV.ocA)});''')
rep("m.addLayer(MAPV.mlA); ", "")
rep("m.addLayer(MAPV.mll); m.addLayer(MAPV.ocA);",
    "m.addLayer(MAPV.mll); m.addLayer(MAPV.ocA);\n  const mlGate=()=>{const on=m.getZoom()>=8; if(on&&!m.hasLayer(MAPV.mlA))m.addLayer(MAPV.mlA); else if(!on&&m.hasLayer(MAPV.mlA))m.removeLayer(MAPV.mlA)}; m.on(\"zoomend\",mlGate); mlGate();")
open(page, "w").write(h); print("map drawing lightened")
