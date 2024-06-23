from shapely.geometry import Point, MultiLineString

from helpers import crs_transform_point, xy_to_4326_lat_long
from database import db_engine, gdf_from_sql
from queries import pedestrian_network_query, administrative_regions_query, residential_buildings_query, poi_parks_query
from network import build_network_from_geodataframe, visualize_network, find_nearest_node, visualize_nearest_node, shortest_path, visualize_path

import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()


# Get data
database = db_engine(os.getenv('DB_CONNECTION_STRING'))
SCOPE = 'Lozenec'
with database.connect() as db_connection:
  gdf_pedestrian_network = gdf_from_sql(db_connection, pedestrian_network_query(SCOPE))
  gdf_adm_regions = gdf_from_sql(db_connection, administrative_regions_query())
  gdf_residential_buildings_lozenec = gdf_from_sql(db_connection, residential_buildings_query(SCOPE))
  gdf_poi_parks = gdf_from_sql(db_connection, poi_parks_query(SCOPE))

pedestrian_network = build_network_from_geodataframe(gdf_pedestrian_network, save_as = "lib/saves/pedestrian_network.graph")

residential = Point(320214.1127607809, 4724927.958534905)
poi = Point(322992.9803363154, 4725712.959335221)

visualize_nearest_node(pedestrian_network, poi, residential, save_as = "lib/saves/no_path.png")
