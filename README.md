# robot-rail-system

## Nodes
- NAV2 Route Server
    1. Give GeoJson
    2. serve interface to go from point a to point b along the edges
- NAV2 Map Server
    1. Give map
    2. publish it (available to Route server)
- Rviz Setup
    1. Show map
    2. Show nodes and edges
    3. show robot modell (would be a huge upgrade)
    4. show interactivly which path is beeing taken when driving (upgrade)
- Station click node (DONE)
    1. Node is clicked in rviz
    2. What was clicked? Is it a station?
    3. if its a station, invoke the right command at the route server
- yaml to geoJson
- launch file (for robot)
    1. transform publishers
    2. 
