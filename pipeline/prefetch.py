"""Fetch every water search (waterfront-filtered and all listings, for every box of every water in props.json) through the
map-data feed, four at a time, into <out>/csv and <out>/csv_all as <group>_<index>[_<box>].csv. run.py then reads them
(LOCAL_CSV mode). Existing files are kept, so an interrupted run resumes. Boxes over Redfin's 350-row cap are split in four, twice."""
import json, os, random, sys, threading, time, urllib.parse
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import rfjson, shard
def one(b, wf):
    w, e, s, n = b
    poly = urllib.parse.quote(f"{w} {s},{e} {s},{e} {n},{w} {n},{w} {s}")
    url = ("https://www.redfin.com/stingray/api/gis-csv?al=1&min_price=100000&max_price=750000&num_homes=350"
           f"&ord=redfin-recommended-asc&page_number=1&poly={poly}&sf=1,2,3,5,6,7&status=9&uipt=1,5&v=8" + ("&wf=true" if wf else ""))
    for a in range(5):
        try:
            body = rfjson.fetch_csv(url); time.sleep(2 + random.random() * 2); return body
        except Exception as ex:
            print("retry", a, ex, flush=True); time.sleep(30 * (a + 1))
    raise RuntimeError("redfin down")
def fetch(b, wf, depth=0):
    body = one(b, wf)
    if body.count("\n") < 350 or depth >= 2: return body
    w, e, s, n = b; mx, my = (w + e) / 2, (s + n) / 2
    parts = [fetch(q, wf, depth + 1) for q in [(w, mx, s, my), (mx, e, s, my), (w, mx, my, n), (mx, e, my, n)]]
    return parts[0] + "".join(p.split("\n", 1)[1] for p in parts[1:])
def run(P, out, threads=4):
    for d in ("csv", "csv_all"): os.makedirs(os.path.join(out, d), exist_ok=True)
    jobs = []
    for st, ents in P.items():
        for i, e in enumerate(ents):
            if e.get("skip"): continue
            q = json.loads(urllib.parse.unquote(e["z"].split("=", 1)[1]))["mapBounds"]
            b = (q["west"], q["east"], q["south"], q["north"])
            bl = [tuple(x) for x in e.get("boxes", [])] or [b]
            for k, bb in enumerate(bl):
                for wf in (True, False): jobs.append((st, i if k == 0 else f"{i}_{k}", bb, wf))
    jobs = shard.take(jobs)      # one slice of the searches when the refresh runs as parallel jobs
    done = [0]; lock = threading.Lock(); fails = []
    def job(j):
        st, i, b, wf = j; f = os.path.join(out, "csv" if wf else "csv_all", f"{st}_{i}.csv")
        if not os.path.exists(f):
            try:
                body = fetch(b, wf); open(f + ".tmp", "w").write(body); os.replace(f + ".tmp", f)
            except Exception as ex: fails.append((st, i, wf)); print("FAILED", st, i, wf, ex, flush=True)
        with lock:
            done[0] += 1
            if done[0] % 250 == 0: print(done[0], "of", len(jobs), time.strftime("%H:%M"), flush=True)
    with ThreadPoolExecutor(threads) as ex: list(ex.map(job, jobs))
    print("PREFETCH DONE", len(jobs) - len(fails), "of", len(jobs), "failed", len(fails), flush=True)
    return len(jobs), len(fails)
if __name__ == "__main__":
    root = os.path.dirname(os.path.abspath(__file__))
    run(json.load(open(os.path.join(root, "props.json"))), sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "wcsv"))
