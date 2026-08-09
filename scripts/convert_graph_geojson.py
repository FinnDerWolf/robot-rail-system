#!/usr/bin/env python3
"""
Konvertiert das eigene Format (nodes.geojson mit {name: {x,y,is_door}},
edges.geojson mit [[from, to], ...]) in eine einzige GeoJSON-Datei,
die dem nav2_route GeoJsonGraphFileLoader-Konventionen entspricht:
  - Node-Feature: Point, properties.id (int), properties.metadata.name,
    properties.frame
  - Edge-Feature: LineString, properties.id (int), properties.startid,
    properties.endid

Kanten in edges.geojson werden als ungerichtete Paare interpretiert und
standardmäßig in BEIDE Richtungen als separate, gerichtete Nav2-Edges
geschrieben (üblich für begehbare Flure/Räume). Mit --directed nur die
angegebene Richtung erzeugen.

Nutzung:
    python3 convert_graph_geojson.py nodes.geojson edges.geojson graph.geojson
    python3 convert_graph_geojson.py nodes.geojson edges.geojson graph.geojson --directed
"""

import json
import sys


def convert(nodes_path, edges_path, out_path, directed=False, frame="map"):
    with open(nodes_path, "r", encoding="utf-8") as f:
        nodes_data = json.load(f)["nodes"]

    with open(edges_path, "r", encoding="utf-8") as f:
        edges_data = json.load(f)["edges"]

    # Namen -> fortlaufende numerische ID
    name_to_id = {name: i + 1 for i, name in enumerate(nodes_data.keys())}

    node_features = []
    for name, props in nodes_data.items():
        node_features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [props["x"], props["y"]],
            },
            "properties": {
                "id": name_to_id[name],
                "frame": frame,
                "metadata": {
                    "name": name,
                    "is_door": props.get("is_door", False),
                },
            },
        })

    coords_by_name = {name: (props["x"], props["y"]) for name, props in nodes_data.items()}

    edge_features = []
    next_edge_id = 1
    for start_name, end_name in edges_data:
        pairs = [(start_name, end_name)]
        if not directed:
            pairs.append((end_name, start_name))

        for a, b in pairs:
            if a not in name_to_id or b not in name_to_id:
                raise ValueError(f"Kante referenziert unbekannten Knoten: {a} -> {b}")

            edge_features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [list(coords_by_name[a]), list(coords_by_name[b])],
                },
                "properties": {
                    "id": next_edge_id,
                    "startid": name_to_id[a],
                    "endid": name_to_id[b],
                    "metadata": {},
                },
            })
            next_edge_id += 1

    merged = {
        "type": "FeatureCollection",
        "features": node_features + edge_features,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    print(f"{len(node_features)} Knoten, {len(edge_features)} Kanten "
          f"({'gerichtet' if directed else 'bidirektional'}) -> {out_path}")


def main():
    args = sys.argv[1:]
    directed = "--directed" in args
    args = [a for a in args if a != "--directed"]

    if len(args) != 3:
        print(f"Usage: {sys.argv[0]} nodes.geojson edges.geojson output.geojson [--directed]")
        sys.exit(1)

    convert(args[0], args[1], args[2], directed=directed)


if __name__ == "__main__":
    main()
