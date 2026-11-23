"""Water-use permits and water rights near a spring vent."""
import json, math, time, urllib.request, urllib.parse
def _get(url, data=None):
    for a in range(4):
        try: return json.load(urllib.request.urlopen(url, data, timeout=120))
        except Exception as e: err = e; time.sleep(5 * (a + 1))
    raise err
def _q(url, lon, lat, r_m, fields="*", geom=False):
    d = r_m / 111000; kx = math.cos(math.radians(lat))
    q = dict(geometry=f"{lon - d / kx},{lat - d},{lon + d / kx},{lat + d}", geometryType="esriGeometryEnvelope", inSR=4326, outSR=4326,
             spatialRel="esriSpatialRelIntersects", outFields=fields, returnGeometry=str(geom).lower(), f="json")
    return _get(url + "/query", urllib.parse.urlencode(q).encode()).get("features", [])
J = "https://permitting.sjrwmd.com/arcgis02/rest/services/%s/EPermit_CUP/MapServer/%d"
def ms(v):
    if v in (None, ""): return None
    try: return time.strftime("%Y-%m-%d", time.gmtime(v / 1000))
    except Exception: return str(v)
def fl_permits(lon, lat, r_m=400):
    out = []
    for dist, layers in (("SRWMD", [2, 1]), ("SJRWMD", [2, 1]), ("NWFWMD", [1])):
        for L in layers:
            try: fs = _q(J % (dist, L), lon, lat, r_m)
            except Exception: continue
            for f in fs:
                a = f["attributes"]; a = {k.split(".")[-1]: v for k, v in a.items()}
                out.append(dict(agency=dist, id=a.get("OFFCL_PRMT_ID") or a.get("CUR_PRMT_ID"), name=a.get("PRMT_PROJ_NM") or a.get("SITE_NM"),
                                use=a.get("RULE_TYPE_DESC"), status="pending" if L == 1 and dist != "NWFWMD" else (a.get("PRMT_STTS") or "permitted"),
                                holder=a.get("OWNER") or a.get("APPLICANT"), expires=ms(a.get("PRMT_EXPIR_DT")), acres=a.get("PROJ_ACRES")))
    try:
        for f in _q("https://www25.swfwmd.state.fl.us/arcgis12/rest/services/OpenData/RegulatoryPro/MapServer/6", lon, lat, r_m):
            a = f["attributes"]
            if (a.get("WITHDRAWAL_STATUS_DESC") or "").lower().startswith(("inactive", "plugged", "abandon")): continue
            out.append(dict(agency="SWFWMD", id=a.get("WUP_PERMIT_NBR"), name=a.get("PERMITTEE"), use=a.get("WITHDRAWAL_USE_DESC") or a.get("WATER_USE_CLASS_DESC"),
                            status=a.get("WUP_APP_STATUS_DESC"), holder=a.get("OWNERNAME"), gpd=a.get("PERM_AVG_ANNUAL_WD_RATE"), kind=a.get("WITHDRAWAL_TYPE_DESC")))
    except Exception: pass
    seen = set(); res = []
    for p in out:
        k = (p["agency"], p["id"])
        if k not in seen: seen.add(k); res.append(p)
    return res
TCEQ = "https://gisweb.tceq.texas.gov/arcgis/rest/services/WaterRights/WaterRightsViewer/MapServer"
def tx_rights(lon, lat, r_m=800):
    out = []
    for f in _q(TCEQ + "/3", lon, lat, r_m):
        a = f["attributes"]; out.append(dict(agency="TCEQ", id=a.get("WR_ID"), type=a.get("WR_TYPE_NO"), kind=a.get("TYPE")))
    gcd = None
    try:
        q = dict(geometry=f"{lon},{lat}", geometryType="esriGeometryPoint", inSR=4326, spatialRel="esriSpatialRelIntersects", outFields="DISTNAME,GCD_HOME", returnGeometry="false", f="json")
        g = _get(TCEQ + "/6/query?" + urllib.parse.urlencode(q)).get("features", [])
        gcd = g[0]["attributes"] if g else None
    except Exception: pass
    seen = set(); res = []
    for p in out:
        if p["id"] not in seen: seen.add(p["id"]); res.append(p)
    return res, gcd
if __name__ == "__main__":
    print(fl_permits(-82.6619, 29.4885, 1500)[:5])     # Manatee Springs area
    print(fl_permits(-82.6845, 29.8300, 2000)[:5])     # Ginnie Springs area
    print(tx_rights(-98.1253, 29.7140))
