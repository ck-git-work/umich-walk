"""Generate everything from places.json + build/routes.geojson.

Outputs:
  kml/1-walk.kml, kml/2-food.kml, kml/3-hill-dorms.kml, kml/4-extras.kml  -> import into Google My Maps
  docs/index.html                                                         -> the guide page (GitHub Pages)

Run tools/build_route.py first if any via points changed.
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
MI = 1609.34
KML_FILES = {"route": "1-walk.kml", "food": "2-food.kml", "hill": "3-hill-dorms.kml", "extras": "4-extras.kml"}
# The plain pin image My Maps itself uses in its exports; IconStyle <color> tints it.
PIN = "https://www.gstatic.com/mapspro/images/stock/503-wht-blank_maps.png"


def kml_color(rgb, alpha="ff"):
    """KML colors are written aabbggrr, the reverse of web #rrggbb."""
    return alpha + rgb[4:6] + rgb[2:4] + rgb[0:2]


def directions_url(p):
    return f"https://www.google.com/maps/dir/?api=1&destination={p['lat']},{p['lng']}&travelmode=walking"


def pin_title(p):
    return f"{p['order']} · {p['name']}" if p.get("order") else p["name"]


def write_kml(data, routes, layer_id):
    layer = data["layers"][layer_id]
    places = sorted((p for p in data["places"] if p["layer"] == layer_id), key=lambda p: p.get("order", 0))
    lines = [f for f in routes["features"] if f["properties"]["layer"] == layer_id]
    e = html.escape
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
        f"<name>{e(layer['name'])}</name>",
        f'<Style id="pin"><IconStyle><color>{kml_color(layer["color"])}</color><scale>1.1</scale>'
        f"<Icon><href>{PIN}</href></Icon></IconStyle></Style>",
        f'<Style id="line"><LineStyle><color>{kml_color(layer.get("line_color", layer["color"]), "e6")}</color>'
        f"<width>{6 if layer_id == 'route' else 4}</width></LineStyle></Style>",
    ]
    for p in places:
        desc = p["note"]
        if p.get("address"):
            desc += f"<br><br>{e(p['address'])}"
        out.append(
            f"<Placemark><name>{e(pin_title(p))}</name><styleUrl>#pin</styleUrl>"
            f"<description><![CDATA[{desc}]]></description>"
            f"<Point><coordinates>{p['lng']},{p['lat']},0</coordinates></Point></Placemark>"
        )
    for f in lines:
        label = {"main": "The walk", "hill": "Hill dorms detour (out and back)", "arb": "To the Arb"}[f["properties"]["id"]]
        coords = " ".join(f"{x:.6f},{y:.6f},0" for x, y in f["geometry"]["coordinates"])
        out.append(
            f"<Placemark><name>{label} ({f['properties']['meters'] / MI:.1f} mi)</name><styleUrl>#line</styleUrl>"
            f"<LineString><tessellate>1</tessellate><coordinates>{coords}</coordinates></LineString></Placemark>"
        )
    out.append("</Document></kml>")
    path = ROOT / "kml" / KML_FILES[layer_id]
    path.parent.mkdir(exist_ok=True)
    path.write_text("\n".join(out), encoding="utf-8")
    print("wrote", path.relative_to(ROOT), f"({len(places)} pins, {len(lines)} lines)")


def stop_card(p, numbered=True):
    e = html.escape
    num = f'<span class="num">{p["order"]}</span>' if numbered and p.get("order") else '<span class="dot"></span>'
    addr = f'<div class="addr">{e(p["address"])}</div>' if p.get("address") else ""
    return (
        f'<li class="stop">{num}<div class="body"><h3>{e(p["name"])}</h3>{addr}'
        f'<p>{e(p["note"])}</p>'
        f'<a class="dir" href="{directions_url(p)}" target="_blank" rel="noopener">Walking directions ↗</a></div></li>'
    )


def build_page(data, routes):
    tmpl = (ROOT / "tools" / "page_template.html").read_text(encoding="utf-8")
    by_layer = lambda lid: [p for p in data["places"] if p["layer"] == lid]
    meters = {f["properties"]["id"]: f["properties"]["meters"] for f in routes["features"]}
    mid = data.get("mymaps_mid", "").strip()
    walk_mi = meters["main"] / MI
    walk_min = round(walk_mi * 20 / 5) * 5  # ~20 min per mile, rounded to 5 minutes

    if mid:
        map_block = (f'<iframe class="map" src="https://www.google.com/maps/d/embed?mid={html.escape(mid)}" '
                     'title="Walking map" loading="lazy" allowfullscreen></iframe>')
        open_url = f"https://www.google.com/maps/d/viewer?mid={html.escape(mid)}"
    else:  # preview mode until the My Maps map exists: draw the same data with Leaflet
        map_block = '<div class="map" id="leaflet"></div>'
        open_url = "#"

    hill = {p["id"]: p for p in by_layer("hill")}
    extras = {p["id"]: p for p in by_layer("extras")}
    replacements = {
        "{{TITLE}}": html.escape(data["title"]),
        "{{MAP}}": map_block,
        "{{OPEN_URL}}": open_url,
        "{{OPEN_HIDDEN}}": "" if mid else " hidden",
        "{{WALK_MI}}": f"{walk_mi:.1f}",
        "{{WALK_MIN}}": str(walk_min),
        "{{HILL_MI}}": f"{meters['hill'] / MI:.1f}",
        "{{STOPS}}": "\n".join(stop_card(p) for p in sorted(by_layer("route"), key=lambda p: p["order"])),
        "{{HILL}}": "\n".join(stop_card(hill[k], False) for k in ("h_palmer", "h_stockwell", "h_mojo", "h_alicelloyd")),
        "{{ARB}}": stop_card(extras["x_arb"], False),
        "{{NORTH}}": stop_card(extras["x_north"], False),
        "{{FOOD}}": "\n".join(stop_card(p, False) for p in by_layer("food")),
        "{{LEAFLET_DATA}}": json.dumps({"places": data["places"], "layers": data["layers"], "routes": routes}) if not mid else "null",
    }
    for k, v in replacements.items():
        tmpl = tmpl.replace(k, v)
    out = ROOT / "docs" / "index.html"  # GitHub Pages serves from /docs on main
    out.parent.mkdir(exist_ok=True)
    out.write_text(tmpl, encoding="utf-8")
    print("wrote", out.relative_to(ROOT), f"(walk {walk_mi:.2f} mi, ~{walk_min} min walking; My Maps id: {mid or 'not set'})")


def main():
    data = json.loads((ROOT / "places.json").read_text(encoding="utf-8"))
    routes = json.loads((ROOT / "build" / "routes.geojson").read_text(encoding="utf-8"))
    for layer_id in KML_FILES:
        write_kml(data, routes, layer_id)
    build_page(data, routes)


if __name__ == "__main__":
    main()
