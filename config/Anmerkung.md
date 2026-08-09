In route_server:params.yaml muss der Pfad zu graph.geojson vermutlich angepasst werden

Launch-File mit 
```
ros2 launch robot_rail_system route_server_launch.py
```


Testbefehl für den Route-Server:
```
ros2 action send_goal /compute_route nav2_msgs/action/ComputeRoute "{start_id: 1, goal_id: 10, use_start: true, use_poses: false}" --feedback
``
