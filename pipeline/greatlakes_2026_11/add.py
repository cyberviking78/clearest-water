"""Append the 13 Great Lakes shorelines (out/gl.json from build.py) to props.json and shore/<ST>.json, and write the page rows
(Lakes tab and Property list) to out/extra3.json. Only listings on the lake are kept for these ("on_only"; run.py skips "near").
Clarity is open-lake clarity from published surveys; nearshore water is often less clear."""
import json, os, re, urllib.parse
LIVE = "/home/claude/live"; HERE = os.path.dirname(os.path.abspath(__file__)); OUT = HERE + "/out"
h = open(LIVE + "/page.work.html").read()
_i = h.find("const NAMES={"); NAMES = dict(re.findall(r'([A-Z]{2}):"([^"]+)"', h[_i:h.find("}", _i)]))
P = json.load(open(LIVE + "/pipeline/props.json")); GL = json.load(open(OUT + "/gl.json"))
EPA = ("EPA Great Lakes Biology Monitoring Program", "https://www.epa.gov/sites/default/files/2021-04/documents/2019_glbmp_annual_report_07-12-2019_508_compliant.pdf")
DL = ("Dobiesz & Lester 2009, Journal of Great Lakes Research", "https://www.harkness.ca/PDFs/Contributions%202000s/Dobiesz%20and%20Lester%202009.pdf")
NCCA = "EPA's 2010 coastal survey rated {p} of the lake's nearshore area poor for clarity."
CL = {   # (feet, metres, what the figure is, source, nearshore share rated poor)
    "Superior": (39, 12, "Open-lake average in summer", EPA, "27%"),
    "Michigan": (49, 15, "Open-lake average in spring", EPA, "29%"),
    "Huron": (28, 8.5, "Open-lake August average, 1968–2002", DL, None),
    "Ontario": (23, 7, "Open-lake average in summer", EPA, "25%"),
    "Erie-W": (4, 1.1, "Western-basin August average, 1968–2002", DL, "67%"),
    "Erie-C": (19, 5.8, "Central-basin August average, 1968–2002; the western basin, west of Sandusky, averages about 4 ft", DL, "67%"),
    "Erie-E": (19, 5.7, "Eastern-basin August average, 1968–2002", DL, "67%"),
}
ERIE = {"MI": "Erie-W", "OH": "Erie-C", "PA": "Erie-E", "NY": "Erie-E"}
def zurl(b, att):
    fs = {"sort": {"value": "globalrelevanceex"}, "price": {"min": 100000, "max": 750000}, "tow": {"value": False}, "mf": {"value": False},
          "con": {"value": False}, "apa": {"value": False}, "apco": {"value": False}, "manu": {"value": False}}
    if att: fs["att"] = {"value": att}
    s = json.dumps({"pagination": {}, "isMapVisible": True, "isListVisible": True, "mapBounds": {"west": b[0], "east": b[1], "south": b[2], "north": b[3]}, "filterState": fs}, separators=(",", ":"))
    return "https://www.zillow.com/homes/for_sale/?searchQueryState=" + urllib.parse.quote(s, safe="")
def lwpath(st, cty):
    return f"{NAMES[st].lower().replace(' ', '-')}-land-for-sale/{cty.lower().replace(' ', '-').replace('.', '')}-county/waterfront-property/price-100000-750000"
if any(e.get("gl") for L in P.values() for e in L): raise SystemExit("already added")
tab, PR, shore = {}, {}, {}
for st, L in GL.items():
    for g in L:
        key = ERIE[st] if g["lake"] == "Erie" else g["lake"]
        ft, m, what, (srcn, src), poor = CL[key]
        n = f"Lake {g['lake']} shoreline"
        w, s, e_, nn = g["bbox"]; zb = [w, e_, s, nn]
        mid = g["geom"]["coordinates"]
        e = dict(t="lake", n=n, rk=None, v=f"about {ft} ft open lake", c=", ".join(g["counties"]), z=zurl(zb, "waterfront"), za=zurl(zb, None),
                 lw=[[c, "https://www.landwatch.com/" + lwpath(st, c)] for c in g["counties"]], lat=round((s + nn) / 2, 4), lon=round((w + e_) / 2, 4),
                 added="2026-11-11", gl=True, on_only=True, boxes=g["boxes"])
        P[st].append(e); i = len(P[st]) - 1
        shore.setdefault(st, {})[f"{st}_{i}"] = dict(name=n, method="Great Lakes shoreline (TIGER AREAWATER edge)", matched=["Lk " + g["lake"]], geom=g["geom"])
        note = f"{what}. " + (NCCA.format(p=poor) + " " if poor else "") + f"{g['km']:,} km of shoreline searched in {len(g['counties'])} " + ("parishes" if st == "LA" else "counties") + "; only listings on the lake are kept."
        tab.setdefault(st, []).append(dict(n=n, x=True, g="gl", gl=True, ft=ft, m=m, note=note, src=src, srcn=srcn, c=", ".join(g["counties"])))
        PR.setdefault(st, []).append(["g", n, None, f"about {ft} ft open-lake clarity", [s, nn, w, e_], [[c, lwpath(st, c)] for c in g["counties"]]])
        print(st, n, ft, "ft", len(g["boxes"]), "cells")
json.dump(P, open(OUT + "/props.json", "w"), ensure_ascii=False)
os.makedirs(OUT + "/shore", exist_ok=True)
for st, d in shore.items():
    S = json.load(open(f"{LIVE}/pipeline/shore/{st}.json")); S.update(d)
    json.dump(S, open(f"{OUT}/shore/{st}.json", "w"), separators=(",", ":"))
json.dump(dict(tab=tab, PR=PR), open(OUT + "/extra3.json", "w"), ensure_ascii=False)
