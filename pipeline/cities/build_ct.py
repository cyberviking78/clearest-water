"""Assemble the Cities tab data (CT) from matches.json; mark houses first seen this run as new.
Usage: build_ct.py <date>   -> ct.json, seen_cities.json, meta_cities.json"""
import json, os, re, sys, datetime
ROOT = os.path.dirname(os.path.abspath(__file__)); TRD = os.path.join(os.path.dirname(ROOT), "trails")
TODAY = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
CITIES = json.load(open(os.path.join(TRD, "bigcities.json")))
M = json.load(open(os.path.join(ROOT, "matches.json")))
seen_p = os.path.join(ROOT, "seen_cities.json"); meta_p = os.path.join(ROOT, "meta_cities.json")
seen = json.load(open(seen_p)) if os.path.exists(seen_p) else {}
meta = json.load(open(meta_p)) if os.path.exists(meta_p) else {}
baseline = not seen
prev = meta.get("prev") if meta.get("date") == TODAY else meta.get("date")
prev_urls = set(meta.get("urls", []))

def cname(n):
    n = n.replace("Urban ", "")
    if re.search(r"government|urban county", n): n = re.split(r"[-/]", n)[0]
    return re.split(r" (?:city|town|municipality|CDP|urban county|metro government|metropolitan government|consolidated government)\b", n)[0].strip()
AB = {"Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO","Connecticut":"CT","Delaware":"DE","District of Columbia":"DC","Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY"}
CT_C = [[cname(c["name"]), AB.get(c["st"], c["st"]), c["pop"]] for c in CITIES]
L = []
for m in sorted(M["houses"], key=lambda m: (m["ci"], m["tid"], m["dist"])):
    url = m["url"]; first = seen.get(url, [TODAY])[0]
    is_new = (not baseline) and url not in seen
    seen[url] = [first, TODAY]
    L.append([m["ci"], m["tid"], m["price"], m["beds"], m["baths"], m["sqft"], m["acres"], m["addr"], m["city"], m["st"], m["dom"], m["dist"],
              url.replace("https://www.redfin.com", ""), m["seg"], first, is_new, m["lat"], m["lon"], m["year"], m["water"], m["wtier"]])
W = [[w["ci"], w["tid"], w["dist"], w["seg"], w["path"], w["water"], w["tier"], w["price"], w["type"], w["beds"], w["baths"], w["sqft"], w["acres"],
      w["addr"], w["city"], w["st"], w["dom"], w["new"], w["lat"], w["lon"]] for w in sorted(M["water"], key=lambda w: w["dist"])
     if w["path"] not in {x[12] for x in L if x[19]}]     # houses already listed with their water
cur = {x[12] for x in L}
CT = dict(date=TODAY, prev=None if baseline else prev, cities=CT_C, L=L, W=W)
json.dump(CT, open(os.path.join(ROOT, "ct.json"), "w"), separators=(",", ":"), ensure_ascii=False)
json.dump(seen, open(seen_p, "w"), separators=(",", ":"))
gone = len(prev_urls - {"https://www.redfin.com" + u for u in cur}) if prev_urls else 0
json.dump(dict(date=TODAY, prev=CT["prev"], n=len(L), new=sum(1 for x in L if x[15]), gone=gone, both=sum(1 for x in L if x[19]) + len(W),
               urls=sorted("https://www.redfin.com" + u for u in cur)), open(meta_p, "w"), separators=(",", ":"))
print("CT", len({x[0] for x in L}), "cities with houses,", len(L), "houses,", sum(1 for x in L if x[15]), "new,", gone, "gone;",
      sum(1 for x in L if x[19]), "houses also on the water,", len(W), "water listings near trails; size", len(json.dumps(CT, separators=(",", ":"))) // 1024, "KB")
