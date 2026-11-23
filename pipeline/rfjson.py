"""Drop-in replacement for Redfin's gis-csv download.

Redfin's CSV export leaves out listings from MLSs whose rules don't allow downloads (central Indiana's MIBOR,
NorthstarMLS, Canopy, NWMLS and many more), so whole metros come back nearly empty. The same search through Redfin's
map-data endpoint (/stingray/api/gis, with mpt=99 so the filters and polygon are honored) returns every listing.
fetch_csv(url) takes the usual gis-csv URL, runs it against the map-data endpoint and returns text in the CSV layout the
pipelines already parse (same header and column positions), so nothing downstream changes.
"""
import csv, io, json, urllib.request
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
HEADER = ["SALE TYPE", "SOLD DATE", "PROPERTY TYPE", "ADDRESS", "CITY", "STATE OR PROVINCE", "ZIP OR POSTAL CODE", "PRICE", "BEDS", "BATHS",
          "LOCATION", "SQUARE FEET", "LOT SIZE", "YEAR BUILT", "DAYS ON MARKET", "$/SQUARE FEET", "HOA/MONTH", "STATUS",
          "NEXT OPEN HOUSE START TIME", "NEXT OPEN HOUSE END TIME", "URL", "SOURCE", "MLS#", "FAVORITE", "INTERESTED", "LATITUDE", "LONGITUDE"]
TYPES = {1: "Single Family Residential", 2: "Condo/Co-op", 3: "Townhouse", 4: "Multi-Family (2-4 Unit)", 5: "Vacant Land", 6: "Other",
         7: "Mobile/Manufactured Home", 8: "Co-op", 13: "Ranch"}
def _v(x):
    return x.get("value") if isinstance(x, dict) else x
def to_json_url(csv_url):
    u = csv_url.replace("/stingray/api/gis-csv?", "/stingray/api/gis?")
    return u if "mpt=" in u else u + "&mpt=99"
def fetch_csv(csv_url, timeout=90):
    raw = urllib.request.urlopen(urllib.request.Request(to_json_url(csv_url), headers={"User-Agent": UA, "Accept": "application/json"}),
                                 timeout=timeout).read().decode("utf-8", "replace")
    if not raw.startswith("{}&&"):
        raise RuntimeError("unexpected response: " + raw[:100].replace("\n", " "))
    d = json.loads(raw[4:])
    if d.get("resultCode") not in (0, None):
        raise RuntimeError("Redfin error: " + str(d.get("errorMessage"))[:100])
    out = io.StringIO(); w = csv.writer(out, lineterminator="\n"); w.writerow(HEADER)
    for h in (d.get("payload") or {}).get("homes", []):
        ll = _v(h.get("latLong")) or {}
        price = _v(h.get("price")); addr = _v(h.get("streetLine"))
        if price is None or not addr or ll.get("latitude") is None: continue
        unit = _v(h.get("unitNumber"))
        w.writerow(["MLS Listing", "", TYPES.get(h.get("uiPropertyType"), "Other"), f"{addr} {unit}".strip() if unit and unit not in addr else addr,
                    h.get("city") or "", h.get("state") or "", _v(h.get("postalCode")) or h.get("zip") or "", price, h.get("beds") if h.get("beds") is not None else "",
                    h.get("baths") if h.get("baths") is not None else "", _v(h.get("location")) or "", _v(h.get("sqFt")) or "", _v(h.get("lotSize")) or "",
                    _v(h.get("yearBuilt")) or "", _v(h.get("dom")) if _v(h.get("dom")) is not None else "", _v(h.get("pricePerSqFt")) or "", _v(h.get("hoa")) or "",
                    h.get("mlsStatus") or "", "", "", "https://www.redfin.com" + (h.get("url") or ""), "", _v(h.get("mlsId")) or "", "", "",
                    ll["latitude"], ll["longitude"]])
    return out.getvalue()
