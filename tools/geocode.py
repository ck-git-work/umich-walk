"""Look up candidate coordinates for each place with OpenStreetMap's Nominatim.

Prints every candidate so a human can pick the right one; it does not write places.json.
Nominatim's usage policy: at most 1 request/second and an identifying User-Agent.
"""
import json
import sys
import time
import urllib.parse
import urllib.request

QUERIES = {
    "start": "East William Street & South Main Street, Ann Arbor",
    "main_kingsley": "Kingsley Street & North Main Street, Ann Arbor",
    "zingermans": "Zingerman's Delicatessen, Ann Arbor",
    "burton": "Burton Memorial Tower, Ann Arbor",
    "league": "Michigan League, Ann Arbor",
    "hill_aud": "Hill Auditorium, Ann Arbor",
    "diag_m": "The Diag, University of Michigan, Ann Arbor",
    "angell": "Angell Hall, Ann Arbor",
    "shapiro": "Shapiro Undergraduate Library, Ann Arbor",
    "hatcher": "Hatcher Graduate Library, Ann Arbor",
    "west_hall": "West Hall, Ann Arbor",
    "east_quad": "East Quadrangle, Ann Arbor",
    "ross": "Ross School of Business, Ann Arbor",
    "law_quad": "Law Quadrangle, Ann Arbor",
    "law_library": "Cook Legal Research Library, Ann Arbor",
    "union": "Michigan Union, Ann Arbor",
    "cube": "Endover, Ann Arbor",
    "rally_house": "Rally House, State Street, Ann Arbor",
    "cottage_inn": "Cottage Inn, East William Street, Ann Arbor",
    "pizza_house": "Pizza House, Church Street, Ann Arbor",
    "frita": "Frita Batidos, Ann Arbor",
    "palmer_field": "Palmer Field, Ann Arbor",
    "stockwell": "Stockwell Hall, Ann Arbor",
    "mojo": "Mosher-Jordan Hall, Ann Arbor",
    "alice_lloyd": "Alice Lloyd Hall, Ann Arbor",
    "arb": "Nichols Arboretum, Ann Arbor",
    "arb_entrance": "Nichols Arboretum Washington Heights entrance, Ann Arbor",
    "north_campus": "Lurie Tower, Ann Arbor",
    "duderstadt": "Duderstadt Center, Ann Arbor",
}

UA = "umich-walk-map-builder/1.0"


def search(q):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "jsonv2", "limit": 3, "addressdetails": 0}
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    keys = sys.argv[1:] or list(QUERIES)
    out = {}
    for k in keys:
        try:
            res = search(QUERIES[k])
        except Exception as e:  # keep going; report the failure
            res = [{"error": str(e)}]
        out[k] = [
            {
                "lat": r.get("lat"),
                "lon": r.get("lon"),
                "name": r.get("display_name", r.get("error")),
                "type": f'{r.get("category")}/{r.get("type")}',
            }
            for r in res
        ]
        print(k, json.dumps(out[k][:2], ensure_ascii=False), flush=True)
        time.sleep(1.2)


if __name__ == "__main__":
    main()
