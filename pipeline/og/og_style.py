"""Nov 13, 2026: old-growth forests and listings easier to see on the map (Chad: the light green was hard to see). Forest areas get a
dark green outline (2.5 px) over a deeper green fill; listing dots are dark green with a white ring (houses) or a thick dark green
ring around a white centre (land), and larger. Dark theme: a vivid green instead. Idempotent; usage: og_style.py <file> [<file>...]
(the page and pipeline/og/og_tab.py, so a fresh install gets the same look)."""
import sys
R = [
    ("--og:#3b6b2c; --og-soft:#e5efdd;", "--og:#2f5d22; --og-soft:#e5efdd; --og-map:#0b4a14; --og-dot:#ffffff;"),
    ("--og:#93c97c; --og-soft:#1d2c18;", "--og:#93c97c; --og-soft:#1d2c18; --og-map:#33b249; --og-dot:#0d1a0b;"),
    (".lg i.og{background:var(--og)} .lg i.oga{background:color-mix(in srgb,var(--og) 30%,transparent);border:1.5px solid var(--og);border-radius:3px;box-shadow:none}",
     ".lg i.og{background:var(--og-map);border:2px solid var(--og-dot);box-shadow:0 0 0 1px var(--og-map)} .lg i.oga{background:color-mix(in srgb,var(--og-map) 28%,transparent);border:2.5px solid var(--og-map);border-radius:3px;box-shadow:none}"),
    (".mc.ogc{background:color-mix(in srgb,var(--og) 88%,transparent)}", ".mc.ogc{background:var(--og-map);border-color:var(--og-dot)}"),
    ('if(document.getElementById("showog").checked){const oc=tok("--og");', 'if(document.getElementById("showog").checked){const oc=tok("--og-map"), od=tok("--og-dot");'),
    ('const st={color:oc,weight:1.5,opacity:.9,fillColor:oc,fillOpacity:.22,dashArray:f[10]==="approx"?"4 4":null};',
     'const st={color:oc,weight:2.5,opacity:1,fillColor:oc,fillOpacity:.26,dashArray:f[10]==="approx"?"6 4":null};'),
    ('L.circleMarker([x[15],x[16]],{radius:x[6]>=50?9:7,color:x[2]==="l"?oc:surf,weight:x[2]==="l"?2.5:1.5,fillColor:oc,fillOpacity:x[2]==="l"?.25:.95})',
     'L.circleMarker([x[15],x[16]],{radius:x[6]>=50?10:8,color:x[2]==="l"?oc:od,weight:x[2]==="l"?3.5:2.5,fillColor:x[2]==="l"?od:oc,fillOpacity:x[2]==="l"?.9:1})'),
]
for fn in sys.argv[1:]:
    s = open(fn).read(); n = 0
    for o, nw in R:
        if nw in s: continue
        if o in s: s = s.replace(o, nw); n += 1
        else: print("  not found in", fn, ":", o[:70])
    open(fn, "w").write(s); print(fn, n, "changes")
