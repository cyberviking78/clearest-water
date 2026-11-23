"""Pull Redfin houses ($100k-750k) in boxes along qualifying trails -> rf/<i>.csv (resumable)."""
import collections, json, os, random, sys, threading, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import rfjson, shard   # Redfin map-data feed (includes MLS listings the CSV hides)
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
OUT = os.path.join(ROOT, "rf")
FAIL = [0]
def redfin(b):
    w, e, s, n = b
    poly = urllib.parse.quote(f"{w} {s},{e} {s},{e} {n},{w} {n},{w} {s}")
    url = ("https://www.redfin.com/stingray/api/gis-csv?al=1&min_price=100000&max_price=750000&num_homes=350"
           f"&ord=redfin-recommended-asc&page_number=1&poly={poly}&sf=1,2,3,5,6,7&status=9&uipt=1&v=8")
    for a in range(5):
        try:
            body = rfjson.fetch_csv(url)
            if body.startswith("SALE TYPE"):
                time.sleep(2.5 + random.random() * 2); return body
            raise RuntimeError(body[:100])
        except Exception as ex:
            print("retry", a, ex, flush=True); time.sleep(30 * (a + 1))
    FAIL[0] += 1
    if FAIL[0] > 25: print("TOO MANY FAILURES", flush=True); os._exit(2)
    raise RuntimeError("redfin down")
def fetch(b, depth=0):
    body = redfin(b)
    if body.count("\n") < 350 or depth >= 3: return body
    w, e, s, n = b; mx, my = (w + e) / 2, (s + n) / 2
    parts = [fetch(q, depth + 1) for q in [(w, mx, s, my), (mx, e, s, my), (w, mx, my, n), (mx, e, my, n)]]
    return parts[0] + "".join(p.split("\n", 1)[1] if "\n" in p else "" for p in parts[1:])
def merged():
    B = json.load(open(os.path.join(ROOT, "boxes.json")))
    g = collections.defaultdict(list)
    for w, e, s, n in B: g[(round(w / 0.05) // 3, round(s / 0.04) // 3)].append((w, e, s, n))
    return [(min(x[0] for x in v), max(x[1] for x in v), min(x[2] for x in v), max(x[3] for x in v)) for k, v in sorted(g.items())]
if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    boxes = merged()
    json.dump(boxes, open(os.path.join(ROOT, "rf_boxes.json"), "w"))
    done = [0]; lock = threading.Lock()
    def job(ib):
        i, b = ib; f = f"{OUT}/{i}.csv"
        if not os.path.exists(f):
            try: body = fetch(b)
            except Exception as ex: print("box", i, "failed", ex, flush=True); return
            open(f, "w").write(body)
        with lock:
            done[0] += 1
            if done[0] % 250 == 0: print(done[0], "of", len(boxes), time.strftime("%H:%M"), flush=True)
    with ThreadPoolExecutor(4) as ex: list(ex.map(job, shard.take(enumerate(boxes))))
    n = len(os.listdir(OUT))
    print("PULL DONE", n, "of", len(boxes), flush=True)
