"""Temperate rainforest country (misty, big-tree forest with ferns and wildflowers), from PRISM 30-year normals.
  core:    annual precipitation >= 70 in and annual mean temperature 5-15 C (Pacific coast ranges, Olympics, west-slope Cascades,
           Klamath-Siskiyou, north Sierra, southern Appalachian Blue Ridge escarpment and Smokies)
  fog:     coast redwood fog belt, 36.4-42 N within 40 km of the Pacific: >= 40 in and mean 8-16 C
  inland:  inland temperate rainforest (cedar-hemlock wet belt of north Idaho, NE Washington, NW Montana): >= 40 in, mean 3-9.5 C
  cloud:   Appalachian cloud forest (cloud-immersed spruce-fir and northern hardwood highlands, Smokies to the White Mountains):
           >= 50 in and elevation above 1,370 m at 35.5 N, falling 70 m per degree north (about 1,160 m in West Virginia, 760 m in
           the Adirondacks and White Mountains)
  maine:   Downeast Maine fog coast (boreal spruce-fir fog forest east of Penobscot Bay, within 15 km of the sea)
  Southeast Alaska (no PRISM grid here) is added in build: the Tongass boundary plus about 6-11 km.
Sources: PRISM Climate Group, Oregon State University: 1991-2020 annual precipitation normal (800 m), 1981-2010 annual mean
temperature normal (4 km), 800 m elevation grid. Cells are 30 arc-seconds (about 800 m).
Writes zones.geojson (dissolved, simplified polygons with "kind") and rainpts.json (rain in inches and elevation in metres for
every zone cell, keyed by PRISM cell index row*7025+col). Run once; the refresh doesn't need it."""
import numpy as np, json, shapely, shapefile, os, math, pyproj
from shapely.ops import transform
HERE=os.path.dirname(os.path.abspath(__file__))
from shapely.geometry import shape, box, mapping
import rasterio.features, affine
P="/home/claude/geo_src/prism/"
def load(f): a=np.fromfile(P+f,dtype="<f4").reshape(3105,7025); a[a==-9999]=np.nan; return a
X0,Y0,D=-125.016666666666,49.933333665556,0.00833333333
ppt=load("ppt.bil"); tm4=np.fromfile(P+"tmean.bil",dtype="<f4").reshape(621,1405); tm4[tm4==-9999]=np.nan     # PRISM 1981-2010 mean temperature, 4 km
ti=np.clip(np.round((49.916666666669-(Y0-np.arange(3105)*D))/0.041666666667).astype(int),0,620)
tj=np.clip(np.round(((X0+np.arange(7025)*D)+125.0)/0.041666666667).astype(int),0,1404)
tm=tm4[ti][:,tj]
X0,Y0,D=-125.016666666666,49.933333665556,0.00833333333
lat=(Y0-np.arange(3105)*D)[:,None]; lon=(X0+np.arange(7025)*D)[None,:]
with np.errstate(invalid="ignore"):
    core=(ppt>=1778)&(tm>=5)&(tm<=15)
    inland=(lon>-118.6)&(lon<-113.5)&(lat>45.8)&(lat<49.0)&(ppt>=1016)&(tm>=3)&(tm<=9.5)
    dem=np.fromfile(P+"dem800.bil",dtype="<i4").reshape(3105,7025).astype("f4"); dem[dem==-9999]=np.nan   # stored as integer metres
    cloud=(lon>-85)&(lon<-67)&(lat>34.5)&(lat<47.5)&(ppt>=1270)&(dem>=1370-70*(lat-35.5))
    fogbox=(lon<-121.5)&(lat>36.4)&(lat<42.0)&(ppt>=1016)&(tm>=8)&(tm<=16)
# distance to the Pacific for the fog belt: from the California coastline
ca=[shape(s.__geo_interface__) for s,r in zip(shapefile.Reader("/home/claude/geo_src/state500k.zip").shapes(),shapefile.Reader("/home/claude/geo_src/state500k.zip").records()) if r["STUSPS"]=="CA"][0]
ocean=box(-130,30,-117,43).difference(ca.buffer(0.0))
rr,cc=np.nonzero(fogbox); pts=shapely.points(lon[0,cc],lat[rr,0])
d=shapely.distance(pts,ocean)*111*np.cos(np.radians(lat[rr,0]))
fog=np.zeros_like(core); fog[rr[d<=40],cc[d<=40]]=True
me=[shape(s.__geo_interface__) for s,r in zip(shapefile.Reader("/home/claude/geo_src/state500k.zip").shapes(),shapefile.Reader("/home/claude/geo_src/state500k.zip").records()) if r["STUSPS"]=="ME"][0]
mbox=(lon>-69.0)&(lat<45.3)&(lat>43.8)&np.isfinite(ppt)
rr,cc=np.nonzero(mbox); pts=shapely.points(lon[0,cc],lat[rr,0]); inme=shapely.contains(me,pts)
d=shapely.distance(pts,me.boundary)*111*np.cos(np.radians(lat[rr,0]))
ok=inme&(d<=15)&(lon[0,cc]<-66.95)            # the coast, not the inland border with New Brunswick
maine=np.zeros_like(core); maine[rr[ok],cc[ok]]=True
Z=np.zeros(ppt.shape,np.uint8); Z[maine]=5; Z[cloud]=4; Z[inland]=3; Z[fog&~core]=2; Z[core]=1
r_,c_=np.nonzero(Z)               # rain and elevation for every zone cell (and a 3-cell margin), for the listing details
M=np.zeros_like(Z,bool); M[Z>0]=True
from scipy.ndimage import binary_dilation
M=binary_dilation(M,iterations=3)&np.isfinite(ppt)
rr,cc=np.nonzero(M)
ix=(rr*7025+cc).astype(np.int64); o=np.argsort(ix)
json.dump(dict(note="PRISM cells in and around rainforest country: idx delta-encoded (cell = row*7025+col of the 30-arc-second CONUS grid), ppt annual inches, elev metres",
               idx=np.diff(np.concatenate([[0],ix[o]])).tolist(), ppt=np.round(ppt[rr,cc]/25.4).astype(int)[o].tolist(), elev=dem[rr,cc].astype(int)[o].tolist()),
          open(HERE+"/rainpts.json","w"),separators=(",",":"))
T=affine.Affine(D,0,X0-D/2,0,-D,Y0+D/2)
feats=[]
for k,name in ((1,"core"),(2,"fog"),(3,"inland"),(4,"cloud"),(5,"maine")):
    polys=[shape(g) for g,v in rasterio.features.shapes((Z==k).astype(np.uint8),mask=(Z==k),transform=T) if v==1]
    U=shapely.union_all(polys).buffer(0.004).buffer(-0.004)
    U=shapely.MultiPolygon([p for p in getattr(U,"geoms",[U]) if p.area>0.0015]) # drop specks under ~10 km2
    feats.append(dict(type="Feature",properties=dict(kind=name,km2=round(U.area*111*111*0.7)),geometry=mapping(U.simplify(0.006))))
    print(name, len(U.geoms), "pieces", feats[-1]["properties"]["km2"], "km2-ish")
# Southeast Alaska: the Tongass National Forest boundary plus a margin (towns and private land inside and around it)
S=json.load(open(HERE+"/../og/sites.json")); GE=json.load(open(HERE+"/../og/geom.json"))
tg=shape(GE[[i for i,s_ in enumerate(S) if s_["n"]=="Tongass National Forest"][0]])
tg=shapely.MultiPolygon([p for p in tg.simplify(0.01).geoms if p.area>2e-4])
U=shapely.union_all([p.buffer(0.1,3) for p in tg.geoms])         # about 11 km north-south, 6 km east-west
feats.append(dict(type="Feature",properties=dict(kind="alaska",km2=0),geometry=mapping(U.simplify(0.01))))
json.dump(dict(type="FeatureCollection",features=feats),open(HERE+"/zones.geojson","w"))
print("zones.geojson", os.path.getsize(HERE+"/zones.geojson")//1024, "KB; rainpts", os.path.getsize(HERE+"/rainpts.json")//1024, "KB")
