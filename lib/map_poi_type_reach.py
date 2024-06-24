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

def merge_gdf(absolute, isochron):
  merged_gdf = absolute.merge(isochron, on='geom', suffixes=('_absolute', '_isochron'))

  # Compute the 'different' column
  merged_gdf['different'] = (
      (merged_gdf['buildings_within_reach_absolute'] != merged_gdf['buildings_within_reach_isochron']) | 
      (merged_gdf['appartments_within_reach_absolute'] != merged_gdf['appartments_within_reach_isochron'])
  )

  # Select the desired columns
  result_gdf = merged_gdf[['geom', 
                          'buildings_within_reach_absolute', 
                          'appartments_within_reach_absolute', 
                          'buildings_within_reach_isochron', 
                          'appartments_within_reach_isochron',
                          'service_distance_polygon',
                          'subgroup_isochron',
                          'different']]

  return result_gdf
  
def draw_accessability(database, poi_type, color):
  with database.connect() as connection:
    gdf_poi_reach_isochron = gdf_from_sql(connection, f"select * from zvezdi_work.results_{poi_type}_reach_isochron")
    gdf_poi_reach_absolute = gdf_from_sql(connection, f"select * from zvezdi_work.results_{poi_type}_reach_absolute")

  merged = merge_gdf(gdf_poi_reach_absolute, gdf_poi_reach_isochron)

  # Create layers
  pois_marker_cluster = folium.FeatureGroup(name = f"{poi_type}")
  polygons_layer = folium.FeatureGroup(name=f"{poi_type} isochron reach", show=False)

  # Add points from isochron
  for idx, row in merged.iterrows():
    lon, lat = crs_transform_coords(row["geom"].x, row["geom"].y)
    marker = folium.CircleMarker(
      location=[lat, lon],
      radius=5,
      color= 'red' if row['different'] else color,
      fill=True,
      fill_color='red' if row['different'] else color,
      fill_opacity=1,
      popup=f"""<b>{row['subgroup_isochron']}</b><br>
      Buildings isochron: {row['buildings_within_reach_isochron']}<br>
      Buildings absolute: {row['buildings_within_reach_absolute']}<br>
      Appartments isochron: {row['appartments_within_reach_isochron']}<br>
      Appartments absolute: {row['appartments_within_reach_absolute']}<br>
      """
    )
    marker.add_to(pois_marker_cluster)

    # Add polygons as reach
    polygon_geometry = wkt.loads(row['service_distance_polygon'])
    polygon_geometry = crs_transform_polygon(polygon_geometry)

    folium.GeoJson(
      polygon_geometry.__geo_interface__,
      style_function = lambda x: {'fillColor': color, 'fillOpacity': 0.1, 'weight': 2, 'color': color},
      name = f"{row['subgroup_isochron']}",
      show = True
    ).add_to(polygons_layer)

  return [pois_marker_cluster, polygons_layer]

# Coordinates for the center of Sofia
sofia_coords = [42.6977, 23.3219]

# Create a map centered on Sofia
m = folium.Map(location=sofia_coords, zoom_start=13)

layers_mobility = draw_accessability(database, 'poi_mobility', 'blue')
layers_parks = draw_accessability(database, 'poi_parks', 'green')

for layer in layers_mobility + layers_parks:
  layer.add_to(m)

# Add Layer Control to the map
folium.LayerControl().add_to(m)

m.save('lib/saves/poi_type_reach_with_polygons.html')
m
