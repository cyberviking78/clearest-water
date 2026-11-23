"""Turn the Mountain Lakes tab into Wild Lakes (Nov 19, 2026): new name and intro, a "how it qualified" filter (blue satellite colour or
a wild shore) in place of the elevation filter, each lake's colour or shore score on its row and popup, and the new explanation.
Run on a page that has the Mountain Lakes tab (ml_tab.py + ml_v2.py). Idempotent. Usage: wl_tab.py page.html"""
import sys
p = sys.argv[1]; h = open(p).read()
if "How the wild lake search works" in h: print("wild lakes already applied"); sys.exit()
def rep(a, b, n=1):
    global h
    assert h.count(a) == n, (h.count(a), a[:100]); h = h.replace(a, b)
rep('ml:"Houses and land on the shore of mountain lakes and ponds in the West, named or not: montane, subalpine and alpine lakes, the cold, clear, sapphire-blue kind, with a satellite link to check the water."',
    'ml:"Houses and land on the shore of clear, unspoiled lakes and ponds, named or not, at any elevation, in the West and in Tennessee, West Virginia, North Carolina, Maine, Vermont and New Hampshire: lakes whose water reads blue from satellite, and ponds ringed by forest or wild land. Each has a satellite link to check the water."')
rep(">Mountain Lakes<", ">Wild Lakes<")
rep("<h2>How the mountain lake search works</h2>", "<h2>How the wild lake search works</h2>")
rep("x[0])).size} mountain lakes (${nu} unnamed)", "x[0])).size} wild lakes (${nu} unnamed)")
rep("more listings reach a mountain lake's shore at over $750,000", "more listings reach a wild lake's shore at over $750,000")
rep("(nM?` · ${nM} on mountain lakes`:\"\")", "(nM?` · ${nM} on wild lakes`:\"\")")
rep(">On a mountain lake<", ">On a wild lake<")
rep(">Mountain lake<", ">Wild lake<")
rep("Show mountain lakes with listings on the shore", "Show wild lakes with listings on the shore")
rep("/* mountain lakes */", "/* wild lakes */"); rep("/* ---------- mountain lakes tab ---------- */", "/* ---------- wild lakes tab ---------- */")
# filter: how the lake qualified, in place of elevation
rep('<select id="mlelev" aria-label="Lake elevation" data-mode="ml" hidden><option value="0">Any elevation</option><option value="5000">5,000 ft and up</option><option value="7000">7,000 ft and up</option><option value="9000">9,000 ft and up</option></select>',
    '<select id="mlelev" aria-label="How the lake qualified" data-mode="ml" hidden><option value="">Blue water and wild shores</option><option value="colour">Blue water (satellite colour)</option><option value="shore">Wild shore (mostly ponds)</option></select>')
rep('emin=+document.getElementById("mlelev").value', 'how=document.getElementById("mlelev").value')
rep('&&k[3]>=emin&&', '&&(how!=="colour"&&how!=="shore"||k[10]===how)&&')
# colour / shore on each lake row and popup
rep('''${k[7]?` · <b>${k[7]} ft clear</b> (measured)`:""} · near ${esc(L[0][8])}</small>''',
    '''${k[7]?` · <b>${k[7]} ft clear</b> (measured)`:""}${k[8]?` · <b>blue water</b> from satellite (${k[8]} nm)`:k[9]!=null?` · <b>wild shore</b>, ${k[9]}% forest or wild land`:""} · near ${esc(L[0][8])}</small>''')
rep('''${k[7]?` · ${k[7]} ft clear (measured)`:""}</div>''',
    '''${k[7]?` · ${k[7]} ft clear (measured)`:""}${k[8]?` · blue water from satellite`:k[9]!=null?` · wild shore (${k[9]}%)`:""}</div>''')
# explanation
a = h.index("  <p><b>Lakes.</b> Every lake and pond of an acre or more in the western mountains, named or not, at montane, subalpine or alpine height")
b = h.index("  <p><b>Property.</b>", a)
NEW = """  <p><b>Lakes.</b> Every lake and pond of an acre or more, named or not and at any elevation, in Washington, Oregon, California, Idaho, Montana, Wyoming, Nevada, Utah, Colorado, Arizona, New Mexico, Tennessee, West Virginia, North Carolina, Maine, Vermont and New Hampshire, from the Census Bureau's water maps, is checked three ways. <b>Is it really water?</b> The 2021 national land-cover map (USGS NLCD, 30 m) must show it as open water; this drops dried-up and seasonal ponds and old map outlines, the "lakes" with no water in them. River channels, ditches, tailings and sewage ponds, lakes wholly inside a national park or wilderness area, and any lake the Lakes tab measures at under 15 ft of clarity are left out.</p>
  <p><b>Blue water.</b> For larger lakes, usually 25 acres and up, satellites have recorded the water's colour: LimnoSat-US (Topp and others, 2020) gives the dominant colour of about 53,000 US lakes in Landsat images, and this uses the typical summer colour from 2013 to 2020. A lake is kept when it reads blue, a dominant wavelength of 505 nm or less, about the bluest third of US lakes. For scale: Crater Lake 472, Tahoe 478, Sebago 484, Flathead 486, Summersville 495, Fontana 498, Watauga 503; murky Utah Lake 549, Upper Klamath 553, western Lake Erie 560. A colour reading is an average over the summers and over the lake; a lake can be clearer in spring or in its deep middle.</p>
  <p><b>Wild shore.</b> Ponds and lakes too small for the satellite record are kept when the land within 200 m of the water is at least 75% forest, shrub, grassland, wetland or bare rock, with no more than 5% development and 10% farmland. That keeps the pond in the woods and leaves out the farm pond, the golf course and the subdivision basin. It cannot see the water itself, so check each one with its <b>Satellite</b> link. Where the lake has been measured since 2000, its measured clarity shows too. That leaves <span class="mlnl"></span> lakes.</p>
  <p><b>Why some states have so few.</b> <span class="mlhi"></span> Where a state has few listings at any price, its clear lakes lie mostly inside national forest, so the shore is public land. Where most listings are above the range, price is the barrier.</p>
"""
h = h[:a] + NEW + h[b:]
open(p, "w").write(h); print("wild lakes applied")
