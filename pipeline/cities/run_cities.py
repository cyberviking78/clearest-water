"""Monthly city trail-side house refresh. Usage: python3 run_cities.py <page.html>   (needs pandas, shapely, pyproj)
Run after the Property, Springheads and Trails steps (it reads ../listings.json and ../heads/sh.json for water listings).
boxes.json (Redfin cells along trails that touch a city over 200k) is built once by make_city_boxes.py and reused.
1. pull_cities.py: Redfin single-family houses $100k-750k in ~400 boxes.  2. match_cities.py: houses inside city limits within 400 m
of a named trail segment, plus water listings in cities within 1 mile of a trail.  3. build_ct.py: tab data, new flags.  4. ct_tab.py."""
import os, sys, json, shutil, subprocess, datetime
ROOT = os.path.dirname(os.path.abspath(__file__))
page = os.path.abspath(sys.argv[1])
os.chdir(ROOT)
if not os.environ.get("KEEP_RF"): shutil.rmtree("rf", ignore_errors=True)
def run(*a):
    print(">", " ".join(a), flush=True)
    subprocess.run([sys.executable, "-W", "ignore", *a], check=True)
run("pull_cities.py")
n, tot = len(os.listdir("rf")), len(json.load(open("rf_boxes.json")))
if n < 0.97 * tot:
    sys.exit(f"Only {n} of {tot} Redfin searches completed; not updating the page.")
run("match_cities.py")
run("build_ct.py", datetime.date.today().isoformat())
run("ct_tab.py", page, "ct.json")
m = json.load(open("meta_cities.json"))
print(f"CITIES DONE {m['date']}: {m['n']} city trail-side houses, {m['new']} new since {m['prev']}, {m['gone']} gone, {m['both']} with water and trail access", flush=True)
