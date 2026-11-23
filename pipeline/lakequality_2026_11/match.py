import json, csv, re, statistics, sys, collections
csv.field_size_limit(10**9)
S='/tmp/claude-0/-home-claude/7954ff2d-1aca-5169-bbaa-419cda25cfd1/scratchpad/lq'
cand=json.load(open(S+'/lq_missing15.json')); cty=json.load(open(S+'/cty.json'))
STOP={'lake','reservoir','res','lk','pond','the','of','lac','mid','deep','lpd','hole','d'}
QUAL={'little','big','upper','lower','north','south','west','east','middle'}
OV=json.load(open('/home/claude/work/lq/overrides.json'))
def core(n,c):
    n=n.lower()
    pre=c.lower()+'-'
    if n.startswith(pre): n=n[len(pre):]
    n=re.sub(r"[^a-z0-9 ]"," ",n)
    return [w for w in n.split() if w not in STOP] or [w for w in n.split() if w not in ('lake','reservoir')]
unit={'m':3.28084,'ft':1,'cm':0.0328084,'in':1/12,'mm':0.00328084}
cache={}
def load(code):
    if code in cache: return cache[code]
    st={}
    for r in csv.DictReader(open(f'{S}/wqp/Station_{code}.csv',encoding='utf-8',errors='replace')):
        st[r['MonitoringLocationIdentifier']]=(r['MonitoringLocationName'],r['LatitudeMeasure'],r['LongitudeMeasure'],r['MonitoringLocationTypeName'])
    res={}
    for r in csv.DictReader(open(f'{S}/wqp/Result_{code}.csv',encoding='utf-8',errors='replace')):
        v=r['ResultMeasureValue']; u=(r['ResultMeasure/MeasureUnitCode'] or '').strip().lower()
        try: v=float(v)
        except: continue
        if u not in unit: continue
        res.setdefault(r['MonitoringLocationIdentifier'],[]).append((r['ActivityStartDate'],v*unit[u],r['ResultDetectionConditionText'],r['ActivityStartDate'][5:7]))
    cache[code]=(st,res); return cache[code]
out=[]
for c in cand:
    stt,n,cn,ft,ac,href=c
    code=''.join(cty[f'{stt}|{cn.lower()}'])
    st,res=load(code)
    words=core(n,cn)
    ov=OV.get(stt+'|'+n)
    hits=[]
    if ov=='skip': continue
    for sid,(nm,la,lo,ty) in st.items():
        if sid not in res: continue
        nml=re.sub(r"[^a-z0-9 ]"," ",nm.lower())
        if ov:
            if re.search(ov,nml): hits.append(sid)
            continue
        if all(re.search(r'\b'+re.escape(w)+r'\b',nml) for w in words) and not any(re.search(r'\b'+q+r'\b',nml) for q in QUAL-set(words)):
            hits.append(sid)
    vals=[x for s in hits for x in res[s]]
    # summer only? keep all, report both
    vs0=[v for d,v,dc,m in vals if 0<v<=148]
    md0=statistics.median(vs0) if vs0 else 0
    keep=[(d,v) for d,v,dc,m in vals if 0<v<=148 and v<=3*md0]
    vs=[v for d,v in keep]
    by=collections.defaultdict(list)
    for d,v in keep: by[d[:4]].append(v)
    yavg=round(sum(statistics.median(x) for x in by.values())/len(by),1) if by else None
    yrs=sorted({d[:4] for d,v,dc,m in vals if 0<v<=148})
    rec=dict(st=stt,n=n,cty=cn,lq=ft,ac=ac,words=words,stations=[(s,st[s][0],st[s][1],st[s][2]) for s in hits],
             k=len(vs),yrs=len(yrs),y0=yrs[0] if yrs else None,y1=yrs[-1] if yrs else None,
             med=round(statistics.median(vs),1) if vs else None,avg=round(sum(vs)/len(vs),1) if vs else None,
             mx=round(max(vs),1) if vs else None,yavg=yavg)
    out.append(rec)
    print(f"{stt} {n[:34]:34} lq{ft:5} k{rec['k']:4} y{rec['yrs']:2} {rec['y0']}-{rec['y1']} med {rec['med']} avg {rec['avg']} mx {rec['mx']} st{len(hits)} {[st[s][0][:30] for s in hits][:3]}")
json.dump(out,open(S+'/lq_wqp.json','w'),indent=0)
