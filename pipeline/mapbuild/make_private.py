"""Make the private copy of the page: the same page, with street, topo and satellite basemaps under the map's own layers.
The basemap tiles load from outside servers (OpenStreetMap, USGS, Esri), which is why this copy can't be shared publicly;
the main page stays self-contained. Run after every refresh of the main page, then publish both.
Usage: python3 make_private.py <page.html> <page.private.html>"""
import sys
src, dst = sys.argv[1], sys.argv[2]
h = open(src).read()
assert "function geoInit(m){" in h, "run map_detail.py first"
def rep(old, new):
    global h
    assert h.count(old) == 1, old[:80]
    h = h.replace(old, new)

# other water and our own roads step aside when a tile basemap already draws them
rep("geoShow(m,N.rv,wt&&!det); geoShow(m,N.lk,wt&&!det);", "geoShow(m,N.rv,wt&&!det&&!GEO.tiles); geoShow(m,N.lk,wt&&!det&&!GEO.tiles);")
rep("geoShow(m,G.rv,v&&wt&&!hyOn); geoShow(m,G.lk,v&&wt&&!hyOn)", "geoShow(m,G.rv,v&&wt&&!hyOn&&!GEO.tiles); geoShow(m,G.lk,v&&wt&&!hyOn&&!GEO.tiles)")
rep("const v=vis.has(s)&&z>=11&&wt; geoShow(m,G.a,v);", "const v=vis.has(s)&&z>=11&&wt&&!GEO.tiles; geoShow(m,G.a,v);")

PRIV = r"""
<script>
/* ---------- private copy: basemaps from outside servers ---------- */
(function(){
  const BASES={
    "Plain map":null,
    "Streets":()=>L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:"© OpenStreetMap contributors"}),
    "Topo":()=>L.tileLayer("https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}",{maxNativeZoom:16,maxZoom:19,attribution:"USGS The National Map"}),
    "Satellite":()=>L.layerGroup([
      L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",{maxZoom:19,attribution:"Imagery: Esri, Maxar, Earthstar Geographics"}),
      L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",{maxZoom:19,opacity:.9})])};
  function tiles(m){
    if(MAPV.tilesOn)return; MAPV.tilesOn=true;
    m.setMaxZoom(19); const p=m.createPane("tiles"); p.style.zIndex=250;
    const layers={}; Object.entries(BASES).forEach(([k,f])=>{layers[k]=f?f():L.layerGroup()});
    Object.values(layers).forEach(l=>{const each=t=>{if(t.options)t.options.pane="tiles"; if(t.on)t.on("tileerror",()=>{if(!MAPV.tileWarn){MAPV.tileWarn=true;
      const e=document.getElementById("mapcount"); if(e)e.insertAdjacentHTML("afterend",'<span class="hint" style="color:var(--warn)">Some map tiles did not load; switch the basemap or reload.</span>')}})};
      if(l.eachLayer)l.eachLayer(each); else each(l)});
    let cur="Streets"; try{const v=localStorage.getItem("cw-base"); if(v&&layers[v])cur=v}catch(e){}
    const apply=name=>{GEO.tiles=name!=="Plain map"; GEO.baseName=name;
      if(MAPV.base)MAPV.base.setStyle({fillOpacity:GEO.tiles?0:1,opacity:GEO.tiles?.5:1});
      if(MAPV.counties)MAPV.counties.setStyle({opacity:GEO.tiles?0:.8});
      if(typeof styleStates==="function")styleStates();
      const r=document.getElementById("georoad"); if(r)r.checked=!GEO.tiles;
      try{localStorage.setItem("cw-base",name)}catch(e){}
      geoUpdate()};
    m.addLayer(layers[cur]);
    L.control.layers(layers,null,{collapsed:false,position:"topright"}).addTo(m);
    m.on("baselayerchange",e=>apply(e.name));
    const _sb=styleBase; styleBase=function(){_sb(); apply(cur=Object.keys(layers).find(k=>m.hasLayer(layers[k]))||"Plain map")};
    apply(cur);
  }
  const _gi=geoInit; geoInit=function(m){_gi(m); tiles(m)};
  if(MAPV.map)tiles(MAPV.map);
})();
</script>
<style>
.leaflet-control-layers{background:var(--surface);color:var(--ink);border:1px solid var(--rule)!important;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.15)!important;font:13px/1.5 var(--body)}
.leaflet-control-layers-expanded{padding:6px 10px}
.leaflet-control-layers label{display:flex;align-items:center;gap:5px;margin:1px 0}
.privnote{font-size:13px;color:var(--muted);margin:0 0 6px}
</style>"""
rep('<div id="mapwrap" data-mode="map" hidden>',
    '<div id="mapwrap" data-mode="map" hidden>\n  <p class="privnote"><b>Private copy.</b> Street, topo and satellite maps load from OpenStreetMap, USGS and Esri, so this version opens only for you. The shareable page has the same layers on a plain map.</p>')
import re
h = re.sub(r"<title>([^<]*)</title>", lambda m: "<title>" + m.group(1) + " (Private)</title>", h, count=1)
i = h.rindex("</script>") + len("</script>")
h = h[:i] + PRIV + h[i:]
open(dst, "w").write(h)
print("private copy written", dst)
