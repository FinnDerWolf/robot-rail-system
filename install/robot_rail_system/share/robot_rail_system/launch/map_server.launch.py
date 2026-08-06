from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():
    package_share = get_package_share_directory("robot_rail_system")

    map_yaml = os.path.join(
        package_share,
        "maps",
        "my_map.yaml"
    )

    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[{
            "yaml_filename": map_yaml
        }]
    )

    return LaunchDescription([
        map_server
    ])
