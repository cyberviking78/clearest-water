"""Second trail pull: US bike-relevant path segments from Overture Maps, now also keeping unnamed cycleways of any length
and footways that carry access rules (footway + bicycle=yes/designated). -> raw/ov_<n>.parquet"""
import os, sys, time, urllib.parse, concurrent.futures as cf
import pyarrow.fs as pfs, pyarrow.dataset as ds, pyarrow.compute as pc, pyarrow.parquet as pq
REL = "2026-10-21.0"
p = urllib.parse.urlparse(os.environ["HTTPS_PROXY"])
s3 = pfs.S3FileSystem(anonymous=True, region="us-west-2", proxy_options={"scheme": p.scheme, "host": p.hostname, "port": p.port})
d = ds.dataset(f"overturemaps-us-west-2/release/{REL}/theme=transportation/type=segment/", filesystem=s3, format="parquet")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw"); os.makedirs(OUT, exist_ok=True)
B = [(-125, -66.5, 24.3, 49.5), (-170, -129, 51, 71.5), (-161, -154, 18.8, 22.4)]
x, y = pc.field("bbox", "xmin"), pc.field("bbox", "ymin")
reg = None
for w, e, s, n in B:
    f = (x > w) & (x < e) & (y > s) & (y < n)
    reg = f if reg is None else reg | f
cls = pc.field("class")
flt = reg & (cls.isin(["cycleway", "path", "track", "bridleway"]) | ((cls == "footway") & pc.field("access_restrictions").is_valid()))
cols = ["id", "geometry", "names", "class", "subclass", "road_surface", "access_restrictions"]
def one(i_fn):
    i, fn = i_fn
    o = f"{OUT}/ov_{i}.parquet"
    if os.path.exists(o): return i, -1, 0
    t = time.time()
    for a in range(5):
        try:
            tb = ds.dataset(fn, filesystem=s3, format="parquet").to_table(columns=cols, filter=flt); break
        except Exception as ex:
            print("retry", i, str(ex)[:120], flush=True); time.sleep(20 * (a + 1))
    else:
        return i, None, 0
    pq.write_table(tb, o + ".tmp"); os.replace(o + ".tmp", o)
    return i, tb.num_rows, round(time.time() - t)
with cf.ThreadPoolExecutor(6) as ex:
    for i, n, s in ex.map(one, enumerate(d.files)):
        print(i, n, s, "s", flush=True)
print("PULL DONE", flush=True)
