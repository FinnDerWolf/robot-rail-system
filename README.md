# robot-rail-system

## TODOS
1. Alles auf geoJson umstellen
2. Lokale Costmap anzeigen
3. Stationsnamen anzeigen
4. Einige Knoten verschieben(in geoJason)
5. mux?

## Voraussetzungen

Das Projekt verwendet ROS 2 Jazzy und Nav2. Die benötigten ROS-Pakete können
unter Ubuntu 24.04 einmalig so installiert werden:

```bash
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup
```

## Bauen

Vom Root-Verzeichnis dieses Repositories:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select robot_rail_system
source install/setup.bash
```

Nach Änderungen am Quellcode muss das Paket erneut gebaut und das Setup erneut
geladen werden.

## Neues Terminal vorbereiten

In jedem neuen Terminal müssen ROS 2 und dieser Workspace geladen werden:

```bash
export ROS_DOMAIN_ID=3
source /opt/ros/jazzy/setup.bash
cd <PFAD-ZUM-WORKSPACE>/robot-rail-system
source install/setup.bash
```

## Gesamtsystem starten

```bash
ros2 launch robot_rail_system robot_rail_system.launch.py
```

Die gemeinsame Launch-Datei startet:

- den Map-Server mit `maps/my_map.yaml`,
- AMCL zur Lokalisierung auf dieser vorhandenen Karte,
- den Route Server mit `config/graph.geojson`,
- einen Lifecycle Manager, der Map-Server, AMCL und Route Server aktiviert,
- die für den bisherigen Roboter benötigten TF-Hilfen,
- die Knotenmarker,
- die interaktiven Topologiemarker und
- RViz.

RViz kann bei Bedarf deaktiviert werden:

```bash
ros2 launch robot_rail_system robot_rail_system.launch.py use_rviz:=false
```

Weitere Launch-Argumente:

```bash
ros2 launch robot_rail_system robot_rail_system.launch.py \
  use_sim_time:=false \
  map:=/absoluter/pfad/map.yaml \
  amcl_params_file:=/absoluter/pfad/amcl_params.yaml \
  graph_file:=/absoluter/pfad/graph.geojson \
  route_params_file:=/absoluter/pfad/route_server_params.yaml \
  rviz_config:=/absoluter/pfad/eigene_config.rviz
```

Der Roboter-Treiber und der übrige Nav2-Navigationsstack werden weiterhin
separat gestartet. Map-Server und AMCL dürfen dabei nicht ein zweites Mal
gestartet werden.

## Roboter und Lokalisierung starten

Zuerst den Roboter-Treiber und den LiDAR mit derselben `ROS_DOMAIN_ID` wie auf
diesem Rechner starten. Danach in einem vorbereiteten Terminal:

```bash
ros2 launch robot_rail_system robot_rail_system.launch.py
```

Die Launch-Datei erwartet:

- Odometrie auf `/odom`,
- Laserscans auf `/scan`,
- `frame_id: odom` und `child_frame_id: base_footprint` in den
  Odometrie-Nachrichten.

Vor dem Start kann geprüft werden, ob beide Datenquellen wirklich publizieren:

```bash
ros2 topic echo /odom --once
ros2 topic echo /scan --once --field header
```

Wenn einer der Befehle keine Nachricht erhält, kann AMCL noch keine
Transformation `map -> odom` berechnen. Die Warnung `Message Filter dropping
message ... queue is full` bedeutet in diesem Fall, dass für die Laserscans
keine vollständige TF-Kette nach `odom` verfügbar ist.

RViz lädt automatisch `config/robot_rail_system.rviz`. Darin sind die Karte,
die lokalisierte Roboterpose, Knoten, Kanten, die berechnete Route und interaktive
Topologiemarker bereits eingerichtet. Nach dem Start in RViz:

1. In der Toolbar `2D Pose Estimate` auswählen.
2. Auf der Karte an der ungefähren Roboterposition klicken und den Pfeil in
   Fahrtrichtung ziehen.

AMCL veröffentlicht anschließend `map -> odom`. Die Roboterpose wird dadurch
als Pfeil mit Positionsunsicherheit auf der Karte sichtbar. Die vollständige
TF-Kette ist:

```text
map -> odom -> base_footprint -> base_link -> laser
```

Sie kann so geprüft werden:

```bash
ros2 run tf2_ros tf2_echo map base_link
```

Die Gesamt-Launch-Datei wandelt standardmäßig `/odom` in TF um und ergänzt
`base_link -> laser`. Der vorhandene `robot_state_publisher` liefert bereits
`base_footprint -> base_link` mit der korrekten Roboterhöhe; diese Kante wird
daher standardmäßig nicht ein zweites Mal publiziert. Alle Hilfen sind einzeln
schaltbar:

```bash
ros2 launch robot_rail_system robot_rail_system.launch.py \
  publish_odom_tf:=false \
  publish_base_footprint_to_base_link:=false \
  publish_base_link_to_laser:=false
```

SLAM Toolbox darf in diesem Modus nicht parallel laufen: AMCL lokalisiert auf
der gespeicherten Karte, während SLAM Toolbox sonst einen konkurrierenden
`/map`-Publisher und `map -> odom`-Transform erzeugen würde.

## Komponenten einzeln starten

### Map-Server

```bash
ros2 launch robot_rail_system map_server.launch.py
```

Die einzelne Map-Launch-Datei enthält noch keinen Lifecycle Manager. In einem
zweiten vorbereiteten Terminal:

```bash
ros2 lifecycle set /map_server configure
ros2 lifecycle set /map_server activate
ros2 lifecycle get /map_server
```

Der letzte Befehl sollte `active` ausgeben.

### Route Server

```bash
ros2 launch robot_rail_system route_server_launch.py
```

Optional kann ein anderer Graph übergeben werden:

```bash
ros2 launch robot_rail_system route_server_launch.py \
  graph_file:=/absoluter/pfad/graph.geojson
```

### Knotenmarker

```bash
ros2 run robot_rail_system show_nodes.py
```

### Interaktive Topologiemarker

```bash
ros2 launch robot_rail_system topology_click_node.launch.py
```

### RViz

```bash
rviz2 -d install/robot_rail_system/share/robot_rail_system/config/robot_rail_system.rviz
```

Die mitgelieferte Konfiguration enthält folgende Displays:

- Map mit Topic `/map`
- optionales MarkerArray mit Topic `/node_markers` (standardmäßig deaktiviert,
  da diese roten Marker nicht interaktiv sind)
- MarkerArray mit Topic `/topology_graph_edges`
- InteractiveMarkers mit Namespace `/topology_markers`

## Interaktive Route testen

Nach dem Setzen der Initialpose:

1. In der RViz-Toolbar das Werkzeug `Interact` auswählen.
2. Auf einen beschrifteten grünen oder blauen Topologiemarker klicken.
3. Im Terminal die Meldungen `Station geklickt`, `Sende ComputeRoute` und
   anschließend `Route ... berechnet` prüfen.

Die Click-Node bestimmt über `map -> base_link` den der aktuellen
Roboterposition nächstgelegenen Graphknoten und fordert von dort eine Route zum
angeklickten Knoten an. Der berechnete Pfad erscheint in RViz als blaue Linie
über das Topic `/plan`. Das testet die Interaktion und Routenberechnung; das
tatsächliche Abfahren der Route benötigt später noch den vollständigen
Nav2-Controller- und Navigator-Stack.

### Route Server manuell testen

Beispielroute von `FlurEnde` (ID 1) zu `Raum107` (ID 10):

```bash
ros2 action send_goal /compute_route \
  nav2_msgs/action/ComputeRoute \
  "{start_id: 1, goal_id: 10, use_start: true, use_poses: false}" \
  --feedback
```

Dieser Befehl berechnet dieselbe Art von Route direkt über die Action, ohne
einen RViz-Klick.

## Hilfsskripte

Den eigenen Graphen in das Nav2-GeoJSON-Format konvertieren:

```bash
python3 scripts/convert_graph_geojson.py \
  config/nodes.geojson \
  config/edges.geojson \
  config/graph.geojson
```

## Offene Punkte

- übrigen Nav2-Navigationsstack integrieren
- Gesamtsystem auf dem echten Roboter testen und debuggen
- Präsentation vorbereiten
