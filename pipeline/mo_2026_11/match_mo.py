"""Check how the page's Missouri springs and springheads match mos.json (same rule as fsiFind on the page). Usage: match_mo.py page.html"""
import json, math, re, sys, collections
h = open(sys.argv[1]).read()
def obj(n):
    i = h.find("const " + n + "="); o, _ = json.JSONDecoder().raw_decode(h[i + len("const " + n + "="):]); return o
FSD = obj("FSD"); SH = obj("SH"); M = json.load(open(__file__.rsplit("/", 1)[0] + "/mos.json" if "/" in __file__ else "mos.json"))
STOP = {"spring", "springs", "main", "head", "the", "upper", "lower", "rise", "seep", "sink", "vent", "boil", "run", "complex", "group", "of", "st", "saint"}
def tok(n):
    n = re.sub(r"\(.*?\)|#\s*\w+|\d+", " ", n.lower()); w = [x for x in re.findall(r"[a-z]+", n) if x not in STOP]; return w[0] if w else ""
def dist(a, b, c, d): return math.hypot((a - c) * 111.2, (b - d) * 111.2 * math.cos(math.radians(a))) * 1000
def find(lat, lon, name):
    t = tok(name); best = None
    for r in M:
        d = dist(lat, lon, r[0], r[1])
        if d > 1500: continue
        nm = t and tok(r[2]) == t
        if not nm and d > 300: continue
        s = (0 if nm else 1, 0 if r[5] else 1, 0 if r[6] else 1, d)
        if best is None or s < best[0]: best = (s, r)
    return best and best[1]
for r in FSD["springs"]:
    if r[16] != "MO": continue
    m = find(r[18][0], r[18][1], r[1]); print("Springs tab:", r[1], "->", m and (m[2], m[5] or "-", "1982 p." + str(m[10]) if m[10] else "", "1944 p." + str(m[11]) if m[11] else "", round(dist(r[18][0], r[18][1], m[0], m[1]))))
c = collections.Counter()
for hd in SH["heads"]:
    if hd[1] != "MO": continue
    m = find(hd[8], hd[9], hd[0]); c["no match" if not m else (m[5] or ("book" if (m[10] or m[11]) else "inventory only"))] += 1
print("Missouri springheads:", dict(c))
