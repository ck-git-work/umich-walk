"""Turn the via points in places.json into street-following walking lines.

Calls the public OSRM foot-routing server once per route and saves the result to
build/routes.geojson (one LineString per route, with distance in meters).
Re-run only when the via points change; everything else reads the saved file.
"""
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OSRM = "https://routing.openstreetmap.de/routed-foot/route/v1/foot/"
UA = {"User-Agent": "umich-walk-map-builder/1.0"}


def route(vias):
    # OSRM wants "lng,lat;lng,lat;..." (longitude first)
    coords = ";".join(f"{lng},{lat}" for lat, lng in vias)
    url = OSRM + coords + "?overview=full&geometries=geojson&continue_straight=false"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        data = json.load(r)
    if data.get("code") != "Ok":
        raise RuntimeError(data)
    best = data["routes"][0]
    return best["geometry"], best["distance"], [leg["distance"] for leg in best["legs"]]


def main():
    places = json.loads((ROOT / "places.json").read_text(encoding="utf-8"))
    features = []
    for rid, r in places["routes"].items():
        geom, dist, legs = route(r["vias"])
        print(f"{rid}: {dist / 1609.34:.2f} mi; legs (m): {[round(x) for x in legs]}")
        features.append({
            "type": "Feature",
            "properties": {"id": rid, "layer": r["layer"], "meters": dist},
            "geometry": geom,
        })
    out = ROOT / "build" / "routes.geojson"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
