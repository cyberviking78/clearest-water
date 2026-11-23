import json, shapefile, zipfile, io, os, subprocess, urllib.parse, time
S='/tmp/claude-0/-home-claude/7954ff2d-1aca-5169-bbaa-419cda25cfd1/scratchpad/lq'
cand=json.load(open(S+'/lq_missing15.json'))
z=zipfile.ZipFile('/home/claude/geo_src/county500k.zip')
r=shapefile.Reader(dbf=io.BytesIO(z.read('cb_2024_us_county_500k.dbf')))
f=[x[0] for x in r.fields[1:]]
cty={}
for rec in r.records():
    d=dict(zip(f,rec)); cty[(d['STUSPS'],d['NAME'].lower())]=(d['STATEFP'],d['COUNTYFP'])
os.makedirs(S+'/wqp',exist_ok=True)
need=set()
for c in cand:
    k=(c[0],c[2].lower().replace('st. louis','st. louis'))
    if k not in cty: print('nocty',c); continue
    need.add(cty[k])
print(len(need))
q=urllib.parse.quote
for sf,cf in sorted(need):
    for kind in ('Result','Station'):
        out=f'{S}/wqp/{kind}_{sf}{cf}.csv'
        if os.path.exists(out) and os.path.getsize(out)>0: continue
        url=(f'https://www.waterqualitydata.us/data/{kind}/search?statecode=US:{int(sf)}&countycode=US:{int(sf)}:{cf}'
             f'&characteristicName={q("Depth, Secchi disk depth")}&siteType={q("Lake, Reservoir, Impoundment")}&mimeType=csv'
             +('&startDateLo=01-01-2000' if kind=='Result' else ''))
        for t in range(3):
            p=subprocess.run(['curl','-s','-m','500','-o',out,'-w','%{http_code}',url],capture_output=True,text=True)
            if p.stdout=='200': break
            time.sleep(5)
        print(kind,sf,cf,p.stdout,os.path.getsize(out) if os.path.exists(out) else 0,flush=True)
json.dump({f'{k[0]}|{k[1]}':v for k,v in cty.items()},open(S+'/cty.json','w'))
