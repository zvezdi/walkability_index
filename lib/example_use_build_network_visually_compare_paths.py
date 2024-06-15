from shapely.geometry import Point, MultiLineString

from helpers import point_xy_to_4326_lat_long, xy_to_4326_lat_long
from database import connect_to_db, get_geodataframe_from_sql, close_connection
from queries import pedestrian_network_query, administrative_regions_query, residential_buildings_query, poi_parks_query
from network import build_network_from_geodataframe, visualize_network, find_nearest_node, visualize_nearest_node, shortest_path, visualize_path

import os
from dotenv import load_dotenv

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
