"""Chad's 22 states: check rivers and creeks known for clear water that aren't on the lists yet against station-level turbidity
(Water Quality Portal, 2016+, plus USGS sensors in TX/ID/WY), the same data reach.py uses.
For each candidate: the clearest stretch (stations chained within 15 km) with 24+ samples over 3+ years.
  measured  -> its median is at or under 3 NTU (gets a measured row and a property search)
  murky     -> enough samples, but every stretch's median is over 3 NTU (left out: the data says it isn't clear)
  unmeasured-> too few samples (a candidate for "known for clear water, not measured", if a published source says so)
Writes out/cands.json"""
import json, re, collections, statistics, math, os
src = open("/home/claude/live/reach/reach.py").read().split("# group by state + river name")[0]
src = src.replace('os.path.dirname(os.path.abspath(__file__))', '"/home/claude/live/reach"')
exec(src)
HERE = "/home/claude/live/crit"; os.makedirs(HERE + "/out", exist_ok=True)
C = json.load(open(HERE + "/cands.json"))
ALLOW = {"the", "lower", "upper", "mainstem", "main", "stem", "in", "on"}   # not "above X River" / "at X River": then X is only a landmark
def toks(s): return canon(s.replace("Beaverkill", "Beaver Kill").replace("Battenkill", "Batten Kill").replace("’", "'")).replace("'", "").split()
def matches(stname, cand):
    t = toks(stname); c = toks(cand)
    for i in range(len(t) - len(c) + 1):
        if t[i:i + len(c)] == c:
            nxt = t[i + len(c)] if i + len(c) < len(t) else ""
            if nxt in ("lake", "reservoir", "res", "pond", "trib", "tributary"): continue
            if i == 0 or t[i - 1] in ALLOW or not t[i - 1].isalpha(): return True
    return False
bys = collections.defaultdict(list)
for sid, (st, nm, lat, lon) in ST.items():
    if S.get(sid): bys[st].append((sid, nm, lat, lon))
out = {}
for st, L in C.items():
    for cand in L:
        hits = [(sid, lat, lon) for sid, nm, lat, lon in bys[st] if matches(nm, cand)]
        res = dict(st=st, river=cand, k=sum(len(S[h[0]]) for h in hits), status="unmeasured")
        if hits:
            n = len(hits); parent = list(range(n))
            def find(i):
                while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
                return i
            for i in range(n):
                for j in range(i + 1, n):
                    if km(hits[i][1:], hits[j][1:]) <= 15: parent[find(i)] = find(j)
            cl = collections.defaultdict(list)
            for i in range(n): cl[find(i)].append(hits[i])
            stretches = []
            for mem in cl.values():
                vals = [v for sid, _, _ in mem for v, y in S[sid]]; yrs = {y for sid, _, _ in mem for v, y in S[sid] if y}
                if len(vals) >= 24 and len(yrs) >= 3:
                    lat = sum(m[1] for m in mem) / len(mem); lon = sum(m[2] for m in mem) / len(mem)
                    stretches.append(dict(m=round(statistics.median(vals), 2), p25=round(float(np.percentile(vals, 25)), 2), p75=round(float(np.percentile(vals, 75)), 2),
                                          k=len(vals), s=len(mem), y=f"{min(yrs)}–{max(yrs)}", lat=lat, lon=lon, pts=[[m[1], m[2]] for m in mem],
                                          site=ST[max(mem, key=lambda m: len(S[m[0]]))[0]][1], near=nearest_place(st, lat, lon)))
            if stretches:
                b = min(stretches, key=lambda x: x["m"])
                res.update(b); res["status"] = "measured" if b["m"] <= 3 else "murky"
                res["all"] = [(x["m"], x["k"], x["near"]) for x in stretches]
        out[f"{st}|{cand}"] = res
        print(st, cand, res["status"], res.get("m", ""), res["k"], res.get("near", ""), res.get("site", "")[:40], flush=True)
json.dump(out, open(HERE + "/out/cands.json", "w"))
