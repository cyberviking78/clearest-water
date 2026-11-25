"""Florida Springs Institute pass (Nov 25, 2026): how each Florida spring's water looks.
Source: the Howard T. Odum Florida Springs Institute's Interactive Florida Springs Map (floridaspringsinstitute.org/springs-map-2-0/),
ArcGIS layer "Florida Spring Locations 2020" (1,011 springs; services2.arcgis.com/euPm04SdnsvTecYy/.../Florida_Spring_Locations_2020).
Each spring carries the field description from the Florida Geological Survey's Springs of Florida (Bulletin 66, 2004, and later
FDEP surveys), a photo link and a water-quality report link. The descriptions say how the water looked on the survey visit,
which turbidity alone doesn't: tannic, tea-coloured water can still test at very low NTU.
Each description is read sentence by sentence, keeping only what is said about the spring's own water (sentences about river,
lake or creek water, and the part of a sentence after "contrasts", are skipped), and the spring is rated:
  blue  - the spring water is described as blue, bluish, blue-green or turquoise, and not as murky, tannic or dark
  clear - described as clear (or crystal clear), not blue, and not as murky, tannic or dark
  tint  - described as tannic, tea-coloured, dark, brown, black, murky, turbid, cloudy or milky (even if also "clear");
          only "slightly" murky or tannic water that is also called clear or blue is rated clear. Sentences that mention a river,
          lake, creek, flood or rain are not used for this, since they usually describe the water the spring flows into
  ""    - the description says nothing about the water's colour or clarity
One visit's description: a spring can look different after heavy rain or when a river floods it.
Usage: looks.py <layer json from the ArcGIS query> <out fsi.json>"""
import json, re, sys
F = [f["attributes"] for f in json.load(open(sys.argv[1]))["features"]]
OTHER = re.compile(r"\b(river|lake|creek|reservoir|marsh|swamp|estuar\w*|gulf|bay)(?:'s)? water|\bwater of the (river|lake|creek)|tannic (river|lake|creek|reservoir)", re.I)
BLUE = re.compile(r"\b(blue|bluish|blue-green\w*|turquoise|aqua\w*|azure|sapphire)\b(?! spring| springs| hole| grotto| run| sink)", re.I)
CLEAR = re.compile(r"\b(clear|crystal|transparent)\b", re.I)
TINT = re.compile(r"\b(not (?:very |as |entirely |completely )?clear|poor(?:er)? visibility|low visibility|tannic|tannin\w*|tea[- ]colou?red|tea[- ]stained|dark|brown\w*|black|stained|murky|turbid\w*|cloudy|milky|opaque)\b", re.I)
ELSEWHERE = re.compile(r"\b(river|creek|lake|reservoir|swamp|marsh|estuar\w*|flood\w*|rain\w*|storm|lagoon)\b", re.I)
WATERY = re.compile(r"\b(water|spring pool|pool|boil|vent|spring run|run)\b", re.I)
def rate(desc):
    blue = clear = tint = mild = False
    for s in re.split(r"(?<=[.;!?])\s+", (desc or "").split("[FGS")[0]):
        s = re.split(r"\bcontrast", s, flags=re.I)[0]
        if not WATERY.search(s) or OTHER.search(s): continue
        s2 = re.sub(r"\b[A-Z][a-z]+ Blue\b|\bBlue [A-Z][a-z]+", "", s)      # names like "Gilchrist Blue", "Blue Grotto"
        s3 = re.sub(r"dark(er)? (limestone|rock|bottom|cave|vent|opening|hole|depths?|areas?)|black (limestone|rock)|brown (algae|sand|rock|limestone|mud)|stained (rock|limestone|bank|tree)\w*", "", s2, flags=re.I)
        if not ELSEWHERE.search(s3):
            for m in TINT.finditer(s3):
                if re.search(r"(slight(ly)?|faint(ly)?|light(ly)?|little|some(what)?)\W+(\w+\W+)?$", s3[:m.start()], re.I): mild = True
                else: tint = True
        if BLUE.search(s2): blue = True
        if CLEAR.search(s2): clear = True
    if mild and not tint: return "clear" if (blue or clear) else "tint"
    return "tint" if tint else "blue" if blue else "clear" if clear else ""
def snippet(desc):
    out = []
    for s in re.split(r"(?<=[.!?])\s+", (desc or "").split("[FGS")[0]):
        if WATERY.search(s) and (BLUE.search(s) or CLEAR.search(s) or TINT.search(s) or re.search(r"\bboil\b", s, re.I)): out.append(s.strip())
    t = " ".join(out[:3]); return t[:420] + ("…" if len(t) > 420 else "")
MAG = {"1st": 1, "2nd": 2, "3rd": 3}
rows = []
for a in F:
    img = (a.get("Image") or "").strip(); pdf = (a.get("WQ_Data") or "").strip()
    rows.append([round(a["Latitude"], 5), round(a["Longitude"], 5), a["Name"], a["County"], MAG.get(a["Mag"], 4), rate(a["Description"]),
                 img if img.startswith("http") and a.get("Foto_Varmi") == "Yes" else "", pdf if pdf.startswith("http") and a.get("WQ_Varmi") == "Yes" else "",
                 snippet(a["Description"])])
json.dump(rows, open(sys.argv[2], "w"), ensure_ascii=False, separators=(",", ":"))
import collections; print(collections.Counter(r[5] for r in rows), "photos", sum(bool(r[6]) for r in rows), "reports", sum(bool(r[7]) for r in rows))
