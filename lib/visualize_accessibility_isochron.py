  # import psycopg2
# import geopandas as gpd
# import networkx as nx
# import matplotlib.pyplot as plt
# import folium

from shapely.geometry import Point, MultiPoint, LineString, MultiLineString, Polygon

from helpers import crs_transform_point, crs_transform_coords, crs_transform_linestring
from database import connect_to_db, get_geodataframe_from_sql, close_connection
from queries import pedestrian_network_query, administrative_regions_query, residential_buildings_query, poi_parks_query, buffered_region_boundary
from network import build_network_from_geodataframe, find_nearest_node, compute_accessibility_isochron
import os
from dotenv import load_dotenv
import networkx as nx
from tqdm import tqdm # progressbar

import folium

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

gdf_buffer_region = get_geodataframe_from_sql(db_connection, buffered_region_boundary(SCOPE))

# Close connection with db
close_connection(db_connection)

pedestrian_network = build_network_from_geodataframe(gdf_pedestrian_network, swap_xy = False, save_as = "lib/saves/pedestrian_network.graph")
results = {}

poi = gdf_poi_parks.sample().iloc[0]
poi_aproximation = Point(find_nearest_node(pedestrian_network, poi.geom))

boundary_points, boundary_linestring = compute_accessibility_isochron(pedestrian_network, poi_aproximation, cutoff=1000, weight='length')
withing_service_distance = Polygon(boundary_linestring)

gdf_survised_buildings = gdf_residential_buildings_lozenec[gdf_residential_buildings_lozenec.geom.apply(lambda x: x.within(withing_service_distance))]
print("all buildings", gdf_residential_buildings_lozenec.shape[0])
print("surviced buildings", gdf_survised_buildings.shape[0])

##### Visuals ########

# Create a map centered around the source point
poi_view = crs_transform_point(poi.geom)
poi_aproximation_view = crs_transform_point(poi_aproximation)
m = folium.Map(location=[poi_aproximation_view.y, poi_aproximation_view.x], zoom_start=15)

# Add the source point marker
folium.Marker([poi_view.y, poi_view.x], popup=f"original {poi}", icon=folium.Icon(color='green')).add_to(m)
folium.Marker([poi_aproximation_view.y, poi_aproximation_view.x], popup=f"approximation {poi_aproximation}", icon=folium.Icon(color='red')).add_to(m)

# Add Region Boundary
def style_buffer_region(feature):
  return {
      'fillColor': 'green',
      'color': 'green',
      'weight': 2,
      'fillOpacity': 0.1
  }

folium.GeoJson(gdf_buffer_region.geom, style_function=style_buffer_region).add_to(m)

# Add boundary points markers
for coordinates in boundary_points:
  point = crs_transform_coords(coordinates[0], coordinates[1], toPoint = True, swap_coords = True)
  folium.Circle([point.x, point.y],
    radius=3,  # Radius in meters
    color='purple',  # Circle outline color
    fill=True,  # Enable fill
    fill_color='purple',  # Fill color
    fill_opacity=0.4,
    popup='Boundary Point', 
  ).add_to(m)

# Add the boundary linestring
if boundary_linestring:
  folium.PolyLine(
    locations=crs_transform_linestring(boundary_linestring, swap_coords = True).coords,
    color='blue',
    weight=5,
    opacity=0.8,
  ).add_to(m)

# Add all buildings
for idx, residential in gdf_residential_buildings_lozenec.iterrows():
  point = crs_transform_point(residential.geom, swap_coords = True)
  folium.Circle([point.x, point.y],
    radius=3,
    color='orange',
    fill=True,
    fill_color='orange',
    fill_opacity=0.4,
    popup='Residential', 
  ).add_to(m)

# Add surviced buidlings
for idx, residential in gdf_survised_buildings.iterrows():
  point = crs_transform_point(residential.geom, swap_coords = True)
  folium.Circle([point.x, point.y],
    radius=3,
    color='green',
    fill=True,
    fill_color='green',
    fill_opacity=0.4,
    popup='Residential', 
  ).add_to(m)


# Display the map
m.save('lib/saves/accessibility_isochron.html')
m