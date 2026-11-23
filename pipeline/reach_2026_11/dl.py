"""Station-level turbidity (2016+) for stream sites in every state from the Water Quality Portal -> cache/res_<ST>.csv, cache/st_<ST>.csv"""
import os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
F = {"AL":"01","AK":"02","AZ":"04","AR":"05","CA":"06","CO":"08","CT":"09","DE":"10","FL":"12","GA":"13","HI":"15","ID":"16","IL":"17","IN":"18","IA":"19","KS":"20","KY":"21","LA":"22","ME":"23","MD":"24","MA":"25","MI":"26","MN":"27","MS":"28","MO":"29","MT":"30","NE":"31","NV":"32","NH":"33","NJ":"34","NM":"35","NY":"36","NC":"37","ND":"38","OH":"39","OK":"40","OR":"41","PA":"42","RI":"44","SC":"45","SD":"46","TN":"47","TX":"48","UT":"49","VT":"50","VA":"51","WA":"53","WV":"54","WI":"55","WY":"56"}
B = "https://www.waterqualitydata.us/data/{}/search?statecode=US:{}&siteType=Stream&characteristicName=Turbidity&startDateLo=01-01-2016&mimeType=csv&zip=no"
def one(st):
    for kind, extra in (("st", ""), ("res", "&dataProfile=narrowResult")):
        f = f"cache/{kind}_{st}.csv"
        if os.path.exists(f) and os.path.getsize(f) > 200: continue
        for a in range(4):
            try:
                b = urllib.request.urlopen(urllib.request.Request(B.format("Station" if kind == "st" else "Result", F[st]) + extra, headers={"User-Agent": "Mozilla/5.0"}), timeout=1200).read()
                open(f + ".tmp", "wb").write(b); os.replace(f + ".tmp", f); break
            except Exception as e:
                print(st, kind, "retry", a, str(e)[:80], flush=True); time.sleep(30 * (a + 1))
    print(st, "done", flush=True)
with ThreadPoolExecutor(4) as ex: list(ex.map(one, sorted(F)))
print("DL DONE", flush=True)
