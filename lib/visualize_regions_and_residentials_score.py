from shapely.geometry import Point, MultiLineString, MultiPoint

from helpers import crs_transform_coords, crs_transform_multipolygon, crs_transform_polygon
from database import db_engine, gdf_from_sql
from queries import residential_buildings_with_service_level_query, administrative_regions_with_service_level_query, poi_reach_query

import folium
from folium.plugins import MarkerCluster
import itertools
from helpers import crs_transform_coords, crs_transform_polygon
from shapely import wkt

import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Get data
SCOPE = 'Lozenec'
database = db_engine(os.getenv('DB_CONNECTION_STRING'))

with database.connect() as db_connection:
  gdf_adm_regions_service_levels = gdf_from_sql(db_connection, administrative_regions_with_service_level_query())
  gdf_residential_buildings_service_levels_lozenec = gdf_from_sql(db_connection, residential_buildings_with_service_level_query(SCOPE))
  
center_lon, center_lat = crs_transform_coords(gdf_residential_buildings_service_levels_lozenec.geometry.x.mean(), gdf_residential_buildings_service_levels_lozenec.geometry.y.mean())
m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

# Create a Residential Cluster layer
residentials_cluster = MarkerCluster(name = "Residential buildings")
for idx, row in gdf_residential_buildings_service_levels_lozenec.iterrows():
  lon, lat = crs_transform_coords(row["geom"].x, row["geom"].y)
  marker = folium.CircleMarker(
    location = [lat, lon],
    radius = 10,
    color = '#426e0e',
    fill = True,
    fill_color = '#426e0e',
    fill_opacity = 1,
    popup = f"Service level: <b>{row['service_index']}</b><br>Floors: {row['floorcount']}<br>Appartments: {row['appcount']}"
  )
  marker.add_to(residentials_cluster)
residentials_cluster.add_to(m)

color_mapping = {
  0: 'RGB(180, 40, 40)',
  10: 'RGB(180, 40, 40)',
  20: 'RGB(230, 40, 40)',
  30: 'RGB(212, 146, 15)',
  40: 'RGB(230, 178, 76)',
  50: 'RGB(230, 230, 28)',
  60: 'RGB(172, 204, 67)',
  70: 'RGB(147, 179, 43)',
  80: 'RGB(129, 161, 24)',
  90: 'RGB(125, 153, 32)',
  100: 'RGB(93, 117, 12)',
}

# Create a Administrative Regions Layer and add it to the map
def color_for(value, color_mapping):
  for (prev_cutoff, prev_color), (curr_cutoff, curr_color) in itertools.pairwise(sorted(color_mapping.items())):
    if value >= prev_cutoff and value < curr_cutoff:
      return curr_color
  return 'black'

adm_regions_layer = folium.FeatureGroup(name="Administrative Regions systematic")
for _idx, region in gdf_adm_regions_service_levels.iterrows():
  region_4326 = crs_transform_multipolygon(region.geom)
  for polygon in list(region_4326.geoms):
    folium.Polygon(
      locations = [(lat, lon) for lon, lat in polygon.exterior.coords], 
      color = color_for(round(region.weighted_service_index), color_mapping),
      fill = True,
      fill_color = color_for(round(region.weighted_service_index), color_mapping),
      fill_opacity = 0.5,
      popup = f"""{region.obns_lat}<br>
        Index: {round(region.service_index, 2)}<br>
        Weighted Index: {round(region.weighted_service_index, 2)}<br>
        Buildings: {round(region.buildings_count)}<br>
        Appartments: {round(region.appcount)}
      """
    ).add_to(adm_regions_layer)
adm_regions_layer.add_to(m)

adm_regions_layer_pca = folium.FeatureGroup(name="Administrative Regions PCA", show = False)
for _idx, region in gdf_adm_regions_service_levels.iterrows():
  region_4326 = crs_transform_multipolygon(region.geom)
  for polygon in list(region_4326.geoms):
    folium.Polygon(
      locations = [(lat, lon) for lon, lat in polygon.exterior.coords], 
      color = color_for(round(region.weighted_service_index_pca), color_mapping),
      fill = True,
      fill_color = color_for(round(region.weighted_service_index_pca), color_mapping),
      fill_opacity = 0.5,
      popup = f"""{region.obns_lat}<br>
        Index PCA: {round(region.service_index_pca, 2)}<br>
        Weighted Index PCA: {round(region.weighted_service_index_pca, 2)}<br>
        Buildings: {round(region.buildings_count)}<br>
        Appartments: {round(region.appcount)}
      """
    ).add_to(adm_regions_layer_pca)
adm_regions_layer_pca.add_to(m)

# Create legend
legend_html = '''
<div style="position: fixed; 
            bottom: 50px; left: 50px; width: 150px; height: auto; 
            background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
            padding: 10px; line-height:18px;">
 &nbsp; <b>Walkability Index</b> <br>
'''

for (prev_value, prev_color), (curr_value, curr_color) in itertools.pairwise(color_mapping.items()):
    legend_html += f'''
    &nbsp; <i style="background:{curr_color}; width: 12px; height: 12px; float: left; margin-right: 8px; opacity: 1;"></i> {prev_value} - {curr_value} <br>
    '''

legend_html += '</div>'
m.get_root().html.add_child(folium.Element(legend_html))

# Create poi leayers
def poi_reach_layer(poi_type, gdf_poi_reach):
  poi_cluster = MarkerCluster(name = f"{poi_type.replace('_', ' ').capitalize()} Reach", show = False)

  # Add points to the Parks layer
  for idx, row in gdf_poi_reach.iterrows():
    point = row.geom.geoms[0] if isinstance(row.geom, MultiPoint) else row.geom

    lon, lat = crs_transform_coords(point.x, point.y)
    marker = folium.CircleMarker(
      location=[lat, lon],
      radius=10,
      color='#426e0e',
      fill=True,
      fill_color='#426e0e',
      fill_opacity=1,
      popup=f"""
        <b>{row['subgroup']}</b><br>
        Buildings within reach: {row['buildings_within_reach']}<br>
        Appartments within reach: {row['appartments_within_reach']}
      """
    )
    marker.add_to(poi_cluster)

    polygon_geometry = wkt.loads(row['service_distance_polygon'])
    polygon_geometry = crs_transform_polygon(polygon_geometry)

    folium.GeoJson(
      polygon_geometry.__geo_interface__,
      style_function = lambda x: {'fillColor': '#7fb045', 'fillOpacity': 0.1, 'weight': 2, 'color': '#719c3e'},
      popup = f"""<b>{row['subgroup']}</b><br>Point({point.x}, {point.y})""",
      show = True
    ).add_to(poi_cluster)
  
  return poi_cluster

with database.connect() as db_connection:
    pois = {
      'poi_culture': gdf_from_sql(db_connection, poi_reach_query('poi_culture', SCOPE)),
      'poi_health': gdf_from_sql(db_connection, poi_reach_query('poi_health', SCOPE)),
      'poi_kids': gdf_from_sql(db_connection, poi_reach_query('poi_kids', SCOPE)),
      'poi_mobility': gdf_from_sql(db_connection, poi_reach_query('poi_mobility', SCOPE)),
      'poi_others': gdf_from_sql(db_connection, poi_reach_query('poi_others', SCOPE)),
      'poi_parks': gdf_from_sql(db_connection, poi_reach_query('poi_parks', SCOPE)),
      'poi_schools': gdf_from_sql(db_connection, poi_reach_query('poi_schools', SCOPE)),
      'poi_sport': gdf_from_sql(db_connection, poi_reach_query('poi_sport', SCOPE)),
    }

for poi_type, gdf_poi_reach in pois.items():
  poi_layer = poi_reach_layer(poi_type, gdf_poi_reach)
  poi_layer.add_to(m)

# Add Layer Control to the map
folium.LayerControl().add_to(m)

# Display the map
m.save('lib/saves/map_regions_and_residentials_with_service_level.html')
m
