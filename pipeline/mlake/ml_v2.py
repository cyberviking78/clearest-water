"""Mountain Lakes, second version (Nov 18, 2026): new explanation (USGS NHD check, big-lake rule, measured clarity, the
unmeasured dam reservoirs left out), measured clarity shown on each lake, and a live note of the shore listings above $750,000
by state (ML.H) explaining why some states have so few. Applies to a page that already has the tab (ml_tab.py), and to
ml_tab.py itself so a fresh build matches. Idempotent. Usage: ml_v2.py page.html"""
import re, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
LAKES = """  <p><b>Lakes.</b> Every lake and pond of an acre or more in the western mountains, named or not, at montane, subalpine or alpine height: no more than 1,300 m (4,300 ft) below the regional treeline, with the land rising at least 350 m around it. That is roughly 6,700 ft and up in central Colorado, about 6,000 ft around Lake Tahoe, 4,300 ft in the Oregon Cascades, 2,800 ft in the Washington Cascades and 3,200 ft around Glacier. Big lakes (50 acres or more) in deep mountain valleys count too even when they sit lower, when they are at least 1,000 ft up and the land rises 600 m (2,000 ft) within 8 km: Priest, Pend Oreille, Coeur d'Alene, Chelan, Wenatchee, Wallowa and Bear Lake. Elevations are from PRISM's 800 m grid, so a lake's can be off by a couple of hundred feet.</p>
  <p><b>Checked against USGS water maps.</b> Every lake is checked against the USGS National Hydrography Dataset and kept only when it maps the water as a lake or pond that holds water all year. That removes river channels the Census map had drawn as lake area (the South Platte at Hartsel, the Big Thompson at Drake, Clear Creek at Dumont, the Salmon at Stanley), dry and seasonal ponds, marshes and stock tanks, and gives each lake its official USGS name. A lake listed as unnamed has no name on any federal map but is a real, year-round pond.</p>
  <p><b>Clarity.</b> Where the lake has been measured since 2000 (Secchi-disk readings from the Water Quality Portal, USGS, EPA and state agencies), the lake shows its measured clarity, and any lake measured under 15 ft, your cut-off, is left out: Grand Lake (10 ft), Lake Granby, Shadow Mountain, Steamboat, Upper Klamath (3 ft), Canyon Ferry, Koocanusa and others. Most high lakes have never been measured; cold, high lakes in rock and forest basins are usually clear and deep blue, but check each one with its <b>Satellite</b> link. Large man-made reservoirs with no clarity record are left out (Lake Almanor, Big Bear, Ennis, Hebgen, Alder, Lake Roosevelt), and so are lakes wholly inside a national park or wilderness area, where nothing is for sale. That leaves <span class="mlnl"></span> lakes.</p>
  <p><b>Why some states have so few.</b> <span class="mlhi"></span> Where a state has few listings at any price, as in Wyoming and Oregon, its mountain lakes lie almost entirely inside national forest, so the shore is public land. Where most listings are above the range, as at Lake Chelan, price is the barrier.</p>"""
def patch(h, js_only=False):
    if "mlhi" in h: return h, False
    # explanation: replace the Lakes and Why these paragraphs
    a = h.index("  <p><b>Lakes.</b> Every lake and pond of an acre or more in the western mountains, named or not, from the Census Bureau's TIGER water maps")
    b = h.index("  <p><b>Property.</b> Houses and land on Redfin priced $100,000 to $750,000", a)
    h = h[:a] + LAKES + "\n" + h[b:]
    # measured clarity on each lake row and in the popup
    old = '''${k[2]>=10?Math.round(k[2]).toLocaleString():k[2]} acres · ${k[3].toLocaleString()} ft · near ${esc(L[0][8])}</small>'''
    assert h.count(old) == 1, "row"
    h = h.replace(old, '''${k[2]>=10?Math.round(k[2]).toLocaleString():k[2]} acres · ${k[3].toLocaleString()} ft${k[7]?` · <b>${k[7]} ft clear</b> (measured)`:""} · near ${esc(L[0][8])}</small>''')
    old = '''<div class="pp-water">On <b>${esc(mlName(k))}</b> · ${k[3].toLocaleString()} ft · ${k[2]>=10?Math.round(k[2]):k[2]} acres</div>'''
    assert h.count(old) == 1, "popup"
    h = h.replace(old, '''<div class="pp-water">On <b>${esc(mlName(k))}</b> · ${k[3].toLocaleString()} ft · ${k[2]>=10?Math.round(k[2]):k[2]} acres${k[7]?` · ${k[7]} ft clear (measured)`:""}</div>''')
    # live note: shore listings above $750k by state
    old = 'document.querySelectorAll(".mlnl").forEach(e=>e.textContent=ML.nlakes.toLocaleString());'
    assert h.count(old) == 1, "mlnl"
    h = h.replace(old, old + '''
document.querySelectorAll(".mlhi").forEach(e=>{const H=(ML.H||[]).filter(x=>x[18]===0), c={}; H.forEach(x=>c[x[9]]=(c[x[9]]||0)+1);
  const L0=ML.L.filter(x=>x[18]===0), c0={}; L0.forEach(x=>c0[x[9]]=(c0[x[9]]||0)+1);
  const st=Object.keys(c).sort((a,b)=>c[b]-c[a]);
  e.textContent=H.length?`The search also looks above your price range: ${H.length.toLocaleString()} more listings reach a mountain lake's shore at over $750,000 (${st.map(s=>`${s} ${c[s]}`).join(", ")}), against ${L0.length.toLocaleString()} at $750,000 or less. ${["WY","OR"].map(s=>`${NAMES[s]||s}: ${c0[s]||0} in range, ${c[s]||0} above`).join("; ")}.`:""});''')
    return h, True
p = sys.argv[1]; h = open(p).read(); h, ch = patch(h); open(p, "w").write(h); print("mountain lakes v2", "applied" if ch else "already applied")
# the tab builder: same text and code for a fresh build
t = open(HERE + "/ml_tab.py").read()
if "mlhi" not in t:
    a = t.index("  <p><b>Lakes.</b> Every lake and pond of an acre or more in the western mountains, named or not, from the Census Bureau's TIGER water maps")
    b = t.index("  <p><b>Property.</b>", a); t = t[:a] + LAKES + "\n" + t[b:]
    open(HERE + "/ml_tab.py", "w").write(t)
    print("ml_tab.py text updated (run ml_v2.py on a freshly built page for the code changes)")
