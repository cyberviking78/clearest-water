"""Stream LimnoSat-US (Topp et al. 2020, Zenodo 4139695; Landsat surface reflectance for 56,792 US lakes, 1984-2020) and keep, for each
lake (HydroLakes id), its typical summer colour: the median dominant wavelength (dWL, nm) of cloud-free June-September observations
from 2013-2020 (Landsat 8 era plus Landsat 7), with the number of observations. Writes lake_color.json {hylak_id: [median dWL, n]}.
Usage: curl -sL <csv url> | python3 limnosat_color.py"""
import sys, csv, json, statistics
from collections import defaultdict
v = defaultdict(list); n = 0
r = csv.reader(sys.stdin); h = next(r); I = {k: i for i, k in enumerate(h)}
for row in r:
    n += 1
    if n % 2000000 == 0: print(n, "rows", len(v), "lakes", flush=True, file=sys.stderr)
    try:
        y = int(row[I["year"]]); mo = int(row[I["date"]][5:7])
        if y < 2013 or not 6 <= mo <= 9: continue
        d = float(row[I["dWL"]])
    except Exception: continue
    if 380 <= d <= 700: v[row[I["Hylak_id"]]].append(d)
out = {k: [round(statistics.median(x)), len(x)] for k, x in v.items()}
json.dump(out, open("lake_color.json", "w"), separators=(",", ":"))
print("rows", n, "lakes with summer colour 2013-2020:", len(out), file=sys.stderr)
