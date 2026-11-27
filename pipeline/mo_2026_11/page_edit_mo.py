"""Put the Missouri springs pass on the page (Nov 27, 2026). Builds on fsi_2026_11/page_edit_fsi.py, coords_links.py and
spring_line.py. Idempotent: once applied, a rerun only refreshes the MOS data.
- const MOS: mos.json rows (build_mo.py): [lat, lon, name, county, magnitude, look, photo, "", words, "mo", 1982 page,
  1944 page, 1944 photo page, public land, 1982 photo, photo page, photo credit].
- fsiFind looks through Florida (FSI) and Missouri (MOS) springs, so Missouri springs and springheads get the same look badge,
  words and photo as Florida ones, plus links to their pages in the 1944 and 1982 Missouri spring books.
- The Spring look menu covers Florida and Missouri; "with a photo" counts a Commons photo or a photo in either book.
- springLL (the vent used for coordinates and the straight line) uses the Missouri inventory point when it matches by name
  within 300 m, as it does with the Florida survey point.
Usage: page_edit_mo.py <page.html>"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
page = sys.argv[1]; h = open(page).read()
N = json.load(open(HERE + "/mos.json"))
nb = sum(1 for r in N if r[5] == "blue"); nc = sum(1 for r in N if r[5] == "clear"); nph = sum(1 for r in N if r[6])
NOTE = (f'''  <p><b>Missouri springs.</b> Missouri has no equivalent of the Florida Springs Institute's map, so its springs draw on three sources: the '''
        f'''<a href="https://gis.dnr.mo.gov/host/rest/services/water/water_springs/MapServer/0" target="_blank" rel="noopener">Department of Natural Resources spring inventory</a> '''
        f'''(the exact point, size, public-land flag and field notes for 4,457 springs), '''
        f'''<a href="https://digital.library.missouri.edu/sites/default/files/2025-02/mu_417688.pdf" target="_blank" rel="noopener"><i>The Large Springs of Missouri</i></a> (Missouri Geological Survey, 1944; 118 springs, with photo plates of the best known) and '''
        f'''<a href="https://share.mo.gov/nr/mgs/MGSData/Books/Water%20Resources/Springs%20of%20Missouri/WR29revised.pdf" target="_blank" rel="noopener"><i>Springs of Missouri</i></a> (1982; about 100 springs, many with photos). '''
        f'''The books mostly describe settings (bluffs, caves, mills, wilderness gorges) rather than colour, so only {nb} Missouri springs are rated clear blue and {nc} clear, among them Blue Spring on the Current River (the 1944 book calls it "the deepest blue of all"), Alley, Round, Warner Bay, Boiling, Kelly and Big Spring in Laclede County. '''
        f'''Each Missouri spring and springhead links to its pages in both books and, where one exists, a photo from Wikimedia Commons ({nph} springs: taken within 450 m of the vent and titled with the spring's name, or found by name and checked by hand). The 1982 book's pages are given as printed; its PDF numbers them a little differently.</p>\n''')
data = "const MOS=" + json.dumps(json.load(open(HERE + "/mos.json")), separators=(",", ":"), ensure_ascii=False) + ";\n"
if "const MOS=" in h:
    h = re.sub(r"const MOS=\[.*?\];\n", lambda m: data, h, count=1, flags=re.S)
    h = re.sub(r"  <p><b>Missouri springs\.</b>.*?</p>\n", lambda m: NOTE, h, count=1, flags=re.S)
    open(page, "w").write(h); print("MOS data and note refreshed"); sys.exit()
assert h.count("const SRC=[") == 1; h = h.replace("const SRC=[", data + "const SRC=[")
def rep(old, new):
    global h
    assert h.count(old) == 1, (h.count(old), old[:120]); h = h.replace(old, new)

rep('''const FSIC=new Map();''', '''const FSIC=new Map(); let SPLC=null; const SPL=()=>SPLC||(SPLC=typeof MOS!=="undefined"?FSI.concat(MOS):FSI);
const FSST=new Set(["FL","MO"]);
const B44="https://digital.library.missouri.edu/sites/default/files/2025-02/mu_417688.pdf", B82="https://share.mo.gov/nr/mgs/MGSData/Books/Water%20Resources/Springs%20of%20Missouri/WR29revised.pdf";''')
rep('''  for(const r of FSI){const d=Math.hypot(''', '''  for(const r of SPL()){const d=Math.hypot(''')
rep('''function fsiRow(r){if(r[16]!=="FL")return null;''', '''function fsiRow(r){if(!FSST.has(r[16]))return null;''')
rep('''function fsiHead(hd){return hd[1]==="FL"?fsiFind(hd[8],hd[9],hd[0]):null}''', '''function fsiHead(hd){return FSST.has(hd[1])?fsiFind(hd[8],hd[9],hd[0]):null}''')
rep('''v==="photo"?!!f[6]:true}''', '''v==="photo"?!!(f[6]||f[12]||f[14]):true}''')
rep('''function fsiBox(f){if(!f||!(f[5]||f[6]||f[7]))return "";''', '''function fsiBox(f){if(f&&f[9]==="mo")return moBox(f); if(!f||!(f[5]||f[6]||f[7]))return "";''')
rep('''function fsiPop(f){if(!f||!(f[5]||f[6]))return "";''', '''function fsiPop(f){if(f&&f[9]==="mo")return moPop(f); if(!f||!(f[5]||f[6]))return "";''')
JS = r'''/* ---------- Missouri springs: inventory, 1944 and 1982 spring books, Commons photos (pipeline/mo_2026_11) ---------- */
function moLinks(f){const L=[];
  if(f[6])L.push(`<a href="${esc(f[15]||f[6])}" target="_blank" rel="noopener" title="${esc(f[16]||"")}">Photo</a>`);
  if(f[12])L.push(`<a href="${B44}#page=${f[12]}" target="_blank" rel="noopener">1944 photo</a>`);
  if(f[11])L.push(`<a href="${B44}#page=${f[11]}" target="_blank" rel="noopener">1944 description</a>`);
  if(f[10])L.push(`<a href="${B82}" target="_blank" rel="noopener" title="Springs of Missouri (1982), page ${f[10]} as printed">Springs of Missouri, p. ${f[10]}${f[14]?" (photo)":""}</a>`);
  return L.join("")}
function moBox(f){if(!(f[5]||f[6]||f[8]||f[10]||f[11]))return "";
  const img=f[6];
  return `<div class="fsi">${img?`<a class="fsi-ph" href="${esc(f[15]||img)}" target="_blank" rel="noopener"><img src="${esc(img)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.parentNode.remove()"></a>`:""}<div>${fsiBadge(f)||`<span class="fl">Look not described</span>`} <span class="fsi-src">Missouri spring inventory: ${esc(f[2])}${f[4]<9?`, magnitude ${f[4]}`:""}${f[13]?" · public land":""}</span>${f[8]?`<q>${esc(f[8])}</q>`:""}<span class="fsi-l">${moLinks(f)}</span>${f[16]?`<span class="fsi-cr">Photo: ${esc(f[16])}</span>`:""}</div></div>`}
function moPop(f){if(!(f[5]||f[6]||f[8]||f[12]))return "";
  return `<div class="pp-sub">${fsiBadge(f)||"Missouri spring inventory"}${f[8]?` <i>${esc(f[8].length>160?f[8].slice(0,157)+"…":f[8])}</i>`:""} ${moLinks(f).replace(/<a /g,'<a style="margin-right:8px" ')}</div>`}
'''
rep("/* ---------- clickable spring coordinates", JS + "/* ---------- clickable spring coordinates")
rep('''  if(r[16]==="FL"&&typeof fsiRow==="function"){const f=fsiRow(r);''', '''  if(FSST.has(r[16])&&typeof fsiRow==="function"){const f=fsiRow(r);''')
rep('''<option value="blue">Clear blue springs only (Florida)</option><option value="clear">Clear or blue springs (Florida)</option><option value="photo">Springs with a photo (Florida)</option>''',
    '''<option value="blue">Clear blue springs only (FL, MO)</option><option value="clear">Clear or blue springs (FL, MO)</option><option value="photo">Springs with a photo (FL, MO)</option>''')
rep('''.fsi-src{font-size:11.5px}''', '''.fsi-src{font-size:11.5px}.fsi-cr{display:block;font-size:10.5px;opacity:.75;margin-top:2px}''')
rep('''  <p><b>Also clear and blue</b> lists''', NOTE + '''  <p><b>Also clear and blue</b> lists''')
SRCL = (' ["Missouri Department of Natural Resources: spring inventory (points, magnitude, field notes)","https://gis.dnr.mo.gov/host/rest/services/water/water_springs/MapServer/0"],\n'
        ' ["Beckman & Hinchey: The Large Springs of Missouri (Missouri Geological Survey, 1944; University of Missouri Digital Library scan)","https://digital.library.missouri.edu/sites/default/files/2025-02/mu_417688.pdf"],\n'
        ' ["Vineyard & Feder: Springs of Missouri (Missouri Water Resources Report 29, revised 1982)","https://share.mo.gov/nr/mgs/MGSData/Books/Water%20Resources/Springs%20of%20Missouri/WR29revised.pdf"],\n'
        ' ["Wikimedia Commons: photos near Missouri springs (credited on each photo)","https://commons.wikimedia.org/"],\n')
i = h.index("const SRC=[") + len("const SRC=["); assert h[i] == "\n"; h = h[:i + 1] + SRCL + h[i + 1:]
open(page, "w").write(h); print("Missouri springs added to the page")
