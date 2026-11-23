"""Redfin search boxes covering 400 m on either side of every qualifying trail, minus boxes entirely inside cities over 200k -> boxes.json"""
import glob, json, math, os
import numpy as np, shapely
from shapely.geometry import shape, box
ROOT = os.path.dirname(os.path.abspath(__file__))
DY, DX = 0.04, 0.05
cells = set()
for f in glob.glob(os.path.join(ROOT, "geom", "g*.json")):
    for tid, segs in json.load(open(f)).items():
        for name, c in segs:
            ls = shapely.linestrings(c)
            n = max(2, int(shapely.length(ls) / 0.002) + 1)
            pts = shapely.get_coordinates(shapely.line_interpolate_point(ls, np.linspace(0, 1, n), normalized=True))
            for x, y in pts:
                ex = 0.0037 / math.cos(math.radians(y)); ey = 0.0037
                for cx in range(math.floor((x - ex) / DX), math.floor((x + ex) / DX) + 1):
                    for cy in range(math.floor((y - ey) / DY), math.floor((y + ey) / DY) + 1):
                        cells.add((cx, cy))
big = [shape(c["geom"]) for c in json.load(open(os.path.join(ROOT, "bigcities.json")))]
for g in big: shapely.prepare(g)
tree = shapely.STRtree(big)
out = []
for cx, cy in sorted(cells):
    b = box(cx * DX, cy * DY, (cx + 1) * DX, (cy + 1) * DY)
    if any(big[i].contains(b) for i in tree.query(b)): continue
    out.append([round(cx * DX, 4), round((cx + 1) * DX, 4), round(cy * DY, 4), round((cy + 1) * DY, 4)])
json.dump(out, open(os.path.join(ROOT, "boxes.json"), "w"))
print(len(cells), "cells,", len(out), "outside big-city limits")
