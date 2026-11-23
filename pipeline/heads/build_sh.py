"""Assemble the Springheads tab data (SH) from heads.json + matches.json. Usage: build_sh.py <date> [--baseline]"""
import json, re, sys, os, datetime
from law import law
ROOT = os.path.dirname(os.path.abspath(__file__))
H = json.load(open(os.path.join(ROOT, "heads.json")))
M = json.load(open(os.path.join(ROOT, "matches.json")))
TODAY = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else datetime.date.today().isoformat()
seen_p = os.path.join(ROOT, "seen_heads.json")
seen = json.load(open(seen_p)) if os.path.exists(seen_p) else {}
baseline = "--baseline" in sys.argv or not seen
meta_p = os.path.join(ROOT, "meta_heads.json")
meta = json.load(open(meta_p)) if os.path.exists(meta_p) else {}
prev = meta.get("prev") if meta.get("date") == TODAY else meta.get("date")
if baseline: prev = meta.get("prev")

CODE = re.compile(r"(?i)^\(?[A-Z]{0,3}[- ]?\(?[A-Z]?-?\s?\d|^[A-Z]{2,3}-?\d{2,}|^\d|^spring\s*#?\d*$|^springs$|^unnamed")
def display(name, county):
    n = re.sub(r"\s+-\s+(?=\S*\d)\S{4,}$", "", (name or "").strip())
    if re.fullmatch(r"[A-Z][a-z]? Sp\d+", n): n = ""
    m = re.search(r"((?:[A-Z][a-z'.]+\s){1,4}Springs?)\b", n)
    if CODE.match(n) or not n:
        if m and not re.match(r"(?i)unnamed", m.group(1)): return m.group(1)
        return "Unnamed spring" + (f", {county.replace(' County', '')} Co." if county else "")
    n = re.sub(r"\bSpgs?\b", "Springs", n).replace("Spgs", "Springs")
    return n
ORG = re.compile(r"(?i)\b(LLC|L\.L\.C|INC|CORP|COMPANY|CO\b|LP\b|LTD|TRUST|WATER|UTILIT|CITY|COUNTY|TOWN|DISTRICT|BRANDS|BOTTL|NESTLE|ASSOC|AUTHORITY|CLUB|CAMP|RANCH|FARMS?|GROVES?|DAIRY|NURSERY|GOLF|PARK)\b")

used = {}
heads_out = []
for i, h in enumerate(H):
    usgs = next((x for x in h["ids"] if x.startswith("USGS-")), None)
    heads_out.append([display(h["name"], h.get("county")), h["st"], (h.get("county") or "").replace(" County", "") or None, h["mag"],
                      h.get("q"), h.get("last"), h.get("lastq"), ",".join(h["src"]), round(h["lat"], 5), round(h["lon"], 5),
                      usgs[5:] if usgs else None, bool(h.get("public")), bool(h.get("hist"))])
L = []
for r in sorted(M, key=lambda r: (r["tier"], H[r["head"]]["mag"], r["price"])):
    url = r["url"]; first = seen.get(url, [TODAY])[0]
    is_new = (not baseline) and url not in seen
    seen[url] = [first, TODAY]
    perms = []
    for p in r.get("permits") or []:
        if p.get("agency") == "TCEQ":
            perms.append(["TCEQ", p.get("id"), None, p.get("kind"), None, None, None])
        else:
            nm = p.get("name") if p.get("name") and (ORG.search(p.get("name") or "") ) else None
            hold = p.get("holder") if p.get("holder") and ORG.search(p.get("holder") or "") else None
            perms.append([p["agency"], p.get("id"), nm or hold, p.get("use"), p.get("status"), p.get("expires"), p.get("gpd")])
    gcd = r.get("gcd")
    L.append([r["head"], r["tier"], r["price"], "l" if str(r["type"]).startswith("Vacant") else "h", r.get("beds"), r.get("baths"), r.get("sqft"),
              r.get("acres"), r["addr"], r["city"], r.get("dom"), r.get("gap"), url.replace("https://www.redfin.com", ""), r.get("parcel_acres"),
              first, is_new, round(r["lat"], 5), round(r["lon"], 5), r.get("note"), perms,
              [gcd["DISTNAME"].strip().title(), (gcd.get("GCD_HOME") or "").strip() or None] if gcd else None])
states = sorted({h["st"] for h in H})
SH = dict(date=TODAY if not ("--baseline" in sys.argv and meta.get("date")) else meta["date"], prev=prev, heads=heads_out, L=L,
          law={s: law(s) for s in states}, n_states=len(states))
json.dump(SH, open(os.path.join(ROOT, "sh.json"), "w"), separators=(",", ":"), ensure_ascii=False)
json.dump(seen, open(seen_p, "w"), separators=(",", ":"))
json.dump(dict(date=SH["date"], prev=prev, n=len(L), new=sum(1 for x in L if x[15])), open(meta_p, "w"))
print("SH", len(heads_out), "heads,", len(L), "listings,", sum(1 for x in L if x[15]), "new; size", len(json.dumps(SH, separators=(",", ":"))) // 1024, "KB")
