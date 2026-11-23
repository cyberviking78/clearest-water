"""Monthly trail-side house refresh. Usage: python3 run_trails.py <page.html>   (needs pandas, shapely, pyproj, scipy)
The trail network (trails.json, geom/, boxes.json) is built once by overture_pull.py + usgs_pull.py + build_trails.py + make_boxes.py
and reused; this script only re-collects listings.
1. pull_trails.py: Redfin houses $100k-750k in ~5,700 boxes along the trails.  2. match_trails.py: houses within 400 m of a
named trail segment, outside cities over 200k.  3. build_tr.py: tab data, marks houses first seen this run as new.  4. tr_tab.py: writes it into the page."""
import os, sys, json, shutil, subprocess, datetime
ROOT = os.path.dirname(os.path.abspath(__file__))
page = os.path.abspath(sys.argv[1])
os.chdir(ROOT)
if not os.environ.get("KEEP_RF"): shutil.rmtree("rf", ignore_errors=True)
def run(*a):
    print(">", " ".join(a), flush=True)
    subprocess.run([sys.executable, "-W", "ignore", *a], check=True)
run("pull_trails.py")
n, tot = len(os.listdir("rf")), len(json.load(open("rf_boxes.json")))
if n < 0.97 * tot:
    sys.exit(f"Only {n} of {tot} Redfin searches completed; not updating the page.")
run("match_trails.py")
run("build_tr.py", datetime.date.today().isoformat())
run("tr_tab.py", page, "tr.json")
m = json.load(open("meta_trails.json"))
print(f"TRAILS DONE {m['date']}: {m['n']} trail-side houses, {m['new']} new since {m['prev']}, {m['gone']} gone", flush=True)
