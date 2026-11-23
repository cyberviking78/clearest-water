"""Oceanfront, step 2: satellite water clarity in front of each piece of open-ocean coast (runs on GitHub: NOAA's ERDDAP
server isn't reachable from everywhere).
Data: NOAA CoastWatch, S-NPP VIIRS Kd490 (diffuse attenuation of blue light, m^-1; lower is clearer), science quality.
  Atlantic: U.S. East Coast 750 m annual composites (noaacwecnNPPVIIRSSQkd490EastCoastAnnual), 2015-2025.
  Pacific: global 4 km monthly composites (noaacwNPPVIIRSSQkd490Monthly), 2021-2025 (no 750 m West Coast product exists).
Each pixel's typical value is its median over those years; each coast piece takes the median of the pixels found seaward of
it (along the open-sea bearing and 25 degrees either side; 1-3 km out on the Atlantic, 4-8 km on the Pacific where pixels are
coarser). Input coast_all.json (build_coast.py); output kd.json {piece id: Kd490 median}."""
import json, math, os, sys, io, time, urllib.request, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
E = "https://coastwatch.noaa.gov/erddap/griddap/"
DS = {"A": ("noaacwecnNPPVIIRSSQkd490EastCoastAnnual", "2015-01-01", "2025-12-31", "level", 0.00617, (1, 2, 3)),
      "P": ("noaacwNPPVIIRSSQkd490Monthly", "2021-01-01", "2025-12-31", "altitude", 0.0375, (4, 6, 8))}
C = [[r[0], r[1], r[6][len(r[6]) // 2][0], r[6][len(r[6]) // 2][1], r[7], r[8]] for r in json.load(open(HERE + "/coast_all.json"))]   # [id, st, lon, lat, arc, bearing]
PAC = {"CA", "OR", "WA"}
def get(url):
    for a in range(5):
        try: return urllib.request.urlopen(url, timeout=300).read().decode()
        except Exception as ex:
            err = str(ex)
            if "HTTP Error 404" in err or "HTTP Error 400" in err: return None
            time.sleep(10 * (a + 1))
    print("failed", url[:160], err, flush=True); return None
def tile(reg, la0, lo0):
    ds, t0, t1, lev, res, _ = DS[reg]
    la1, lo1 = la0 + 1.1, lo0 + 1.1; la0, lo0 = la0 - 0.1, lo0 - 0.1      # a little overlap so pieces near a tile edge find pixels
    for a, b in ((la0, la1), (la1, la0)):
        q = f"{E}{ds}.csv0?kd_490[({t0}T00:00:00Z):({t1}T00:00:00Z)][0][({a}):({b})][({lo0}):({lo1})]"
        t = get(q)
        if t: break
    if not t: return None
    vals = collections.defaultdict(list)
    for line in t.splitlines():
        p = line.split(",")
        if len(p) < 5: continue
        try: v = float(p[4])
        except ValueError: continue
        if not (0.005 < v < 6): continue
        vals[(round(float(p[2]), 5), round(float(p[3]), 5))].append(v)
    return {k: float(np.median(v)) for k, v in vals.items()}
tiles = collections.defaultdict(list)
for r in C:
    reg = "P" if r[1] in PAC else "A"
    tiles[(reg, math.floor(r[3]), math.floor(r[2]))].append(r)
print(len(tiles), "one-degree tiles", flush=True)
KD = {}
for n, ((reg, la0, lo0), rows) in enumerate(sorted(tiles.items())):
    g = tile(reg, la0, lo0)
    if not g: print("no data", reg, la0, lo0, flush=True); continue
    res = DS[reg][4]; dists = DS[reg][5]
    idx = {(round(la / res), round(lo / res)): v for (la, lo), v in g.items()}
    for r in rows:
        lon, lat, brg = r[2], r[3], r[5]; k = math.cos(math.radians(lat)); found = []
        for d in dists:
            for off in (-25, 0, 25):
                a = math.radians(brg + off)
                x = lon + math.sin(a) * d / 111.0 / k; y = lat + math.cos(a) * d / 111.0
                v = idx.get((round(y / res), round(x / res)))
                if v is not None: found.append(v)
        if found: KD[r[0]] = round(float(np.median(found)), 4)
    print(n + 1, "of", len(tiles), reg, la0, lo0, len(g), "pixels", flush=True)
json.dump(KD, open(HERE + "/kd.json", "w"))
print("KD DONE", len(KD), "of", len(C), "pieces", flush=True)
