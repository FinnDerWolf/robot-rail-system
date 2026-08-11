import json
import yaml

# Load YAML file containing GeoJSON-like structure
with open("nodes.yaml", "r") as f:
  data = yaml.safe_load(f)

# Dump to a GeoJSON file
with open("nodes.geojson", "w") as f:
  json.dump(data, f, indent=2)
