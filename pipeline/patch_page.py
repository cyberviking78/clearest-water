"""Write listing data, run info and the listing UI into the Clearest Water page. Safe to run repeatedly."""
import json, re, sys

RENDER = r'''const TIER=[["on","On the water"],["near","Near · MLS waterfront"],["un","MLS waterfront · shore not mapped"]];
const money=n=>"$"+n.toLocaleString("en-US");
const fmtD=s=>s?new Date(s+"T12:00:00").toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"}):"";
const NEAR=()=>{const e=document.getElementById("incnear");return !e||e.checked};
function listingsFor(k,wi,pt,nw){return (LS[k]||[]).filter(x=>x[0]===wi&&(!pt||x[3]===pt)&&(!nw||x[15])&&wtOK(x[12])&&(NEAR()||x[1]!==1))}
function lItem(x,g){
  const [wi,t,price,ty,beds,baths,sqft,ac,addr,city,dom,dist,path,flag,first,isNew]=x;
  const facts=ty==="h"?[beds!=null?beds+" bd":null,baths!=null?baths+" ba":null,sqft?sqft.toLocaleString()+" sq ft":null,ac?ac+" ac":null]:["Land",ac?ac+" ac":null];
  const d=dist!=null?(t===0&&dist<15?"at the shore":`${dist} m from shore`):"";
  const seen=first&&first!==RUN.date?` · on our list since ${fmtD(first)}`:"";
  return `<li${isNew?' class="is-new"':""}><span class="pr">${money(price)}${isNew?' <span class="newb">New</span>':""}</span><span class="ad">${esc(addr)}, ${esc(city)}<small>${facts.filter(Boolean).join(" · ")}${dom!=null?` · ${dom} days listed`:""}${d?` · ${d}`:""}${seen}</small></span><span><span class="tier ${TIER[t][0]}">${t===0&&!flag?"On the water · not marked waterfront":TIER[t][1]}</span> <a href="https://www.redfin.com${esc(path)}" target="_blank" rel="noopener">Redfin</a></span>${wtLine(path)}${g?springPair(g,x):""}</li>`}
function renderSprings(){
  const q=document.getElementById("q").value.trim().toLowerCase(), s=sel.value, pt=document.getElementById("ptype").value,
    only=document.getElementById("haslist").checked, nw=document.getElementById("newonly").checked;
  const hitS=r=>(!s||r[16]===s)&&(!q||(r[1]+" "+r[2]+" "+r[11]+" "+NAMES[r[16]]).toLowerCase().includes(q)||r[16].toLowerCase()===q);
  const hitR=r=>(!s||r[13]===s)&&(!q||(r[1]+" "+r[2]+" "+r[10].join(" ")+" "+NAMES[r[13]]).toLowerCase().includes(q)||r[13].toLowerCase()===q);
  const block=(g,wi)=>{const L=listingsFor(g,wi,pt,nw); const c=[0,1,2].map(t=>L.filter(x=>x[1]===t).length), cn=L.filter(x=>x[15]).length;
    const chips=(cn?`<span class="cnt new">${cn} new</span>`:"")+[[0,"on"],[1,"near"],[2,"un"]].filter(([t])=>c[t]).map(([t,cl])=>`<span class="cnt ${cl}">${c[t]} ${["on the water","near","unmapped"][t]}</span>`).join("");
    return L.length?`<details class="lst"${nw?" open":""}><summary>${L.length} listing${L.length===1?"":"s"} ${chips}</summary><ul class="lsts">${L.map(x=>lItem(x,g)).join("")}</ul></details>`:`<div class="none-l">No ${pt==="h"?"houses":pt==="l"?"land":"listings"} on Redfin on this water right now.</div>`};
  const keep=(g,wi)=>!(only||nw||WTD())||listingsFor(g,wi,pt,nw).length;
  const val=(m,a,b)=>`<div class="val"><b>${m<1?m.toFixed(2):m.toFixed(1)}</b> <span class="u">NTU</span><span class="sub">IQR ${a}–${b}</span></div>`;
  const zb=bb=>[bb[1],bb[3],bb[0],bb[2]];
  const S=FSD.springs.map((r,i)=>[r,i+1]).filter(([r])=>hitS(r)&&keep(r[17],r[0])&&fsiOKs(r));
  const R=FSD.rivers.map((r,i)=>[r,i+1]).filter(([r])=>hitR(r)&&keep(r[14],r[0]));
  let h=`<article class="state nat"><div class="shead"><h2>Springs by clarity${s?" · "+esc(NAMES[s]):""}</h2><span class="count">${S.length} of ${FSD.springs.length}</span></div><ol>`;
  S.forEach(([r,rank])=>{const [wi,name,cty,m,a,b,n,yrs,y0,y1,sites,runs,bb,lwp,ploc,meth,st,g]=r;
    h+=`<li class="row"><span class="rk">${rank}</span><div class="nm">${esc(name)}<span class="st-tag">${st}</span><small>${esc(cty)} ${st==="LA"?"Parish":"Co."}, ${esc(NAMES[st])} · ${runs?`flows into ${esc(runs)} · `:""}${n} readings · ${yrs} years, ${y0}–${y1}${sites>1?` · ${sites} sites`:""}${gmSpring(r)}</small></div>${val(m,a,b)}
      ${fsiBox(fsiRow(r))}${block(g,wi)}<div class="links"><a href="${zUrl(zb(bb),"waterfront")}" target="_blank" rel="noopener">Zillow waterfront</a><a class="alt" href="${zUrl(zb(bb),null)}" target="_blank" rel="noopener">Zillow all</a><a class="alt" href="${LW+esc(lwp)}" target="_blank" rel="noopener">LandWatch: ${esc(cty)}</a></div></li>`});
  if(!S.length)h+=`<li class="row"><span></span><div class="nm"><small>No springs match.</small></div></li>`;
  const B=(typeof FSB!=="undefined"?FSB:[]).filter(r=>hitS(r)&&keep(r[17],r[0])&&fsiOKs(r));
  if(B.length){h+=`</ol></article><article class="state nat"><div class="shead"><h2>Also clear and blue · Florida field surveys</h2><span class="count">${B.length} of ${FSB.length}</span></div><p class="fsinote">Florida springs the state's field surveys describe as clear and blue that aren't in the ranking above, most because they have fewer than 6 turbidity readings. Found through the Florida Springs Institute; sorted by size.</p><ol>`;
    B.forEach(r=>{const [wi,name,cty,m,a,b,n,yrs,y0,y1,sites,runs,bb,lwp,ploc,meth,st,g,ll,mag,nv]=r;
      h+=`<li class="row"><span class="rk mg" title="Magnitude ${mag}">M${mag}</span><div class="nm">${esc(name)}<span class="st-tag">${st}</span><small>${esc(cty)} Co., ${esc(NAMES[st])} · magnitude ${mag}${nv>1?` · ${nv} vents`:""} · ${runs?`flows into ${esc(runs)} · `:""}${n?`${n} turbidity reading${n>1?"s":""}, ${y0===y1?y0:`${y0}–${y1}`}`:"no turbidity readings on record"}${gmSpring(r)}</small></div>${m!=null?val(m,a,b):`<div class="val"><span class="sub">no turbidity record</span></div>`}
      ${fsiBox(fsiRow(r))}${block(g,wi)}<div class="links"><a href="${zUrl(zb(bb),"waterfront")}" target="_blank" rel="noopener">Zillow waterfront</a><a class="alt" href="${zUrl(zb(bb),null)}" target="_blank" rel="noopener">Zillow all</a><a class="alt" href="${LW+esc(lwp)}" target="_blank" rel="noopener">LandWatch: ${esc(cty)}</a></div></li>`})}
  h+=`</ol></article><article class="state nat"><div class="shead"><h2>Spring-fed rivers${s?" · "+esc(NAMES[s]):""}</h2><span class="count">${R.length} of ${FSD.rivers.length}</span></div><ol>`;
  R.forEach(([r,rank])=>{const [wi,name,cty,m,a,b,n,sites,y0,y1,srcs,bb,lwps,st,g]=r;
    h+=`<li class="row"><span class="rk">${rank}</span><div class="nm">${esc(name)}<span class="st-tag">${st}</span><small>${esc(cty)} ${st==="LA"?"Parish":"Co."}, ${esc(NAMES[st])} · ranked springs nearby: ${esc(srcs.join(", "))} · ${n} samples · ${y0}–${y1}</small></div>${val(m,a,b)}
      ${block(g,wi)}<div class="links"><a href="${zUrl(zb(bb),"waterfront")}" target="_blank" rel="noopener">Zillow waterfront</a><a class="alt" href="${zUrl(zb(bb),null)}" target="_blank" rel="noopener">Zillow all</a>${lwps.map((p,i)=>`<a class="alt" href="${LW+esc(p)}" target="_blank" rel="noopener">LandWatch: ${esc(cty.split(", ")[i]||"")}</a>`).join("")}</div></li>`});
  if(!R.length)h+=`<li class="row"><span></span><div class="nm"><small>No rivers match.</small></div></li>`;
  document.getElementById("list").innerHTML=h+"</ol></article>";
}
function renderProperty(){
  const q=document.getElementById("q").value.trim().toLowerCase(), s=sel.value, pt=document.getElementById("ptype").value,
    only=document.getElementById("haslist").checked, nw=document.getElementById("newonly").checked;
  let html="";
  keys.forEach(k=>{if(s&&s!==k)return; const rows=(PR[k]||[]).filter(r=>!r[7]);
    const stateHit=!q||NAMES[k].toLowerCase().includes(q)||k.toLowerCase()===q;
    let shown=(stateHit?rows:rows.filter(r=>(r[1]+" "+r[5].map(c=>c[0]).join(" ")).toLowerCase().includes(q))).map(r=>[r,PR[k].indexOf(r)]);
    if(only||nw||WTD())shown=shown.filter(([r,wi])=>listingsFor(k,wi,pt,nw).length);
    if(!shown.length&&!(stateHit&&!rows.length&&!only&&!nw))return;
    const all=(LS[k]||[]).filter(x=>(!pt||x[3]===pt)&&(!nw||x[15])&&wtOK(x[12])&&(NEAR()||x[1]!==1)), nOn=all.filter(x=>x[1]===0).length, nNew=all.filter(x=>x[15]).length;
    html+=`<article class="state"><div class="shead"><h2>${esc(NAMES[k])}<span class="ab">${k}</span></h2><span class="count">${all.length} listing${all.length===1?"":"s"}${all.length?` · ${nOn} on the water`:""}${nNew&&!nw?` · ${nNew} new`:""}</span></div><ol>`;
    shown.forEach(([r,wi])=>{const cty=r[5].map(c=>c[0]).join(", ");
      const lw=r[5].map(c=>`<a class="alt" href="${LW+esc(c[1])}" target="_blank" rel="noopener">LandWatch: ${esc(c[0])}</a>`).join("");
      const L=listingsFor(k,wi,pt,nw); const c=[0,1,2].map(t=>L.filter(x=>x[1]===t).length), cn=L.filter(x=>x[15]).length;
      const chips=(cn?`<span class="cnt new">${cn} new</span>`:"")+[[0,"on"],[1,"near"],[2,"un"]].filter(([t])=>c[t]).map(([t,cl])=>`<span class="cnt ${cl}">${c[t]} ${["on the water","near","unmapped"][t]}</span>`).join("");
      html+=`<li class="row"><span class="rk type">${r[0]==="l"?"Lake":r[0]==="g"?"Great Lake":"River"}</span><div class="nm">${esc(r[1])}<small>${r[0]==="g"?`Great Lakes shoreline · ${esc(r[3])} · only listings on the lake`:r[2]?`#${r[2]} ${r[0]==="l"?"clearest lake":"clearest river"} · ${esc(r[3])}`:"Known for clear water · not measured"}${cty?` · ${r[0]==="g"&&r[5].length>3?r[5].length+" counties":esc(cty)+" "+(k==="LA"?"Parish":"Co.")}`:""}</small></div><span></span>
        ${L.length?`<details class="lst"${nw?" open":""}><summary>${L.length} listing${L.length===1?"":"s"} ${chips}</summary><ul class="lsts">${L.map(lItem).join("")}</ul></details>`:`<div class="none-l">No ${pt==="h"?"houses":pt==="l"?"land":"listings"} on Redfin on the water right now.</div>`}
        ${r[0]==="g"?(r[5].length>3?"":`<div class="links">${lw}</div>`):`<div class="links"><a href="${zUrl(r[4],"waterfront")}" target="_blank" rel="noopener">Zillow waterfront</a><a class="alt" href="${zUrl(r[4],null)}" target="_blank" rel="noopener">Zillow all</a>${lw}</div>`}</li>`});
    html+="</ol>";
    if(!rows.length)html+=`<div class="snote"><strong>Gaps.</strong> This state has no lakes or rivers on the lists.</div>`;
    html+="</article>"});
  document.getElementById("list").innerHTML=html||`<p class="empty">${nw?"No new listings match.":"No lake, river or state matches that search."}</p>`;
}
'''

FACTS = r'''const PL=Object.entries(LS).filter(([k])=>k!=="FS"&&k!=="SP").flatMap(([k,v])=>v), tot=PL.length, nn=PL.filter(x=>x[15]).length;
    document.getElementById("facts").innerHTML=`<span class="chip"><b>${tot.toLocaleString()}</b> listings on or near the water</span>`+(RUN.prev?`<span class="chip"><b>${nn}</b> new since ${fmtD(RUN.prev)}</span><span class="chip">${RUN.gone} sold or removed</span>`:`<span class="chip">First check · new listings are flagged from next month</span>`)+`<span class="chip">Redfin, ${fmtD(RUN.date)}</span>`;'''


def patch(page, LS, meta):
    h = open(page).read()

    def rep(old, new):
        nonlocal h
        assert h.count(old) == 1, "pattern not found once: " + old[:80]
        h = h.replace(old, new)

    data = "const LS=" + json.dumps(LS, separators=(",", ":"), ensure_ascii=False) + ";\nconst RUN=" + json.dumps(meta, separators=(",", ":")) + ";\n"
    h = re.sub(r"const LS=\{.*?\};\n(const RUN=\{.*?\};\n)?", lambda m: data, h, count=1, flags=re.S)
    if 'id="newonly"' not in h:
        rep('<label class="toggle" data-mode="property" hidden><input id="haslist" type="checkbox"> Only waters with listings</label>',
            '<label class="toggle" data-mode="property" hidden><input id="haslist" type="checkbox"> Only waters with listings</label>\n  <label class="toggle" data-mode="property" hidden><input id="newonly" type="checkbox"> Only new listings</label>')
        rep(".st-tag{", ".newb{font-family:var(--body);font-size:10.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--surface);background:var(--lake);border-radius:4px;padding:1px 5px;vertical-align:2px;margin-left:4px}\nul.lsts li.is-new{border-color:var(--lake)}\n.cnt.new{background:var(--lake);color:var(--surface)}\n.st-tag{")
        rep('"ptype","haslist"]', '"ptype","haslist","newonly"]')
    start = h.index("const TIER="); end = h.index("function renderNational(){")
    h = h[:start] + RENDER + h[end:]
    h = re.sub(r'(if\(m==="property"\)\{\n)    (?:const (?:tot|PL)=.*?\n    )?document\.getElementById\("facts"\)\.innerHTML=`.*?`;', lambda m: m.group(1) + "    " + FACTS, h, count=1, flags=re.S)
    h = re.sub(r"collected on (?:October 28, 2026|<span class=\"rundate\">[^<]*</span>)",
               lambda m: f'collected on <span class="rundate">{meta["date"]}</span>', h, count=1)
    if "rundate" in h and "querySelectorAll(\".rundate\")" not in h:
        rep("setMode(mode);\n</script>", 'document.querySelectorAll(".rundate").forEach(e=>e.textContent=fmtD(e.textContent));\nsetMode(mode);\n</script>')
    if "<b>New</b> marks listings" not in h:
        rep("<b>Near · MLS waterfront</b> means", "<b>New</b> marks listings that weren't on Redfin at the previous monthly check. <b>Near · MLS waterfront</b> means")
    open(page, "w").write(h)
    return len(h)


if __name__ == "__main__":
    import os
    root = os.path.dirname(os.path.abspath(__file__))
    patch(sys.argv[1], json.load(open(os.path.join(root, "listings.json"))),
          {k: v for k, v in json.load(open(os.path.join(root, "meta.json"))).items() if k != "urls"})
