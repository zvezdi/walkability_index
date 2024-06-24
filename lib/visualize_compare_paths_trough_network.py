from shapely.geometry import Point


from database import db_engine, gdf_from_sql
from queries import pedestrian_network_query, administrative_regions_query, residential_buildings_query, poi_query
from network import build_network_from_geodataframe, find_nearest_node, shortest_path, visualize_path

import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()


# Get data
SCOPE = 'Lozenec'
database = db_engine(os.getenv('DB_CONNECTION_STRING'))
with database.connect() as db_connection:
  gdf_pedestrian_network = gdf_from_sql(db_connection, pedestrian_network_query(SCOPE))
  gdf_adm_regions = gdf_from_sql(db_connection, administrative_regions_query())
  gdf_residential_buildings_lozenec = gdf_from_sql(db_connection, residential_buildings_query(SCOPE))
  gdf_poi_parks = gdf_from_sql(db_connection, poi_query('poi_parks', SCOPE))

pedestrian_network = build_network_from_geodataframe(gdf_pedestrian_network, save_as = "lib/saves/pedestrian_network.graph")
# visualize_network(pedestrian_network, save_as = "lib/saves/pedestrian_network.png")

sample_residential_building = Point(320543.353, 4725717.825)
print("residential building", sample_residential_building)

sample_poi_park = Point(322166.775, 4728236.865)
print("poi park", sample_poi_park)

closest_node_to_buidling = find_nearest_node(pedestrian_network, sample_residential_building)
closest_node_to_park = find_nearest_node(pedestrian_network, sample_poi_park)

# visualize_nearest_node(pedestrian_network, sample_residential_building, Point(closest_node_to_buidling), save_as = "lib/saves/closest_node.png")
# visualize_nearest_node(pedestrian_network, sample_poi_park, Point(closest_node_to_park), save_as = "lib/saves/closest_node.png")
path_min_time, time_cost = shortest_path(pedestrian_network, sample_residential_building, sample_poi_park, weight='time')
path_min_length, length_cost = shortest_path(pedestrian_network, sample_residential_building, sample_poi_park, weight='length')
# visualize_path(pedestrian_network, sample_residential_building, sample_poi_park, path_time = path_min_time, save_as="lib/saves/visualize_path.png")
print("minutes cost", time_cost)
print("meters cost", length_cost)
visualize_path(pedestrian_network, sample_residential_building, sample_poi_park, path_time = path_min_time, path_length = path_min_length, save_as="lib/saves/compare_paths.png")
