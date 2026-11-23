"""Split a refresh's Redfin searches across parallel GitHub Actions jobs.
SHARD="k/N" keeps every N-th search starting at k (the files keep their usual names, so the shards' downloads simply sit side
by side when the final job gathers them). PULL_ONLY=1 makes a runner stop once its searches are saved. KEEP_RF=1 tells the
runners not to clear downloads that are already in place (the final job reuses the shards' files and only searches what's missing)."""
import os
def take(seq):
    s = os.environ.get("SHARD")
    if not s: return list(seq)
    k, n = map(int, s.split("/")); return list(seq)[k::n]
def pull_only(): return bool(os.environ.get("PULL_ONLY"))
def keep_rf(): return bool(os.environ.get("KEEP_RF"))
