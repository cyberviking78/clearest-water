"""Counties of interest: counties within reach of a ranked water, springhead, qualifying trail or current listing."""
import json, glob, shapefile, shapely, numpy as np
from shapely.geometry import shape
P="/home/claude/live/pipeline"
sf=shapefile.Reader("/vsizip/x") if False else shapefile.Reader("/home/claude/geo_src/county500k.zip")
C=[(r.record["GEOID"], r.record["STUSPS"], shape(r.shape.__geo_interface__)) for r in sf.iterShapeRecords()]
cg=[c[2] for c in C]; tree=shapely.STRtree(cg)
hit={}
def mark(geoms, why, buf):
    gs=shapely.buffer(np.array(geoms,dtype=object), buf) if buf else np.array(geoms,dtype=object)
    a,b=tree.query(gs, predicate="intersects")
    for j in set(b.tolist()): hit.setdefault(C[j][0],set()).add(why)
# trails
tl=[]
for f in glob.glob(P+"/trails/geom/g*.json"):
    for tid,Lg in json.load(open(f)).items():
        for n,c in Lg:
            if len(c)>1: tl.append(shapely.LineString(c))
mark(tl,"trail",0.005)
# ranked waters
ws=[]
for f in glob.glob(P+"/shore/*.json"):
    for k,v in json.load(open(f)).items():
        if v.get("geom"): ws.append(shape(v["geom"]))
mark(ws,"water",0.02)
H=json.load(open(P+"/heads/heads.json"))
mark([shapely.Point(h["lon"],h["lat"]) for h in H],"spring",0.02)
print(len(C),"counties;",len(hit),"of interest")
import collections; print(collections.Counter(w for v in hit.values() for w in v))
json.dump(sorted(hit), open("coi.json","w"))
