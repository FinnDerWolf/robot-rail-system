Nachdem roboter mit lidar gestartet ist und die domain id gleich gesetzt ist, müssen folgende befehle ausgeführt werden um fehlende transforms auszugleichen und die map in rviz zu simulieren

python3 odom_to_tf.py

ros2 run tf2_ros static_transform_publisher 0 0 0.2 0 0 0 base_link laser

ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 base_footprint base_link

ros2 launch slam_toolbox online_async_launch.py slam_params_file:=$[PATH TO mapper_params_online_async.yaml in this folder]

ros2 launch nav2_bringup bringup_launch.py slam:=True use_sim_time:=false


