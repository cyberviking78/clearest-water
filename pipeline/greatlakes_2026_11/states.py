"""Bolder state outlines. They used to sit under the street/topo/satellite tiles (and were pale grey on the plain map), so on
the web copy you mostly saw the basemap's own faint borders. Now a separate outline layer sits above the basemap: dark on
Streets and Topo, white on Satellite, mid-grey on the plain map. Idempotent. Usage: states.py <page.html> [make_private.py]"""
import sys
p = sys.argv[1]; h = open(p).read()
def rep(t, old, new):
    assert t.count(old) == 1, (t.count(old), old[:80]); return t.replace(old, new)
if "function stLineStyle" not in h:
    h = rep(h, "--map-line:#c4d2d4;", "--map-line:#c4d2d4; --map-state:#71848a;")
    assert h.count("--map-line:#2c3f42;") == 2; h = h.replace("--map-line:#2c3f42;", "--map-line:#2c3f42; --map-state:#7e979d;")
    h = rep(h, '''[["geoBase",200],["geoWater",320]''', '''[["geoBase",200],["geoStates",300],["geoWater",320]''')
    h = rep(h, '''if(p==="geoLabel"||p==="geoBand"||p==="geoBase")e.style.pointerEvents="none";''', '''if(p==="geoLabel"||p==="geoBand"||p==="geoBase"||p==="geoStates")e.style.pointerEvents="none";''')
    h = rep(h, '''      MAPV.counties=L.geoJSON(topojson.feature(t,t.objects.counties),{interactive:false,pane:"geoBase"});''',
               '''      MAPV.counties=L.geoJSON(topojson.feature(t,t.objects.counties),{interactive:false,pane:"geoBase"});
      MAPV.stl=L.geoJSON(topojson.mesh(t,t.objects.states),{interactive:false,pane:"geoStates",style:stLineStyle}).addTo(m);''')
    h = rep(h, '''function styleBase(){''', '''// state outlines: their own layer above any basemap
function stLineStyle(){const b=GEO.tiles?(GEO.baseName||"Streets"):"";
  if(b==="Satellite")return {color:"#ffffff",weight:2,opacity:.9,fill:false};
  if(b)return {color:"#2a2e4a",weight:2.4,opacity:.8,fill:false};
  return {color:tok("--map-state"),weight:1.4,opacity:1,fill:false}}
function styleStates(){if(MAPV.stl)MAPV.stl.setStyle(stLineStyle())}
function styleBase(){''')
    h = rep(h, '''  if(MAPV.counties)MAPV.counties.setStyle({color:tok("--map-line"),weight:.5,opacity:.8,fill:false});
}''', '''  if(MAPV.counties)MAPV.counties.setStyle({color:tok("--map-line"),weight:.5,opacity:.8,fill:false});
  styleStates();
}''')
    open(p, "w").write(h); print("page: state outlines updated")
if len(sys.argv) > 2:
    q = sys.argv[2]; s = open(q).read()
    if "GEO.baseName" not in s:
        s = rep(s, '''    const apply=name=>{GEO.tiles=name!=="Plain map";''', '''    const apply=name=>{GEO.tiles=name!=="Plain map"; GEO.baseName=name;''')
        s = rep(s, '''      if(MAPV.counties)MAPV.counties.setStyle({opacity:GEO.tiles?0:.8});''', '''      if(MAPV.counties)MAPV.counties.setStyle({opacity:GEO.tiles?0:.8});
      if(typeof styleStates==="function")styleStates();''')
        open(q, "w").write(s); print("make_private.py updated")
