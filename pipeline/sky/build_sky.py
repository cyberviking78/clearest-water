"""Dark night skies overlay (run once a year, when David Lorenz publishes a new atlas).
Source: Light Pollution Atlas 2025, David Lorenz (University of Wisconsin), https://djlorenz.github.io/astronomy/lp/ --
artificial sky brightness at zenith modelled from 2025 VIIRS night lights, 1/120 degree, North America image
(NorthAmerica2025.png, 7N-75N, 180W-51W). Each colour is one light-pollution zone: 0, 1a, 1b, 2a, 2b ... 7b.
Writes sky.json: per region a zone grid (one byte per cell, 15 = outside the US), gzip + base64, at 1/60 degree
(the brighter of each 2x2 block, so a cell is never shown darker than any part of it).
Usage: build_sky.py NorthAmerica2025.png state500k.zip"""
import sys, io, gzip, base64, json, zipfile, numpy as np, shapefile, shapely
from shapely.geometry import shape
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
COLS = [(0,0,0),(34,34,34),(66,66,66),(20,47,114),(33,84,216),(15,87,20),(31,161,42),(110,100,30),(184,166,37),(191,100,30),(253,150,80),(251,90,73),(251,153,138),(160,160,160),(242,242,242)]
a = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(np.int32)
key = a[..., 0] * 65536 + a[..., 1] * 256 + a[..., 2]
Z = np.full(key.shape, 255, np.uint8)
for i, c in enumerate(COLS): Z[key == c[0] * 65536 + c[1] * 256 + c[2]] = i
print("unmatched pixels:", int((Z == 255).sum())); Z[Z == 255] = 0
X0, Y0, R = -180.0, 75.0, 120
z = zipfile.ZipFile(sys.argv[2]); n = [x for x in z.namelist() if x.endswith(".shp")][0][:-4]
sf = shapefile.Reader(shp=io.BytesIO(z.read(n + ".shp")), dbf=io.BytesIO(z.read(n + ".dbf")), shx=io.BytesIO(z.read(n + ".shx")))
ST = {r.record["STUSPS"]: shape(r.shape.__geo_interface__) for r in sf.iterShapeRecords()}
REG = {"conus": ([-125.0, 24.0, -66.5, 49.5], [k for k in ST if k not in ("AK", "HI", "PR", "VI", "GU", "MP", "AS")]),
       "ak": ([-170.0, 51.0, -129.5, 71.5], ["AK"]), "hi": ([-160.5, 18.5, -154.5, 22.5], ["HI"])}
out = {}
for name, ((w, s, e, nn), sts) in REG.items():
    land = shapely.union_all([ST[k] for k in sts]); shapely.prepare(land)
    c0, c1 = round((w - X0) * R), round((e - X0) * R); r0, r1 = round((Y0 - nn) * R), round((Y0 - s) * R)
    sub = Z[r0:r1, c0:c1]; h, wd = sub.shape[0] // 2, sub.shape[1] // 2
    g = sub[:h * 2, :wd * 2].reshape(h, 2, wd, 2).max(axis=(1, 3))
    lon = w + (np.arange(wd) + .5) / 60; lat = nn - (np.arange(h) + .5) / 60
    LO, LA = np.meshgrid(lon, lat)
    inside = shapely.contains_xy(land.buffer(0.02), LO, LA)        # a little past the shoreline, so lakeshore and coastal lots are covered
    g = np.where(inside, g, 15).astype(np.uint8)
    b = base64.b64encode(gzip.compress(g.tobytes(), 9)).decode()
    out[name] = dict(w=w, n=nn, res=60, cols=int(wd), rows=int(h), b=b)
    print(name, g.shape, "zones:", {int(k): int(v) for k, v in zip(*np.unique(g[g < 15], return_counts=True))}, len(b) // 1024, "KB")
json.dump(out, open("sky.json", "w"), separators=(",", ":"))
