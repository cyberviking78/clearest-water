"""Turbidity and station records from the Water Quality Portal around each candidate spring (vents' box + ~600 m), since 2000."""
import json, os, re, subprocess, urllib.parse, time, sys
import re
key = lambda c: re.sub(r"\W+", "_", c["lead"][2])
C = json.load(open("cands.json")); os.makedirs("cache/wqp", exist_ok=True)
for i, c in enumerate(C):
    la = [v[0] for v in c["vents"]]; lo = [v[1] for v in c["vents"]]
    bb = f"{min(lo)-.007:.4f},{min(la)-.006:.4f},{max(lo)+.007:.4f},{max(la)+.006:.4f}"
    for kind in ("Result", "Station"):
        out = f"cache/wqp/{kind}_{key(c)}.csv"
        if os.path.exists(out) and os.path.getsize(out) > 0: continue
        url = (f"https://www.waterqualitydata.us/data/{kind}/search?bBox={bb}&characteristicName=Turbidity&mimeType=csv"
               + ("&startDateLo=01-01-2000&dataProfile=narrowResult" if kind == "Result" else ""))
        for t in range(3):
            p = subprocess.run(["curl", "-s", "-m", "300", "-o", out, "-w", "%{http_code}", url], capture_output=True, text=True)
            if p.stdout == "200": break
            time.sleep(5)
        print(i, kind, p.stdout, os.path.getsize(out) if os.path.exists(out) else 0, flush=True)
