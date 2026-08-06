import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('robot_rail_system')

    # 1. Launch-Argumente
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Setze auf true fuer Simulation, false fuer echten Roboter'
    )

    nodes_file_arg = DeclareLaunchArgument(
        'nodes_file',
        default_value=os.path.join(pkg_share, 'config', 'nodes.geojson'),
        description='Pfad zur nodes.geojson'
    )

    edges_file_arg = DeclareLaunchArgument(
        'edges_file',
        default_value=os.path.join(pkg_share, 'config', 'edges.geojson'),
        description='Pfad zur edges.geojson'
    )

    # 2. Topology Click Node definieren
    click_node = Node(
        package='robot_rail_system',
        executable='topology_click_node.py',
        name='topology_click_node',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'nodes_file': LaunchConfiguration('nodes_file'),
            'edges_file': LaunchConfiguration('edges_file')
        }]
    )

    return LaunchDescription([
        use_sim_time_arg,
        nodes_file_arg,
        edges_file_arg,
        click_node
    ])