import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory('robot_rail_system')
    params_file = LaunchConfiguration('params_file')
    graph_file = LaunchConfiguration('graph_file')
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_params_file = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(
            package_share,
            'config',
            'route_server_params.yaml',
        ),
        description='Full path to the route_server params file',
    )

    declare_graph_file = DeclareLaunchArgument(
        'graph_file',
        default_value=os.path.join(
            package_share,
            'config',
            'graph.geojson',
        ),
        description='Full path to the Nav2 route graph',
    )

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock if true',
    )

    lifecycle_nodes = ['route_server']

    route_server_node = Node(
        package='nav2_route',
        executable='route_server',
        name='route_server',
        output='screen',
        parameters=[
            params_file,
            {
                'graph_filepath': graph_file,
                'use_sim_time': use_sim_time,
            },
        ],
    )

    lifecycle_manager_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_route',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'autostart': True},
            {'node_names': lifecycle_nodes},
        ],
    )

    return LaunchDescription([
        declare_params_file,
        declare_graph_file,
        declare_use_sim_time,
        route_server_node,
        lifecycle_manager_node,
    ])
