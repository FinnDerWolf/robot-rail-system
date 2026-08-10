Der Pfad zu `graph.geojson` wird von der Launch-Datei automatisch aus dem
installierten Paket ermittelt. Ein anderer Graph kann über das Argument
`graph_file` gesetzt werden.

Route Server starten:

```
ros2 launch robot_rail_system route_server_launch.py
```

Testbefehl für den Route-Server:

```
ros2 action send_goal /compute_route nav2_msgs/action/ComputeRoute "{start_id: 1, goal_id: 10, use_start: true, use_poses: false}" --feedback
```
