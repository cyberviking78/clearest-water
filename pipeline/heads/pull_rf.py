import json, os, sys, time, random, urllib.parse, urllib.request, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import rfjson, shard   # Redfin map-data feed (includes MLS listings the CSV hides)
from concurrent.futures import ThreadPoolExecutor
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
MINP = os.environ.get("MINP", "100000"); MAXP = os.environ.get("MAXP", "")
OUT = os.environ.get("RFDIR", "rf")
def redfin(b):
    w, e, s, n = b
    poly = urllib.parse.quote(f"{w} {s},{e} {s},{e} {n},{w} {n},{w} {s}")
    url = (f"https://www.redfin.com/stingray/api/gis-csv?al=1&min_price={MINP}" + (f"&max_price={MAXP}" if MAXP else "") + "&num_homes=350"
           f"&ord=redfin-recommended-asc&page_number=1&poly={poly}&sf=1,2,3,5,6,7&status=9&uipt=1,5&v=8")
    for a in range(5):
        try:
            body = rfjson.fetch_csv(url)
            if body.startswith("SALE TYPE"):
                time.sleep(2.5 + random.random() * 2); return body
            raise RuntimeError(body[:100])
        except Exception as ex:
            print("retry", a, ex, flush=True); time.sleep(30 * (a + 1))
    raise RuntimeError("redfin down")
def job(i_b):
    i, b = i_b; f = f"{OUT}/{i}.csv"
    if os.path.exists(f): return
    body = redfin(b[:4])
    if body.count("\n") >= 350:
        w, e, s, n = b[:4]; mx, my = (w + e) / 2, (s + n) / 2
        parts = [redfin(q) for q in [(w, mx, s, my), (mx, e, s, my), (w, mx, my, n), (mx, e, my, n)]]
        body = parts[0] + "".join(p.split("\n", 1)[1] if "\n" in p else "" for p in parts[1:])
    open(f, "w").write(body)
boxes = json.load(open("boxes.json"))
done = [0]; lock = threading.Lock()
def run(x):
    job(x)
    with lock:
        done[0] += 1
        if done[0] % 100 == 0: print(done[0], "of", len(boxes), time.strftime("%H:%M"), flush=True)
with ThreadPoolExecutor(4) as ex: list(ex.map(run, shard.take(enumerate(boxes))))
print("DONE", flush=True)
