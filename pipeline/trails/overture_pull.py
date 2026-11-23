"""Pull US bike-relevant path segments from Overture Maps transportation -> raw/overture_<n>.parquet"""
import os, sys, time, urllib.parse
import pyarrow.fs as pfs, pyarrow.dataset as ds, pyarrow.compute as pc, pyarrow.parquet as pq
REL = sys.argv[1] if len(sys.argv) > 1 else "2026-10-21.0"
p = urllib.parse.urlparse(os.environ["HTTPS_PROXY"])
s3 = pfs.S3FileSystem(anonymous=True, region="us-west-2", proxy_options={"scheme": p.scheme, "host": p.hostname, "port": p.port})
d = ds.dataset(f"overturemaps-us-west-2/release/{REL}/theme=transportation/type=segment/", filesystem=s3, format="parquet")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
B = [(-125, -66.5, 24.3, 49.5), (-170, -129, 51, 71.5), (-161, -154, 18.8, 22.4)]   # lower 48, AK, HI
x, y = pc.field("bbox", "xmin"), pc.field("bbox", "ymin")
reg = None
for w, e, s, n in B:
    f = (x > w) & (x < e) & (y > s) & (y < n)
    reg = f if reg is None else reg | f
flt = reg & pc.field("class").isin(["cycleway", "path", "track", "bridleway"])
cols = ["id", "geometry", "names", "class", "subclass", "road_surface", "access_restrictions", "connectors"]
for i, fn in enumerate(d.files):
    o = f"{OUT}/overture_{i}.parquet"
    if os.path.exists(o): continue
    t = time.time()
    for a in range(4):
        try:
            tb = ds.dataset(fn, filesystem=s3, format="parquet").to_table(columns=cols, filter=flt); break
        except Exception as ex:
            print("retry", i, ex, flush=True); time.sleep(20)
    pq.write_table(tb, o)
    print(i, tb.num_rows, round(time.time() - t), "s", flush=True)
print("PULL DONE", flush=True)
