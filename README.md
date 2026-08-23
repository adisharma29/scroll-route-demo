# Scroll-Route Demo — Whitefield → Calangute

A scroll-driven map story: the camera drives along a real road route from
Whitefield, Bengaluru to Calangute Beach, Goa while you scroll. Built with
MapLibre GL over OpenStreetMap data, inspired by the scroll-craft of pear.no.

**Live behavior:** 8 viewport-heights of scroll = 624 km of NH 48. The camera
eases along the polyline (north-up, pitch 45°), the travelled route draws in
gold behind a grey ghost of the full route, and checkpoint toasts fire as you
pass Tumakuru, Chitradurga, Hubballi, and Belagavi.

## Files

```
index.html                      # the entire demo — one self-contained page
data/route_whitefield_calangute.json
                                # polyline (1,889 pts), total length, checkpoint fractions
tools/fetch_route_mcp.py        # pulls routes + polyline from the Vyntel Google Maps MCP
tools/fetch_checkpoints_mcp.py  # resolves checkpoint city coordinates via the same MCP
```

## How it works

### Data pipeline (tools/)

1. `fetch_route_mcp.py` opens a direct asyncio MCP client session against the
   Vyntel MCP server (streamable HTTP + `httpx2.AsyncClient` with auth headers
   from `~/.hermes/config.yaml`) and calls the `vyntel_google_maps` tool with
   `action: "routes"`, `polyline: true`. Returns 3 alternatives; we use NH 48
   (624,965 m) with its 1,580-point `[lng, lat]` polyline.
2. `fetch_checkpoints_mcp.py` searches each checkpoint city on the same MCP to
   get exact coordinates, then projects them onto the polyline by nearest point.
3. A build step densifies the polyline: every segment longer than 800 m is
   linearly subdivided (1,580 → 1,889 points, max gap 0.8 km). This kills the
   straight-line chords Google's sparse points would otherwise draw across
   highway bends.
4. Cumulative haversine distance is precomputed; each checkpoint gets a journey
   fraction `t` (Tumakuru 0.143, Chitradurga 0.359, Hubballi 0.686,
   Belagavi 0.813, Calangute 0.999).

### Rendering (index.html)

- **MapLibre GL 4.7** + CARTO dark-matter tiles (OSM data), `interactive: false`
  — scroll belongs to the story, not the map.
- **Custom inertial scroll engine** (no Lenis/GSAP): wheel/touch set a `target`,
  a rAF loop lerps `current += (target - current) * 0.085` and calls
  `scrollTo()` itself. A passive `scroll` listener resyncs only if the browser
  and the engine disagree by more than 2 px (find-in-page, scrollbar drag).
  Honors `prefers-reduced-motion`.
- **Arc-length positioning**: scroll progress `t` maps to distance `t · total`,
  which maps to a point + segment index on the polyline. The camera, the
  travelled line's head, and the checkpoint markers all derive from this same
  index — they can never disagree.
- **Camera**: fixed north-up (`bearing: 0`), pitch 45°, center eased toward the
  car position with a per-frame lerp (0.06), zoom breathing 8.4 → 6.2 → 8.4
  over the journey (wide in the middle, intimate at the ends).
- **Layers**: grey full-route ghost, gold travelled line (`line-blur: 0.4`),
  checkpoint circles, checkpoint toast on crossing each `t`.

## Bugs found and fixed (documented for posterity)

1. **Straight-line chords across bends** — Google's polyline had ~30 gaps over
   2 km (max 5.8 km). Fix: densify every segment > 800 m at build time.
2. **Map rotating left/right while scrolling (felt like flicker)** — v1 set the
   camera bearing to the local road heading; every curve swung the whole map.
   Fix: fixed north-up bearing + smoothed camera center.
3. **A moving straight chord on the travelled line** — the car position used
   arc-length but the drawn line's end used a point-count fraction
   (`t · N`). On unevenly spaced points these diverge by up to ~340 points
   (~100 km here), so the last segment stretched into a long straight chord
   that moved with scroll. Fix: derive the drawn line's end index from
   arc-length too. Same bug fixed for checkpoint marker placement.

**Lesson: when animating along a polyline, pick ONE parameterization (arc
length) and use it everywhere.**

## Run it

```bash
python3 -m http.server 8792
# open http://localhost:8792/index.html and scroll
```

No build step, no API keys in the page — the route data is baked into
`index.html` (and kept separately in `data/` for reuse). Internet is needed
only for the MapLibre CDN and map tiles.

## Regenerate the data

Requires access to the Vyntel MCP server (URL + headers configured in
`~/.hermes/config.yaml` under `mcp_servers.vyntel`) and the hermes venv
(`mcp`, `httpx2`, `yaml` packages):

```bash
python tools/fetch_route_mcp.py        # writes /tmp/route_raw.json
python tools/fetch_checkpoints_mcp.py  # writes /tmp/checkpoints.json
# then rebuild data/route_whitefield_calangute.json (densify + project checkpoints)
```

## Credits

- Scroll-craft inspiration: [pear.no](https://pear.no) (custom lerp scroller,
  scroll-scrubbed sequences)
- Map: [MapLibre GL](https://maplibre.org/) · tiles © CARTO · data ©
  OpenStreetMap contributors
- Routes: Google Maps via the Vyntel MCP server (estimates, no live traffic)
