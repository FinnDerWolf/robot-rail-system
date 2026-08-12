import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory('robot_rail_system')

    map_file = LaunchConfiguration('map')
    amcl_params_file = LaunchConfiguration('amcl_params_file')
    controller_params_file = LaunchConfiguration('controller_params_file')
    graph_file = LaunchConfiguration('graph_file')
    publish_base_footprint_to_base_link = LaunchConfiguration(
        'publish_base_footprint_to_base_link'
    )
    publish_base_link_to_laser = LaunchConfiguration(
        'publish_base_link_to_laser'
    )
    publish_odom_tf = LaunchConfiguration('publish_odom_tf')
    route_params_file = LaunchConfiguration('route_params_file')
    rviz_config = LaunchConfiguration('rviz_config')
    use_rviz = LaunchConfiguration('use_rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_map = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(package_share, 'maps', 'my_map.yaml'),
        description='Full path to the map YAML file',
    )
    declare_graph_file = DeclareLaunchArgument(
        'graph_file',
        default_value=os.path.join(package_share, 'config', 'graph.geojson'),
        description='Full path to the Nav2 route graph',
    )
    declare_amcl_params_file = DeclareLaunchArgument(
        'amcl_params_file',
        default_value=os.path.join(
            package_share,
            'config',
            'amcl_params.yaml',
        ),
        description='Full path to the AMCL params file',
    )
    declare_controller_params_file = DeclareLaunchArgument(
        'controller_params_file',
        default_value=os.path.join(
            package_share,
            'config',
            'controller_server_params.yaml',
        ),
        description='Full path to the controller_server params file',
    )
    declare_publish_odom_tf = DeclareLaunchArgument(
        'publish_odom_tf',
        default_value='true',
        description='Publish odom to base TF from the robot /odom topic',
    )
    declare_publish_base_footprint_to_base_link = DeclareLaunchArgument(
        'publish_base_footprint_to_base_link',
        default_value='false',
        description='Publish base_footprint to base_link if the robot does not',
    )
    declare_publish_base_link_to_laser = DeclareLaunchArgument(
        'publish_base_link_to_laser',
        default_value='true',
        description='Connect the SICK laser mount to base_link',
    )
    declare_route_params_file = DeclareLaunchArgument(
        'route_params_file',
        default_value=os.path.join(
            package_share,
            'config',
            'route_server_params.yaml',
        ),
        description='Full path to the route_server params file',
    )
    declare_rviz_config = DeclareLaunchArgument(
        'rviz_config',
        default_value=os.path.join(
            package_share,
            'config',
            'robot_rail_system.rviz',
        ),
        description='Full path to the RViz configuration file',
    )
    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Start RViz together with the system',
    )
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock if true',
    )

    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'yaml_filename': map_file,
        }],
    )

    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[
            amcl_params_file,
            {'use_sim_time': use_sim_time},
        ],
    )

    route_server = Node(
        package='nav2_route',
        executable='route_server',
        name='route_server',
        output='screen',
        parameters=[
            route_params_file,
            {
                'graph_filepath': graph_file,
                'use_sim_time': use_sim_time,
            },
        ],
    )

    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[
            controller_params_file,
            {'use_sim_time': use_sim_time},
        ],
    )

    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_robot_rail_system',
        output='screen',
        parameters=[{
            'autostart': True,
            'node_names': [
                'map_server',
                'amcl',
                'route_server',
                'controller_server',
            ],
            'use_sim_time': use_sim_time,
        }],
    )

    odom_to_tf = Node(
        condition=IfCondition(publish_odom_tf),
        package='robot_rail_system',
        executable='odom_to_tf.py',
        name='odom_to_tf',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    base_footprint_to_base_link = Node(
        condition=IfCondition(publish_base_footprint_to_base_link),
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_footprint_to_base_link',
        output='screen',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0',
            '--roll', '0', '--pitch', '0', '--yaw', '0',
            '--frame-id', 'base_footprint',
            '--child-frame-id', 'base_link',
        ],
    )

    base_link_to_laser_mount = Node(
        condition=IfCondition(publish_base_link_to_laser),
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_link_to_laser_mount',
        output='screen',
        arguments=[
            # The SICK driver already publishes laser_mount_link -> laser with
            # z=0.05595 m. This edge completes the intended total laser height
            # of 0.2 m without assigning a second parent directly to laser.
            '--x', '0', '--y', '0', '--z', '0.14405',
            '--roll', '0', '--pitch', '0', '--yaw', '0',
            '--frame-id', 'base_link',
            '--child-frame-id', 'laser_mount_link',
        ],
    )

    show_nodes = Node(
        package='robot_rail_system',
        executable='show_nodes.py',
        name='show_nodes',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    topology_click_node = Node(
        package='robot_rail_system',
        executable='topology_click_node.py',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    rviz = Node(
        condition=IfCondition(use_rviz),
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    return LaunchDescription([
        declare_map,
        declare_graph_file,
        declare_amcl_params_file,
        declare_controller_params_file,
        declare_publish_odom_tf,
        declare_publish_base_footprint_to_base_link,
        declare_publish_base_link_to_laser,
        declare_route_params_file,
        declare_rviz_config,
        declare_use_rviz,
        declare_use_sim_time,
        map_server,
        amcl,
        route_server,
        controller_server,
        lifecycle_manager,
        odom_to_tf,
        base_footprint_to_base_link,
        base_link_to_laser_mount,
        show_nodes,
        topology_click_node,
        rviz,
    ])
