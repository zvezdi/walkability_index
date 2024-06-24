from shapely.geometry import MultiPoint

from helpers import crs_transform_coords, crs_transform_multipolygon, crs_transform_polygon
from database import db_engine, gdf_from_sql
from queries import residential_buildings_with_service_level_query, poi_reach_query, buffered_region_boundary

import folium
from folium.plugins import MarkerCluster
import itertools
from helpers import crs_transform_coords, crs_transform_polygon
from shapely import wkt

import os
from dotenv import load_dotenv

COLOR_MAPPING = {
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

def color_for(value):
  for (prev_cutoff, prev_color), (curr_cutoff, curr_color) in itertools.pairwise(sorted(COLOR_MAPPING.items())):
    if value >= prev_cutoff and value < curr_cutoff:
      return curr_color
  return 'black'

def create_legend(color_mapping):
  # Create legend
  legend_html = '''
  <div style="position: fixed; 
              bottom: 50px; left: 50px; width: 150px; height: auto; 
              background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
              padding: 10px; line-height:18px;">
  &nbsp; <b>Walkability Index</b> <br>
  '''

  for (prev_value, _prev_color), (curr_value, curr_color) in itertools.pairwise(color_mapping.items()):
      legend_html += f'''
      &nbsp; <i style="background:{curr_color}; width: 12px; height: 12px; float: left; margin-right: 8px; opacity: 1;"></i> {prev_value} - {curr_value} <br>
      '''

  legend_html += '</div>'

  return legend_html

def popup(content):
  html = f"""
    <div style="width: 200px; text-align: center;">
      {content}
    </div>
  """
  return html

def residentials_service_level_layer(gdf_residentials_service_levels, color_metric=None, show=True):
  residentials_cluster = MarkerCluster(name = f"Residential buildings {color_metric}", show=show)
  for idx, row in gdf_residentials_service_levels.iterrows():
    lon, lat = crs_transform_coords(row["geom"].x, row["geom"].y)
    marker = folium.CircleMarker(
      location = [lat, lon],
      radius = 5,
      color = color_for(round(row[color_metric])),
      fill = True,
      fill_color = color_for(round(row[color_metric])),
      fill_opacity = 1,
      popup = popup(f"""
        Service level Systematic: <b>{round(row['service_index'], 2)}</b><br>
        Service level PCA: <b>{round(row['service_index_pca'], 2)}</b><br>
        Floors: {row['floorcount']}<br>
        Apps: {row['appcount']}
      """)
    )
    marker.add_to(residentials_cluster)

  return residentials_cluster

def ge_service_level_layer(gdf_ge_service_levels, color_metric=None, show=True):
  ge_layer = folium.FeatureGroup(name=f"GE {color_metric}", show=show)
  for _idx, ge in gdf_ge_service_levels.iterrows():
    ge_4326 = crs_transform_multipolygon(ge.geom)
    for polygon in list(ge_4326.geoms):
      folium.Polygon(
        locations = [(lat, lon) for lon, lat in polygon.exterior.coords], 
        color = color_for(round(ge[color_metric])),
        fill = True,
        fill_color = color_for(round(ge[color_metric])),
        fill_opacity = 0.5,
        popup = popup(f"""{ge.regname}({ge.rajon})<br>
          Index Systematic: {round(ge.service_index, 2)}<br>
          Weighted Index Systematic: {round(ge.weighted_service_index, 2)}<br>
          Index PCA: {round(ge.service_index_pca, 2)}<br>
          Weighted Index PCA: {round(ge.weighted_service_index_pca, 2)}<br>
          Buildings: {round(ge.buildings_count)}<br>
          Apps: {round(ge.appcount)}
        """)
      ).add_to(ge_layer)

  return ge_layer

def adm_regions_service_level_layer(gdf_adm_regions_service_levels, color_metric=None, show=True):
  adm_regions_layer = folium.FeatureGroup(name=f"Administrative Regions {color_metric}", show=show)
  for _idx, region in gdf_adm_regions_service_levels.iterrows():
    region_4326 = crs_transform_multipolygon(region.geom)
    for polygon in list(region_4326.geoms):
      folium.Polygon(
        locations = [(lat, lon) for lon, lat in polygon.exterior.coords], 
        color = color_for(round(region[color_metric])),
        fill = True,
        fill_color = color_for(round(region[color_metric])),
        fill_opacity = 0.5,
        popup = popup(f"""{region.obns_lat}<br>
          Index Systematic: {round(region.service_index, 2)}<br>
          Weighted Index Systematic: {round(region.weighted_service_index, 2)}<br>
          Index PCA: {round(region.service_index_pca, 2)}<br>
          Weighted Index PCA: {round(region.weighted_service_index_pca, 2)}<br>
          Buildings: {round(region.buildings_count)}<br>
          Apps: {round(region.appcount)}
        """)
      ).add_to(adm_regions_layer)

  return adm_regions_layer

def poi_reach_layer(poi_type, gdf_poi_reach, draw_isochron=False):
  poi_cluster = MarkerCluster(name = f"{poi_type.replace('_', ' ').capitalize()} Reach", show = False)

  # Add points to the Parks layer
  for idx, row in gdf_poi_reach.iterrows():
    point = row.geom.geoms[0] if isinstance(row.geom, MultiPoint) else row.geom

    lon, lat = crs_transform_coords(point.x, point.y)
    marker = folium.CircleMarker(
      location=[lat, lon],
      radius=5,
      color='#426e0e',
      fill=True,
      fill_color='#426e0e',
      fill_opacity=1,
      popup=popup(f"""
        <b>{row['subgroup']}</b><br>
        Buildings within reach: {row['buildings_within_reach']}<br>
        Appartments within reach: {row['appartments_within_reach']}
      """)
    )
    marker.add_to(poi_cluster)

    if draw_isochron:
      polygon_geometry = wkt.loads(row['service_distance_polygon'])
      polygon_geometry = crs_transform_polygon(polygon_geometry)

      folium.GeoJson(
        polygon_geometry.__geo_interface__,
        style_function = lambda x: {'fillColor': '#7fb045', 'fillOpacity': 0.1, 'weight': 2, 'color': '#719c3e'},
        popup = popup(f"""<b>{row['subgroup']}</b><br>Point({point.x}, {point.y})"""),
        show = True
      ).add_to(poi_cluster)
  
  return poi_cluster

# Load environment variables from a .env file
load_dotenv()

# Get data
SCOPE = 'Lozenec'
database = db_engine(os.getenv('DB_CONNECTION_STRING'))

with database.connect() as db_connection:
  gdf_adm_regions_service_levels = gdf_from_sql(db_connection, "select * from zvezdi_work.results_gen_adm_regions_service_level_absolute")
  gdf_ge_service_level = gdf_from_sql(db_connection, "select * from zvezdi_work.results_ge_service_level_absolute")
  gdf_residential_buildings_service_levels_lozenec = gdf_from_sql(db_connection, residential_buildings_with_service_level_query(SCOPE, analytics_type='absolute'))
  gdf_buffer_region = gdf_from_sql(db_connection, buffered_region_boundary(SCOPE))
center_lon, center_lat = crs_transform_coords(gdf_residential_buildings_service_levels_lozenec.geometry.x.mean(), gdf_residential_buildings_service_levels_lozenec.geometry.y.mean())
map = folium.Map(location=[center_lat, center_lon], zoom_start=14)

# Layers
residentials_layer = residentials_service_level_layer(gdf_residential_buildings_service_levels_lozenec, color_metric="service_index", show=True)
residentials_layer_pca = residentials_service_level_layer(gdf_residential_buildings_service_levels_lozenec, color_metric="service_index_pca", show=False)
residentials_layer.add_to(map)
residentials_layer_pca.add_to(map)

ge_layer = ge_service_level_layer(gdf_ge_service_level, color_metric="weighted_service_index", show=False)
ge_layer_pca = ge_service_level_layer(gdf_ge_service_level, color_metric="weighted_service_index_pca", show=False)
ge_layer.add_to(map)
ge_layer_pca.add_to(map)

adm_regions_layer = adm_regions_service_level_layer(gdf_adm_regions_service_levels, color_metric="weighted_service_index", show=True)
adm_regions_layer_pca = adm_regions_service_level_layer(gdf_adm_regions_service_levels, color_metric="weighted_service_index_pca", show=False)
adm_regions_layer.add_to(map)
adm_regions_layer_pca.add_to(map)

with database.connect() as db_connection:
    pois = {
      'poi_culture': gdf_from_sql(db_connection, poi_reach_query('poi_culture', SCOPE, analytics_type='absolute')),
      'poi_health': gdf_from_sql(db_connection, poi_reach_query('poi_health', SCOPE, analytics_type='absolute')),
      'poi_kids': gdf_from_sql(db_connection, poi_reach_query('poi_kids', SCOPE, analytics_type='absolute')),
      'poi_mobility': gdf_from_sql(db_connection, poi_reach_query('poi_mobility', SCOPE, analytics_type='absolute')),
      'poi_others': gdf_from_sql(db_connection, poi_reach_query('poi_others', SCOPE, analytics_type='absolute')),
      'poi_parks': gdf_from_sql(db_connection, poi_reach_query('poi_parks', SCOPE, analytics_type='absolute')),
      'poi_schools': gdf_from_sql(db_connection, poi_reach_query('poi_schools', SCOPE, analytics_type='absolute')),
      'poi_sport': gdf_from_sql(db_connection, poi_reach_query('poi_sport', SCOPE, analytics_type='absolute')),
    }

for poi_type, gdf_poi_reach in pois.items():
  poi_layer = poi_reach_layer(poi_type, gdf_poi_reach)
  poi_layer.add_to(map)

# Add Layer Control to the map
folium.LayerControl().add_to(map)
# Add legend
legend = create_legend(COLOR_MAPPING)
map.get_root().html.add_child(folium.Element(legend))

# Display the map
map.save('lib/saves/map_lozenec_service_level.html')
map
