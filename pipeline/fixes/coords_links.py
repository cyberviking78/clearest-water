"""Spring coordinates you can click (Nov 25, 2026).
Every spring on the Springs tab and every springhead on the Springheads tab shows its vent's coordinates; clicking them opens
Google Maps in a new tab with a pin on that exact point ("satellite" opens the same spot in satellite view, zoomed in).
Each springhead listing also shows the vent's coordinates and a "vent and listing" link that opens Google Maps with both
points pinned (as a walking route), so the vent's position relative to the house or lot is visible at once. The same links
are in the springhead popups on the map.
Which coordinates: springheads use their inventory point (the one the parcel checks use). Florida springs on the Springs tab use
the Florida Springs Institute's survey vent when it matches by name within 300 m, otherwise the spring's own point.
Also tightens fsiFind's name test: "big" and "little" now count as name words, so Little King Spring no longer borrows
Big King Spring's survey (and pipeline/fsi_2026_11/page_edit_fsi.py and match_check.py are changed to match).
renderSprings is rewritten by patch_page.py on every refresh, so its edits are made to patch_page.py's RENDER too.
Idempotent. Usage: coords_links.py page.html [patch_page.py]"""
import os, sys
page = sys.argv[1]; pp = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "patch_page.py")
h = open(page).read()
def rep(old, new, t):
    if new in t: return t
    assert t.count(old) == 1, (t.count(old), old[:100]); return t.replace(old, new)

# ---- Springs tab (patch_page.py RENDER + page) ----
RS = [
 ('''${n} readings · ${yrs} years, ${y0}–${y1}${sites>1?` · ${sites} sites`:""}</small></div>${val(m,a,b)}''',
  '''${n} readings · ${yrs} years, ${y0}–${y1}${sites>1?` · ${sites} sites`:""}${gmSpring(r)}</small></div>${val(m,a,b)}'''),
 ('''${n?`${n} turbidity reading${n>1?"s":""}, ${y0===y1?y0:`${y0}–${y1}`}`:"no turbidity readings on record"}</small></div>''',
  '''${n?`${n} turbidity reading${n>1?"s":""}, ${y0===y1?y0:`${y0}–${y1}`}`:"no turbidity readings on record"}${gmSpring(r)}</small></div>'''),
]
for o, n in RS: h = rep(o, n, h)
P = open(pp).read()
for o, n in RS: P = rep(o, n, P)
open(pp, "w").write(P)

JS = r'''/* ---------- clickable spring coordinates (pipeline/fixes/coords_links.py) ---------- */
const gmF=v=>(+v).toFixed(5);
function gmLink(lat,lon,label){if(lat==null||lon==null)return "";const ll=gmF(lat)+","+gmF(lon);
  return `<span class="gm">${label?label+" ":""}<a href="https://www.google.com/maps/search/?api=1&query=${ll}" target="_blank" rel="noopener" title="Open this point in Google Maps">${gmF(lat)}, ${gmF(lon)}</a> <a class="gm-sat" href="https://www.google.com/maps/@?api=1&map_action=map&center=${ll}&zoom=19&basemap=satellite" target="_blank" rel="noopener" title="Same spot in satellite view">satellite</a></span>`}
function gmBoth(vlat,vlon,lat,lon){if(vlat==null||lat==null)return "";
  return `<a href="https://www.google.com/maps/dir/?api=1&origin=${gmF(lat)},${gmF(lon)}&destination=${gmF(vlat)},${gmF(vlon)}&travelmode=walking" target="_blank" rel="noopener" title="Google Maps with the listing and the vent both pinned">vent and listing on Google Maps</a>`}
function gmSpring(r){let ll=r[18]||[(r[12][1]+r[12][3])/2,(r[12][0]+r[12][2])/2];
  if(r[16]==="FL"&&typeof fsiRow==="function"){const f=fsiRow(r); if(f&&fsiTok(f[2])===fsiTok(r[1])){const cl=Math.cos(ll[0]*Math.PI/180);
    if(Math.hypot((f[0]-ll[0])*111200,(f[1]-ll[1])*111200*cl)<=300)ll=[f[0],f[1]]}}
  return ` · ${gmLink(ll[0],ll[1],"vent")}`}
'''
h = rep("/* ---------- map tab ---------- */", JS + "/* ---------- map tab ---------- */", h)
CSS = '''.gm{white-space:nowrap}.gm a{font-family:var(--mono);font-size:11.5px;color:var(--lake);font-weight:500}.gm a.gm-sat{font-family:var(--body);font-weight:600;margin-left:2px}
.pp-gm{font-size:12px;margin-top:4px}.pp-gm a{color:var(--lake)}
'''
h = rep("/* springheads */", CSS + "/* springheads */", h)

# ---- Springheads tab: the vent on each springhead row, the vent + listing on each listing ----
h = rep('''${pub?" · on public land":""}</small></div><span></span>''',
        '''${pub?" · on public land":""} · ${gmLink(lat,lon,"vent")}</small></div><span></span>''', h)
h = rep('''  const xs=[];
  if(note)xs.push(esc(note[0].toUpperCase()+note.slice(1))+".");''',
        '''  const xs=[], hv=SH.heads[hi];
  if(hv[8]!=null)xs.push(`<span>${gmLink(hv[8],hv[9],"Vent:")} · listing point ${gmLink(lat,lon)} · ${gmBoth(hv[8],hv[9],lat,lon)}</span>`);
  if(note)xs.push(esc(note[0].toUpperCase()+note.slice(1))+".");''', h)

# ---- map popups ----
h = rep('''near the vent</span>`:""}</div>${fsiPop(fsiHead(hd))}''',
        '''near the vent</span>`:""}</div>${fsiPop(fsiHead(hd))}${hd[8]!=null?`<div class="pp-gm">${gmLink(hd[8],hd[9],"Vent:")}<br>${gmBoth(hd[8],hd[9],x[16],x[17])}</div>`:""}''', h)
h = rep('''${fsiPop(fsiFind(l.getLatLng().lat,l.getLatLng().lng,l.options.nm))}<div class="pp-links"></div>''',
        '''${fsiPop(fsiFind(l.getLatLng().lat,l.getLatLng().lng,l.options.nm))}<div class="pp-gm">${gmLink(l.getLatLng().lat,l.getLatLng().lng,"Vent:")}</div><div class="pp-links"></div>''', h)

# ---- fsiFind: "big" and "little" are name words ----
h = h.replace('const FSISTOP=new Set(["spring","springs","main","head","the","big","little","upper",',
              'const FSISTOP=new Set(["spring","springs","main","head","the","upper",')
open(page, "w").write(h); print("coordinate links added")
