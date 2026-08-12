# robot-rail-system

Dieses Projekt wurde im Rahmen des Moduls "Robotik" im Sommersemester 2026 an der Hochschule Fulda entwickelt und setzt autonomes fahren eines Roboters entlang eines vorgegebenen "Schienensystems" um.

## Bringup

Zum starten des Systems werden ein Volksbot mit **SICK** Lidar und ein PC mit Ubuntu 24.04 und ros2 benötigt.

### Vorraussetzungen (auf PC)

Die benötigten ROS-Pakete können
unter Ubuntu 24.04 so installiert werden:

```bash
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup
```

### Build (auf PC)

Vom Root-Verzeichnis dieses Repositories:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select robot_rail_system
source install/setup.bash
```

### Gesamtsystem starten

Den Volksbot per ssh in neuem Terminal starten(in einem Terminal auf dem Bot ausführen):
```bash
cd ~/ros2_ws
source install/setup.bash
ros2 launch volksbot_driver volksbot_lidar_sick.py
```

Das System auf dem PC in ursprünglichem Terminal starten:
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


## Kollaboratoren und "Wer hat was gemacht"

1. Finn Wolf
    - Controller Server implementiert
    - Allgemeine Launch Datei geschrieben
    - Rviz setup und Config
    - Initiale Map creation mit Slam
    - Dokumentation
    - odom_to_tf skript

2. Christian
    - Graph editor und yamlToGeojson skripte
    - GeoJson config
    - Route Server implementiert

3. Hakan
    - Map Server implementiert
    - viele kleien fleiß Aufgaben im Team

4. Jonas Schmidt
    - topology_click_node implementiert