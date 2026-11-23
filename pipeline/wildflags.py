"""Creek and pond flags for acreage listings (Old Growth, Rainforest). The lot is taken as a circle of its stated acreage around
the listing's map point (the point is usually the house or the parcel centre, so this is approximate: "likely on the lot").
  creek: a stream or river (TIGER/Line LINEARWATER H3010, or AREAWATER H3010 for wide rivers) crosses that circle -> its name, or ""
  pond:  a lake or pond (AREAWATER H2030 lake/pond, H2040 reservoir) of a quarter acre or more touches it -> its acres (largest)
Census TIGER/Line 2024 county files are downloaded as needed from www2.census.gov and cached in pipeline/.tiger (or $TIGER_CACHE
with aw/<fips>.zip and lw/<fips>.zip already there)."""
import os, math, urllib.request, shapefile, shapely, pyproj
from shapely.geometry import shape, Point
from shapely.ops import transform
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("TIGER_CACHE") or HERE + "/.tiger"
URL = {"aw": "https://www2.census.gov/geo/tiger/TIGER2024/AREAWATER/tl_2024_{}_areawater.zip",
       "lw": "https://www2.census.gov/geo/tiger/TIGER2024/LINEARWATER/tl_2024_{}_linearwater.zip",
       "cty": "https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_county_500k.zip"}
def _get(kind, fips=None):
    d = CACHE + ("/" + kind if fips else ""); os.makedirs(d, exist_ok=True)
    f = f"{d}/{fips}.zip" if fips else f"{CACHE}/county500k.zip"
    if not os.path.exists(f) or os.path.getsize(f) < 100:
        for a in range(3):
            try:
                urllib.request.urlretrieve(URL[kind].format(fips) if fips else URL[kind], f + ".tmp"); os.replace(f + ".tmp", f); break
            except Exception as ex:
                if "404" in str(ex): return None
                import time; time.sleep(5)
        else: return None
    return f
_cty = None
def county_of(lon, lat):
    global _cty
    if _cty is None:
        f = _get("cty"); R = shapefile.Reader(f)
        G = [shape(s.__geo_interface__) for s in R.shapes()]; F = [r["STATEFP"] + r["COUNTYFP"] for r in R.iterRecords()]
        _cty = (shapely.STRtree(G), G, F)
    t, G, F = _cty; p = Point(lon, lat)
    for i in t.query(p):
        if G[i].contains(p): return F[i]
    i = t.nearest(p); return F[i]
_water = {}
def water(fips):
    if fips in _water: return _water[fips]
    lines, polys = [], []
    f = _get("lw", fips)
    if f:
        for sr in shapefile.Reader(f).iterShapeRecords():
            if sr.record["MTFCC"] == "H3010": lines.append((shape(sr.shape.__geo_interface__), (sr.record["FULLNAME"] or "").strip(), "creek"))
    f = _get("aw", fips)
    if f:
        for sr in shapefile.Reader(f).iterShapeRecords():
            m = sr.record["MTFCC"]
            if m not in ("H2030", "H2040", "H3010"): continue
            ac = (sr.record["AWATER"] + sr.record["ALAND"]) / 4046.86
            if m != "H3010" and ac < 0.25: continue
            try: g = shape(sr.shape.__geo_interface__).buffer(0)
            except Exception: continue
            polys.append((g, (sr.record["FULLNAME"] or "").strip(), "creek" if m == "H3010" else "pond", ac))
    G = [x[0] for x in lines] + [x[0] for x in polys]
    _water[fips] = (shapely.STRtree(G) if G else None, lines + polys)
    return _water[fips]
def flags(pts):
    """pts: [(lat, lon, acres)] -> [(creek name, "" for unnamed, or None; pond acres or None)]"""
    out = []
    for lat, lon, acres in pts:
        try:
            t, items = water(county_of(lon, lat))
        except Exception:
            out.append((None, None)); continue
        if t is None: out.append((None, None)); continue
        r = math.sqrt(max(acres or 1, 1) * 4046.86 / math.pi)
        f = pyproj.Transformer.from_crs(4326, pyproj.CRS.from_proj4(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m"), always_xy=True)
        circ = Point(0, 0).buffer(r, 24); deg = r / 111000 / max(math.cos(math.radians(lat)), 0.2)
        creek, pond = None, None
        for i in t.query(Point(lon, lat).buffer(deg * 1.2)):
            it = items[i]; g = transform(f.transform, it[0])
            if not g.intersects(circ): continue
            if it[2] == "creek":
                if creek is None or (not creek and it[1]): creek = it[1]
            else:
                pond = max(pond or 0, round(it[3], 1))
        out.append((creek, pond))
    return out
