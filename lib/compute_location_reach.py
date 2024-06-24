import geopandas as gpd
from shapely.geometry import MultiPoint
from tqdm import tqdm # progressbar

from network import find_nearest_node, compute_accessibility_isochron, snap_point_to_edge, nearby_nodes

def accessibility_area(network, source_location, weight_type, max_weight):
  return compute_accessibility_isochron(network, source_location, weight_type, max_weight)

def within_accessibility_area(accessibility_polygon, gdf_locations):
  return gdf_locations[gdf_locations.geom.apply(lambda x: x.within(accessibility_polygon))]

def compute_poi_absolute_reach(pedestrian_network, gdf_points_of_interest, gdf_residential_buildings, weight_type = 'length', max_weight = 1000):
  poi_reach = []

  for i, poi in tqdm(gdf_points_of_interest.iterrows(), total=gdf_points_of_interest.shape[0], desc="Processing poi"):
    # Make sure to use the precomputed snapped_to_node, as recomputing it might result in a different node as the network has changes since adding it
    poi_node = poi["snapped_to_node"]
    accessible_nodes = nearby_nodes(pedestrian_network, poi_node, weight_type, max_weight)
    serviced_buildings = gdf_residential_buildings[gdf_residential_buildings["snapped_to_node"].apply(lambda x: x in accessible_nodes)]

    if serviced_buildings.empty:
      # TODO: Mark the POIs that do not serve any buildings, will be interesting to investigate them
      continue

    poi_reach.append({
      'id': poi.id,
      'geom': poi.geom,
      'subgroup': poi.subgroup,
      'buildings_within_reach': serviced_buildings.shape[0],
      'appartments_within_reach': serviced_buildings['appartments'].sum(),
    })

  gdf_poi_reach = gpd.GeoDataFrame(poi_reach, geometry='geom')
  gdf_poi_reach.set_crs(epsg=7801, inplace=True)

  return gdf_poi_reach

def compute_poi_reach(pedestrian_network, gdf_points_of_interest, gdf_residential_buildings, weight_type = 'length', max_weight = 1000, snap_to = 'edge'):
  poi_reach = []

  # Not sure if this should be at that level. Should strike a balance between coping and keeping the graph small
  # When we snap_to node the network does not change, no need to copy it
  pedestrian_network_copy = pedestrian_network.copy() if snap_to == 'egde' else pedestrian_network

  for i, poi in tqdm(gdf_points_of_interest.iterrows(), total=gdf_points_of_interest.shape[0], desc="Processing poi"):
    # TODO: This could be extended to work with MultiPoint and take into account different entrances of parks/buildings when computing the reach
    # The data I have currently has a single point wraped in MultiPoint
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
      # TODO: Mark the POIs that do not serve any buildings, will be interesting to investigate them
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

def compute_buildings_absolute_reach(pedestrian_network, gdf_residential_buildings, pois, weight_type = 'length', max_weight = 1000):
  residentials_reach = []

  for i, residential in tqdm(gdf_residential_buildings.iterrows(), total=gdf_residential_buildings.shape[0], desc="Processing poi"):
    # Make sure to use the precomputed snapped_to_node, as recomputing it might result in a different node as the network has changes since adding it
    residential_node = residential["snapped_to_node"]
    accessible_nodes = nearby_nodes(pedestrian_network, residential_node, weight_type, max_weight)

    buidling_info = {
      'id': residential.id,
      'geom': residential.geom,
      'floorcount': residential['floors'],
      'appcount': residential['appartments'],
    }

    for gdf_poi_type in pois:
      reachable_pois = gdf_poi_type[gdf_poi_type["snapped_to_node"].apply(lambda x: x in accessible_nodes)]
      buidling_info.update(reachable_pois['subgroup'].value_counts().to_dict())

    residentials_reach.append(buidling_info)

  gdf_residentials_reach = gpd.GeoDataFrame(residentials_reach, geometry='geom')
  gdf_residentials_reach.set_crs(epsg=7801, inplace=True)

  return gdf_residentials_reach


def compute_buildings_reach(pedestrian_network, gdf_residential_buildings, pois, weight_type = 'length', max_weight = 1000, snap_to = 'edge'):
  residentials_reach = []

  # Not sure if this should be at that level. Should strike a balance between coping and keeping the graph small
  # When we snap_to node the network does not change, no need to copy it
  pedestrian_network_copy = pedestrian_network.copy() if snap_to == 'egde' else pedestrian_network

  for i, residential in tqdm(gdf_residential_buildings.iterrows(), total=gdf_residential_buildings.shape[0], desc="Processing poi"):
    # Make sure to work with point geomerty
    if snap_to == 'edge':
      residential_approx_id = snap_point_to_edge(pedestrian_network_copy, residential.geom)
    elif snap_to == 'node': # snap to node
      residential_approx_id = find_nearest_node(pedestrian_network_copy, residential.geom)
    else:
      raise "snap_to = 'node'|'edge'"

    accessibility_polygon = accessibility_area(pedestrian_network_copy, residential_approx_id, weight_type, max_weight)

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
