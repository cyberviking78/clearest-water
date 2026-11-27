"""Parse "The Large Springs of Missouri" (Beckman & Hinchey, Missouri Geological Survey, 1944; scan at the University of Missouri
Digital Library, digital.library.missouri.edu/sites/default/files/2025-02/mu_417688.pdf) into one entry per spring:
name, also-called names, county, PDF page where its description starts, PDF page of its photo plate (if any), and its description
text (the words before the flow-measurement table, with OCR-split words joined; "about" drops the location sentence). Usage: book1944.py src/V029_pages.json book1944.json"""
import json, re, sys
from wordfreq import zipf_frequency          # pip install wordfreq
P = json.load(open(sys.argv[1]))
def ocr_join(t):
    """The scan's OCR splits words ("remar kable", "southea st"): join two pieces when the joined word is commoner than either, or the first piece is not a word."""
    w = t.split(" "); out = []; i = 0
    while i < len(w):
        if i + 1 < len(w) and re.fullmatch(r"[a-z]+", w[i]) and re.fullmatch(r"[a-z]+[.,;:]?", w[i + 1]):
            b = w[i + 1].rstrip(".,;:"); j = w[i] + b
            zj, za, zb = zipf_frequency(j, "en"), zipf_frequency(w[i], "en"), zipf_frequency(b, "en")
            if zj >= 2.5 and (zj > max(za, zb) or za < 2.0):     # "remar kable"; "deepe st" (a stub like "deepe" isn't a word)
                out.append(w[i] + w[i + 1]); i += 2; continue
        out.append(w[i]); i += 1
    return " ".join(out)
# plates: PDF page that carries "PLATE <roman>" in its header
plate_page = {}
for i, t in enumerate(P):
    m = re.search(r"PL\s*\.?\s*A\s*T\s*E\s+([IVXLivxl]+)\b", t[:400])
    if m: plate_page[m.group(1).upper()] = i + 1
text, starts = "", []
for i, t in enumerate(P[49:], start=50):
    starts.append((len(text), i)); text += "\n" + t
def page_at(pos):
    pg = starts[0][1]
    for s, p in starts:
        if s <= pos: pg = p
        else: break
    return pg
HEAD = re.compile(r"\n\s{2,}([A-Z][A-Z'’.\-]+(?:[ ,]+[A-Z][A-Z'’.\-]+)*?(?:,? (?:EAST|WEST|NORTH|SOUTH|UPPER|LOWER))?)\s*(?:\(([^)]{3,80})\))?\s+(?:is|are|was|were|rises|issues)\b")
heads = [m for m in HEAD.finditer(text) if re.search(r"SPRING|EYE|RISE|BLUE HOLE|BOIL", m.group(1))]
out = []
for k, m in enumerate(heads):
    end = heads[k + 1].start() if k + 1 < len(heads) else len(text)
    body = text[m.start():end]
    desc = re.split(r"M\S{0,2}eas\S{0,3}\s?u?\S{0,3}\s?r?\s?e?ments? of (?:the )?flow|Measurements? of (?:the )?flow|Date\s+Second-feet|Records of the daily flow", body)[0]
    desc = re.sub(r"\n[^\n]*(?:Missouri Geological Survey|Large Springs of Missouri|Larg\(Springs)[^\n]*\n", "\n", desc)
    desc = re.sub(r"-\n\s*", "", desc); desc = re.sub(r"\s+", " ", desc).strip()
    desc = re.split(r"\s\d[\d,]*\.?\d*\s+\d[\d,]{4,}|\.{6,}|\bDate\b", desc)[0]        # a flow table the split above missed
    desc = re.sub(r"M\S{1,3}SSOURI\W[^()]{0,60}?PLATE\s+[IVXLl]+\s+A\..*?\)\.?(?:\s+B\..*?\)\.?)?", " ", desc)   # a photo plate's captions
    desc = ocr_join(desc)
    place = re.sub(r"^.*?\bCount(?:y|ies)\b.*?\.(?=\s+[A-Z])", "", desc, count=1, flags=re.S).strip()   # the "is located in sec. ..., T. ..N." sentence
    cty = re.search(r"([A-Z][a-z]+(?: [A-Z][a-z]+)?(?:\s*and\s*[A-Z][a-z]+)?)\s+Count(?:y|ies)", body[:700])
    plates = re.findall(r"plates?\s+([IVXL]+)\s*-?\s*[AB]?", body)
    also = re.findall(r"also (?:called|known as) ([A-Z][\w' ]+?(?:Spring|Springs))", body[:400])
    name = re.sub(r"\s+", " ", m.group(1)).title().replace("’", "'")
    out.append({"name": name, "also": also, "county": cty.group(1) if cty else "", "page": page_at(m.start()),
                "plates": sorted({plate_page[p] for p in plates if p in plate_page}), "desc": desc[:1500], "about": place[:1200]})
json.dump(out, open(sys.argv[2], "w"), indent=0, ensure_ascii=False)
print(len(out), "springs;", sum(1 for o in out if o["plates"]), "with photo plates")
for o in out[:8] + [o for o in out if o["plates"]][:6]: print(o["page"], o["plates"], o["name"], "|", o["county"], "|", o["also"], "|", o["desc"][:110])
