#!/usr/bin/env python3

import json
import os

from ament_index_python.packages import get_package_share_directory

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import Point
from interactive_markers.interactive_marker_server import (
    InteractiveMarkerServer,
)
from nav2_msgs.action import ComputeRoute, FollowPath
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformException, TransformListener
from visualization_msgs.msg import (
    InteractiveMarker,
    InteractiveMarkerControl,
    Marker,
    MarkerArray,
)

# GEOJSON Path
GEOJSON_PATH = os.path.join(
    get_package_share_directory("robot_rail_system"),
    "config",
    "new_graph.geojson",
)

# Laedt die GEOJSON
def load_geojson(path):

    with open(path, "r", encoding="utf-8") as file:
        geojson = json.load(file)

    nodes_data = {}
    edges_data = []

    for feature in geojson.get("features", []):
        geometry = feature.get("geometry")
        properties = feature.get("properties", {})

        if geometry is None:
            continue

        geometry_type = geometry.get("type")

        # Nodes auslesen
        if geometry_type == "Point":

            coordinates = geometry.get("coordinates", [])

            if len(coordinates) < 2:
                print(
                    "WARNUNG: Point ohne gültige Koordinaten gefunden."
                )
                continue

            node_id = properties.get("id")

            metadata = properties.get("metadata", {})
            node_name = metadata.get("name")

            if node_id is None:
                print(
                    "WARNUNG: Node ohne ID gefunden. "
                    f"Name: {node_name}"
                )
                continue

            if node_name is None:
                node_name = f"node_{node_id}"

            nodes_data[node_name] = {
                "id": int(node_id),
                "x": float(coordinates[0]),
                "y": float(coordinates[1]),
                "is_door": bool(properties.get("is_door", False)),
            }

        # Edges auslesen
        elif geometry_type == "LineString":

            start_id = properties.get("startid")
            end_id = properties.get("endid")

            if start_id is None or end_id is None:
                print(
                    "WARNUNG: LineString ohne startid/endid gefunden."
                )
                continue

            edges_data.append(
                [
                    int(start_id),
                    int(end_id),
                ]
            )

    # IDs auf Namen umwandeln
    id_to_name = {
        data["id"]: name
        for name, data in nodes_data.items()
    }

    named_edges = []

    for start_id, end_id in edges_data:

        if start_id not in id_to_name:
            print(
                f"WARNUNG: Edge verweist auf unbekannten "
                f"Startknoten {start_id}"
            )
            continue

        if end_id not in id_to_name:
            print(
                f"WARNUNG: Edge verweist auf unbekannten "
                f"Endknoten {end_id}"
            )
            continue

        named_edges.append(
            [
                id_to_name[start_id],
                id_to_name[end_id],
            ]
        )

    print(
        f"GeoJSON geladen: "
        f"{len(nodes_data)} Nodes, "
        f"{len(named_edges)} Edges"
    )

    return nodes_data, named_edges

# TopologyClickNode
class TopologyClickNode(Node):

    def __init__(self):
        super().__init__("topology_click_node")

        # Versuchen die GEOJSON zu laden
        try:
            self.nodes_data, self.edges_data = load_geojson(
                GEOJSON_PATH
            )

        except FileNotFoundError:
            self.get_logger().error(
                f"GeoJSON nicht gefunden: {GEOJSON_PATH}"
            )
            raise

        except json.JSONDecodeError as error:
            self.get_logger().error(
                f"GeoJSON ist ungültig: {error}"
            )
            raise

        except Exception as error:
            self.get_logger().error(
                f"Fehler beim Laden der GeoJSON: {error}"
            )
            raise

        # Route Client
        self.route_client = ActionClient(
            self,
            ComputeRoute,
            "/compute_route",
        )

        self.follow_path_client = ActionClient(
            self,
            FollowPath,
            "/follow_path",
        )

        # TF laden
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(
            self.tf_buffer,
            self,
        )

        # Edge Publisher
        self.edge_pub = self.create_publisher(
            MarkerArray,
            "/topology_graph_edges",
            10,
        )

        # Interactive Marker Server
        self.server = InteractiveMarkerServer(
            self,
            "topology_markers",
        )

        # Marker erstellen
        self._create_station_markers()

        #Edge Timer
        self.timer = self.create_timer(
            2.0,
            self._publish_graph_edges,
        )

        self.get_logger().info(
            "Topology Click Node gestartet!"
        )

        self.get_logger().info(
            f"GeoJSON: {len(self.nodes_data)} Nodes, "
            f"{len(self.edges_data)} Edges"
        )

        self.get_logger().info(
            "Warte auf Klicks auf Knoten/Stationen in RViz..."
        )

    # Interaktive Marker
    def _create_station_markers(self):
    
        # Erstellt für jede Node einen Marker
        for node_name, data in self.nodes_data.items():
    
            int_marker = InteractiveMarker()
    
            int_marker.header.frame_id = "map"
            int_marker.name = node_name
    
            door_label = "[Tuer]" if data["is_door"] else ""
    
            int_marker.description = (
                f"{node_name} {door_label}"
            )
    
            # Position des Interactive Markers
            int_marker.pose.position.x = data["x"]
            int_marker.pose.position.y = data["y"]
            int_marker.pose.position.z = 0.15
    
            int_marker.pose.orientation.w = 1.0
    
            # Control
            control = InteractiveMarkerControl()
    
            control.always_visible = True
            control.interaction_mode = (
                InteractiveMarkerControl.BUTTON
            )
    
            # Node Zylinder
            node_marker = Marker()
    
            node_marker.type = Marker.CYLINDER
    
            node_marker.scale.x = 0.35
            node_marker.scale.y = 0.35
            node_marker.scale.z = 0.15
    
            # Türen = Blau
            # normale Nodes = Grün
    
            if data["is_door"]:
                node_marker.color.r = 0.2
                node_marker.color.g = 0.5
                node_marker.color.b = 1.0
            else:
                node_marker.color.r = 0.1
                node_marker.color.g = 0.8
                node_marker.color.b = 0.2
    
            node_marker.color.a = 0.9
    
            control.markers.append(node_marker)
    
            # Node Name
            name_marker = Marker()
    
            name_marker.type = Marker.TEXT_VIEW_FACING
    
            # Text über dem Knoten
            name_marker.pose.position.x = 0.0
            name_marker.pose.position.y = 0.0
            name_marker.pose.position.z = 0.35
    
            # Name des Nodes
            name_marker.text = node_name
    
            # Schriftgröße
            name_marker.scale.z = 0.30
    
            # Schwarze Schrift
            name_marker.color.r = 0.0
            name_marker.color.g = 0.0
            name_marker.color.b = 0.0
            name_marker.color.a = 1.0
    
            control.markers.append(name_marker)
    
            # Registrieren der Marker
            int_marker.controls.append(control)
    
            self.server.insert(
                int_marker,
                feedback_callback=self._on_marker_click,
            )

        self.server.applyChanges()

    # Click Handler
    def _on_marker_click(self, feedback):

        # Wird ausgelöst wenn auf Marker geclickt wird
        if feedback.event_type == feedback.BUTTON_CLICK:

            clicked_node = feedback.marker_name

            if clicked_node in self.nodes_data:

                node_info = self.nodes_data[clicked_node]

                graph_id = node_info["id"]
                node_x = node_info["x"]
                node_y = node_info["y"]

                self.get_logger().info(
                    "Station geklickt: "
                    f"{clicked_node} "
                    f"(Graph-ID {graph_id}, "
                    f"Position {node_x}, {node_y})"
                )

                self.send_route_goal(
                    clicked_node,
                    graph_id,
                )

            else:

                self.get_logger().warn(
                    f"Unbekanntes Element angeklickt: "
                    f"{clicked_node}"
                )

    # Route Command
    def send_route_goal(
        self,
        node_name: str,
        graph_id: int,
    ):

        # Fordert Route an
        if not self.route_client.server_is_ready():

            self.get_logger().error(
                "Route Server /compute_route ist "
                "nicht verfügbar."
            )

            return

        start_node = self._find_nearest_start_node()

        if start_node is None:
            return

        start_name, start_id = start_node

        goal = ComputeRoute.Goal()

        goal.start_id = start_id
        goal.goal_id = graph_id

        goal.use_start = True
        goal.use_poses = False

        self.get_logger().info(
            f"Sende ComputeRoute: "
            f"{start_name} (ID {start_id}) -> "
            f"{node_name} (ID {graph_id})"
        )

        future = self.route_client.send_goal_async(goal)

        future.add_done_callback(
            lambda response:
            self._route_goal_response(
                response,
                node_name,
            )
        )

    # Suche nächste Node
    def _find_nearest_start_node(self):

        # Finde den nächsten Knoten
        try:
            transform = self.tf_buffer.lookup_transform(
                "map",
                "base_link",
                Time(),
            )
        except TransformException as error:
            self.get_logger().error(
                "Startknoten kann ohne "
                "map -> base_link nicht bestimmt werden: "
                f"{error}"
            )
            return None
            
        robot_x = transform.transform.translation.x
        robot_y = transform.transform.translation.y

        nearest_name, nearest_data = min(
            self.nodes_data.items(),
            key=lambda item:
            (
                (item[1]["x"] - robot_x) ** 2
                +
                (item[1]["y"] - robot_y) ** 2
            ),
        )

        distance = (
            (
                nearest_data["x"] - robot_x
            ) ** 2
            +
            (
                nearest_data["y"] - robot_y
            ) ** 2
        ) ** 0.5

        nearest_id = nearest_data["id"]

        self.get_logger().info(
            f"Nächster Startknoten: "
            f"{nearest_name} "
            f"(ID {nearest_id}, "
            f"Abstand {distance:.2f} m)"
        )

        return nearest_name, nearest_id

    # Route Response
    def _route_goal_response(
        self,
        future,
        node_name: str,
    ):

        try:
            goal_handle = future.result()
        except Exception as error:
            self.get_logger().error(
                f"Route-Anfrage für {node_name} "
                f"fehlgeschlagen: {error}"
            )

            return

        if not goal_handle.accepted:

            self.get_logger().error(
                f"Route Server hat das Ziel "
                f"{node_name} abgelehnt."
            )

            return

        self.get_logger().info(
            f"Route Server berechnet die Route "
            f"nach {node_name} ..."
        )

        result_future = (
            goal_handle.get_result_async()
        )

        result_future.add_done_callback(
            lambda result:
            self._route_result(
                result,
                node_name,
            )
        )

    # Route Result
    def _route_result(
        self,
        future,
        node_name: str,
    ):

        try:
            wrapped_result = future.result()
        except Exception as error:
            self.get_logger().error(
                f"Routenberechnung für {node_name} "
                f"fehlgeschlagen: {error}"
            )

            return

        result = wrapped_result.result

        if (
            wrapped_result.status
            != GoalStatus.STATUS_SUCCEEDED
            or
            result.error_code
            != ComputeRoute.Result.NONE
        ):

            self.get_logger().error(
                f"Keine Route nach {node_name}: "
                f"Status {wrapped_result.status}, "
                f"Fehlercode {result.error_code}"
            )

            return

        self.get_logger().info(
            f"Route nach {node_name} berechnet: "
            f"{len(result.route.nodes)} Knoten, "
            f"{len(result.path.poses)} Pfadpunkte, "
            f"Kosten {result.route.route_cost:.3f}"
        )

        self._send_follow_path(
            node_name,
            result.path,
        )

    # Follow Path
    def _send_follow_path(
        self,
        node_name: str,
        path,
    ):

        if not path.poses:

            self.get_logger().error(
                f"Route nach {node_name} "
                f"enthält keine Pfadpunkte."
            )

            return

        if not self.follow_path_client.server_is_ready():

            self.get_logger().error(
                "Controller Server /follow_path "
                "ist nicht verfügbar."
            )

            return

        goal = FollowPath.Goal()

        goal.path = path
        goal.controller_id = "FollowPath"
        goal.goal_checker_id = "goal_checker"
        goal.progress_checker_id = "progress_checker"

        self.get_logger().info(
            f"Sende FollowPath für {node_name} "
            f"an den Controller Server."
        )

        future = (
            self.follow_path_client.send_goal_async(
                goal
            )
        )

        future.add_done_callback(
            lambda response:
            self._follow_path_goal_response(
                response,
                node_name,
            )
        )

    # Follow Path Response
    def _follow_path_goal_response(
        self,
        future,
        node_name: str,
    ):

        try:
            goal_handle = future.result()
        except Exception as error:
            self.get_logger().error(
                f"FollowPath-Anfrage für {node_name} "
                f"fehlgeschlagen: {error}"
            )

            return

        if not goal_handle.accepted:

            self.get_logger().error(
                f"Controller Server hat den Pfad "
                f"nach {node_name} abgelehnt."
            )

            return

        self.get_logger().info(
            f"Roboter fährt nach {node_name} ..."
        )

        result_future = (
            goal_handle.get_result_async()
        )

        result_future.add_done_callback(
            lambda result:
            self._follow_path_result(
                result,
                node_name,
            )
        )

    # Follow Path Result
    def _follow_path_result(
        self,
        future,
        node_name: str,
    ):

        try:
            wrapped_result = future.result()
        except Exception as error:
            self.get_logger().error(
                f"Fahrt nach {node_name} "
                f"fehlgeschlagen: {error}"
            )

            return

        result = wrapped_result.result

        if (
            wrapped_result.status
            != GoalStatus.STATUS_SUCCEEDED
            or
            result.error_code
            != FollowPath.Result.NONE
        ):

            self.get_logger().error(
                f"Fahrt nach {node_name} "
                f"nicht erfolgreich: "
                f"Status {wrapped_result.status}, "
                f"Fehlercode {result.error_code}, "
                f"Meldung: {result.error_msg}"
            )

            return

        self.get_logger().info(
            f"Ziel {node_name} erreicht."
        )

    # Edge visualisierung
    def _publish_graph_edges(self):
        # Zeichne alle Edges aus der GEOJSON
        marker_array = MarkerArray()

        line_marker = Marker()

        line_marker.header.frame_id = "map"

        line_marker.header.stamp = (
            self.get_clock().now().to_msg()
        )

        line_marker.ns = "topology_edges"
        line_marker.id = 0

        line_marker.type = Marker.LINE_LIST
        line_marker.action = Marker.ADD

        line_marker.scale.x = 0.05

        # Farbe: Gelb

        line_marker.color.r = 1.0
        line_marker.color.g = 0.9
        line_marker.color.b = 0.1
        line_marker.color.a = 0.7

        for start_name, end_name in self.edges_data:

            if (
                start_name not in self.nodes_data
                or
                end_name not in self.nodes_data
            ):
                continue

            start_data = self.nodes_data[start_name]
            end_data = self.nodes_data[end_name]

            p_start = Point()

            p_start.x = float(start_data["x"])
            p_start.y = float(start_data["y"])
            p_start.z = 0.05

            p_end = Point()

            p_end.x = float(end_data["x"])
            p_end.y = float(end_data["y"])
            p_end.z = 0.05

            line_marker.points.append(p_start)
            line_marker.points.append(p_end)

        marker_array.markers.append(line_marker)

        self.edge_pub.publish(marker_array)

# Main
def main(args=None):
    rclpy.init(args=args)
    node = TopologyClickNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
