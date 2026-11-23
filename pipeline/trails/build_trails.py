"""Build the national list of qualifying bike trails from raw/overture_*.parquet + raw/usgs.json.

A trail = a connected network of named bike paths, multi-use paths and bike-legal trails.
Qualifies when its total length is >= 20 miles (loops, trail systems) or its longest end-to-end
route is >= 10 miles (a linear trail ridden out and back). Writes trails.json (attributes) and
geom/<region>.json (simplified lines, lon/lat) used to measure listing distances.
"""
import glob, json, math, os, re, sys, time, collections
import numpy as np
import pyarrow.parquet as pq, pyarrow.compute as pc
import shapely
from shapely.geometry import LineString
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra

ROOT = os.path.dirname(os.path.abspath(__file__))
MI = 1609.344
T = {"L48": Transformer.from_crs(4326, 5070, always_xy=True), "AK": Transformer.from_crs(4326, 3338, always_xy=True),
     "HI": Transformer.from_crs(4326, 26904, always_xy=True)}
OFF = {"L48": 0.0, "AK": 1e8, "HI": 2e8}           # keep regions apart in one coordinate space
def region(lon, lat):
    if lat > 50.5 and lon < -129: return "AK"
    if lon < -154 and lat < 23: return "HI"
    return "L48"

ROADY = re.compile(r"(?i)\b(road|rd|street|st|avenue|ave|boulevard|blvd|drive|dr|highway|hwy|lane|ln|pike|court|ct|place|pl|circle|cir|parkway|pkwy|expressway|freeway|sidewalk|sidepath|crosswalk|bike lane|parking|driveway|alley|service road)\b\.?$")
SIDE = re.compile(r"(?i)side ?path|sidewalk|bike lane|cycle track")
TRAILY = re.compile(r"(?i)trail|path|greenway|bikeway|rail|loop|towpath|canal|levee|river|creek|mtb|bike|single ?track|connector|corridor|spur|run\b")
MTB = re.compile(r"(?i)mountain bike|\bmtb\b|single ?track|bike park|flow trail|pump track|freeride|downhill")
def good_name(n):
    n = (n or "").strip()
    if len(n) < 3: return False
    if SIDE.search(n): return False
    if ROADY.search(n) and not TRAILY.search(n): return False
    return True
def norm(n): return re.sub(r"[^a-z0-9]", "", (n or "").lower().replace("trail", "").replace("path", ""))[:40]
SURF = {"paved": "P", "paving_stones": "P", "metal": "P", "wood": "P", "gravel": "G", "unpaved": "G", "dirt": "D", "unknown": "U"}

def bike_ok(acc, cls):
    """None = no bike info, True = bikes allowed/designated, False = bikes denied, 'motor' = open to motor vehicles.
    A bicycle-specific rule wins over a general one (access=no + bicycle=designated is a bike trail)."""
    bike = None; gen_denied = False; motor = False
    for a in acc or []:
        modes = set(((a.get("when") or {}).get("mode")) or [])
        t = a["access_type"]
        if "bicycle" in modes:
            if t == "denied": return False
            bike = True
        elif not modes and t == "denied": gen_denied = True
        elif t == "allowed" and modes & {"motor_vehicle", "car", "motorcycle", "vehicle"} and cls == "track": motor = True
    if bike: return True
    if motor: return "motor"
    if gen_denied: return False
    return None

def load_overture():
    segs = []
    for f in sorted(glob.glob(os.path.join(ROOT, "raw", "overture_*.parquet"))):
        t = pq.read_table(f)
        if not t.num_rows: continue
        nmc = pc.struct_field(t["names"], "primary")
        t = t.filter(pc.or_(pc.equal(t["class"], "cycleway"), pc.is_valid(nmc)))
        if not t.num_rows: continue
        names = pc.struct_field(t["names"], "primary").to_pylist()
        cls = t["class"].to_pylist(); sub = t["subclass"].to_pylist()
        surf = t["road_surface"].to_pylist(); acc = t["access_restrictions"].to_pylist()
        geo = t["geometry"].to_pylist(); ids = t["id"].to_pylist()
        for i in range(t.num_rows):
            c, n = cls[i], names[i]
            b = bike_ok(acc[i], c)
            if b is False or b == "motor": continue
            if c == "cycleway":
                if sub[i] == "cycle_crossing": n = n or ""
                elif not good_name(n): n = ""          # unnamed cycleways only bridge gaps (kept if short)
            else:
                if b is not True: continue                       # paths/tracks/bridleways need bikes allowed
                if not good_name(n): n = ""                      # unnamed ones only bridge gaps (kept if short)
            s = "U"
            if surf[i]:
                s = SURF.get(surf[i][0]["value"], "U")
            segs.append(("o", ids[i], n or "", c, s, geo[i]))
        print(os.path.basename(f), len(segs), flush=True)
    return segs

def main():
    t0 = time.time()
    segs = load_overture()
    G = shapely.from_wkb([s[5] for s in segs])
    # USGS bike-legal trails
    U = json.load(open(os.path.join(ROOT, "raw", "usgs.json")))
    ug, ua = [], []
    for a, paths in U:
        n = a.get("name") or a.get("namealternate")
        if not good_name(n) or (a.get("ohvover50inches") in ("Y", "Yes")): continue
        for p in paths:
            if len(p) >= 2: ug.append(LineString(p)); ua.append(a)
    print("overture", len(segs), "usgs", len(ug), round(time.time() - t0), "s", flush=True)

    # project everything
    def proj(geoms):
        out = []
        for g in geoms:
            c = shapely.get_coordinates(g)
            r = region(c[0, 0], c[0, 1])
            x, y = T[r].transform(c[:, 0], c[:, 1])
            out.append((LineString(np.column_stack([np.asarray(x) + OFF[r], y])), r))
        return out
    PO = proj(G); PU = proj(ug)
    # drop unnamed cycleways longer than 400 m (likely sidepaths); keep short ones as connectors
    keep = [i for i, s in enumerate(segs) if s[2] or PO[i][0].length <= 400]
    segs = [segs[i] for i in keep]; PO = [PO[i] for i in keep]; G = [G[i] for i in keep]
    # USGS segments duplicating an Overture line: drop when 70% of sample points are within 25 m
    tree = shapely.STRtree([p[0] for p in PO])
    keepu = []
    for j, (g, r) in enumerate(PU):
        pts = shapely.line_interpolate_point(g, np.linspace(0, 1, 6), normalized=True)
        hit = tree.query(pts, predicate="dwithin", distance=25)
        frac = len(set(hit[0])) / 6
        if frac < 0.7: keepu.append(j)
    print("usgs kept", len(keepu), "of", len(PU), round(time.time() - t0), "s", flush=True)
    for j in keepu:
        a = ua[j]
        s = "U"
        ts = (a.get("trailsurface") or "").lower()
        if re.search(r"asphalt|concrete|paved|boardwalk", ts): s = "P"
        elif re.search(r"gravel|aggregate|crushed|limestone|cinder", ts): s = "G"
        elif re.search(r"native|dirt|soil|natural|rock", ts): s = "D"
        segs.append(("u", str(a.get("objectid")), (a.get("name") or a.get("namealternate")).strip(), "usgs", s, None))
        PO.append(PU[j]); G.append(ug[j])
    n = len(segs)
    L = np.array([p[0].length for p in PO])
    # nodes = endpoints snapped to 5 m
    ends = np.array([[*shapely.get_coordinates(p[0])[0], *shapely.get_coordinates(p[0])[-1]] for p in PO])
    E = np.vstack([ends[:, :2], ends[:, 2:]])                      # 2n endpoints: seg i start = i, end = n+i
    key = np.round(E / 5).astype(np.int64)
    _, node = np.unique(key[:, 0] * 10**9 + key[:, 1], return_inverse=True)
    nn = node.max() + 1
    rows = list(node[:n]); cols = list(node[n:]); w = list(np.maximum(L, 1))
    # links: endpoints within 25 m of each other; same-name ends within 300 m; ends touching another line within 15 m
    from scipy.spatial import cKDTree
    kd = cKDTree(E)
    nm = [norm(s[2]) for s in segs]
    for a, b in kd.query_pairs(25, output_type="ndarray"):
        if node[a] != node[b]: rows.append(node[a]); cols.append(node[b]); w.append(float(np.hypot(*(E[a] - E[b]))))
    deg = np.bincount(node, minlength=nn)
    dead = np.where(deg[node] == 1)[0]
    kd2 = cKDTree(E[dead])
    for a, b in kd2.query_pairs(300, output_type="ndarray"):
        ia, ib = dead[a], dead[b]
        sa, sb = ia % n, ib % n
        if sa != sb and nm[sa] and nm[sa] == nm[sb] and node[ia] != node[ib]:
            rows.append(node[ia]); cols.append(node[ib]); w.append(float(np.hypot(*(E[ia] - E[ib]))))
    tree = shapely.STRtree([p[0] for p in PO])
    pts = shapely.points(E[dead])
    pi, si = tree.query(pts, predicate="dwithin", distance=15)
    for a, sidx in zip(pi, si):
        ia = dead[a]
        if ia % n == sidx: continue
        # connect the dead end to the nearer endpoint node of the touched segment (the trail network is joined either way)
        rows.append(node[ia]); cols.append(node[sidx]); w.append(15.0)
    M = coo_matrix((w, (rows, cols)), shape=(nn, nn)).tocsr()
    M = M.maximum(M.T)
    ncomp, lab = connected_components(M, directed=False)
    seg_comp = lab[node[:n]]
    tot = np.bincount(seg_comp, weights=L, minlength=ncomp)
    named_len = np.bincount(seg_comp, weights=L * np.array([bool(s[2]) for s in segs]), minlength=ncomp)
    print("components", ncomp, "with >=10 mi:", int((tot >= 10 * MI).sum()), round(time.time() - t0), "s", flush=True)
    qual = {}
    for c in np.where((tot >= 10 * MI) & (named_len >= 5 * MI))[0]:
        if tot[c] >= 20 * MI:
            qual[c] = None; continue
        nodes = np.where(lab == c)[0]
        sub = M[nodes][:, nodes]
        d0 = dijkstra(sub, directed=False, indices=0); d0[np.isinf(d0)] = -1
        far = int(np.argmax(d0))
        d1 = dijkstra(sub, directed=False, indices=far); d1[np.isinf(d1)] = -1
        D = float(d1.max())
        if D >= 10 * MI: qual[c] = D
    print("qualifying trails", len(qual), round(time.time() - t0), "s", flush=True)

    trails = []; geom = collections.defaultdict(list)
    bycomp = collections.defaultdict(list)
    for i, c in enumerate(seg_comp):
        if c in qual: bycomp[c].append(i)
    for tid, (c, idx) in enumerate(sorted(bycomp.items(), key=lambda kv: -tot[kv[0]])):
        nl = collections.Counter(); kl = collections.Counter(); src = collections.Counter()
        for i in idx:
            s = segs[i]
            if s[2]: nl[s[2]] += L[i]
            src[s[0]] += L[i]
            if MTB.search(s[2]) or (s[4] == "D" and s[3] != "cycleway"): k = "m"
            elif s[4] == "P": k = "p"
            elif s[4] in "GD": k = "g"
            else: k = "u"
            kl[k] += L[i]
        names = [k for k, _ in nl.most_common(6)]
        share = {k: round(kl[k] / tot[c], 2) for k in "pgmu" if kl[k]}
        tags = [k for k in "gmp" if kl[k] >= 0.15 * tot[c] or kl[k] >= 5 * MI]
        known = kl["p"] + kl["g"] + kl["m"]
        typ = max("pgm", key=lambda k: kl[k]) if known >= 0.3 * tot[c] else "u"
        lonlat = np.vstack([shapely.get_coordinates(G[i]) for i in idx])
        reg = region(lonlat[0, 0], lonlat[0, 1])
        bb = [round(float(lonlat[:, 0].min()), 4), round(float(lonlat[:, 1].min()), 4), round(float(lonlat[:, 0].max()), 4), round(float(lonlat[:, 1].max()), 4)]
        trails.append(dict(id=tid, name=names[0] if names else "Unnamed trail", also=names[1:], mi=round(tot[c] / MI, 1),
                           route_mi=None if qual[c] is None else round(qual[c] / MI, 1), type=typ, tags=tags,
                           share=share, src={k: round(v / tot[c], 2) for k, v in src.items()},
                           bbox=bb, region=reg))
        for i in idx:
            if not segs[i][2]: continue                      # distances are measured to named trail segments only
            g = shapely.simplify(G[i], 0.00008)
            geom[tid].append([segs[i][2], [[round(x, 5), round(y, 5)] for x, y in shapely.get_coordinates(g)]])
    json.dump(trails, open(os.path.join(ROOT, "trails.json"), "w"), separators=(",", ":"))
    os.makedirs(os.path.join(ROOT, "geom"), exist_ok=True)
    # split geometry into files of < ~12 MB by trail id ranges
    chunk, size, k = {}, 0, 0
    for tid in sorted(geom):
        s = len(json.dumps(geom[tid], separators=(",", ":")))
        if size + s > 12_000_000 and chunk:
            json.dump(chunk, open(os.path.join(ROOT, "geom", f"g{k}.json"), "w"), separators=(",", ":")); k += 1; chunk, size = {}, 0
        chunk[tid] = geom[tid]; size += s
    json.dump(chunk, open(os.path.join(ROOT, "geom", f"g{k}.json"), "w"), separators=(",", ":"))
    print("TRAILS DONE", len(trails), "trails,", round(sum(t["mi"] for t in trails)), "miles,", collections.Counter(t["type"] for t in trails), round(time.time() - t0), "s", flush=True)

if __name__ == "__main__":
    main()
