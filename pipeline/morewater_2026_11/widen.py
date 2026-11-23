"""Search each water's whole mapped shoreline, not just the box around its sampling station.
For every lake or river whose shore/channel (shore/<ST>.json) runs past its search box, add "boxes": the original box plus grid
cells (0.15 deg lon x 0.12 deg lat) that touch the shoreline buffered by ~1.5 km (listings count up to ~1.2 km from shore).
run.py and prefetch_water.py search every box in "boxes" when present. The Zillow links widen to the whole shoreline too."""
import json, math, os, sys, urllib.parse
import shapely
from shapely.geometry import shape, box
P_PATH = "/home/claude/live/pipeline/props.json"; SH = "/home/claude/live/pipeline/shore"
P = json.load(open(P_PATH))
DX, DY = 0.15, 0.12
def zurl(b, att):
    fs = {"sort": {"value": "globalrelevanceex"}, "price": {"min": 100000, "max": 750000}, "tow": {"value": False}, "mf": {"value": False},
          "con": {"value": False}, "apa": {"value": False}, "apco": {"value": False}, "manu": {"value": False}}
    if att: fs["att"] = {"value": att}
    s = json.dumps({"pagination": {}, "isMapVisible": True, "isListVisible": True, "mapBounds": {"west": b[0], "east": b[1], "south": b[2], "north": b[3]}, "filterState": fs}, separators=(",", ":"))
    return "https://www.zillow.com/homes/for_sale/?searchQueryState=" + urllib.parse.quote(s, safe="")
changed = {}; ncells = 0
for st, L in P.items():
    S = json.load(open(f"{SH}/{st}.json"))
    for i, e in enumerate(L):
        g = S.get(f"{st}_{i}", {}).get("geom")
        if not g: continue
        q = json.loads(urllib.parse.unquote(e["z"].split("=", 1)[1]))["mapBounds"]
        ob = [q["west"], q["east"], q["south"], q["north"]]
        G = shape(g); w, s, E, n = G.bounds
        if max(ob[0] - w, E - ob[1], ob[2] - s, n - ob[3]) <= 0.005: continue
        zone = G.buffer(0.015)
        cells = []
        for cx in range(math.floor(zone.bounds[0] / DX), math.floor(zone.bounds[2] / DX) + 1):
            for cy in range(math.floor(zone.bounds[1] / DY), math.floor(zone.bounds[3] / DY) + 1):
                b = box(cx * DX, cy * DY, (cx + 1) * DX, (cy + 1) * DY)
                if b.intersects(zone):
                    c = b.intersection(zone).bounds        # shrink each cell to the shore zone inside it
                    if c[2] - c[0] < 0.01: c = ((c[0] + c[2]) / 2 - 0.005, c[1], (c[0] + c[2]) / 2 + 0.005, c[3])
                    if c[3] - c[1] < 0.01: c = (c[0], (c[1] + c[3]) / 2 - 0.005, c[2], (c[1] + c[3]) / 2 + 0.005)
                    cells.append([round(c[0], 4), round(c[2], 4), round(c[1], 4), round(c[3], 4)])
        e["boxes"] = [ob] + cells; ncells += len(cells)
        pad = 0.012; zb = [w - pad, E + pad, s - pad, n + pad]
        e["z"] = zurl(zb, "waterfront"); e["za"] = zurl(zb, None)
        changed[f"{st}_{i}"] = [round(zb[2], 4), round(zb[3], 4), round(zb[0], 4), round(zb[1], 4)]   # page PR bbox: [south, north, west, east]
json.dump(P, open(P_PATH, "w"), ensure_ascii=False)
json.dump(changed, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "widened.json"), "w"))
print(len(changed), "waters widened;", ncells, "extra search cells")
