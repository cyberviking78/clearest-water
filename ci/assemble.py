"""Final job of the GitHub refresh: with every shard's Redfin downloads already in place, run the refresh steps in their usual
order (each reuses the downloads and only searches what's missing), then rebuild the site page.
Writes ci/last_run.json, which the Claude report task reads. Exits non-zero only if the main water step fails, in which case
nothing should be committed. Usage (from the repository root): python3 ci/assemble.py"""
import json, os, shutil, subprocess, sys, time, datetime
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PL = os.path.join(REPO, "pipeline"); PAGE = os.path.join(PL, "page.html")
os.environ["KEEP_RF"] = "1"; os.environ.pop("SHARD", None); os.environ.pop("PULL_ONLY", None)
STEPS = [("waters", "run.py"), ("springheads", "heads/run_heads.py"), ("trails", "trails/run_trails.py"),
         ("water_trails", "trails/water_trails.py"), ("cities", "cities/run_cities.py"), ("old_growth", "og/run_og.py"),
         ("rainforest", "rain/run_rain.py"), ("wild_lakes", "wild/run_wild.py"), ("oceanfront", "ocean/run_ocean.py")]
out = dict(date=datetime.date.today().isoformat(), run=os.environ.get("GITHUB_RUN_ID"), steps={})
def save(): json.dump(out, open(os.path.join(REPO, "ci", "last_run.json"), "w"), indent=1)
for name, script in STEPS:
    if not os.path.exists(os.path.join(PL, script)): continue
    shutil.copy(PAGE, PAGE + ".bak"); t = time.time()
    print(f"::group::{name}", flush=True)
    p = subprocess.run([sys.executable, "-W", "ignore", os.path.join(PL, script), PAGE], cwd=PL, capture_output=True, text=True)
    sys.stdout.write(p.stdout[-20000:]); sys.stderr.write(p.stderr[-8000:]); print("::endgroup::", flush=True)
    lines = [l for l in p.stdout.splitlines() if l.strip()]
    out["steps"][name] = dict(ok=p.returncode == 0, minutes=round((time.time() - t) / 60, 1), last=lines[-3:] if lines else [],
                              error=None if p.returncode == 0 else (p.stderr.strip().splitlines() or ["exit %d" % p.returncode])[-1][:400])
    if p.returncode != 0:
        shutil.copy(PAGE + ".bak", PAGE)          # a failed step leaves the page as it was
        print(f"::warning::{name} failed: {out['steps'][name]['error']}", flush=True)
        if name == "waters": save(); sys.exit(1)
    save()
os.remove(PAGE + ".bak")
h = open(PAGE).read()
if "#mapwrap.max{" not in h:
    subprocess.run([sys.executable, os.path.join(PL, "fixes", "restore_css.py"), PAGE], check=True); h = open(PAGE).read()
out["checks"] = {k: (k in h) for k in ("#mapwrap.max{", 'id="geosky"', "How the wild lake search works", "found through LakeQuality")}
subprocess.run([sys.executable, os.path.join(PL, "mapbuild", "make_site.py"), PAGE, REPO], check=True)
save(); print(json.dumps(out, indent=1))
