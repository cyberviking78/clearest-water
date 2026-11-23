# Clearest Water by State

A web copy of the "Clearest Water by State" page: the clearest lakes, rivers and springs by state, and homes and land for sale
on or near them, near springheads, and along long bike trails, with live street, topo and satellite maps.

- `index.html` is the web copy of the page. GitHub rebuilds and publishes it itself on the 1st and 15th of the month: the
  "Refresh listings" workflow (`.github/workflows/refresh.yml`) searches Redfin in parallel jobs, runs every refresh step in
  `pipeline/` (see `pipeline/README.md`), commits the result here and asks GitHub Pages to publish it. It can also be started by
  hand from the Actions tab.
- `pipeline/page.html` is the same page as published on claude.ai; `ci/last_run.json` records how the last refresh went.
- `map/` holds the map's own layers (trails, ranked waters, springheads, city limits, roads, towns, creeks and ponds), built once.

Map data: trails © OpenStreetMap contributors and USGS; water from the USGS National Hydrography Dataset via US Census TIGER, and
Natural Earth; roads, towns and outlines from the US Census Bureau. Basemaps: OpenStreetMap, USGS The National Map, Esri.
Satellite water clarity for the oceanfront search: NOAA CoastWatch (VIIRS Kd490). Listings: Redfin.
