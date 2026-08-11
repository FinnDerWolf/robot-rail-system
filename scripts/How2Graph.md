# Erstellen eines Graphen

#### 1. Graph-Programm mit eigener Map starten

```
python3 graph_editor.py --map my_map.yaml
```

> - Benötigt map.yaml und map.pgm  
> - --map erhält den Pfad der Karte

#### 2. edges.yaml und nodes.yaml in .geoJson umwandeln
```
python3 convertYaml2Geojson.py
```
> Auswahl der konvertierten Datei über Anpassung im Skript

#### 3. Graph aus nodes.geojson und edges.geojson zusammensetzen
```
python3 convert_graph_geojson.py nodes.geojson edges.geojson graph.geojson
```
> - Übergabe von nodes.geojson, edges.geojson  
> - Ausgabe in graph.json (beliebiger Name)
