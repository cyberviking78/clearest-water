"""Monthly springhead-listing refresh. Usage: python3 run_heads.py <page.html>   (run after run.py; needs pandas, shapely)
1. Pull Redfin listings (houses + land from $100k, no upper limit) in boxes.json around every springhead in heads.json (about 2,100 searches).
2. cands.py: listings within ~1.5 km of a vent.  3. match.py: state parcel maps decide whether the vent is on the lot; permits near the vent.
4. build_sh.py: tab data, marks listings first seen this run as new.  5. sh_tab.py: writes the data into the page."""
import os, sys, shutil, subprocess, datetime
ROOT = os.path.dirname(os.path.abspath(__file__))
page = os.path.abspath(sys.argv[1])
os.chdir(ROOT)
if not os.environ.get("KEEP_RF"):
    for d in ("rf", "rf_hi"): shutil.rmtree(d, ignore_errors=True)
os.makedirs("rf", exist_ok=True)
def run(*a):
    print(">", " ".join(a), flush=True)
    subprocess.run([sys.executable, "-W", "ignore", *a], check=True)
run("pull_rf.py")
n = len(os.listdir("rf"))
if n < 2000:
    sys.exit(f"Only {n} of the Redfin searches completed; not updating the page.")
run("cands.py"); run("match.py")
run("build_sh.py", datetime.date.today().isoformat())
run("sh_tab.py", page, "sh.json")
import json
m = json.load(open("meta_heads.json"))
print(f"HEADS DONE {m['date']}: {m['n']} springhead listings, {m['new']} new since {m['prev']}", flush=True)
