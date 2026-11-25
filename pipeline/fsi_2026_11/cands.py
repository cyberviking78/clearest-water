"""Clear-blue FSI springs not yet on the Springs tab: farther than 1.5 km from every Florida spring and spring-fed river we
rank, grouped so vents within 1.5 km of each other become one entry (named after the largest, then the one with a photo).
Usage: cands.py page.html fsi.json out.json"""
import json, math, sys
h = open(sys.argv[1]).read()
def obj(name):
    i = h.find("const " + name + "="); o, _ = json.JSONDecoder().raw_decode(h[i + len("const " + name + "="):]); return o
FSI = json.load(open(sys.argv[2])); FSD = obj("FSD")
def dist(a, b, c, d): return math.hypot((a - c) * 111.2, (b - d) * 111.2 * math.cos(math.radians(a))) * 1000
have = []
for r in FSD["springs"]:
    if r[16] == "FL": have.append(r[18] if r[18] else ((r[12][1] + r[12][3]) / 2, (r[12][0] + r[12][2]) / 2))
for r in FSD["rivers"]:
    if r[13] == "FL": pass        # rivers are long; a spring on a ranked river still gets its own row
blue = [r for r in FSI if r[5] == "blue" and min(dist(r[0], r[1], a, b) for a, b in have) > 1500]
blue.sort(key=lambda r: (r[4], 0 if r[6] else 1))
groups = []
for r in blue:
    g = next((g for g in groups if any(dist(r[0], r[1], x[0], x[1]) <= 1500 for x in g)), None)
    (g.append(r) if g else groups.append([r]))
out = [{"lead": g[0], "vents": g} for g in groups]
json.dump(out, open(sys.argv[3], "w"), ensure_ascii=False, indent=0)
print(len(blue), "blue vents,", len(out), "entries")
for o in out: print(f"  m{o['lead'][4]} {'P' if o['lead'][6] else ' '} {o['lead'][2]} ({len(o['vents'])} vents)")
