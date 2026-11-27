"""Missouri springs: exact points, how the water is described, and where the photos are (Nov 27, 2026).
Missouri has no counterpart to the Florida Springs Institute's map (a survey description and a photo for each spring), so this
pulls together the three sources that exist:
  1. Missouri Department of Natural Resources spring inventory (gis.dnr.mo.gov/host/rest/services/water/water_springs/MapServer/0;
     4,457 springs; src/modnr_springs.json): the point, name, county, magnitude, public-land flag, and field notes, a few of which
     describe the water ("Deep blue pool", "looks blue").
  2. "The Large Springs of Missouri" (Beckman & Hinchey, Missouri Geological Survey, 1944; scan at the University of Missouri
     Digital Library): 118 spring descriptions (book1944.py -> book1944.json), with photo plates for the best-known springs.
  3. "Springs of Missouri" (Vineyard & Feder, Water Resources Report 29, revised 1982): about 100 spring descriptions with photos;
     wr29_notes.txt has, for each, its page, the words used for the water, the setting, and whether it has a photo.
Book entries are matched to the inventory by name and county (the largest spring of that name in that county; two Blue Springs in
Shannon County are told apart by size). Look: blue / clear / tint / "" with the Florida rules (../fsi_2026_11/looks.py) applied
to the 1944 description, the 1982 words and the inventory notes; "deep green" counts as clear; blue from any source wins.
Writes mos.json rows: [lat, lon, name, county, magnitude (9 = not rated), look, "", 1944 link page, words, "mo", 1982 page,
1944 description page, 1944 photo page, on public land (1/0), 1982 book has a photo (1/0), Commons photo page, photo credit]
([6] is the Commons photo, when there is one) for every inventory spring of magnitude 1-4 and every book spring.
Usage: build_mo.py"""
import json, math, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "fsi_2026_11"))
from looks import rate, snippet
A = [f["attributes"] for f in json.load(open(HERE + "/src/modnr_springs.json"))]
B44 = json.load(open(HERE + "/book1944.json"))
W82 = []
for line in open(HERE + "/wr29_notes.txt"):
    if line.startswith("#") or not line.strip(): continue
    n, c, p, col, setting, ph = [x.strip() for x in line.split("|")]
    W82.append({"name": n, "county": c, "page": int(p), "color": "" if col == "-" else col, "setting": setting, "photo": ph == "y"})
def norm(n): return re.sub(r"[^a-z]", "", re.sub(r"springs\b", "spring", re.sub(r"\(.*?\)", "", (n or "").lower())))
def title(n):
    t = " ".join(w.capitalize() if not re.fullmatch(r"(mc|mac)\w+", w.lower()) else w[:2].capitalize() + w[2:].capitalize() for w in (n or "").lower().split())
    return re.sub(r"\bMc ([A-Z])", r"Mc\1", t)
byk = collections.defaultdict(list)
for i, a in enumerate(A):
    if a["LATITUDE"] is None: continue
    byk[(norm(a["NAMEPRIM"]), (a["COUNTY"] or "").lower())].append(i)
def mag(a): m = a["MAGNITUDE"]; return int(m) if m and m > 0 else 9
import difflib
COUNTIES = sorted({(a["COUNTY"] or "").lower() for a in A if a["COUNTY"]})
BYC = collections.defaultdict(list)
for (nm, c), ids in byk.items(): BYC[c].append(nm)
def fixc(c):
    c = (c or "").lower().strip()
    if c in COUNTIES or not c: return c
    m = difflib.get_close_matches(c, COUNTIES, 1, 0.6) or [x for x in COUNTIES if x.endswith(c) or c.endswith(x)]
    return m[0] if m else c
def pick(name, county, nth=0, alt=()):
    county = fixc(county)
    order = lambda ids: sorted(ids, key=lambda i: (mag(A[i]), -(A[i]["MAXFLOW"] or 0)))
    for nm in (name,) + tuple(alt):
        ids = order(byk.get((norm(nm), county), []))
        if ids: return ids[min(nth, len(ids) - 1)]
    for nm in (name,) + tuple(alt):                     # spelling differs (Pulltight/Pulltite, Meramec/Maramec, OCR)
        m = difflib.get_close_matches(norm(nm), BYC.get(county, []), 1, 0.8)
        if m: return order(byk[(m[0], county)])[0]
    for nm in (name,) + tuple(alt):                     # county unreadable: the name alone, if it's distinctive
        if norm(nm) in ("bigspring", "bluespring", "cavespring", "coldspring", "spring"): continue
        ids = order([i for (n, c), v in byk.items() if n == norm(nm) for i in v])
        if len(ids) == 1 or (ids and not county): return ids[0]
    return None
info = collections.defaultdict(dict); unmatched = []
seen = collections.Counter()
for b in sorted(B44, key=lambda b: b["page"]):
    k = (norm(b["name"]), b["county"].lower()); i = pick(b["name"].replace(" ", "") if False else b["name"], b["county"], seen[k], b["also"]); seen[k] += 1
    if i is None:
        i = pick(re.sub(r"\s+", "", b["name"]).replace("Spring", " Spring"), b["county"])   # OCR splits like "Bea Ver Spring"
    if i is None: unmatched.append(("1944", b["name"], b["county"])); continue
    if "b44" in info[i]: continue
    info[i]["b44"] = b
dups = collections.Counter((norm(w["name"]), w["county"].lower()) for w in W82); seen = collections.Counter()
for w in sorted(W82, key=lambda w: -w["page"]):        # same name and county twice: the later page goes to the larger spring
    k = (norm(w["name"]), w["county"].lower()); i = pick(w["name"], w["county"], seen[k]); seen[k] += 1
    if i is None: unmatched.append(("1982", w["name"], w["county"])); continue
    info[i]["w82"] = w
def setting_words(desc):
    keep = []
    for s in re.split(r"(?<=[.!?])\s+", desc):
        if re.search(r"\bsec\.|\bT\. ?\d|\bR\. ?\d|reached|is located|are located|Measurements|gallons|second-feet|highway|Route", s, re.I): continue
        keep.append(s.strip())
    t = " ".join(keep); return t[:330] + ("…" if len(t) > 330 else "")
rows = []
for i, a in enumerate(A):
    if a["LATITUDE"] is None: continue
    I = info.get(i, {}); m = mag(a)
    if m > 4 and not I: continue
    looks, words = [], []
    if "b44" in I:
        looks.append(rate(" ".join("Water: " + x for x in re.split(r"(?<=[.;!?])\s+", I["b44"]["about"]))));   # every sentence is about the spring ("it is usually clear")
        words.append("1944: " + (snippet(I["b44"]["about"]) or setting_words(I["b44"]["about"])))
    if "w82" in I:
        w = I["w82"]; col = w["color"]
        looks.append("blue" if re.search(r"blue", col, re.I) else "clear" if re.search(r"clear|green", col, re.I) else "")
        words.append("1982: " + "; ".join(x for x in (col, w["setting"]) if x))
    notes = " ".join(x for x in (a["FLD_NOTES"], a["PREV_CMNTS"]) if x and x.strip())
    if re.search(r"\bblue\b", notes, re.I) and not re.search(r"blue (spring|hole|lick)", notes, re.I): looks.append("blue")
    if notes and len(words) < 2: words.append("State inventory: " + re.sub(r"\s+", " ", notes)[:160])
    look = "blue" if "blue" in looks else "clear" if "clear" in looks else "tint" if "tint" in looks else ""
    b = I.get("b44"); w = I.get("w82")
    rows.append([round(a["LATITUDE"], 5), round(a["LONGITUDE"], 5), title(a["NAMEPRIM"]) or "Spring", title(a["COUNTY"]), m, look, "", "",
                 " · ".join(words)[:520], "mo", w["page"] if w else 0, b["page"] if b else 0, (b["plates"] or [0])[0] if b else 0,
                 1 if (a.get("PUBLIC_LAND") or "").upper() == "Y" else 0, 1 if (w and w["photo"]) else 0])
# photos: Wikimedia Commons files within 450 m of the vent (src/commons.json, read by a GitHub Actions job for the points in
# src/commons_pts.json); it must name the spring in its title and mention a spring; the nearest such file wins
if os.path.exists(HERE + "/src/commons.json"):
    COM = json.load(open(HERE + "/src/commons.json")); PTS = {str(p[0]): p for p in json.load(open(HERE + "/src/commons_pts.json"))}
    GEN = {"spring", "springs", "big", "blue", "cave", "cold", "mill", "the", "upper", "lower", "little", "rise", "of"}
    at = {(r[2], round(r[0], 4), round(r[1], 4)): r for r in rows}
    for k, files in COM.items():
        p = PTS.get(k.split("|", 1)[0])
        if not p: continue
        r = at.get((p[1], round(p[2], 4), round(p[3], 4)))
        if not r: continue
        toks = [w for w in re.findall(r"[a-z]+", r[2].lower()) if w not in GEN]
        def score(f):
            t = f["title"].lower().replace("_", " "); d = math.hypot((f["lat"] - r[0]) * 111200, (f["lon"] - r[1]) * 87000) if f.get("lat") else 999
            return (0 if (toks and all(w in t for w in toks)) or r[2].lower() in t else 1, 0 if "spring" in t else 1, d)
        f = min((f for f in files if f.get("thumb")), key=score, default=None)
        # keep only a photo that names this spring and is about a spring (not a nearby road, town or a different spring)
        if not f or score(f)[0] or "spring" not in (f["title"] + " " + (f.get("desc") or "")).lower(): continue
        credit = ", ".join(x for x in (re.sub(r"\s+", " ", f.get("artist") or "").strip()[:60], f.get("license") or "") if x)
        r[6] = f["thumb"].split("?")[0]; r += [""] * (17 - len(r)); r[15] = f["page"]; r[16] = credit
for r in rows: r += [""] * (17 - len(r))
# photos with no map position, found by name on Commons and checked by hand (src/commons_named.json: name, county, 1982 page)
if os.path.exists(HERE + "/src/commons_named.json"):
    for c in json.load(open(HERE + "/src/commons_named.json")):
        for r in rows:
            if r[2] == c["name"] and r[3] == c["county"] and (not c["page82"] or r[10] == c["page82"]) and not r[6]:
                r[6], r[15], r[16] = c["thumb"], c["page"], c["credit"]; break
json.dump(rows, open(HERE + "/mos.json", "w"), ensure_ascii=False, separators=(",", ":"))
c = collections.Counter(r[5] for r in rows)
print(len(rows), "Missouri springs;", dict(c), "; 1944 descriptions", sum(1 for r in rows if r[11]), "(photos", sum(1 for r in rows if r[12]), ");",
      "1982 descriptions", sum(1 for r in rows if r[10]))
print("not matched to the inventory:", unmatched)
