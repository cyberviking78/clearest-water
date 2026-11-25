"""Check how the page's Florida springs and springheads match the FSI springs (same rule as fsiFind() on the page)."""
import json, math, re, sys, collections
h = open(sys.argv[1]).read()
def obj(name):
    i = h.find("const " + name + "="); o, _ = json.JSONDecoder().raw_decode(h[i + len("const " + name + "="):]); return o
FSI = json.load(open(sys.argv[2])); FSD = obj("FSD"); SH = obj("SH")
STOP = {"spring", "springs", "main", "head", "the", "big", "little", "upper", "lower", "rise", "seep", "sink", "vent", "boil", "run", "complex", "group", "of", "st", "saint"}
def tok(n):
    n = re.sub(r"\(.*?\)|#\s*\w+|\d+", " ", n.lower()); w = [x for x in re.findall(r"[a-z]+", n) if x not in STOP]; return w[0] if w else ""
def dist(a, b, c, d): return math.hypot((a - c) * 111.2, (b - d) * 111.2 * math.cos(math.radians(a))) * 1000
def find(lat, lon, name):
    t = tok(name); best = None
    for r in FSI:
        d = dist(lat, lon, r[0], r[1])
        if d > 1500: continue
        nm = t and tok(r[2]) == t
        if not nm and d > 300: continue
        score = (0 if nm else 1, 0 if r[5] else 1, 0 if r[6] else 1, d)
        if best is None or score < best[0]: best = (score, r)
    return best and best[1]
c = collections.Counter(); miss = []
for r in FSD["springs"]:
    if r[16] != "FL": continue
    lat, lon = r[18] if r[18] else ((r[12][1] + r[12][3]) / 2, (r[12][0] + r[12][2]) / 2)
    m = find(lat, lon, r[1]); c[m[5] if m else "nomatch"] += 1
    if not m: miss.append(r[1])
    elif tok(m[2]) != tok(r[1]): print("  by distance:", r[1], "->", m[2])
print("Springs tab FL", sum(c.values()), dict(c)); print("unmatched:", miss)
c = collections.Counter()
for hd in SH["heads"]:
    if hd[1] != "FL": continue
    m = find(hd[8], hd[9], hd[0]); c[m[5] if m else "nomatch"] += 1
print("FL springheads", sum(c.values()), dict(c))
withL = {x[0] for x in SH["L"]}
c = collections.Counter(); names = collections.defaultdict(list)
for i in withL:
    hd = SH["heads"][i]
    if hd[1] != "FL": continue
    m = find(hd[8], hd[9], hd[0]); c[m[5] if m else "nomatch"] += 1
    if m and m[5] == "blue": names["blue"].append(hd[0])
print("FL springheads with listings", dict(c), names["blue"])
