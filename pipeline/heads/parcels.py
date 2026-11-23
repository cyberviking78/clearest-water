"""Parcel polygon at a point, for states with public statewide parcels."""
import json, time, urllib.request, urllib.parse
from shapely.geometry import shape, Point
SRC = {
    "AR": ("query", "https://gis.arkansas.gov/arcgis/rest/services/FEATURESERVICES/Planning_Cadastre/FeatureServer/6",
           dict(id="parcelid", owner="ownername", addr="adrlabel", acres=None, county="county")),
    "FL": ("query", "https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer/0",
           dict(id="PARCEL_ID", owner="OWN_NAME", addr="PHY_ADDR1", acres=None, county="CO_NO")),
    "TX": ("identify", "https://feature.geographic.texas.gov/arcgis/rest/services/Parcels/stratmap_land_parcels_48_most_recent/MapServer",
           dict(id="prop_id", owner="owner_name", addr="situs_addr", acres="gis_area", county="county")),
}
def _get(url, data=None):
    for a in range(4):
        try:
            return json.load(urllib.request.urlopen(url, data, timeout=120))
        except Exception as e:
            err = e; time.sleep(5 * (a + 1))
    raise err
def _poly(geom):
    if "rings" in geom:
        from shapely.geometry import Polygon, MultiPolygon
        from shapely.ops import unary_union
        polys = [Polygon(r) for r in geom["rings"] if len(r) >= 4]
        # rings: outer + holes mixed; union of all outers minus holes approximated by symmetric difference
        g = polys[0]
        for p in polys[1:]:
            g = g.symmetric_difference(p)
        return g.buffer(0)
    return shape(geom).buffer(0)
UT = "https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/Parcels_%s/FeatureServer/0"
def parcels_at(st, lon, lat, tol_m=0, county=None):
    """Return [(geom, attrs)] for parcels at (or within tol_m of) the point."""
    if st == "UT" and county:
        c = county.replace(" County", "").replace(" ", "")
        kind, url, F = "query", UT % c, dict(id="PARCEL_ID", owner="OWNER", addr="PARCEL_ADD", acres=None, county="COUNTY_NAME")
    elif st not in SRC: return None
    else: kind, url, F = SRC[st]
    d = tol_m / 111000
    if kind == "query":
        geom = f"{lon},{lat}" if not tol_m else f"{lon-d},{lat-d},{lon+d},{lat+d}"
        q = dict(geometry=geom, geometryType="esriGeometryPoint" if not tol_m else "esriGeometryEnvelope", inSR=4326, outSR=4326,
                 spatialRel="esriSpatialRelIntersects", outFields="*", returnGeometry="true", f="json")
        r = _get(url + "/query", urllib.parse.urlencode(q).encode())
        feats = [(f["geometry"], f["attributes"]) for f in r.get("features", []) if f.get("geometry")]
    else:
        q = dict(geometry=f"{lon},{lat}", geometryType="esriGeometryPoint", sr=4326, layers="all:0", tolerance=max(1, int(tol_m / 3)) if tol_m else 0,
                 mapExtent=f"{lon-0.01},{lat-0.01},{lon+0.01},{lat+0.01}", imageDisplay="600,600,96", returnGeometry="true", f="json")
        r = _get(url + "/identify?" + urllib.parse.urlencode(q))
        feats = [(x["geometry"], x["attributes"]) for x in r.get("results", []) if x.get("geometry")]
    out = []
    for g, a in feats:
        a = {k.split(".")[-1]: v for k, v in a.items()}
        lk = {k.lower(): v for k, v in a.items()}
        out.append((_poly(g), dict(id=lk.get(F["id"].lower()), owner=lk.get(F["owner"].lower()), addr=lk.get(F["addr"].lower()), county=lk.get(F["county"].lower()))))
    return out
if __name__ == "__main__":
    for st, p in [("TX", (-98.1253, 29.7140)), ("AR", (-91.5404, 36.4961))]:
        r = parcels_at(st, *p); print(st, [(round(g.area * 1e8), a) for g, a in r])
