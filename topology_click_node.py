#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Point
from visualization_msgs.msg import InteractiveMarker, InteractiveMarkerControl, Marker, MarkerArray
from interactive_markers.interactive_marker_server import InteractiveMarkerServer
from nav2_simple_commander.robot_navigator import BasicNavigator

# Knoten und Kanten
NODES_DATA = {
    "FlurEnde": {"x": -0.646, "y": 11.6, "is_door": False},
    "RaumFront": {"x": -0.129, "y": 16.404, "is_door": False},
    "Eingang105": {"x": -0.455, "y": 14.457, "is_door": True},
    "105Mitte": {"x": 2.993, "y": 17.653, "is_door": False},
    "Ende105": {"x": 5.861, "y": 17.653, "is_door": False},
    "EinganLab": {"x": 4.728, "y": 8.286, "is_door": True},
    "FlurLab": {"x": 4.959, "y": 11.154, "is_door": False},
    "LabTuer": {"x": 4.173, "y": 7.43, "is_door": False},
    "FlurMitte": {"x": 9.03, "y": 10.899, "is_door": False},
    "Raum107": {"x": 11.366, "y": 12.31, "is_door": False},
    "Raum109": {"x": 11.181, "y": 9.951, "is_door": False},
    "FlurEcke": {"x": 7.943, "y": 8.91, "is_door": False},
    "Tafel": {"x": -1.262, "y": 6.805, "is_door": False},
    "Pult": {"x": -1.771, "y": 3.22, "is_door": False},
    "EckeLab": {"x": 3.387, "y": 0.584, "is_door": False},
    "FensterLab": {"x": -1.632, "y": 0.838, "is_door": False}
}

EDGES_DATA = [
    ["FlurEnde", "Eingang105"],
    ["Eingang105", "RaumFront"],
    ["RaumFront", "105Mitte"],
    ["105Mitte", "Ende105"],
    ["FlurEnde", "FlurLab"],
    ["FlurLab", "EinganLab"],
    ["EinganLab", "LabTuer"],
    ["LabTuer", "Tafel"],
    ["LabTuer", "EckeLab"],
    ["EckeLab", "FensterLab"],
    ["Tafel", "Pult"],
    ["Pult", "FensterLab"],
    ["FlurLab", "FlurMitte"],
    ["FlurMitte", "Raum107"],
    ["Raum109", "Raum107"],
    ["FlurMitte", "Raum109"],
    ["FlurMitte", "FlurEcke"],
    ["FlurEcke", "Raum109"],
    ["Raum107", "FlurEcke"]
]


class TopologyClickNode(Node):
    def __init__(self):
        super().__init__('topology_click_node')

        # Nav2 Simple Commander Client initialisieren
        self.navigator = BasicNavigator()

        # Publisher für visuelle Darstellung Kanten
        self.edge_pub = self.create_publisher(MarkerArray, '/topology_graph_edges', 10)

        # Interactive Marker Server für RVIZ
        self.server = InteractiveMarkerServer(self, 'topology_markers')

        # Visualisierungen & Marker hochfahren
        self._create_station_markers()
        
        # Timer, um Kanten immer wieder zu Zeichnen
        self.timer = self.create_timer(2.0, self._publish_graph_edges)

        self.get_logger().info('Topology Click Node gestartet!')
        self.get_logger().info('Warte auf Klicks auf Knoten/Stationen in RVIZ...')

    # INTERACTIVE MARKER
    def _create_station_markers(self):
        # Erstellt für jeden Knoten in NODES_DATA einen anklickbaren Marker in RVIZ.
        for node_id, data in NODES_DATA.items():
            int_marker = InteractiveMarker()
            int_marker.header.frame_id = "map"
            int_marker.name = node_id
            int_marker.description = f"{node_id} {'[Tuer]' if data['is_door'] else ''}"
            int_marker.pose.position.x = data['x']
            int_marker.pose.position.y = data['y']
            int_marker.pose.position.z = 0.15

            control = InteractiveMarkerControl()
            control.always_visible = True
            control.interaction_mode = InteractiveMarkerControl.BUTTON

            # Marker für den Knoten
            marker = Marker()
            marker.type = Marker.CYLINDER
            marker.scale.x = 0.35
            marker.scale.y = 0.35
            marker.scale.z = 0.15

            # Türen = Blau, Normale Knoten = Grün
            if data['is_door']:
                marker.color.r = 0.2
                marker.color.g = 0.5
                marker.color.b = 1.0
            else:
                marker.color.r = 0.1
                marker.color.g = 0.8
                marker.color.b = 0.2
            
            marker.color.a = 0.9

            control.markers.append(marker)
            int_marker.controls.append(control)

            # In Server eintragen & Callback verknüpfen
            self.server.insert(int_marker, feedback_callback=self._on_marker_click)

        self.server.applyChanges()

    # EVENT HANDLER & ROUTE COMMAND
    def _on_marker_click(self, feedback):
        # Wird ausgelöst wenn in Rviz auf Knoten gedrueckt wird
        if feedback.event_type == feedback.BUTTON_CLICK:
            clicked_node = feedback.marker_name

            # What was clicked? Is it a station?
            if clicked_node in NODES_DATA:
                node_info = NODES_DATA[clicked_node]
                self.get_logger().info(
                    f"-> [STATION GEKLICKT] ID: '{clicked_node}' | Pos: ({node_info['x']}, {node_info['y']})"
                )

                # Invoke command at route server
                self.send_route_goal(clicked_node, node_info)
            else:
                self.get_logger().warn(f"Unbekanntes Element angeklickt: {clicked_node}")

    def send_route_goal(self, node_id: str, node_info: dict):
        # Erstellt das Ziel und übergibt es an Nav2
        goal_pose = PoseStamped()
        goal_pose.header.frame_id = "map"
        goal_pose.header.stamp = self.get_clock().now().to_msg()
        
        goal_pose.pose.position.x = float(node_info['x'])
        goal_pose.pose.position.y = float(node_info['y'])
        goal_pose.pose.orientation.w = 1.0  # Standarmäßig Ausrichtung 0 Grad

        self.get_logger().info(f"Sende Ziel an Nav2 Route Server -> {node_id}")
        
        # Aufruf an Nav2
        self.navigator.goToPose(goal_pose)

    # EDGES VISUALISIERUNG (KANTEN)
    def _publish_graph_edges(self):
        # Zeichnet die Kanten als gelbe Linien in RVIZ.
        marker_array = MarkerArray()
        
        line_marker = Marker()
        line_marker.header.frame_id = "map"
        line_marker.header.stamp = self.get_clock().now().to_msg()
        line_marker.ns = "topology_edges"
        line_marker.id = 0
        line_marker.type = Marker.LINE_LIST
        line_marker.action = Marker.ADD
        line_marker.scale.x = 0.05  # Linien-Dicke in Metern
        
        # Farbe
        line_marker.color.r = 1.0
        line_marker.color.g = 0.9
        line_marker.color.b = 0.1
        line_marker.color.a = 0.7

        for start_id, end_id in EDGES_DATA:
            if start_id in NODES_DATA and end_id in NODES_DATA:
                p_start = Point()
                p_start.x = float(NODES_DATA[start_id]['x'])
                p_start.y = float(NODES_DATA[start_id]['y'])
                p_start.z = 0.05

                p_end = Point()
                p_end.x = float(NODES_DATA[end_id]['x'])
                p_end.y = float(NODES_DATA[end_id]['y'])
                p_end.z = 0.05

                line_marker.points.append(p_start)
                line_marker.points.append(p_end)

        marker_array.markers.append(line_marker)
        self.edge_pub.publish(marker_array)


# MAIN MAIN FUNCTION
def main(args=None):
    rclpy.init(args=args)
    node = TopologyClickNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()