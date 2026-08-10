#!/usr/bin/env python3

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import Point
from interactive_markers.interactive_marker_server import InteractiveMarkerServer
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

# Knoten und Kanten
NODES_DATA = {
    'FlurEnde': {'id': 1, 'x': -0.646, 'y': 11.6, 'is_door': False},
    'RaumFront': {'id': 2, 'x': -0.129, 'y': 16.404, 'is_door': False},
    'Eingang105': {'id': 3, 'x': -0.455, 'y': 14.457, 'is_door': True},
    '105Mitte': {'id': 4, 'x': 2.993, 'y': 17.653, 'is_door': False},
    'Ende105': {'id': 5, 'x': 5.861, 'y': 17.653, 'is_door': False},
    'EinganLab': {'id': 6, 'x': 4.728, 'y': 8.286, 'is_door': True},
    'FlurLab': {'id': 7, 'x': 4.959, 'y': 11.154, 'is_door': False},
    'LabTuer': {'id': 8, 'x': 4.173, 'y': 7.43, 'is_door': False},
    'FlurMitte': {'id': 9, 'x': 9.03, 'y': 10.899, 'is_door': False},
    'Raum107': {'id': 10, 'x': 11.366, 'y': 12.31, 'is_door': False},
    'Raum109': {'id': 11, 'x': 11.181, 'y': 9.951, 'is_door': False},
    'FlurEcke': {'id': 12, 'x': 7.943, 'y': 8.91, 'is_door': False},
    'Tafel': {'id': 13, 'x': -1.262, 'y': 6.805, 'is_door': False},
    'Pult': {'id': 14, 'x': -1.771, 'y': 3.22, 'is_door': False},
    'EckeLab': {'id': 15, 'x': 3.387, 'y': 0.584, 'is_door': False},
    'FensterLab': {'id': 16, 'x': -1.632, 'y': 0.838, 'is_door': False},
}

EDGES_DATA = [
    ['FlurEnde', 'Eingang105'],
    ['Eingang105', 'RaumFront'],
    ['RaumFront', '105Mitte'],
    ['105Mitte', 'Ende105'],
    ['FlurEnde', 'FlurLab'],
    ['FlurLab', 'EinganLab'],
    ['EinganLab', 'LabTuer'],
    ['LabTuer', 'Tafel'],
    ['LabTuer', 'EckeLab'],
    ['EckeLab', 'FensterLab'],
    ['Tafel', 'Pult'],
    ['Pult', 'FensterLab'],
    ['FlurLab', 'FlurMitte'],
    ['FlurMitte', 'Raum107'],
    ['Raum109', 'Raum107'],
    ['FlurMitte', 'Raum109'],
    ['FlurMitte', 'FlurEcke'],
    ['FlurEcke', 'Raum109'],
    ['Raum107', 'FlurEcke'],
]


class TopologyClickNode(Node):
    def __init__(self):
        super().__init__('topology_click_node')

        # Verbindet Klicks mit dem bereits laufenden Nav2 Route Server.
        self.route_client = ActionClient(self, ComputeRoute, '/compute_route')
        self.follow_path_client = ActionClient(
            self,
            FollowPath,
            '/follow_path',
        )
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Publisher für visuelle Darstellung Kanten
        self.edge_pub = self.create_publisher(
            MarkerArray,
            '/topology_graph_edges',
            10,
        )

        # Interactive Marker Server für RViz
        self.server = InteractiveMarkerServer(self, 'topology_markers')

        # Visualisierungen & Marker hochfahren
        self._create_station_markers()

        # Timer, um Kanten immer wieder zu Zeichnen
        self.timer = self.create_timer(2.0, self._publish_graph_edges)

        self.get_logger().info('Topology Click Node gestartet!')
        self.get_logger().info('Warte auf Klicks auf Knoten/Stationen in RVIZ...')

    # INTERACTIVE MARKER
    def _create_station_markers(self):
        # Erstellt für jeden Knoten einen anklickbaren Marker in RViz.
        for node_id, data in NODES_DATA.items():
            int_marker = InteractiveMarker()
            int_marker.header.frame_id = 'map'
            int_marker.name = node_id
            door_label = '[Tuer]' if data['is_door'] else ''
            int_marker.description = f'{node_id} {door_label}'
            int_marker.pose.position.x = data['x']
            int_marker.pose.position.y = data['y']
            int_marker.pose.position.z = 0.15
            int_marker.pose.orientation.w = 1.0

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
            self.server.insert(
                int_marker,
                feedback_callback=self._on_marker_click,
            )

        self.server.applyChanges()

    # EVENT HANDLER & ROUTE COMMAND
    def _on_marker_click(self, feedback):
        # Wird ausgelöst wenn in Rviz auf Knoten gedrueckt wird
        if feedback.event_type == feedback.BUTTON_CLICK:
            clicked_node = feedback.marker_name

            # What was clicked? Is it a station?
            if clicked_node in NODES_DATA:
                node_info = NODES_DATA[clicked_node]
                graph_id = node_info['id']
                node_x = node_info['x']
                node_y = node_info['y']
                self.get_logger().info(
                    'Station geklickt: '
                    f'{clicked_node} (Graph-ID {graph_id}, '
                    f'Position {node_x}, {node_y})'
                )

                self.send_route_goal(clicked_node, graph_id)
            else:
                self.get_logger().warn(
                    f'Unbekanntes Element angeklickt: {clicked_node}'
                )

    def send_route_goal(self, node_name: str, graph_id: int):
        """Fordert eine Route von der aktuellen Roboterpose zum Zielknoten an."""
        if not self.route_client.server_is_ready():
            self.get_logger().error(
                'Route Server /compute_route ist nicht verfügbar.'
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
            f'Sende ComputeRoute: {start_name} (ID {start_id}) -> '
            f'{node_name} (ID {graph_id})'
        )
        future = self.route_client.send_goal_async(goal)
        future.add_done_callback(
            lambda response: self._route_goal_response(response, node_name)
        )

    def _find_nearest_start_node(self):
        """Ermittelt den nächsten Graphknoten zur lokalisierten Roboterpose."""
        try:
            transform = self.tf_buffer.lookup_transform(
                'map',
                'base_link',
                Time(),
            )
        except TransformException as error:
            self.get_logger().error(
                'Startknoten kann ohne map -> base_link nicht bestimmt werden: '
                f'{error}'
            )
            return None

        robot_x = transform.transform.translation.x
        robot_y = transform.transform.translation.y
        nearest_name, nearest_data = min(
            NODES_DATA.items(),
            key=lambda item: (
                (item[1]['x'] - robot_x) ** 2
                + (item[1]['y'] - robot_y) ** 2
            ),
        )
        distance = (
            (nearest_data['x'] - robot_x) ** 2
            + (nearest_data['y'] - robot_y) ** 2
        ) ** 0.5
        nearest_id = nearest_data['id']
        self.get_logger().info(
            f'Nächster Startknoten: {nearest_name} '
            f'(Graph-ID {nearest_id}, Abstand {distance:.2f} m)'
        )
        return nearest_name, nearest_id

    def _route_goal_response(self, future, node_name: str):
        """Verarbeitet, ob der Route Server die Anfrage angenommen hat."""
        try:
            goal_handle = future.result()
        except Exception as error:
            self.get_logger().error(
                f'Route-Anfrage für {node_name} fehlgeschlagen: {error}'
            )
            return

        if not goal_handle.accepted:
            self.get_logger().error(
                f'Route Server hat das Ziel {node_name} abgelehnt.'
            )
            return

        self.get_logger().info(
            f'Route Server berechnet die Route nach {node_name} ...'
        )
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(
            lambda result: self._route_result(result, node_name)
        )

    def _route_result(self, future, node_name: str):
        """Uebergibt eine erfolgreich berechnete Route an den Controller."""
        try:
            wrapped_result = future.result()
        except Exception as error:
            self.get_logger().error(
                f'Routenberechnung für {node_name} fehlgeschlagen: {error}'
            )
            return

        result = wrapped_result.result
        if (
            wrapped_result.status != GoalStatus.STATUS_SUCCEEDED
            or result.error_code != ComputeRoute.Result.NONE
        ):
            self.get_logger().error(
                f'Keine Route nach {node_name}: '
                f'Status {wrapped_result.status}, Fehlercode {result.error_code}'
            )
            return

        self.get_logger().info(
            f'Route nach {node_name} berechnet: '
            f'{len(result.route.nodes)} Knoten, '
            f'{len(result.path.poses)} Pfadpunkte, '
            f'Kosten {result.route.route_cost:.3f}'
        )

        self._send_follow_path(node_name, result.path)

    def _send_follow_path(self, node_name: str, path):
        """Sendet den berechneten Pfad an den Nav2 Controller Server."""
        if not path.poses:
            self.get_logger().error(
                f'Route nach {node_name} enthaelt keine Pfadpunkte.'
            )
            return

        if not self.follow_path_client.server_is_ready():
            self.get_logger().error(
                'Controller Server /follow_path ist nicht verfuegbar.'
            )
            return

        goal = FollowPath.Goal()
        goal.path = path
        goal.controller_id = 'FollowPath'
        goal.goal_checker_id = 'goal_checker'
        goal.progress_checker_id = 'progress_checker'

        self.get_logger().info(
            f'Sende FollowPath fuer {node_name} an den Controller Server.'
        )
        future = self.follow_path_client.send_goal_async(goal)
        future.add_done_callback(
            lambda response: self._follow_path_goal_response(
                response,
                node_name,
            )
        )

    def _follow_path_goal_response(self, future, node_name: str):
        """Verarbeitet, ob der Controller den Pfad angenommen hat."""
        try:
            goal_handle = future.result()
        except Exception as error:
            self.get_logger().error(
                f'FollowPath-Anfrage fuer {node_name} fehlgeschlagen: {error}'
            )
            return

        if not goal_handle.accepted:
            self.get_logger().error(
                f'Controller Server hat den Pfad nach {node_name} abgelehnt.'
            )
            return

        self.get_logger().info(f'Roboter faehrt nach {node_name} ...')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(
            lambda result: self._follow_path_result(result, node_name)
        )

    def _follow_path_result(self, future, node_name: str):
        """Loggt den Abschluss oder den Fehler der Pfadverfolgung."""
        try:
            wrapped_result = future.result()
        except Exception as error:
            self.get_logger().error(
                f'Fahrt nach {node_name} fehlgeschlagen: {error}'
            )
            return

        result = wrapped_result.result
        if (
            wrapped_result.status != GoalStatus.STATUS_SUCCEEDED
            or result.error_code != FollowPath.Result.NONE
        ):
            self.get_logger().error(
                f'Fahrt nach {node_name} nicht erfolgreich: '
                f'Status {wrapped_result.status}, '
                f'Fehlercode {result.error_code}, '
                f'Meldung: {result.error_msg}'
            )
            return

        self.get_logger().info(f'Ziel {node_name} erreicht.')

    # EDGES VISUALISIERUNG (KANTEN)
    def _publish_graph_edges(self):
        # Zeichnet die Kanten als gelbe Linien in RVIZ.
        marker_array = MarkerArray()

        line_marker = Marker()
        line_marker.header.frame_id = 'map'
        line_marker.header.stamp = self.get_clock().now().to_msg()
        line_marker.ns = 'topology_edges'
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
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
