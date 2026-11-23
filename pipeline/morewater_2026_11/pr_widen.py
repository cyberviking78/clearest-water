"""Point each widened water's Zillow links (page PR rows) at its whole shoreline. Usage: pr_widen.py <page.html> <widened.json>"""
import json, sys
page, W = sys.argv[1], json.load(open(sys.argv[2]))
h = open(page).read(); k = "const PR="; i = h.find(k)
PR, end = json.JSONDecoder().raw_decode(h[i + len(k):])
n = 0
for key, bb in W.items():
    st, wi = key.rsplit("_", 1)
    if st in PR and int(wi) < len(PR[st]): PR[st][int(wi)][4] = bb; n += 1
h = h[:i] + k + json.dumps(PR, separators=(",", ":"), ensure_ascii=False) + h[i + len(k) + end:]
open(page, "w").write(h); print(n, "page water rows widened")
