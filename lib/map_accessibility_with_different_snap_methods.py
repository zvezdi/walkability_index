import geopandas as gpd
from shapely.geometry import MultiPoint, MultiPolygon

from helpers import crs_transform_point, crs_transform
from database import db_engine, gdf_from_sql
from queries import pedestrian_network_query, administrative_regions_query, residential_buildings_query, poi_query, buffered_region_boundary
from network import build_network_from_geodataframe, find_nearest_node, compute_accessibility_isochron,snap_point_to_edge, node_to_point, compute_accessibility_boundary_points, filter_nodes_within_accessibility_isochron
import os
from dotenv import load_dotenv

import folium

def filter_points_within_isochron(geo_data_frame, alpha_shape):
  if isinstance(alpha_shape, MultiPolygon):
    filtered_gdf = geo_data_frame[geo_data_frame.geometry.apply(lambda x: any(x.within(polygon) for polygon in alpha_shape.geoms))]
  else:
    filtered_gdf = geo_data_frame[geo_data_frame.geometry.apply(lambda x: x.within(alpha_shape))]
  return filtered_gdf

def draw_accessibility(layer, pedestrian_network, gdf_residential_buildings, node_id, color):
  point = node_to_point(pedestrian_network, node_id)

  boundary_points, boundary_linestring = compute_accessibility_boundary_points(pedestrian_network, node_id, weight_type='length', max_weight=1000)
  isochron = compute_accessibility_isochron(pedestrian_network, node_id, weight_type='length', max_weight=1000)
  # filtered_nodes_snap_to_node = filter_nodes_within_accessibility_isochron(pedestrian_network, isochron)
  gdf_survised_buildings = filter_points_within_isochron(gdf_residential_buildings, isochron)

  point_view = crs_transform_point(point, swap_coords=True)

  folium.Marker([point_view.x, point_view.y], popup=f"approximation {point}", icon=folium.Icon(color=color)).add_to(layer)

  ## Add boundary points markers node approximation
  for node in boundary_points:
    point = crs_transform_point(node_to_point(pedestrian_network, node), swap_coords = True)
    folium.Circle([point.x, point.y],
      radius=3,  # Radius in meters
      color='purple',  # Circle outline color
      fill=True,  # Enable fill
      fill_color='purple',  # Fill color
      fill_opacity=0.4,
      popup='Boundary Point', 
    ).add_to(layer)

  ## Add isochron
  view_isochron = crs_transform(isochron, swap_coords=False)
  # Add Region Boundary
  def style_buffer_region(feature):
    return {
      'fillColor': color,
      'color': color,
      'weight': 2,
      'fillOpacity': 0.1,
    }

  # Create a GeoDataFrame with the Polygon and dynamic value
  view_isochron_with_meta = gpd.GeoDataFrame({
    'geometry': [view_isochron],
    'serviced_buildings': [gdf_survised_buildings.shape[0]]})

  # Convert GeoDataFrame to GeoJSON format
  geojson_data = view_isochron_with_meta.to_json()

  folium.GeoJson(
    geojson_data,
    style_function=style_buffer_region,
    popup=folium.GeoJsonPopup(fields=['serviced_buildings'])
  ).add_to(layer)

  ## Add surviced buidlings node approximation
  for idx, residential in gdf_survised_buildings.iterrows():
    point = crs_transform_point(residential.geom, swap_coords = True)
    folium.Circle([point.x, point.y],
      radius=3,
      color='green',
      fill=True,
      fill_color='green',
      fill_opacity=0.4,
      popup='Residential', 
    ).add_to(layer)

  return layer

# Load environment variables from a .env file
load_dotenv()

# Get data
database = db_engine(os.getenv('DB_CONNECTION_STRING'))
SCOPE = 'Lozenec'
with database.connect() as db_connection:
  gdf_pedestrian_network = gdf_from_sql(db_connection, pedestrian_network_query(SCOPE))
  gdf_adm_regions = gdf_from_sql(db_connection, administrative_regions_query())
  gdf_residential_buildings_lozenec = gdf_from_sql(db_connection, residential_buildings_query(SCOPE))
  gdf_pois = gdf_from_sql(db_connection, poi_query('poi_schools', SCOPE))

  gdf_buffer_region = gdf_from_sql(db_connection, buffered_region_boundary(SCOPE))

pedestrian_network = build_network_from_geodataframe(gdf_pedestrian_network, save_as = "lib/saves/pedestrian_network.graph")
results = {}

poi = gdf_pois.sample().iloc[0]
poi_geometry = poi.geom.geoms[0] if isinstance(poi.geom, MultiPoint) else poi.geom

##### Visuals ########

# Create a map centered around the source point
poi_view = crs_transform_point(poi_geometry, swap_coords=True)
m = folium.Map(location=[poi_view.x, poi_view.y], zoom_start=15)

# Add Region Boundary
def style_buffer_region(feature):
  return {
      'fillColor': 'green',
      'color': 'green',
      'weight': 2,
      'fillOpacity': 0.1
  }

folium.GeoJson(gdf_buffer_region.geom, style_function=style_buffer_region).add_to(m, name = "Buffer Lozenec")

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

# Add the source point marker
folium.Marker([poi_view.x, poi_view.y], popup=f"original {poi}", icon=folium.Icon(color='green')).add_to(m)

# Add layer for node approximation
node_approx_layer = folium.FeatureGroup(name="Node Approximation").add_to(m)
# snap to node
poi_snaped_to_node_node_id = find_nearest_node(pedestrian_network, poi_geometry)
draw_accessibility(
  node_approx_layer, 
  pedestrian_network,
  gdf_residential_buildings_lozenec, 
  poi_snaped_to_node_node_id,
  color = "red"
)

# Add layer for edge approximation
edge_approx_layer = folium.FeatureGroup(name="Edge Approximation").add_to(m)
# snap to edge
poi_snaped_to_edge_node_id = snap_point_to_edge(pedestrian_network, poi_geometry)

draw_accessibility(
  edge_approx_layer,
  pedestrian_network,
  gdf_residential_buildings_lozenec,
  poi_snaped_to_edge_node_id,
  color = "blue"
)

# Add Layer Control to the map
folium.LayerControl().add_to(m)

# Display the map
m.save('lib/saves/compare_accessibility_with_different_snap_methods.html')
m