# import psycopg2
import geopandas as gpd
# import networkx as nx
# import matplotlib.pyplot as plt
# import folium

from shapely.geometry import Point, MultiLineString, Polygon

from database import connect_to_db, get_geodataframe_from_sql, close_connection
from queries import pedestrian_network_query, administrative_regions_query, residential_buildings_query, poi_parks_query
from network import build_network_from_geodataframe, find_nearest_node, shortest_path, compute_accessibility_isochron
from helpers import crs_transform_coords

import os
from dotenv import load_dotenv
import networkx as nx
from tqdm import tqdm # progressbar
from collections import defaultdict

import folium
from folium.plugins import MarkerCluster

# Load environment variables from a .env file
load_dotenv()

# Establish connection with db
db_connection = connect_to_db(os.getenv('DB_CONNECTION_STRING'))

# Get data
SCOPE = 'Lozenec'
gdf_pedestrian_network = get_geodataframe_from_sql(db_connection, pedestrian_network_query(SCOPE))
gdf_adm_regions = get_geodataframe_from_sql(db_connection, administrative_regions_query())
gdf_residential_buildings_lozenec = get_geodataframe_from_sql(db_connection, residential_buildings_query(SCOPE))
gdf_poi_parks = get_geodataframe_from_sql(db_connection, poi_parks_query(SCOPE))

# Close connection with db
close_connection(db_connection)

pedestrian_network = build_network_from_geodataframe(gdf_pedestrian_network, swap_xy = False, save_as = "lib/saves/pedestrian_network.graph")

poi_reach = []
building_service_level = defaultdict(lambda: defaultdict(list)) # building_service_level[building_id][subgroup] = [poi1, poi2, poi3...]

def residential_buildings_serviced_by_poi(network, poi, gdf_residential_buildings, cutoff, weight):
  _boundary_points, boundary_linestring = compute_accessibility_isochron(network, poi, cutoff, weight)
  if boundary_linestring.is_empty or len(list(boundary_linestring.coords)) < 4:
    print(f"Cannot create a surviced area polygon for #{poi}")
    return gpd.GeoDataFrame()
  withing_service_distance = Polygon(boundary_linestring)

  return gdf_residential_buildings[gdf_residential_buildings.geom.apply(lambda x: x.within(withing_service_distance))]


for _i, poi in tqdm(gdf_poi_parks.iterrows(), total=gdf_poi_parks.shape[0], desc="Processing poi"):
  poi_aproximation = find_nearest_node(pedestrian_network, poi.geom)
  serviced_buildings = residential_buildings_serviced_by_poi(
    network = pedestrian_network,
    poi = Point(poi_aproximation), 
    gdf_residential_buildings = gdf_residential_buildings_lozenec,
    cutoff=1000,
    weight='length'
  )

  if serviced_buildings.empty:
    continue

  poi_reach.append({
    'id': poi.id,
    'geom': poi.geom,
    'subgroup': poi.subgroup,
    'buildings_within_reach': serviced_buildings.shape[0],
    'appartments_within_reach': serviced_buildings['appartments'].sum()
  })

  # for _j, building in serviced_buildings.iterrows():
  #   building_service_level[building.id][poi.subgroup].append(poi.id)


gdf_poi_reach = gpd.GeoDataFrame(poi_reach, geometry='geom')
gdf_poi_reach.set_crs(epsg=7801, inplace=True)

center_lon, center_lat = crs_transform_coords(gdf_poi_reach.geometry.x.mean(), gdf_poi_reach.geometry.y.mean())
m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

# Create a MarkerCluster layer
marker_cluster = MarkerCluster().add_to(m)

# Add points to the MarkerCluster layer
for idx, row in gdf_poi_reach.iterrows():
  lon, lat = crs_transform_coords(row["geom"].x, row["geom"].y)
  folium.CircleMarker(location=[lat, lon],
                      radius=5,
                      color='green',
                      fill=True,
                      fill_color='green',
                      fill_opacity=0.6,
                      popup=f"<b>{row['subgroup']}</b><br>Buildings within reach: {row['buildings_within_reach']}<br>Appartments within reach: {row['appartments_within_reach']}").add_to(marker_cluster)

# Display the map
m.save('lib/saves/poi_parks_reach.html')
m