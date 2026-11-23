"""Search Redfin for only the waters added on 2026-11-20 and merge them into listings.json / seen.json / meta.json without
touching other waters' results (they are recorded as already seen, so nothing is flagged new on the page). Then patch the page.
Usage: run_new.py <page.html>"""
import json, os, sys, datetime
ROOT = "/home/claude/live/pipeline"; sys.path.insert(0, ROOT)
import run, patch_page
import pandas as pd
page = sys.argv[1]; TAG = "2026-11-20"
states = sorted({st for st, L in run.P.items() for e in L if e.get("added") == TAG})
for st in states:
    for e in run.P[st]:
        if e.get("added") != TAG: e["skip"] = True
frames = []
for st in states:
    df = run.run_state(st); print(st, len(df), flush=True); frames.append(df)
df = pd.concat([f for f in frames if not f.empty], ignore_index=True)
df.to_pickle(ROOT + "/lakequality_2026_11/out/new_listings.pkl")
P = json.load(open(ROOT + "/props.json"))
LS = json.load(open(ROOT + "/listings.json")); seen = json.load(open(ROOT + "/seen.json")); meta = json.load(open(ROOT + "/meta.json"))
TODAY = datetime.date.today().isoformat()
num = lambda x, nd=0: None if pd.isna(x) else (round(float(x), nd) if nd else int(round(float(x))))
newidx = {st: {i for i, e in enumerate(P[st]) if e.get("added") == TAG} for st in states}
for st in states: LS[st] = [x for x in LS.get(st, []) if x[0] not in newidx[st]]
have = {x[12] for v in LS.values() for x in v}
added = 0
for r in df.sort_values(["tier", "dist"], na_position="last").itertuples():
    u = str(r.url).replace("https://www.redfin.com", "")
    first = seen.get(r.url, [TODAY])[0]
    LS.setdefault(r.st, []).append([int(r.wi), int(r.tier), int(r.price), "l" if str(r.type).startswith("Vacant") else "h",
        num(r.beds), num(r.baths, 1), num(r.sqft), None if pd.isna(r.lot) else round(float(r.lot) / 43560, 2),
        str(r.addr), str(r.city), num(r.dom), num(r.dist), u, bool(r.flag), first, False,
        None if pd.isna(r.lat) else round(float(r.lat), 5), None if pd.isna(r.lon) else round(float(r.lon), 5)])
    seen.setdefault(r.url, [first, TODAY]); added += 1
for st in states: LS[st].sort(key=lambda x: (x[0], x[1], x[2]))
urls = set(meta.get("urls", [])) | set(df.url)
meta.update(n=sum(len(v) for v in LS.values()), urls=sorted(urls))
json.dump(seen, open(ROOT + "/seen.json", "w"), separators=(",", ":"))
json.dump(meta, open(ROOT + "/meta.json", "w"), separators=(",", ":"))
json.dump(LS, open(ROOT + "/listings.json", "w"), separators=(",", ":"), ensure_ascii=False)
patch_page.patch(page, LS, {k: v for k, v in meta.items() if k != "urls"})
print("DONE", added, "listing rows on", len(set(zip(df.st, df.wi))), "new waters; total", meta["n"], flush=True)
