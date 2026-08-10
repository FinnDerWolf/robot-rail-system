import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, LifecycleNode


def generate_launch_description():
    package_share = get_package_share_directory('robot_rail_system')

    params_file = LaunchConfiguration('params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')

    controller_server = LifecycleNode(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        emulate_tty=True,
        parameters=[
            params_file,
            {'use_sim_time': use_sim_time},
        ],
    )

    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_controller',
        output='screen',
        emulate_tty=True,
        parameters=[{
            'autostart': True,
            'node_names': ['controller_server'],
            'use_sim_time': use_sim_time,
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=os.path.join(
                package_share,
                'config',
                'controller_server_params.yaml',
            ),
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
        ),
        controller_server,
        lifecycle_manager,
    ])