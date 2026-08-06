# ROS2 – Entwicklungsstand (Branch `feature/ros2-markerarray`)

## Projektziel

Dieser Branch enthält den aktuellen Entwicklungsstand des ROS2-Pakets `robot_rail_system`.
Das Ziel ist die Visualisierung eines Gebäudegraphen in RViz als Grundlage für Navigation und spätere Pfadplanung.
---

## Bereits implementierte Funktionen


## Aktueller Entwicklungsstand

Der aktuelle Entwicklungsstand bietet folgende Funktionen:

- Laden der Gebäudekarte über den ROS2 Map-Server
- Einlesen der Knotendaten aus der Datei `config/nodes.yaml`
- Automatische Erstellung eines `MarkerArray`
- Visualisierung aller Knoten als rote Marker in RViz
- Verwendung des Karten-Koordinatensystems (`map`)
- Dauerhafte Darstellung der Marker durch die QoS-Einstellung `TRANSIENT_LOCAL`
- Ausführlich kommentierter Quellcode zur besseren Nachvollziehbarkeit
- Versionsverwaltung über Git und GitHub mit einem eigenen Feature-Branch

---

## Nächste Entwicklungsschritte

Die folgenden Funktionen sind bereits geplant:

- Darstellung der Kanten (Edges)
- Aufbau eines vollständigen Gebäudegraphen
- Visualisierung der Verbindungen zwischen den Knoten
- Vorbereitung der Pfadplanung
- Integration in NAV2
- Zusammenführung mit dem Hauptzweig (`main`) nach erfolgreicher Teamabstimmung

- Ein ROS2-Paket (`robot_rail_system`) erstellt
- Kartenkonfiguration mit `my_map.yaml` und `my_map.pgm`
- Launch-Datei für den Map-Server erstellt
- Einlesen der Knoten aus `config/nodes.yaml`
- Visualisierung aller Knoten als `MarkerArray`
- Darstellung der Knoten als rote Kugeln in RViz
- Verwendung von `TRANSIENT_LOCAL` QoS, damit Marker auch nach einem RViz-Neustart erhalten bleiben
- Git-Repository eingerichtet
- Eigener Feature-Branch `feature/ros2-markerarray` erstellt

---

## Projektstruktur

```text
robot_rail_system/
├── config/
│   ├── nodes.yaml
│   └── edges.yaml
├── launch/
│   └── map_server.launch.py
├── maps/
│   ├── my_map.pgm
│   └── my_map.yaml
├── scripts/
│   └── show_nodes.py
├── CMakeLists.txt
└── package.xml
```

---

## Aktueller Entwicklungsstand

Der aktuelle Stand unterstützt:

- Laden der Gebäudekarte
- Einlesen aller Knoten aus einer YAML-Datei
- Visualisierung aller Knoten in RViz
- Vorbereitung der Graphstruktur für die spätere Darstellung der Kanten (Edges)

---

## Geplante Erweiterungen

- Darstellung der Kanten (Edges)
- Vollständiger Gebäudegraph
- Verbindung mit NAV2
- Pfadplanung zwischen zwei Knoten
- Optimierung und Zusammenführung mit dem Hauptzweig (`main`)
