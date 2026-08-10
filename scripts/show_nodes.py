#!/usr/bin/env python3

# Verbindung zur ROS2-Python-Bibliothek
import rclpy
# Zum Einlesen der nodes.yaml-Datei
import yaml
# Basisklasse für einen eigenen ROS2-Node
from rclpy.node import Node
# Ermittelt den Installationspfad unseres ROS2-Packets
from ament_index_python.packages import get_package_share_directory
# Marker für einzelne Objekte und MarkerArray für mehrere Marker
from visualization_msgs.msg import Marker, MarkerArray
from rclpy.qos import QoSProfile, DurabilityPolicy
# Eigener ROS2-Node zum Anzeigen der Knoten in RViz
class ShowNodes(Node):
    """Liest nodes.yaml ein und veröffentlicht Marker für RViz."""

    # Konstruktor des ROS2-Nodes
    def __init__(self):
        # Registriert den Node bei ROS2 unter dem Namen "show_nodes"
        super().__init__("show_nodes")
        # Gibt eine Startmeldung im ROS2-Logger
        self.get_logger().info("ShowNodes gestartet.")
        
        # QoS-Profil für dauerhaft gespeicherte Marker
        qos = QoSProfile(depth=50)
        qos.durability = DurabilityPolicy.TRANSIENT_LOCAL

        # Erstellt einen Publisher für MarkerArrays
        # Dadurch können mehrere Marker gleichzeitig an RViz gesendet werden.
        self.marker_publisher = self.create_publisher(
            MarkerArray,
            "node_markers",
            qos
        )       # Ermittelt den Installationspfad unseres ROS2-Pakets
        package_path = get_package_share_directory("robot_rail_system")
        self.nodes_file = package_path + "/config/nodes.yaml"
        
        # Öffnet die Datei "nodes.yaml" im Lesemodus
        with open(self.nodes_file, "r") as file:

            # Liest den gesamten Inhalt der YAML-Datei ein
            nodes_data = yaml.safe_load(file)

        # Bestätigt im ROS2-Logger die erfolgreiche YAML-Datei Einlesung
        self.get_logger().info("nodes.yaml wurde erfolgreich eingelesen.")

        # Holt den Bereich "nodes" asu den eingelesenen YAML-Daten
        nodes = nodes_data["nodes"]

        # Erstellt eine gemeinsame Nachricht für alle Knotenmarker
        marker_array = MarkerArray()

        # Durchläuft alle Knoten aus der nodes.yaml-Datei
        for marker_id, (name, node) in enumerate(nodes.items()):
            # Gibt den Namen des aktuellen Knotens im ROS"-Logger aus
            self.get_logger().info(name)

            # Liest die x- und y-Koordinaten des aktuellen Knotens aus
            x = node["x"]
            y = node["y"]

            # Erstellt einen neune Marker für den aktuellen Knoten
            marker = Marker()

            # Verwendet das Karten-Koordinatensystem
            marker.header.frame_id = "map"

            # Ordnet alle Knotenmarker derselben Gruppe zu
            marker.ns = "nodes"

            # Fügt den Marker hinzu oder aktualisiert ihn
            marker.action = Marker.ADD

            # Vergibt eine eindeutige ID für jeden Marker
            marker.id = marker_id

            # Setzt eine gültige Orientierung
            marker.pose.orientation.w = 1.0

            # Der Marker wird als Kugel dargestellt
            marker.type = Marker.SPHERE 

            # Position des Markers auf der Karte
            marker.pose.position.x = x
            marker.pose.position.y = y
            marker.pose.position.z = 0.0

            # Größe der Kugel in Metern
            marker.scale.x = 0.20
            marker.scale.y = 0.20
            marker.scale.z = 0.20

            # Farbe der Kugel (ROT)
            marker.color.r = 1.0
            marker.color.g = 0.0
            marker.color.b = 0.0
            marker.color.a = 1.0

            # Fügt den aktuellen Marker dem MarkerArray hinzu
            marker_array.markers.append(marker)

        # Veröffentlicht alle Marker gleichzeitig
        self.marker_publisher.publish(marker_array)

# Startet den ROS2-Node
def main(args=None):
    rclpy.init(args=args)

    node = ShowNodes()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
# Führt main() aus, wenn die Datei direkt gestartet wird
if __name__ == "__main__":
    main()
