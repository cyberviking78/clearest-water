"""Stage C: choose the new trails and write them next to the existing ones.
New trail = a network from the rebuilt graph that (1) qualifies under the original rules (20+ miles in total, or a 10+ mile
end-to-end route), (2) has at least 10 named miles making up at least half its length, (3) lies mostly in the US, and
(4) is less than 15% covered by the existing 1,760 trails (so no duplicates). Existing trails keep their ids and geometry.
Geometry stored for matching houses: named segments, plus unnamed paved bike paths (class cycleway) that are not sidepaths.
Writes trails_new.json and geom_new.json (merged into the pipeline by apply.py)."""
import json, os, pickle, sys, collections, re
import numpy as np, shapely
from shapely.geometry import shape
from scipy.sparse.csgraph import dijkstra
sys.path.insert(0, "/home/claude/live/pipeline/trails")
import build_trails as B
HERE = os.path.dirname(os.path.abspath(__file__)); TR = "/home/claude/live/pipeline/trails"; MI = 1609.344
S = pickle.load(open(os.path.join(HERE, "segs.pkl"), "rb")); C = pickle.load(open(os.path.join(HERE, "comps.pkl"), "rb"))
recs = S["recs"]; G = shapely.from_wkb(S["G"]); orig = C["orig"]; sc = C["seg_comp"]; L = C["L"]; M = C["M"]; lab = C["lab"]
STS = [(s["st"], shape(s["geom"]).buffer(0)) for s in json.load(open(os.path.join(TR, "states.json")))]
stree = shapely.STRtree([g for _, g in STS])
comp = {c: (t, nl, cl) for c, t, nl, cl in C["comps"]}
segs_of = collections.defaultdict(list)
for j in range(len(sc)):
    c = int(sc[j])
    if c in comp: segs_of[c].append(j)
old = json.load(open(os.path.join(TR, "trails.json")))
nid = len(old)
picked = []
for c, (t, nl, cl) in comp.items():
    if nl < 10 or nl < 0.5 * t or cl >= 0.15 * t: continue
    idx = segs_of[c]
    mids = shapely.line_interpolate_point(np.array([G[orig[j]] for j in idx], dtype=object), 0.5, normalized=True)
    a, b = stree.query(mids, predicate="within")
    inus = sum(L[idx[k]] for k in set(a.tolist()))
    if inus < 0.5 * t * MI: continue
    route = None
    if t < 20:
        nodes = np.where(lab == c)[0]; sub = M[nodes][:, nodes]
        d0 = dijkstra(sub, directed=False, indices=0); d0[np.isinf(d0)] = -1
        d1 = dijkstra(sub, directed=False, indices=int(np.argmax(d0))); d1[np.isinf(d1)] = -1
        route = float(d1.max())
        if route < 10 * MI: continue
    st = collections.Counter()
    for p, k in zip(a, b): st[STS[k][0]] += L[idx[p]]
    picked.append((c, t, route, idx, [s for s, _ in st.most_common()]))
picked.sort(key=lambda x: -x[1])
trails, geom = [], {}
for k, (c, t, route, idx, states) in enumerate(picked):
    tid = nid + k
    nl = collections.Counter(); kl = collections.Counter(); src = collections.Counter(); tot = sum(L[j] for j in idx)
    for j in idx:
        r = recs[orig[j]]
        if r[2]: nl[r[2]] += L[j]
        src[r[0]] += L[j]
        if B.MTB.search(r[2]) or (r[4] == "D" and r[3] != "cycleway"): kk = "m"
        elif r[4] == "P": kk = "p"
        elif r[4] in "GD": kk = "g"
        else: kk = "u"
        kl[kk] += L[j]
    names = [n for n, _ in nl.most_common(6)]
    tags = [x for x in "gmp" if kl[x] >= 0.15 * tot or kl[x] >= 5 * MI]
    known = kl["p"] + kl["g"] + kl["m"]
    typ = max("pgm", key=lambda x: kl[x]) if known >= 0.3 * tot else "u"
    ll = np.vstack([shapely.get_coordinates(G[orig[j]]) for j in idx])
    bb = [round(float(ll[:, 0].min()), 4), round(float(ll[:, 1].min()), 4), round(float(ll[:, 0].max()), 4), round(float(ll[:, 1].max()), 4)]
    trails.append(dict(id=tid, name=names[0], also=names[1:], mi=round(tot / MI, 1), route_mi=None if route is None else round(route / MI, 1),
                       type=typ, tags=tags, share={x: round(kl[x] / tot, 2) for x in "pgmu" if kl[x]}, src={x: round(v / tot, 2) for x, v in src.items()},
                       bbox=bb, region=B.region(ll[0, 0], ll[0, 1]), states=states, added="2026-11-10"))
    g = []
    for j in idx:
        r = recs[orig[j]]
        if not r[2] and r[3] != "cycleway": continue
        gg = shapely.simplify(G[orig[j]], 0.00008)
        g.append([r[2] or names[0], [[round(x, 5), round(y, 5)] for x, y in shapely.get_coordinates(gg)]])
    geom[tid] = g
json.dump(trails, open(os.path.join(HERE, "trails_new.json"), "w"), separators=(",", ":"))
json.dump(geom, open(os.path.join(HERE, "geom_new.json"), "w"), separators=(",", ":"))
print("NEW TRAILS", len(trails), round(sum(t["mi"] for t in trails)), "miles;", collections.Counter(t["type"] for t in trails),
      collections.Counter(s for t in trails for s in t["states"][:1]).most_common(12))
for t in trails[:25]: print(" ", t["mi"], t["type"], t["states"][:2], t["name"], "|", "; ".join(t["also"][:2]))
for q in ["Hank Aaron", "Trinity Trails", "Oak Leaf"]:
    print(q, [(t["id"], t["name"], t["mi"]) for t in trails if q in t["name"] or any(q in a for a in t["also"])])
