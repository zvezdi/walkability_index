from shapely.geometry import MultiPoint

from helpers import crs_transform_coords, crs_transform_multipolygon, crs_transform_polygon
from database import db_engine, gdf_from_sql
from queries import residential_buildings_with_service_level_query, poi_reach_query, buffered_region_boundary

import folium
from folium.plugins import MarkerCluster
from helpers import crs_transform_coords, crs_transform_polygon
from shapely import wkt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.colors

import os
from dotenv import load_dotenv

def create_colormap(colors):
  colormap = LinearSegmentedColormap.from_list('custom_gradient', colors, N=100)
  
  return colormap

def color_for(value, colormap):
  # Normalize the value to be between 0 and 1
  normalized_value = value / 100.0
  # Get the RGBA color from the colormap
  rgba_color = colormap(normalized_value)
  # Convert RGBA to a hex color
  hex_color = matplotlib.colors.rgb2hex(rgba_color)

  return hex_color

def create_legend(colors):
  colors_string = ', '.join(colors)  
  legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 20px; 
                background: linear-gradient(to right, {colors_string});
                z-index:9999; font-size:14px;"
          onmousemove="showValue(event)" onmouseout="hideValue()">
    </div>
    <div style="position: fixed; 
                bottom: 30px; left: 50px; width: 200px; height: 20px; 
                background: white; color: black; text-align: center; z-index:9999; font-size:14px;">
                Walkability index
    </div>
    <div id="hoverValue" style="position: fixed; 
                bottom: 70px; left: 50px; width: 50px; height: 20px; 
                background: rgba(255, 255, 255, 0.8); color: black; text-align: center; z-index:9999; font-size:14px; display: none;">
    </div>
    <script>
        function showValue(event) {{
            var element = document.querySelector('[onmousemove]');
            var rect = element.getBoundingClientRect();
            var offsetX = event.clientX - rect.left;
            var value = Math.round((offsetX / rect.width) * 100);
            var hoverValue = document.getElementById('hoverValue');
            hoverValue.style.left = (event.clientX + 10) + 'px';
            hoverValue.style.display = 'block';
            hoverValue.innerHTML = value;
        }}
        function hideValue() {{
            var hoverValue = document.getElementById('hoverValue');
            hoverValue.style.display = 'none';
        }}
    </script>
  '''

  return legend_html

def popup(content_dict):
  html = """
  <div style="border-radius: 5px; background-color: white;">
  """

  for key, value in content_dict.items():
      html += f"""
      <div style="padding: 5px 0; display: flex; flex-wrap: nowrap; justify-content: space-between; gap: 2rem;">
        <span style="font-weight: bold; text-wrap: nowrap;">{key}:</span> <span style="text-wrap: nowrap">{value}</span>
      </div>
      """

  html += "</div>"

  return html

def residentials_service_level_layer(gdf_residentials_service_levels, color_map, color_metric=None, show=True):
  residentials_cluster = MarkerCluster(name = f"Residential buildings {color_metric}", show=show)
  for idx, row in gdf_residentials_service_levels.iterrows():
    lon, lat = crs_transform_coords(row["geom"].x, row["geom"].y)
    marker = folium.CircleMarker(
      location = [lat, lon],
      radius = 5,
      color = color_for(round(row[color_metric]), color_map),
      fill = True,
      fill_color = color_for(round(row[color_metric]), color_map),
      fill_opacity = 1,
      popup = popup({
        "Service level Systematic": round(row['service_index'], 2),
        "Service level PCA": round(row['service_index_pca'], 2),
        "Floors": row['floorcount'],
        "Apps": row['appcount'],
      })
    )
    marker.add_to(residentials_cluster)

  return residentials_cluster

def ge_service_level_layer(gdf_ge_service_levels, color_map, color_metric=None, show=True):
  ge_layer = folium.FeatureGroup(name=f"GE {color_metric}", show=show)
  for _idx, ge in gdf_ge_service_levels.iterrows():
    ge_4326 = crs_transform_multipolygon(ge.geom)
    for polygon in list(ge_4326.geoms):
      folium.Polygon(
        locations = [(lat, lon) for lon, lat in polygon.exterior.coords], 
        color = color_for(round(ge[color_metric]), color_map),
        fill = True,
        fill_color = color_for(round(ge[color_metric]), color_map),
        fill_opacity = 0.5,
        popup = popup({
          "Region": ge.regname,
          "Municipality": ge.rajon,
          "Index Systematic": round(ge.service_index, 2),
          "Weighted Index Systematic": round(ge.weighted_service_index, 2),
          "Index PCA": round(ge.service_index_pca, 2),
          "Weighted Index PCA": round(ge.weighted_service_index_pca, 2),
          "Buildings": round(ge.buildings_count),
          "Apps": round(ge.appcount),
        })
      ).add_to(ge_layer)

  return ge_layer

def adm_regions_service_level_layer(gdf_adm_regions_service_levels, color_map, color_metric=None, show=True):
  adm_regions_layer = folium.FeatureGroup(name=f"Administrative Regions {color_metric}", show=show)
  for _idx, region in gdf_adm_regions_service_levels.iterrows():
    region_4326 = crs_transform_multipolygon(region.geom)
    for polygon in list(region_4326.geoms):
      folium.Polygon(
        locations = [(lat, lon) for lon, lat in polygon.exterior.coords], 
        color = color_for(round(region[color_metric]), color_map),
        fill = True,
        fill_color = color_for(round(region[color_metric]), color_map),
        fill_opacity = 0.5,
        popup = popup({
          "Municipality": region.obns_lat,
          "Index Systematic": round(region.service_index, 2),
          "Weighted Index Systematic": round(region.weighted_service_index, 2),
          "Index PCA": round(region.service_index_pca, 2),
          "Weighted Index PCA": round(region.weighted_service_index_pca, 2),
          "Buildings": round(region.buildings_count),
          "Apps": round(region.appcount),
        })
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
      popup=popup({
        "Subgroup": row['subgroup'],
        "Buildings within reach": row['buildings_within_reach'],
        "Appartments within reach": row['appartments_within_reach'],
      })
    )
    marker.add_to(poi_cluster)

    if draw_isochron:
      polygon_geometry = wkt.loads(row['service_distance_polygon'])
      polygon_geometry = crs_transform_polygon(polygon_geometry)

      folium.GeoJson(
        polygon_geometry.__geo_interface__,
        style_function = lambda x: {'fillColor': '#7fb045', 'fillOpacity': 0.1, 'weight': 2, 'color': '#719c3e'},
        popup = popup({
          "Subgroup": row['subgroup'],
          "Coordinates": f"Point({point.x}, {point.y})"
        }),
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

# Add legend
colors = ['maroon', 'chocolate', 'orange', 'gold', 'yellowgreen', 'forestgreen', 'darkgreen']
color_map = create_colormap(colors)
legend = create_legend(colors)
map.get_root().html.add_child(folium.Element(legend))

# Layers
residentials_layer = residentials_service_level_layer(gdf_residential_buildings_service_levels_lozenec, color_map, color_metric="service_index", show=True)
residentials_layer_pca = residentials_service_level_layer(gdf_residential_buildings_service_levels_lozenec, color_map, color_metric="service_index_pca", show=False)
residentials_layer.add_to(map)
residentials_layer_pca.add_to(map)

ge_layer = ge_service_level_layer(gdf_ge_service_level, color_map, color_metric="weighted_service_index", show=False)
ge_layer_pca = ge_service_level_layer(gdf_ge_service_level, color_map, color_metric="weighted_service_index_pca", show=False)
ge_layer.add_to(map)
ge_layer_pca.add_to(map)

adm_regions_layer = adm_regions_service_level_layer(gdf_adm_regions_service_levels, color_map, color_metric="weighted_service_index", show=True)
adm_regions_layer_pca = adm_regions_service_level_layer(gdf_adm_regions_service_levels, color_map, color_metric="weighted_service_index_pca", show=False)
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
  poi_layer = poi_reach_layer(poi_type, gdf_poi_reach, draw_isochron=False)
  poi_layer.add_to(map)

# Add Layer Control to the map
folium.LayerControl().add_to(map)

# Extract the map's unique ID to reference it in JavaScript
map_id = map.get_name()

# JavaScript code to manage clustering based on zoom level
change_data_on_zoom = f"""
<script>
    document.addEventListener('DOMContentLoaded', function() {{
        var map = {map_id};
        var clusterGroup = map._layers[Object.keys(map._layers).find(key => map._layers[key].hasOwnProperty('_markerCluster'))];
        map.on('zoomend', function () {{
            var zoomLevel = map.getZoom();
            if (zoomLevel >= 13) {{
                var markers = clusterGroup.getLayers();
                clusterGroup.clearLayers();
                markers.forEach(function(marker) {{
                    marker.addTo(map);
                }});
            }} else {{
                console.log(zoomLevel);
                var markers = [];
                map.eachLayer(function(layer) {{
                    if (layer instanceof L.Marker && !(layer instanceof L.MarkerCluster)) {{
                        markers.push(layer);
                    }}
                }});
                markers.forEach(function(marker) {{
                    map.removeLayer(marker);
                    clusterGroup.addLayer(marker);
                }});
                console.log(layer);
                clusterGroup.addTo(map);
            }}
        }});
    }});
</script>
"""

toggle_layers_js_code = f"""
<script>
    document.addEventListener('DOMContentLoaded', function() {{
        var map = {map_id};
        var geLayerName = 'GE weighted_service_index';
        var admRegionsLayerName = 'Administrative Regions weighted_service_index';

        map.on('zoomend', function () {{
            var zoomLevel = map.getZoom();
            console.log(zoomLevel)
            map.eachLayer(function(layer) {{
                console.log(layer)
                console.log(layer.name)
                if (layer.options.name === geLayerName) {{
                    if (zoomLevel <= 13) {{
                        map.addLayer(layer);
                    }} else {{
                        map.removeLayer(layer);
                    }}
                }}
                if (layer.options.name === admRegionsLayerName) {{
                    if (zoomLevel <= 13) {{
                        map.removeLayer(layer);
                    }} else {{
                        map.addLayer(layer);
                    }}
                }}
            }});
        }});
    }});
</script>
"""


# Add the JavaScript to the map
map.get_root().html.add_child(folium.Element(change_data_on_zoom))
map.get_root().html.add_child(folium.Element(toggle_layers_js_code))


# Display the map
map.save('lib/saves/map_lozenec_service_level.html')
map
