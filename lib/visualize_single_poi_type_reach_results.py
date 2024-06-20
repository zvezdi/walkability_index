import geopandas as gpd
from shapely.geometry import Point, MultiLineString, Polygon
from database import db_engine, gdf_from_sql
from helpers import crs_transform_coords, crs_transform_polygon
from shapely import wkt

import os
from dotenv import load_dotenv

import folium
from folium.plugins import MarkerCluster

# Load environment variables from a .env file
load_dotenv()

database = db_engine(os.getenv('DB_CONNECTION_STRING'))
with database.connect() as connection:
  gdf_poi_reach = gdf_from_sql(connection, "select * from zvezdi_work.results_poi_parks_reach")

center_lon, center_lat = crs_transform_coords(gdf_poi_reach.geometry.x.mean(), gdf_poi_reach.geometry.y.mean())
m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

# Create a MarkerCluster layer
parks_marker_cluster = MarkerCluster(name = "Parks").add_to(m)

# Add points to the Parks layer
for idx, row in gdf_poi_reach.iterrows():
  lon, lat = crs_transform_coords(row["geom"].x, row["geom"].y)
  marker = folium.CircleMarker(
    location=[lat, lon],
    radius=10,
    color='#426e0e',
    fill=True,
    fill_color='#426e0e',
    fill_opacity=1,
    popup=f"<b>{row['subgroup']}</b><br>Buildings within reach: {row['buildings_within_reach']}<br>Appartments within reach: {row['appartments_within_reach']}"
  )
  marker.add_to(parks_marker_cluster)

  polygon_geometry = wkt.loads(row['service_distance_polygon'])
  polygon_geometry = crs_transform_polygon(polygon_geometry)

  folium.GeoJson(
    polygon_geometry.__geo_interface__,
    style_function = lambda x: {'fillColor': '#7fb045', 'fillOpacity': 0.1, 'weight': 2, 'color': '#719c3e'},
    popup = f"<b>{row['subgroup']} Polygon</b>",
    name = f"{row['subgroup']} Polygon",
    show = True
  ).add_to(m)

# Display the map
m.save('lib/saves/poi_parks_reach_with_polygons.html')
m
