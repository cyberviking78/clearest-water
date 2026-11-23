"""Add the "Dark night skies" overlay to the map: light-pollution zones 0, 1 and 2 shaded (the darkest skies), switched on
from the map's "Map detail" bar, and a "Night sky" line in every map popup giving the listing's zone. Data: sky.json from
build_sky.py (David Lorenz's Light Pollution Atlas 2025). Idempotent: re-running only refreshes the SKY data.
Usage: sky_tab.py page.html sky.json"""
import json, re, sys
page, sp = sys.argv[1], sys.argv[2]
h = open(page).read()
data = "const SKY=" + json.dumps(json.load(open(sp)), separators=(",", ":")) + ";\n"
if 'id="geosky"' in h:
    h = re.sub(r"const SKY=\{.*?\};\n", lambda m: data, h, count=1, flags=re.S)
    open(page, "w").write(h); print("night sky data refreshed"); sys.exit()
def rep(old, new, count=1):
    global h
    assert h.count(old) == count, f"{h.count(old)}x: {old[:120]}"
    h = h.replace(old, new)
# ---- colors: violet, a hue no other layer uses
rep("--ml-water:#1557d6;", "--ml-water:#1557d6; --sky:#4b1a8c;")
rep("--ml-water:#5b8cff;", "--ml-water:#5b8cff; --sky:#c9a8ff;", count=2)
CSS = """
/* dark night skies */
.lg i.sky0,.lg i.sky1,.lg i.sky2{border-radius:3px;border:0;box-shadow:none}
.lg i.sky0{background:color-mix(in srgb,var(--sky) 62%,transparent)} .lg i.sky1{background:color-mix(in srgb,var(--sky) 42%,transparent)} .lg i.sky2{background:color-mix(in srgb,var(--sky) 20%,transparent)}
.skyleg[hidden]{display:none}
.sky-ln{margin:6px 0 2px;font-size:12.5px;color:var(--muted)} .sky-ln b{color:var(--ink)}
"""
rep(".mc.mlc{", CSS + ".mc.mlc{")
# ---- the switch, in the Map detail bar
rep('<label><input id="georoad" type="checkbox" checked> Roads and towns</label>',
    '<label><input id="georoad" type="checkbox" checked> Roads and towns</label><label><input id="geosky" type="checkbox"> <b>Dark night skies</b></label>'
    '<span class="skyleg" hidden><span class="lg"><i class="sky0"></i>Zone 0, pristine</span> <span class="lg"><i class="sky1"></i>Zone 1, near-pristine</span> '
    '<span class="lg"><i class="sky2"></i>Zone 2, excellent</span></span>')
# ---- notes
rep("""  <h2>About the map</h2>""", """  <h2>About the map</h2>""")
i = h.index("<h2>About the map</h2>"); j = h.index("</section>", i)
NOTE = """  <p><b>Dark night skies.</b> Switch on <i>Dark night skies</i> under the map to shade the darkest skies in the country, and click any listing to see its night-sky zone. The zones come from David Lorenz's Light Pollution Atlas 2025 (University of Wisconsin), which models the artificial glow straight overhead from 2025 satellite night-light data; each zone is 3 times brighter than the one before. Shaded: <b>zone 0</b>, pristine (darker than 21.99 magnitudes per square arcsecond on a sky-quality meter); <b>zone 1</b>, near-pristine (21.89 to 21.99); and, lighter, <b>zone 2</b>, excellent (21.69 to 21.89). Zones 0 and 1 are what light-pollution maps such as lightpollution.app label Bortle 1 and 2, and zone 2 Bortle 3. Lorenz cautions that his maps are not the Bortle scale: Bortle judges the whole sky by eye, including light domes from towns on the horizon, so a dark zenith can still have a glowing horizon. Each map cell is about a mile across and shows the brightest part of it, so a dark cell is dark throughout. The atlas is updated about once a year.</p>
"""
h = h[:j] + NOTE + h[j:]
rep('const SRC=[', 'const SRC=[\n ["David Lorenz, Light Pollution Atlas 2025 (University of Wisconsin): artificial night sky brightness at zenith from 2025 VIIRS night lights","https://djlorenz.github.io/astronomy/lp/"],')
# ---- data + code
JS = data + r"""const SKYN=["0","1a","1b","2a","2b","3a","3b","4a","4b","5a","5b","6a","6b","7a","7b"],
  SKYW=["pristine","near-pristine","near-pristine","excellent","excellent","rural, some glow","rural, some glow","rural-suburban","rural-suburban","suburban","suburban","bright suburban","bright suburban","city","city"],
  SKYM=["darker than 21.99","21.93–21.99","21.89–21.93","21.81–21.89","21.69–21.81","21.51–21.69","21.25–21.51","20.91–21.25","20.49–20.91","20.02–20.49","19.50–20.02","18.95–19.50","18.38–18.95","17.80–18.38","brighter than 17.80"];
const SKYD={};
function skyLoad(){
  if(!SKYD.p)SKYD.p=(async()=>{for(const [k,g] of Object.entries(SKY)){const s=atob(g.b), u=new Uint8Array(s.length); for(let i=0;i<s.length;i++)u[i]=s.charCodeAt(i);
    SKYD[k]=new Uint8Array(await new Response(new Blob([u]).stream().pipeThrough(new DecompressionStream("gzip"))).arrayBuffer())}})();
  return SKYD.p}
function skyAt(lat,lon){for(const k in SKY){const g=SKY[k],a=SKYD[k]; if(!a)continue; const c=Math.floor((lon-g.w)*g.res), r=Math.floor((g.n-lat)*g.res);
  if(c>=0&&c<g.cols&&r>=0&&r<g.rows){const v=a[r*g.cols+c]; if(v<15)return v}} return null}
function skyCanvas(k,rgb){   // the zone grid redrawn in web-mercator rows, so it lines up with the map at every latitude
  const g=SKY[k],a=SKYD[k],s=g.n-g.rows/g.res,e=g.w+g.cols/g.res,my=l=>Math.log(Math.tan(Math.PI/4+l*Math.PI/360)),y0=my(g.n),y1=my(s);
  const W=g.cols,H=Math.round(W*(y0-y1)/((e-g.w)*Math.PI/180)),cv=document.createElement("canvas"); cv.width=W; cv.height=H;
  const ctx=cv.getContext("2d"),im=ctx.createImageData(W,H),d=im.data,AL=[158,108,108,52,52];
  for(let y=0;y<H;y++){const lat=(2*Math.atan(Math.exp(y0-(y+.5)/H*(y0-y1)))-Math.PI/2)*180/Math.PI, r=Math.min(g.rows-1,Math.max(0,Math.floor((g.n-lat)*g.res)));
    for(let x=0;x<W;x++){const v=a[r*W+x]; if(v<5){const o=(y*W+x)*4; d[o]=rgb[0];d[o+1]=rgb[1];d[o+2]=rgb[2];d[o+3]=AL[v]}}}
  ctx.putImageData(im,0,0); return [cv,[[s,g.w],[g.n,e]]]}
function skyUpdate(){
  const m=MAPV.map, on=document.getElementById("geosky").checked; document.querySelector(".skyleg").hidden=!on;
  if(MAPV.sky){MAPV.sky.forEach(l=>m.removeLayer(l)); MAPV.sky=null}
  if(!on||!m)return;
  skyLoad().then(()=>{if(!document.getElementById("geosky").checked||MAPV.sky)return;
    const c=document.createElement("canvas").getContext("2d"); c.fillStyle=tok("--sky")||"#4b1a8c"; const hx=c.fillStyle, rgb=[1,3,5].map(i=>parseInt(hx.substr(i,2),16));
    MAPV.sky=Object.keys(SKY).map((k,i)=>{const [cv,b]=skyCanvas(k,rgb); return L.svgOverlay(cv,b,{pane:"geoSky",interactive:false,attribution:i?"":"Night sky: Light Pollution Atlas 2025, D. Lorenz"}).addTo(m)})
  }).catch(()=>{document.querySelector(".skyleg").innerHTML="<span class='hint'>This browser can't draw the night-sky layer. Try a current Chrome, Safari, Edge or Firefox.</span>"})}
function skyInit(m){
  const p=m.createPane("geoSky"); p.style.zIndex=310; p.style.pointerEvents="none";
  document.getElementById("geosky").addEventListener("change",skyUpdate);
  const re=()=>{if(document.getElementById("geosky").checked)skyUpdate()};
  try{matchMedia("(prefers-color-scheme: dark)").addEventListener("change",re)}catch(e){}
  try{new MutationObserver(re).observe(document.documentElement,{attributes:true,attributeFilter:["data-theme"]})}catch(e){}
  m.on("popupopen",e=>{const ll=e.popup.getLatLng(), pp=e.popup;
    skyLoad().then(()=>{const el=pp.getElement(), c=el&&el.querySelector(".leaflet-popup-content"); if(!c||c.querySelector(".sky-ln"))return;
      const v=skyAt(ll.lat,ll.lng); if(v==null)return;
      const html=`<div class="sky-ln">Night sky: <b>zone ${SKYN[v]}</b>, ${SKYW[v]} · ${SKYM[v]} mag/arcsec²</div>`, box=c.querySelector(".pp-links");
      box?box.insertAdjacentHTML("beforebegin",html):c.insertAdjacentHTML("beforeend",html)}).catch(()=>{})});
  if(document.getElementById("geosky").checked)skyUpdate();
}
"""
rep("function geoInit(m){", JS + "function geoInit(m){")
# popups that already carry their own Satellite link (Old Growth, Rainforest, Mountain Lakes) don't get a second one
rep('if(!box||box.querySelector(".sat"))return; const ll=e.popup.getLatLng();', 'if(!box||box.querySelector(".sat,.sv"))return; const ll=e.popup.getLatLng(), hs=box.querySelector(\'a[href*="basemap=satellite"]\');')
rep('box.insertAdjacentHTML("beforeend",`<a class="alt sat" href="https://www.google.com/maps/@?api=1&map_action=map&center=${la},${lo}&zoom=18&basemap=satellite" target="_blank" rel="noopener">Satellite view</a><a class="alt" href=',
    'box.insertAdjacentHTML("beforeend",`${hs?"":`<a class="alt sat" href="https://www.google.com/maps/@?api=1&map_action=map&center=${la},${lo}&zoom=18&basemap=satellite" target="_blank" rel="noopener">Satellite view</a>`}<a class="alt sv" href=')
rep("  geoInit(m);\n", "  geoInit(m); skyInit(m);\n")
open(page, "w").write(h); print("night sky overlay added")
