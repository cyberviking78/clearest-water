"""Trails in royal blue with a thin contrasting casing, so they read on the street, topo and satellite basemaps
(the old lime/green line was hard to see; brown would clash with the roads). Idempotent. Usage: trail_color.py <page.html>"""
import sys
p = sys.argv[1]; h = open(p).read()
if "--trail-case" in h: print("already applied"); sys.exit()
def rep(old, new, n=1):
    global h
    assert h.count(old) == n, (h.count(old), old[:90]); h = h.replace(old, new)
rep("--trail:#2e7d3a; --trail-soft:#e2f2e4;", "--trail:#2347c8; --trail-soft:#e3e9fb; --trail-case:#ffffff;")
rep("--trail:#7fd38b; --trail-soft:#1b3420;", "--trail:#7d96ff; --trail-soft:#1c2445; --trail-case:#0b1020;", 2)
rep('''function geoTrailStyle(ty,z){const c=tok("--trail");return {color:c,weight:geoTW(z),opacity:ty==="u"?.7:.95,''',
    '''function geoTrailStyle(ty,z){const c=tok("--trail");return {color:c,weight:geoTW(z),opacity:ty==="u"?.8:1,''')
rep('''function geoTrailTip(l){''', '''const GEO_CASE=2.4;
function geoCasing(ll,z){return L.polyline(ll,{renderer:GEO.top,interactive:false,casing:1,color:tok("--trail-case"),weight:geoTW(z)+GEO_CASE,opacity:.85,lineCap:"round",lineJoin:"round"})}
function geoTrailTip(l){''')
rep('''  d.tr.forEach(([tid,ty,e])=>G.tr.addLayer(L.polyline(geoDec(e,1e4),{renderer:GEO.top,tid,ty,...geoTrailStyle(ty,z)})));''',
    '''  const nll=d.tr.map(([tid,ty,e])=>geoDec(e,1e4)); nll.forEach(ll=>G.tr.addLayer(geoCasing(ll,z)));
  d.tr.forEach(([tid,ty,e],i)=>G.tr.addLayer(L.polyline(nll[i],{renderer:GEO.top,tid,ty,...geoTrailStyle(ty,z)})));''')
rep('''  d.tr.forEach(([tid,ty,seg,e])=>{const ll=geoDec(e,1e5);G.tr.addLayer(L.polyline(ll,{renderer:GEO.top,tid,ty,seg:seg||null,...geoTrailStyle(ty,z)}));''',
    '''  const sll=d.tr.map(([tid,ty,seg,e])=>geoDec(e,1e5)); sll.forEach(ll=>G.tr.addLayer(geoCasing(ll,z)));
  d.tr.forEach(([tid,ty,seg,e],i)=>{const ll=sll[i];G.tr.addLayer(L.polyline(ll,{renderer:GEO.top,tid,ty,seg:seg||null,...geoTrailStyle(ty,z)}));''')
rep('''  const set=g=>g&&g.eachLayer(l=>l.setStyle({weight:w}));''', '''  const set=g=>g&&g.eachLayer(l=>l.setStyle({weight:l.options.casing?w+GEO_CASE:w}));''')
rep('''  gs.forEach(g=>{if(m.hasLayer(g))g.bringToBack()})}''', '''  gs.forEach(g=>{if(!m.hasLayer(g))return; const ls=[]; g.eachLayer(l=>ls.push(l)); ls.reverse().forEach(l=>l.bringToBack&&l.bringToBack())})}  // reverse so each group keeps its own drawing order (trail casings under the trails)''')
open(p, "w").write(h); print("trail colour updated")
