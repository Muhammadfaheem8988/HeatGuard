import json
from pathlib import Path

with open('cache/heatmap_Phoenix_AZ_2024-07-15_result.json') as f:
    hm = json.load(f)

tiles = hm['data']['result']['map_data']['features']
print("Heatmap tiles:", len(tiles))
print("Tile props:", tiles[0]['properties'])
print("Tile geom type:", tiles[0]['geometry']['type'])
print("First coord:", tiles[0]['geometry']['coordinates'][0][0])

with open('data/vulnerability_scored.json') as f:
    vuln = json.load(f)
print("\nVuln tracts:", len(vuln))
print("Sample:", json.dumps(vuln[0], indent=2)[:300])

with open('data/maricopa_tracts.geojson') as f:
    tracts = json.load(f)
print("\nTIGER tracts:", len(tracts['features']))
print("Sample props:", tracts['features'][0]['properties'])
print("Geom type:", tracts['features'][0]['geometry']['type'])