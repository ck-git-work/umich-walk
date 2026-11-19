# Ann Arbor & U-M walking guide

A one-link walking map and guide for a campus visit.

- `places.json`: every pin, note and route turn point (the only file to edit by hand)
- `tools/build_route.py`: turns the route turn points into street-following lines (`build/routes.geojson`)
- `tools/build.py`: writes the My Maps import files (`kml/`) and the guide page (`docs/index.html`)

To rebuild after editing `places.json`:

```
python tools/build_route.py   # only if route turn points changed
python tools/build.py
```

To switch the page to the Google My Maps embed, put the map's `mid` (from its share link) in `places.json` → `mymaps_mid` and rebuild.
