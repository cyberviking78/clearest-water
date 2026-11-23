"""Monthly waterfront-listing refresh for the Clearest Water by State page.

Usage: python3 run.py <page.html> [--states IN MI] [--baseline]
(--states reruns only those groups and keeps the rest; --baseline records them without marking anything new;
 the group "FS" is Florida springs and spring-fed rivers)   (run from any directory; needs pandas, shapely)

1. For each lake/river in props.json, pull Redfin listings ($100k-750k, houses + land) in its map area (every box in "boxes"
   when present, which covers the whole mapped shoreline), once with Redfin's waterfront filter and once without, four
   searches at a time via prefetch.py into pipeline/wcsv/ (boxes over Redfin's 350 cap are split in four, twice).
2. Keep listings whose lot reaches the USGS shoreline in shore/<ST>.json ("on"), or MLS-waterfront
   listings within 600 m more ("near"; not for waters marked "on_only", the Great Lakes shorelines).
3. Compare with seen.json to mark listings first seen this run as new, and count ones gone since last run.
4. Write listings.json + meta.json, update seen.json, and patch the page via patch_page.py.
"""
import io, json, math, os, random, sys, time, urllib.parse, urllib.request, datetime
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import rfjson
from shapely.geometry import shape, Point
from shapely.ops import transform
from shapely.validation import make_valid

ROOT = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(ROOT, "props.json")))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
COLS = dict(type=2, addr=3, city=4, zip=6, price=7, beds=8, baths=9, sqft=11, lot=12, year=13, dom=14, url=20, src=21, lat=25, lon=26)
TODAY = datetime.date.today().isoformat()


def redfin(b, wf):
    w, e, s, n = b
    poly = urllib.parse.quote(f"{w} {s},{e} {s},{e} {n},{w} {n},{w} {s}")
    url = ("https://www.redfin.com/stingray/api/gis-csv?al=1&min_price=100000&max_price=750000&num_homes=350"
           f"&ord=redfin-recommended-asc&page_number=1&poly={poly}&sf=1,2,3,5,6,7&status=9&uipt=1,5&v=8" + ("&wf=true" if wf else ""))
    for attempt in range(4):
        try:
            body = rfjson.fetch_csv(url)   # Redfin map-data feed; the CSV export hides listings from MLSs that bar downloads
            if body.startswith("SALE TYPE"):
                time.sleep(2.5 + random.random() * 2)
                return body
            raise RuntimeError("non-CSV response: " + body[:120].replace("\n", " "))
        except Exception as ex:
            print(f"  redfin attempt {attempt+1}: {ex}", flush=True)
            time.sleep(30 * (attempt + 1))
    raise RuntimeError("Redfin unreachable after retries")


def frame(body):
    d = pd.read_csv(io.StringIO(body))
    d = d[d.iloc[:, 3].notna() & d.iloc[:, 7].notna()]
    return pd.DataFrame({k: d.iloc[:, v].values for k, v in COLS.items()})


LOCAL = os.environ.get("LOCAL_CSV")  # rebuild from saved downloads instead of calling Redfin


def fetch(b, wf, key=None):
    if LOCAL and key:
        f = os.path.join(LOCAL, "csv" if wf else "csv_all", f"{key[0]}_{key[1]}.csv")
        return frame(open(f).read()) if os.path.exists(f) and os.path.getsize(f) else pd.DataFrame(columns=list(COLS))
    body = redfin(b, wf)
    if body.count("\n") < 350:
        return frame(body)
    w, e, s, n = b; mx, my = (w + e) / 2, (s + n) / 2
    parts = [frame(redfin(q, wf)) for q in [(w, mx, s, my), (mx, e, s, my), (w, mx, my, n), (mx, e, my, n)]]
    return pd.concat(parts, ignore_index=True).drop_duplicates("url")


def allowance(row, flagged):
    lot = row.lot
    a = min(600.0, 60.0 + math.sqrt(lot * 0.092903)) if pd.notna(lot) and lot > 0 else (150.0 if str(row.type).startswith("Vacant") else 90.0)
    return a if flagged else a - 30


def run_state(st):
    shore = json.load(open(os.path.join(ROOT, "shore", f"{st}.json")))
    out = []
    for i, e in enumerate(P[st]):
        if e.get("skip"): continue      # not clear enough for the property search (rivers over 3 NTU, lakes under 15 ft)
        q = json.loads(urllib.parse.unquote(e["z"].split("=", 1)[1]))["mapBounds"]
        b = (q["west"], q["east"], q["south"], q["north"])
        # "boxes" (when present) covers the whole mapped shoreline: the station box first, then grid cells along the shore
        bl = [tuple(x) for x in e.get("boxes", [])] or [b]
        keys = [(st, i if k == 0 else f"{i}_{k}") for k in range(len(bl))]
        wf = pd.concat([fetch(bb, True, kk) for bb, kk in zip(bl, keys)], ignore_index=True).drop_duplicates("url")
        al = pd.concat([fetch(bb, False, kk) for bb, kk in zip(bl, keys)], ignore_index=True).drop_duplicates("url")
        d = pd.concat([wf, al], ignore_index=True).drop_duplicates("url")
        if d.empty:
            continue
        d["flag"] = d.url.isin(set(wf.url))
        g = shore.get(f"{st}_{i}")
        lat0 = e["lat"]; kx = 111320 * math.cos(math.radians(lat0)); ky = 110540
        proj = lambda x, y, z=None: ((x - e["lon"]) * kx, (y - lat0) * ky)
        if g and g.get("geom"):
            geom = transform(proj, make_valid(shape(g["geom"])))
            for r in d.itertuples(index=False):
                if pd.isna(r.lat) or pd.isna(r.lon):
                    continue
                dist = geom.distance(Point(proj(r.lon, r.lat)))
                a = allowance(r, r.flag)
                if dist <= a:
                    out.append(dict(r._asdict(), st=st, wi=i, dist=round(dist), tier=0))
                elif r.flag and dist <= a + 600 and not e.get("on_only"):   # Great Lakes shorelines keep only listings on the lake
                    out.append(dict(r._asdict(), st=st, wi=i, dist=round(dist), tier=1))
        else:
            for r in d[d.flag].itertuples(index=False):
                out.append(dict(r._asdict(), st=st, wi=i, dist=None, tier=2))
    df = pd.DataFrame(out)
    if df.empty:
        return df
    return df.sort_values(["tier", "dist"], na_position="last").drop_duplicates("url").sort_values(["wi", "tier", "price"])


def main():
    global LOCAL
    if not LOCAL:   # fetch every search four at a time first (resumable), then build from the saved files
        import prefetch
        out = os.path.join(ROOT, "wcsv"); n, nf = prefetch.run(P, out)
        if nf > 0.03 * n:
            raise RuntimeError(f"Redfin unreachable: {nf} of {n} searches failed")
        LOCAL = out
        if os.environ.get("PULL_ONLY"):
            print("PULL ONLY: searches saved", flush=True); return
    args = sys.argv[1:]
    page = args[0]
    baseline_states = "--baseline" in args
    args = [a for a in args if a != "--baseline"]
    states = args[args.index("--states") + 1:] if "--states" in args else list(P)
    frames = []
    for st in states:
        t = time.time(); df = run_state(st); frames.append(df)
        print(f"{st}: {len(df)} listings ({time.time()-t:.0f}s)", flush=True)
    df = pd.concat([f for f in frames if not f.empty], ignore_index=True)

    seen_path = os.path.join(ROOT, "seen.json")
    seen = json.load(open(seen_path)) if os.path.exists(seen_path) else {}
    meta_path = os.path.join(ROOT, "meta.json")
    prev_meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    prev_date = prev_meta.get("prev") if prev_meta.get("date") == TODAY else prev_meta.get("date")   # same-day rerun keeps the real previous run
    prev_urls = set(prev_meta.get("urls", []))
    baseline = not seen

    def num(x, nd=0):
        return None if pd.isna(x) else (round(float(x), nd) if nd else int(round(float(x))))
    LS = {}
    ls_path = os.path.join(ROOT, "listings.json")
    if set(states) != set(P) and os.path.exists(ls_path):
        LS = {k: v for k, v in json.load(open(ls_path)).items() if k not in states}   # keep groups not rerun
    kept_urls = {"https://www.redfin.com" + x[12] for v in LS.values() for x in v}
    for r in df.itertuples():
        first = seen.get(r.url, [TODAY])[0]
        is_new = (not baseline) and (not baseline_states) and r.url not in seen
        LS.setdefault(r.st, []).append([int(r.wi), int(r.tier), int(r.price), "l" if str(r.type).startswith("Vacant") else "h",
            num(r.beds), num(r.baths, 1), num(r.sqft), None if pd.isna(r.lot) else round(float(r.lot) / 43560, 2),
            str(r.addr), str(r.city), num(r.dom), num(r.dist), str(r.url).replace("https://www.redfin.com", ""), bool(r.flag),
            first, is_new, None if pd.isna(r.lat) else round(float(r.lat), 5), None if pd.isna(r.lon) else round(float(r.lon), 5)])
        seen[r.url] = [first, TODAY]
    cur = set(df.url) | kept_urls
    if baseline_states and set(states) != set(P) and prev_meta.get("date"):
        TODAY_ = prev_meta["date"]; prev_date = prev_meta.get("prev")   # adding a group doesn't count as a new monthly run
    else:
        TODAY_ = TODAY
    meta = dict(date=TODAY_, prev=prev_date, n=sum(len(v) for v in LS.values()), new=sum(x[15] for v in LS.values() for x in v),
                gone=len(prev_urls - cur) if prev_urls else 0, urls=sorted(cur))
    json.dump(seen, open(seen_path, "w"), separators=(",", ":"))
    json.dump(meta, open(meta_path, "w"), separators=(",", ":"))
    json.dump(LS, open(os.path.join(ROOT, "listings.json"), "w"), separators=(",", ":"), ensure_ascii=False)
    import patch_page
    patch_page.patch(page, LS, {k: v for k, v in meta.items() if k != "urls"})
    print(f"DONE {TODAY}: {meta['n']} listings, {meta['new']} new since {prev_date}, {meta['gone']} gone", flush=True)


if __name__ == "__main__":
    sys.path.insert(0, ROOT)
    main()
