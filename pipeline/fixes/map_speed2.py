"""Map speed, part 2 (Nov 23, 2026): the bike-trail lines.
The national trail layer drew every one of its 47,410 trail pieces as its own line, twice (a white casing under each blue line),
so the map handled about 95,000 separate lines and restyled each of them on every zoom; the state-level trail layers did the
same (plus a third copy for the 400 m band). Now each trail network's pieces are drawn as one multi-part line (per network and
surface type, and per named segment at state level, so tooltips and popups read the same), and the national lines are joined end to end and thinned
to about 150 m detail, which is finer than a pixel at the zoom levels where they show (below 8). Idempotent.
Usage: map_speed2.py page.html"""
import sys
page = sys.argv[1]; h = open(page).read()
if "function geoSimp(" in h:
    print("trail drawing already merged"); sys.exit()
def rep(old, new):
    global h
    assert h.count(old) == 1, (h.count(old), old[:100]); h = h.replace(old, new)
rep('''  const nll=d.tr.map(([tid,ty,e])=>geoDec(e,1e4)); nll.forEach(ll=>G.tr.addLayer(geoCasing(ll,z)));
  d.tr.forEach(([tid,ty,e],i)=>G.tr.addLayer(L.polyline(nll[i],{renderer:GEO.top,tid,ty,...geoTrailStyle(ty,z)})));''',
'''  const ng=new Map(); d.tr.forEach(([tid,ty,e])=>{const k=tid+"|"+ty; if(!ng.has(k))ng.set(k,{tid,ty,ll:[]}); ng.get(k).ll.push(geoDec(e,1e4))});
  ng.forEach(g=>{g.ll=geoJoin(g.ll).map(ll=>geoSimp(ll,.0014))});
  ng.forEach(g=>G.tr.addLayer(geoCasing(g.ll,z)));
  ng.forEach(g=>G.tr.addLayer(L.polyline(g.ll,{renderer:GEO.top,tid:g.tid,ty:g.ty,...geoTrailStyle(g.ty,z)})));''')
rep('''  const sll=d.tr.map(([tid,ty,seg,e])=>geoDec(e,1e5)); sll.forEach(ll=>G.tr.addLayer(geoCasing(ll,z)));
  d.tr.forEach(([tid,ty,seg,e],i)=>{const ll=sll[i];G.tr.addLayer(L.polyline(ll,{renderer:GEO.top,tid,ty,seg:seg||null,...geoTrailStyle(ty,z)}));
    G.band.addLayer(L.polyline(ll,{renderer:R.geoBand,interactive:false,color:tc,opacity:1,weight:bw,lineCap:"round",lineJoin:"round"}))});''',
'''  const sg=new Map(); d.tr.forEach(([tid,ty,seg,e])=>{const k=tid+"|"+ty+"|"+(seg||""); if(!sg.has(k))sg.set(k,{tid,ty,seg:seg||null,ll:[]}); sg.get(k).ll.push(geoDec(e,1e5))});
  sg.forEach(g=>G.tr.addLayer(geoCasing(g.ll,z)));
  sg.forEach(g=>{G.tr.addLayer(L.polyline(g.ll,{renderer:GEO.top,tid:g.tid,ty:g.ty,seg:g.seg,...geoTrailStyle(g.ty,z)}));
    G.band.addLayer(L.polyline(g.ll,{renderer:R.geoBand,interactive:false,color:tc,opacity:1,weight:bw,lineCap:"round",lineJoin:"round"}))});''')
rep("function geoGroup(){return L.featureGroup()}",
    "function geoGroup(){return L.featureGroup()}\n"
    "function geoSimp(ll,tol){if(ll.length<3)return ll; return L.LineUtil.simplify(ll.map(p=>L.point(p[1],p[0])),tol).map(p=>[p.y,p.x])}\n"
    "function geoJoin(parts){const key=p=>p[0]+','+p[1], out=[], used=new Array(parts.length).fill(false), byStart=new Map();"
    "parts.forEach((ll,i)=>{const k=key(ll[0]); if(!byStart.has(k))byStart.set(k,[]); byStart.get(k).push(i)});"
    "parts.forEach((ll,i)=>{if(used[i])return; used[i]=true; let cur=ll.slice();"
    "for(;;){const nx=(byStart.get(key(cur[cur.length-1]))||[]).find(j=>!used[j]); if(nx==null)break; used[nx]=true; cur=cur.concat(parts[nx].slice(1))}"
    "out.push(cur)}); return out}")
open(page, "w").write(h); print("trail drawing merged")
