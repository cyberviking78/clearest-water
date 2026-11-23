"""Redfin search cells covering 400 m on either side of every qualifying trail, keeping only cells that touch one of the
128 cities over 200k (the Trails tab skips cities; this is the city counterpart) -> boxes.json"""
import glob, json, math, os
import numpy as np, shapely
from shapely.geometry import shape, box
ROOT = os.path.dirname(os.path.abspath(__file__)); TR = os.path.join(os.path.dirname(ROOT), "trails")
DY, DX = 0.04, 0.05
cells = set()
for f in glob.glob(os.path.join(TR, "geom", "g*.json")):
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
big = [shape(c["geom"]) for c in json.load(open(os.path.join(TR, "bigcities.json")))]
for g in big: shapely.prepare(g)
tree = shapely.STRtree(big)
out = []
for cx, cy in sorted(cells):
    b = box(cx * DX, cy * DY, (cx + 1) * DX, (cy + 1) * DY)
    if any(big[i].intersects(b) for i in tree.query(b)):
        out.append([round(cx * DX, 4), round((cx + 1) * DX, 4), round(cy * DY, 4), round((cy + 1) * DY, 4)])
json.dump(out, open(os.path.join(ROOT, "boxes.json"), "w"))
print(len(cells), "trail cells,", len(out), "touch a city over 200k")
