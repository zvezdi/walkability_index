import geopandas as gpd
from shapely.geometry import Point, Polygon, MultiPoint
from tqdm import tqdm # progressbar

from network import find_nearest_node, compute_accessibility_isochron, snap_point_to_edge

def accessibility_area(network, source_location, weight_type, max_weight):
  return compute_accessibility_isochron(network, source_location, weight_type, max_weight)

def within_accessibility_area(accessibility_polygon, gdf_locations):
  return gdf_locations[gdf_locations.geom.apply(lambda x: x.within(accessibility_polygon))]

def compute_poi_reach(pedestrian_network, gdf_points_of_interest, gdf_residential_buildings, weight_type = 'length', max_weight = 1000, snap_to = 'edge'):
  poi_reach = []
  # Not sure if this should be at thet level. Should strike a balance between coping and keeping the graph small
  pedestrian_network_copy = pedestrian_network.copy()

  for i, poi in tqdm(gdf_points_of_interest.iterrows(), total=gdf_points_of_interest.shape[0], desc="Processing poi"):
    # Make sure to work with point geomerty
    poi_geom = poi.geom.geoms[0] if isinstance(poi.geom, MultiPoint) else poi.geom
    if snap_to == 'edge':
      poi_aprox_node_id = snap_point_to_edge(pedestrian_network_copy, poi_geom)
    elif snap_to == 'node': # snap to node
      poi_aprox_node_id = find_nearest_node(pedestrian_network_copy, poi_geom)
    else:
      raise "snap_to = 'node'|'edge'"

    accessibility_polygon = accessibility_area(pedestrian_network_copy, poi_aprox_node_id, weight_type, max_weight)
    serviced_buildings = within_accessibility_area(accessibility_polygon, gdf_residential_buildings)

    if serviced_buildings.empty:
      # TODO: mark the pois that do not serve any buildings in some way, further look is needed into them
      continue

    poi_reach.append({
      'id': poi.id,
      'geom': poi.geom,
      'subgroup': poi.subgroup,
      'buildings_within_reach': serviced_buildings.shape[0],
      'appartments_within_reach': serviced_buildings['appartments'].sum(),
      'service_distance_polygon': accessibility_polygon,
    })

  gdf_poi_reach = gpd.GeoDataFrame(poi_reach, geometry='geom')
  gdf_poi_reach.set_crs(epsg=7801, inplace=True)

  return gdf_poi_reach

def compute_buildings_reach(pedestrian_network, gdf_residential_buildings, pois, weight_type = 'length', max_weight = 1000, snap_to = 'edge'):
  residentials_reach = []

  for i, residential in tqdm(gdf_residential_buildings.iterrows(), total=gdf_residential_buildings.shape[0], desc="Processing poi"):
    # Make sure to work with point geomerty
    if snap_to == 'edge':
      residential_approx_id = snap_point_to_edge(pedestrian_network, residential.geom)
    elif snap_to == 'node': # snap to node
      residential_approx_id = find_nearest_node(pedestrian_network, residential.geom)
    else:
      raise "snap_to = 'node'|'edge'"

    accessibility_polygon = accessibility_area(pedestrian_network, residential_approx_id, weight_type, max_weight)

    buidling_info = {
      'id': residential.id,
      'geom': residential.geom,
      'floorcount': residential['floors'],
      'appcount': residential['appartments'],
      'accessibility_polygon': accessibility_polygon,
    }

    for gdf_poi_type in pois:
      reachable_pois = within_accessibility_area(accessibility_polygon, gdf_poi_type)
      buidling_info.update(reachable_pois['subgroup'].value_counts().to_dict())

    residentials_reach.append(buidling_info)

  gdf_residentials_reach = gpd.GeoDataFrame(residentials_reach, geometry='geom')
  gdf_residentials_reach.set_crs(epsg=7801, inplace=True)

  return gdf_residentials_reach
