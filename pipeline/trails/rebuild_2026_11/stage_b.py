"""Stage B: build the trail network from segs.pkl (same joining rules as build_trails.py), optionally dropping segments
listed in sidepaths.json, find qualifying components and how much of each is already covered by the existing 1,760 trails.
Usage: stage_b.py [sidepaths.json] -> comps.pkl"""
import glob, json, os, pickle, sys, time, collections
import numpy as np, shapely
from shapely.geometry import LineString
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree
sys.path.insert(0, "/home/claude/live/pipeline/trails")
import build_trails as B
HERE = os.path.dirname(os.path.abspath(__file__)); TR = "/home/claude/live/pipeline/trails"; MI = 1609.344
t0 = time.time()
S = pickle.load(open(os.path.join(HERE, "segs.pkl"), "rb"))
recs = S["recs"]; PO = list(shapely.from_wkb(S["PO"])); G = list(shapely.from_wkb(S["G"]))
drop = set(json.load(open(sys.argv[1]))) if len(sys.argv) > 1 else set()
keep = [i for i in range(len(recs)) if i not in drop]
recs = [recs[i] for i in keep]; PO = [PO[i] for i in keep]; G = [G[i] for i in keep]; orig = keep
n = len(recs); L = shapely.length(np.array(PO, dtype=object))
ends = np.array([[*shapely.get_coordinates(p)[0], *shapely.get_coordinates(p)[-1]] for p in PO])
E = np.vstack([ends[:, :2], ends[:, 2:]])
key = np.round(E / 5).astype(np.int64)
_, node = np.unique(key[:, 0] * 10**9 + key[:, 1], return_inverse=True)
nn = node.max() + 1
rows = list(node[:n]); cols = list(node[n:]); w = list(np.maximum(L, 1))
kd = cKDTree(E); nm = [B.norm(r[2]) for r in recs]
for a, b in kd.query_pairs(25, output_type="ndarray"):
    if node[a] != node[b]: rows.append(node[a]); cols.append(node[b]); w.append(float(np.hypot(*(E[a] - E[b]))))
deg = np.bincount(node, minlength=nn); dead = np.where(deg[node] == 1)[0]
kd2 = cKDTree(E[dead])
for a, b in kd2.query_pairs(300, output_type="ndarray"):
    ia, ib = dead[a], dead[b]; sa, sb = ia % n, ib % n
    if sa != sb and nm[sa] and nm[sa] == nm[sb] and node[ia] != node[ib]:
        rows.append(node[ia]); cols.append(node[ib]); w.append(float(np.hypot(*(E[ia] - E[ib]))))
tree = shapely.STRtree(PO)
pi, si = tree.query(shapely.points(E[dead]), predicate="dwithin", distance=15)
for a, sidx in zip(pi, si):
    ia = dead[a]
    if ia % n == sidx: continue
    rows.append(node[ia]); cols.append(node[sidx]); w.append(15.0)
M = coo_matrix((w, (rows, cols)), shape=(nn, nn)).tocsr(); M = M.maximum(M.T)
ncomp, lab = connected_components(M, directed=False)
seg_comp = lab[node[:n]]
tot = np.bincount(seg_comp, weights=L, minlength=ncomp)
named = np.array([bool(r[2]) for r in recs])
named_len = np.bincount(seg_comp, weights=L * named, minlength=ncomp)
print("components", ncomp, round(time.time() - t0), "s", flush=True)
# coverage by the existing trails (their named segments), sampled at 3 points per segment
V = []
for f in glob.glob(os.path.join(TR, "geom", "g*.json")):
    for tid, Lg in json.load(open(f)).items():
        for nm_, c in Lg:
            c = np.array(c); r = B.region(c[0, 0], c[0, 1]); x, y = B.T[r].transform(c[:, 0], c[:, 1])
            V.append((int(tid), LineString(np.column_stack([np.asarray(x) + B.OFF[r], y]))))
vtree = shapely.STRtree([g for _, g in V])
cand = np.where(tot >= 10 * MI)[0]
cset = set(cand.tolist())
idx = np.where(np.isin(seg_comp, cand))[0]
pts = shapely.line_interpolate_point(np.array([PO[i] for i in idx], dtype=object)[:, None], np.array([[0.1, 0.5, 0.9]]), normalized=True)
covered = np.zeros(n, bool); covtid = {}
flat = pts.ravel(); a, b = vtree.query(flat, predicate="dwithin", distance=30)
hitcount = collections.Counter(); tidhit = collections.defaultdict(collections.Counter)
for p, v in zip(a, b):
    s = idx[p // 3]; hitcount[(s, p % 3)] = 1; tidhit[s][V[v][0]] += 1
per = collections.Counter(s for (s, k) in hitcount)
for s, k in per.items():
    if k >= 2: covered[s] = True; covtid[s] = tidhit[s].most_common(1)[0][0]
cov_len = np.bincount(seg_comp, weights=L * covered, minlength=ncomp)
out = []
for c in cand:
    out.append((int(c), float(tot[c] / MI), float(named_len[c] / MI), float(cov_len[c] / MI)))
pickle.dump(dict(orig=orig, seg_comp=seg_comp, L=L, named=named, covered=covered, covtid=covtid, comps=out, M=M, lab=lab, node=node), open(os.path.join(HERE, "comps.pkl"), "wb"))
newish = [x for x in out if x[1] - x[3] >= 10 and x[3] < 0.5 * x[1] and x[2] >= 3]
print("components >= 10 mi:", len(out), "| mostly new (>=10 new mi, <50% covered, >=3 named mi):", len(newish),
      "| new miles", round(sum(x[1] - x[3] for x in newish)), round(time.time() - t0), "s", flush=True)
print("STAGE B DONE", flush=True)
