# Monthly waterfront-listing refresh

All Redfin searches go through `rfjson.py`, which runs the usual gis-csv query against Redfin's map-data endpoint and returns the same CSV layout.
The CSV export itself leaves out listings from MLSs that bar downloads (central Indiana, Minneapolis, Charlotte, Seattle and many more).

This folder travels with the "Clearest Water by State" artifact so a scheduled run can rebuild the Property tab.

Steps for a run:
1. Read every file under `pipeline/` from the artifact into a local folder `pipeline/` (keep the `shore/` subfolder), and read the page itself (`index.html`) to `page.html`.
2. `pip install --break-system-packages -q pandas shapely`
3. `python3 -W ignore pipeline/run.py page.html` (about 1.5 hours; four searches at a time, with pauses between Redfin requests).
   Needs network access to www.redfin.com.
4. Republish `page.html` to the same artifact URL, together with the updated
   `pipeline/seen.json`, `pipeline/meta.json` and `pipeline/listings.json`.
5. Report: the last line of output gives total listings, how many are new since the previous run, and how many are gone.
   New listings are in `pipeline/listings.json` (index 15 is true); index 0 is the water index into `props.json[state]`; indices 16–17 are latitude and longitude, which the Map tab plots.
   The Map tab also needs `map/counties-10m.json` (state and county outlines); it is already published and does not change between runs.

Springheads tab (run after step 3, before republishing):
- `python3 -W ignore pipeline/heads/run_heads.py page.html` (about 40 minutes; about 2,100 Redfin searches for houses and land from $100k with no upper price limit). Needs network access to www.redfin.com,
  services9.arcgis.com and services1.arcgis.com (Florida and Utah parcels), feature.geographic.texas.gov, gis.arkansas.gov,
  permitting.sjrwmd.com, www25.swfwmd.state.fl.us and gisweb.tceq.texas.gov. Its last line reads "HEADS DONE <date>: N springhead listings, X new since <date>".
- Republish `pipeline/heads/seen_heads.json`, `pipeline/heads/meta_heads.json`, `pipeline/heads/sh.json` and `pipeline/heads/matches.json` with the page.
- `pipeline/heads/heads.json` is the springhead inventory (name, state, magnitude, flow, vent points); `boxes.json` holds the Redfin search boxes.
  In `sh.json`, `L` rows are [spring index into `heads`, tier (0 vent on the lot, 1 at the lot's edge, 2 adjoining parcel same owner,
  3 estimated from lot size, 4 parent parcel), price, "h"/"l", beds, baths, sqft, acres, address, city, days listed, metres from lot,
  redfin path, parcel acres, first seen, is new, lat, lon, note, permits, groundwater district]; `heads` rows start [name, state, county, magnitude, cfs, last measured year].

Files:
- `props.json`: the 476 lakes and rivers on the state lists (keyed by state), plus group `FS`: 192 Florida springs and 12 Florida spring-fed rivers, and group `SP`: 95 springs in 20 other states and 6 more spring-fed rivers (Current, Jacks Fork, Snake, Suwannee, Withlacoochee, Steinhatchee). Each entry has map areas and county links; `SP` entries also carry `st` (state).
- `shore/<ST>.json`: USGS National Hydrography Dataset shorelines for each water (simplified to ~10 m). Rivers use the named channel plus at most ~200 m of wider river area; springs use the spring run traced ~5 km downstream (`shore/FS.json`, `shore/SP.json`).
- `seen.json`: every listing URL ever matched, with first-seen and last-seen dates.
- `meta.json`: date of the last run and the listing URLs it found.

Trails tab (run after the Springheads step, before republishing):
- `pip install --break-system-packages -q pyproj scipy` (in addition to pandas and shapely).
- `python3 -W ignore pipeline/trails/run_trails.py page.html` (about 1.5 hours; about 5,700 Redfin searches for single-family houses
  $100k–$750k along the trails). Needs network access to www.redfin.com only. Its last line reads
  "TRAILS DONE <date>: N trail-side houses, X new since <date>, Y gone".
- Republish `pipeline/trails/seen_trails.json`, `pipeline/trails/meta_trails.json`, `pipeline/trails/tr.json` and `pipeline/trails/matches.json` with the page.
- The trail network is fixed between runs: `trails.json` (one row per qualifying network: name, other names, miles, end-to-end miles,
  main type p/g/m/u, tags, surface shares, states, bbox), `geom/g*.json` (named segment lines, lon/lat), `boxes.json` (search cells),
  `bigcities.json` (Census 2024 places over 200,000 people). To rebuild the network from a newer Overture release (needs
  overturemaps-us-west-2.s3.us-west-2.amazonaws.com, carto.nationalmap.gov, www2.census.gov): overture_pull.py <release>, usgs_pull.py,
  build_trails.py, make_boxes.py; build_tr.py then adds each trail's states back to trails.json.
- In `tr.json`, `L` rows are [trail index, price, beds, baths, sqft, acres, address, city, state, days listed, metres to the trail,
  redfin path, nearest trail segment name, first seen, is new, lat, lon, year built]; `trails` rows are
  [name, other names, miles, end-to-end miles or null, main type, tags, surface shares, states, bbox]. Types: g gravel, m mountain bike, p paved path, u surface not recorded.

Water + trails (run last, after the Trails step; takes seconds, no network):
- `python3 -W ignore pipeline/trails/water_trails.py page.html` measures each water and springhead listing (listings.json, heads/sh.json)
  to the nearest named segment of a qualifying trail (trails.json, geom/), keeps those within 1 mile and outside cities over 200k,
  and marks Trails-tab houses that are also water listings. It writes `pipeline/trails/wt.json` and the page's `const WT=` data:
  `w` maps a Redfin path to [trail index, metres, segment name]; `t` maps a Trails-tab house's path to [water name, "on"/"near"/"spring", group].
- The page code that uses it was added once by `wt_tab.py`; `patch_page.py`'s listing template calls `wtOK()` and `wtLine()` from that code.

Cities tab (run last, after the Water + trails step; about 30 minutes, about 400 Redfin searches; needs www.redfin.com):
- `python3 -W ignore pipeline/cities/run_cities.py page.html`. Its last line reads
  "CITIES DONE <date>: N city trail-side houses, X new since <date>, Y gone, Z with water and trail access".
- Republish `pipeline/cities/seen_cities.json`, `pipeline/cities/meta_cities.json`, `pipeline/cities/ct.json` and `pipeline/cities/matches.json` with the page.
- The city counterpart of the Trails tab: single-family houses $100k–$750k inside the 128 cities over 200,000 (trails/bigcities.json) within
  400 m of a qualifying trail, plus water and springhead listings in those cities within 1 mile of a trail. `boxes.json` (built once by
  make_city_boxes.py) holds the trail cells that touch those cities.
- In `ct.json`, `cities` rows are [name, state, population]; `L` rows are [city index, trail index, price, beds, baths, sqft, acres, address,
  city, state, days listed, metres to the trail, redfin path, segment name, first seen, is new, lat, lon, year built, water name or null,
  "on"/"near"/"spring" or null]; `W` rows (water listings in cities near a trail, not already in L) are [city index, trail index, metres,
  segment name, redfin path, water name, tier, price, "h"/"l", beds, baths, sqft, acres, address, city, state, days listed, is new, lat, lon].


Detailed map (built once, Nov 2026; the monthly refresh doesn't rebuild it):
- `map/nat.json` (national view), `map/st/<ST>.json` (state detail, loaded at zoom 8+) and `map/hy/<ST>.json` (ponds, lakes, rivers and creeks
  near trails, ranked waters and springheads, loaded at zoom 11+) were built by `pipeline/mapbuild/build_map.py` and `build_hydro.py` from the trail
  geometry, the ranked-water shapes, heads.json, bigcities.json, Natural Earth, and Census TIGER 2024 roads and water. Lines are delta-encoded integers.
- The page code that draws them was added once by `pipeline/mapbuild/map_detail.py` (idempotent). It sits outside the block `patch_page.py`
  regenerates, so data refreshes leave it alone.
- File copy with basemaps: `python3 pipeline/mapbuild/make_local.py page.html map "Clearest Water by State - satellite map.html"` packs the page and the map
  data into one file with street, topo and satellite basemaps (OpenStreetMap, USGS, Esri). Artifact pages cannot load outside images, so the
  basemaps only work when this file is opened directly in a browser. It needs map/counties-10m.json, map/nat.json and map/st/ locally.
- (make_private.py writes the same page for an artifact; the claude.ai viewer blocks its basemap images, so only its plain map works.)
  basemaps (OpenStreetMap, USGS, Esri). Those load from outside servers, so that copy is published as a separate artifact that can't be shared
  publicly; it needs the same `map/` files.
- Web copy (GitHub Pages, https://cyberviking78.github.io/clearest-water/): `python3 pipeline/mapbuild/make_site.py page.html <clone of
  cyberviking78/clearest-water>` rewrites that repository's index.html (the page with live street, topo and satellite basemaps, marked noindex).
  The repository's map/ folder holds a copy of this artifact's map/ files and doesn't change; commit and push index.html after each refresh.

Trail network additions (Nov 10, 2026; one-time, scripts in pipeline/trails/rebuild_2026_11/):
- The original build dropped unnamed bike paths longer than 400 m and footways open to bikes, and threw away USGS trail names that ran along
  unnamed Overture lines, so trails such as Fort Worth's Trinity Trails and Milwaukee's Hank Aaron State Trail were missing.
- A second Overture pull kept those paths; unnamed paths running along a public road (60%+ of points within 22 m of a Census TIGER road) were
  dropped as sidepaths. Networks that qualify under the original rules, have 10+ named miles making up half their length, lie mostly in the US
  and are less than 15% covered by an existing trail were added as trails 1760-1943 ("added": "2026-11-10" in trails.json; geometry in
  geom/g2.json, which also includes their unnamed paved bike paths). The 1,760 original trails, their ids and geometry are unchanged.

More waters per state (Nov 10, 2026; one-time, scripts in pipeline/morewater_2026_11/):
- Beyond each state's top 5, every lake averaging clearer than 20 ft (20+ readings over 5+ years) and every river with a median under 2 NTU
  (24+ samples over 3+ years) from the national lists was added: 112 lakes and 79 rivers on the Lakes and Rivers tabs (rows with "x": true).
- 170 of them have a mapped shore (US Census TIGER 2024 area/linear water, which carries USGS NHD names and shapes; river reaches are placed
  from Water Quality Portal station locations) and were appended to props.json after each state's existing entries ("added": "2026-11-10"),
  with shorelines in shore/<ST>.json, so the property search covers them. Existing water indexes are unchanged.

Whole-shoreline searches (Nov 10, 2026; scripts widen.py and pr_widen.py in pipeline/morewater_2026_11/):
- Many waters were searched only in a box around their sampling station (Sebago Lake: about 2.5 x 3 miles of a 9 x 13 mile lake).
  The 249 waters whose mapped shore runs past that box now carry "boxes" in props.json: the station box first, then 0.15 x 0.12 degree
  grid cells along the shore (shrunk to ~1.5 km from it), 1,502 cells in all; their Zillow links cover the whole shoreline.
- run.py searches every box, four at a time through prefetch.py (saved under pipeline/wcsv/, resumable), so step 3 takes about 1.5 hours.

Clear river stretches and known-clear unmeasured rivers (Nov 10, 2026; one-time, scripts in pipeline/reach_2026_11/):
- Whole-river medians hide clear reaches (the Frio's monitored sites are mostly far downstream of Concan), and several famous clear
  rivers have no turbidity record in the Water Quality Portal (Texas state monitoring results aren't published there).
- reach.py: station-level stream turbidity (WQP, 2016+; plus USGS continuous sensors in TX, ID and WY sampled weekly; Idaho has none
  active) grouped by river name from the station name and chained within 15 km. A stretch counts at a median under 2 NTU on 24+ samples
  over 3+ years when the river isn't already listed; one stretch (the clearest) per river.
- curated.json: 12 rivers in TX and ID known for clear water, each with a published source. A measured stretch inside a curated reach of
  the same river takes the curated name and extent (Frio, San Marcos); the rest show "not measured" (rows "g": "nm", rk null).
- addwaters2.py: maps them onto TIGER channels (drops names under 25 km of mapped channel), appends props entries ("added":
  "2026-11-10b"), shore shapes, Rivers-tab rows ("g": "reach" / "nm") and Property-list rows. page_edit2.py adds the tab dividers
  and makes every rank display handle a missing rank (also applied to patch_page.py).
- 23 measured stretches and 10 not-measured rivers were added (33 searchable waters). The price cap stays at $750k everywhere.

Great Lakes shorelines (Nov 11, 2026; one-time, scripts in pipeline/greatlakes_2026_11/):
- build.py: one water per state and Great Lake (13: Superior in MN, WI, MI; Michigan in WI, IL, IN, MI; Huron in MI; Erie in MI, OH,
  PA, NY; Ontario in NY). The shoreline is the edge of the TIGER 2024 AREAWATER polygons named for the lake, plus the bays joined to
  it (Green Bay, Saginaw Bay, Grand Traverse Bay, Sandusky Bay...), where it meets land. Search cells: a 0.1 x 0.08 deg grid clipped
  to the shoreline buffered ~800 m (963 cells, each searched with and without Redfin's waterfront filter).
- add.py: props entries with "gl": true, "on_only": true, "rk": null, "added": "2026-11-11"; run.py keeps only listings on the lake
  for these (no "near" tier). Clarity shown is open-lake clarity from published surveys (EPA Great Lakes Biology Monitoring Program;
  Dobiesz & Lester 2009 for Huron and Erie); water near shore is often less clear. Page rows: Lakes tab "g": "gl"; Property list
  rows with type "g".
- page_edit3.py adds them to the page (also patch_page.py). trail_color.py switched the trails to royal blue with a thin casing.
- mapmax.py (Nov 11, 2026) added the full-screen map: a "Full screen" button above the map and a button on the map. It uses the
  browser's full-screen mode where allowed and otherwise fills the window; Filters and Legend & layers open as panels over the map.
- mapmax2.py (Nov 11, 2026): full-screen mode survives opening a listing in another tab or switching apps (the next tap on the map
  goes back to true full screen), and after a reload the page comes back in full screen at the same state, centre and zoom
  (remembered for the browser tab, sessionStorage).
- states.py (Nov 11, 2026): state outlines get their own layer above the basemap (they used to sit under the tiles): dark on
  Streets and Topo, white on Satellite, mid-grey on the plain map. make_private.py tells it which basemap is showing.

Clarity cut-off, more qualifying water, accurate dots (Nov 12, 2026; scripts in pipeline/criteria_2026_11/):
- cutoff.py: no property search on rivers over 3 NTU or lakes under 15 ft (props "skip": true, "skipwhy"); run.py and prefetch.py
  skip them, the Property list leaves them out (PR row index 7 holds the reason), and the Lakes/Rivers tabs mark them "No property
  search". Michigan's Lake Erie shore is skipped; Ohio's is cut back to the central basin (east of Marblehead). Springs unchanged.
  The "Include near-the-water listings" box now applies to the Property tab too and starts unchecked (frontage first).
- newwaters15.py: every lake averaging 15-20 ft and river with a median of 2-3 NTU (same record bar) beyond the top five; tab rows
  "g": "x15" / "x3", props "added": "2026-11-12". page_edit4.py puts them on the page.
- reach3.py: the clearest-stretch finder re-run at 3 NTU. cands.py: rivers and creeks known for clear water in 22 states checked
  against station data (measured at or under 3 NTU -> measured rows; over 3 -> left out; no record -> curated2.json, a published
  source each). addwaters3.py maps and adds them.
- dots.py: river shapes trimmed to the stretches their monitoring stations sit on (plus pieces within 2 km, split by dams or lakes),
  so a second river of the same name in the search box drops out; every water's map dot now sits on the water (PR row index 6,
  FSD springs index 18, FSD rivers index 15; props "dot").

Old Growth tab (Nov 12, 2026; scripts in pipeline/og/):
- Chad's ask: land or homes of at least 25 acres (ideally 50) near old-growth forests, $100k-$750k, with the forests shaded on the
  map. The forests are public or protected, so they serve as anchors and the search looks for private parcels around them.
- build_sites.py (run once; no need to rerun): forests = the Old-Growth Forest Network's dedicated forests (ogfn.json, from the
  network's Google My Maps export Chad supplied: name, state, county, description, coordinates; "future old growth" when the
  description says so) plus big public old-growth landscapes from Wikipedia's List of old-growth forests that the network doesn't
  already cover. Area: the official boundary of the park, wilderness, refuge or preserve the forest is in (USGS National Map
  govunits, Census TIGER 2024 area landmarks) when every distinctive word of the boundary's name is in the forest's name and the
  boundary isn't vastly bigger; otherwise a circle sized to the stated acreage, marked approximate. Writes sites.json, geom.json.
- run_og.py page.html: each forest buffered 5 miles, gridded into search cells, searched on Redfin's map-data feed (houses and land,
  Redfin's 25-acre minimum lot filter, $100k-$750k); lots of 25+ acres matched to the nearest forest edge (straight-line distance
  from the listing point; <= 400 m reads "borders the forest or inside it", which includes inholdings). Writes og.json,
  seen_og.json, meta_og.json and refreshes the page's OG data via og_tab.py (idempotent; first run adds the tab). Its last line
  reads "OG DONE <date>: N listings of 25+ acres near F of S old-growth forests; ...". OG_CSV=<dir> builds from saved searches.
- og.json: S rows [name, st, county, acres, future(0/1), src "ogfn"/"wiki", page, website, lat, lon, kind "boundary"/"approx",
  boundary name, area rings (delta-encoded lon/lat at 1e4) or null, circle radius m (approx) or null, description];
  L rows [forest_index, price, "h"/"l", beds, baths, sqft, acres, address, city, state, days_listed, metres_to_forest_edge,
  redfin_path, first_seen, is_new, lat, lon, year_built, creek (name, "" unnamed, or null), pond acres or null].
- Nov 13, 2026: map colors made stronger (og_style.py: dark green outlines on forest areas, dark green dots with white rings),
  and each Old Growth listing now carries creek and pond flags (index 18, 19; see wildflags.py) and a satellite link.

wildflags.py (Nov 13, 2026): creek and pond flags for acreage listings. The lot is a circle of its acreage around the listing's map
point; "creek" = a TIGER/Line stream or river (LINEARWATER H3010, or AREAWATER H3010) crosses it (its name, "" if unnamed; the
Census stream lines include seasonal creeks); "pond" = a lake, pond or small reservoir of 1/4 acre or more (AREAWATER H2030/H2040)
touches it (largest acres). County TIGER files are downloaded from www2.census.gov as needed and cached in pipeline/.tiger
(not published).

Rainforest tab (Nov 13, 2026; pipeline/rain/):
- Chad's ask: property in misty, big-tree forests with ferns and flowers. Those are temperate rainforests and cloud forests, which
  follow the climate. build_zones.py (run once) draws "rainforest country" from PRISM 30-year normals (annual precipitation
  1991-2020 800 m, mean temperature 1981-2010 4 km, 800 m elevation; files came from GitHub mirrors of PRISM's downloads):
  core = 70+ in of rain and 5-15 C mean (Pacific coast ranges, Olympics, west-slope Cascades, Klamath-Siskiyou, north Sierra,
  southern Blue Ridge escarpment, Smokies); fog = coast redwood fog belt, 36.4-42 N within 40 km of the Pacific, 40+ in, 8-16 C;
  inland = cedar-hemlock wet belt of north Idaho / NE Washington / NW Montana, 40+ in, 3-9.5 C; cloud = Appalachian cloud forest,
  50+ in and above 1,370 m at 35.5 N falling 70 m per degree north; maine = Downeast Maine fog coast within 15 km of the sea east
  of Penobscot Bay; alaska = the Tongass boundary plus a margin. Writes zones.geojson and rainpts.json (rain inches and elevation m
  for each zone cell, key row*7025+col of the PRISM 30" grid).
- run_rain.py page.html: zones gridded (0.25 x 0.2 deg; Alaska 0.5 x 0.4) and searched on Redfin (25+ acres, $100k-$750k,
  houses and land); listings inside a zone kept. Last line "RAIN DONE <date>: N listings ...; X new since <date>; Y gone".
  Then rf_tab.py refreshes the page's RF data (first run adds the tab and the zone shapes, RFZ). RAIN_CSV=<dir> uses saved searches.
- rain.json: kinds, og {forest index: [name, st]}, L rows [zone (0 core, 1 fog, 2 inland, 3 cloud, 4 maine, 5 alaska), price,
  "h"/"l", beds, baths, sqft, acres, address, city, state, days_listed, rain_in, elev_ft, redfin_path, first_seen, is_new, lat, lon,
  year_built, nearest old-growth forest index (og/sites.json) within 10 miles or null, metres to it, creek, pond acres].

Mountain Lakes tab (Nov 13, 2026; pipeline/mlake/):
- Chad's ask: sapphire-blue, clear water, alpine lakes even unnamed, ponds. Satellite imagery and lake-color datasets can't be
  reached from the build machine, so color isn't measured; the search uses setting: cold, high mountain lakes are almost all clear.
  build_lakes.py (run once): every TIGER/Line AREAWATER lake/pond (H2030) of 1+ acre in WA OR CA NV ID MT WY UT CO AZ NM, named or
  not, whose elevation (lowest PRISM 800 m cell touching it) is no more than 1,300 m below a regional treeline (3,500 m at 39 N,
  minus 130 m per degree north, capped at 3,600; 350 m lower west of 120.3 W) and with 350+ m of rise within ~4 km; reservoirs,
  dams, tailings, treatment ponds and lakes wholly inside a national park or wilderness area left out. Writes lakes.json
  ([name, st, county fips, acres, elev_m, lat, lon, threshold_m]) and lakes_geom.json.
- run_lakes.py page.html: lakes gridded (0.15 x 0.12 deg cells cut to 400 m around the lakes), Redfin houses and land
  $100k-$750k; kept when the shore is within the lot's reach of the map point (side of a square of the lot area + 30 m, max 570;
  land with no lot size 120 m, a house 60 m). Last line "ML DONE <date>: N listings on M of 7,193 mountain lakes ...".
  Then ml_tab.py refreshes the page's ML data. ML_CSV=<dir> uses saved searches.
- ml.json: nlakes, K rows (only lakes with listings) [name or "", st, acres, elev_ft, lat, lon, rings delta-encoded at 1e5],
  L rows [lake index in K, price, "h"/"l", beds, baths, sqft, acres, address, city, state, days_listed, metres_to_shore,
  redfin_path, first_seen, is_new, lat, lon, year_built].
- Mountain lakes: lakes the Census map leaves unnamed get their USGS GNIS name (The National Map geonames service, layer 7
  "Other Hydrographic Features", Lake or Reservoir points inside the lake) when one exists, cached in mlake/gnis.json; lakes whose
  GNIS name is "... Reservoir" are dropped. Natural lakes raised by small dams that TIGER codes as reservoirs (H2040) are kept when
  named Lake. The Sierra Nevada gets the wetter-range treeline adjustment.

## Dark night skies (map overlay, added Nov 15, 2026) -- pipeline/sky/
Static overlay, not part of the refresh: the zones live in the page itself (const SKY), so refreshes keep them. Rebuild about
once a year when David Lorenz publishes a new atlas (https://djlorenz.github.io/astronomy/lp/; the images are also on
raw.githubusercontent.com/djlorenz/djlorenz.github.io/master/astronomy/lp<year>/NorthAmerica<year>.png).
- build_sky.py NorthAmerica2025.png state500k.zip: maps the atlas colours to light-pollution zones (0, 1a, 1b, 2a, 2b ... 7b
  = 0..14), keeps the brighter of each 2x2 block (1/60 degree cells), masks to the US (Census cartographic state boundaries
  + ~2 km), and writes sky.json: {conus, ak, hi: {w, n, res, cols, rows, b (gzip + base64 of one byte per cell, 15 = outside)}}.
- sky_tab.py page.html sky.json: adds the "Dark night skies" switch to the map's Map detail bar (zones 0, 1 and 2 shaded in
  violet, redrawn in web-mercator rows in the browser), a "Night sky: zone ..." line in every map popup, the note under the
  map and the source. Idempotent: re-running only replaces the SKY data.

## Mountain Lakes, second version (Nov 18, 2026) -- pipeline/mlake/
The lake list is now built in three steps (run once, or when the lake rules change; the refresh only runs run_lakes.py):
1. build_lakes.py -> lakes_tiger.json / lakes_geom_tiger.json: Census TIGER lakes and ponds of 1+ acre at montane-to-alpine height
   (as before), river/creek/fork/slough-named features dropped, plus a big-lake rule: 50+ acres, at least 300 m up and within 600 m
   of the height cut, with 600 m of rise within ~8 km (Priest, Pend Oreille, Coeur d'Alene, Chelan, Wenatchee, Wallowa, Bear Lake).
2. nhd_lakes.py -> lakes_nhd.json / lakes_geom_nhd.json: each candidate must be at least half covered by USGS NHD (hydro.nationalmap.gov
   Waterbody layer) lake/pond polygons that hold water all year (FCode 39000/39004/39009-39012) or an NHD reservoir named Lake;
   river-shaped outlines (mean width < 40 m and compactness < 0.03) dropped; NHD "Reservoir/Tank/Pit" names dropped; official
   GNIS names from NHD; touching pieces of one named lake joined; Lakes-tab lakes measured under 15 ft (same state) dropped.
   Index 8: 1 when NHD maps the lake as dam-controlled. NHD responses cached in nhd_cache/.
3. clarity.py -> lakes.json / lakes_geom.json: Secchi depths since 2000 from the Water Quality Portal for lakes of 100+ acres and
   dam-controlled lakes (stations within ~300 m of the outline); median under 15 ft (2+ readings) dropped; six large unmeasured dam
   reservoirs dropped by name (Almanor, Big Bear, Ennis, Hebgen, Alder, Lake Roosevelt). Index 9: median clarity ft or null.
run_lakes.py now searches with no upper price: listings over $750,000 go to ml.json "H" (rows as L, but index 0 is
[lake name, state, acres, elevation ft]); the page shows only L and a live count of H by state. K rows gained index 7: measured
clarity ft or null. gnis.json is keyed by "lat,lon" of the lake. ml_v2.py applies the new explanation and clarity display to a
page that already has the tab (idempotent).

## Wild Lakes (Nov 19, 2026; replaces the Mountain Lakes lake list) -- pipeline/wild/
Chad: not "mountain" lakes by elevation, but the beautiful clear lakes and ponds, in the West and in TN, WV, NC, ME, VT, NH.
Built once (re-run to change the rules); the refresh only runs run_wild.py.
1. limnosat_color.py (streams the 3.5 GB LimnoSat-US csv from Zenodo record 4139695) -> lake_color.json {Hylak_id: [median summer
   dominant wavelength nm 2013-2020, n]}; src/HydroLakes_DP.* are the lakes' deepest points from the same record.
2. build_wild.py -> lakes.json / lakes_geom.json. Census TIGER 2024 area water (H2030 lake/pond, H2040 reservoir), 1+ acre, all
   counties of the 17 states (/home/claude/geo_src/aw); touching pieces of a named lake joined; river channels, river/creek/ditch and
   tailings/sewage/quarry names, lakes wholly in national parks or wilderness dropped. NLCD 2021 land cover (MRLC WCS, coverage
   mrlc_download__NLCD_2021_Land_Cover_L48, fetched per 0.5-degree block; results cached in nlcd_blocks/): the outline must be at least
   40% open water (20% under 2 acres). Kept when the satellite colour is 505 nm or less (the lake's own HydroLakes point: lowest id),
   or, with no colour record, when the 200 m ring around it is 75%+ natural cover (classes 12 31 41 42 43 51 52 71 72 90 95), at most
   5% developed (21-24) and 10% farmland (81 82). Lakes-tab lakes measured under 15 ft (same state) dropped.
   Lake row: [name, st, county fips, acres, elev_m, lat, lon, 0, 0, measured ft or null, colour nm or null, natural %, "colour"|"shore"].
3. run_wild.py page.html (the refresh step): Redfin searches over 0.3 x 0.24 degree areas cut to 400 m around the lakes, split into
   quarters up to 6 times where Redfin returns a full page; no upper price (over $750k -> ml.json "H"); same shore test and GNIS
   naming as before; writes wild/ml.json, seen_wl.json, meta_wl.json, gnis.json and refreshes the page's ML data through
   mlake/ml_tab.py. K rows: [name, st, acres, elev ft, lat, lon, rings, measured ft, colour nm, natural %, "colour"|"shore"].
4. wl_tab.py page.html: renames the tab to Wild Lakes and adds the colour / wild-shore display and filter (idempotent).
The mlake/ folder (Mountain Lakes, Nov 13-18) is kept for reference; its run_lakes.py is no longer part of the refresh.

## LakeQuality checklist (Nov 20, 2026) -- pipeline/lakequality_2026_11/
LakeQuality.org (ColdPress LLC) publishes clearest-lake rankings for 24 states (AL AR CO FL GA IA IL KS MI MN MO MT NC ND NE NM NY
OK TX UT VA VT WI WY) at /ranking/clearest/<st>. Only those 24 ranking pages were read (its terms bar bulk downloading; it is
credited and linked on the page). It is a checklist, not a data source: every lake it ranks at 15 ft or clearer that we did not
already search (115) was checked against the Water Quality Portal by us.
1. WQP Result + Station CSVs ("Depth, Secchi disk depth", site type Lake/Reservoir/Impoundment, since 2000) for the 65 counties
   involved; stations matched by the lake's name words (match.py, with per-lake regex overrides). Value = each year's median
   reading averaged across years, after dropping readings over 148 ft or over 3x the lake's median (same as the main list).
   Kept: that average AND the median of all readings both 15 ft+, from 6+ readings or readings in 3+ years. Dropped: no WQP
   readings (satellite-only; all four CO lakes), lakes already searched, national park / recreation area stations
   (Yellowstone, Jackson Lake, Lake Powell), and values WQP doesn't support (Adams Lake WI, Meade Lake KS, Loch Lomond IL...).
2. build_lq.py <scratch dir> page.html: 49 lakes pass (tab group "lq", with a link to each lake's LakeQuality page; 2 shown with
   "No property search": Deer Lake FL has no mapped outline, Big Therriault MT is national forest). Also adds a property search
   for 41 Lakes-tab lakes at 15 ft+ whose shapes earlier passes never found (Chancellor, Smoky, Little McDonald, Elligo...).
   Shapes: Census TIGER 2024 area water named for the lake near its stations; else the water body its stations sit in (TIGER
   names some lakes for their stream, e.g. Boulder Lake WY = "Boulder Crk"); else USGS NHD waterbody (3 pit lakes). Lac du
   Flambeau's Long Interlaken and Flambeau lakes are cut to 2.5 km around their stations (one TIGER polygon spans the chain).
   Props entries carry added "2026-11-20" (and "lq": the LakeQuality path for the 47 searched new lakes).
3. page_edit_lq.py page.html out/extra.json (idempotent): LK rows, PR rows (index-aligned with props), method paragraph, source.
4. map_add_lq.py out/: outlines into map/st/<ST>.json "wt". run_new.py page.html: Redfin search for just these 88 waters,
   merged into listings.json with nothing marked new. From here on the regular refresh (run.py) covers them like any other lake.
