import geopandas as gpd
from shapely.geometry import Point, Polygon
from tqdm import tqdm # progressbar

from network import find_nearest_node, compute_accessibility_isochron

def accesibility_area(network, source_location, cutoff, weight):
  _boundary_points, boundary_linestring = compute_accessibility_isochron(network, source_location, cutoff, weight)

  if not(boundary_linestring) or len(list(boundary_linestring.coords)) < 3:
    with open('lib/logs/residentials_without_boundary.txt', 'a') as file:
      file.write(f"[#{source_location}],\n")
      # TODO: figure out what to do if if a point is in a place in the graph that cannot form a polygone arround withing the cutoff
      # For now I'll just create a simple buffer with some penelty for not using the pedestrian network
    return source_location.buffer(0.8 * cutoff)

  return Polygon(boundary_linestring)

def within_accesibility_area(accesibility_polygon, gdf_locations):
  return gdf_locations[gdf_locations.geom.apply(lambda x: x.within(accesibility_polygon))]

def compute_poi_reach(pedestrian_network, gdf_points_of_interest, gdf_residential_buildings, cutoff = 1000, weight = 'length'):
  poi_reach = []

  for i, poi in tqdm(gdf_points_of_interest.iterrows(), total=gdf_points_of_interest.shape[0], desc="Processing poi"):
    # Try adding a node to the closest edge instead?
    poi_aproximation = Point(find_nearest_node(pedestrian_network, poi.geom))
    accesibility_polygon = accesibility_area(pedestrian_network, poi_aproximation, cutoff, weight)
    serviced_buildings = within_accesibility_area(accesibility_polygon, gdf_residential_buildings)

    if serviced_buildings.empty:
      # TODO: mark the pois that do not serve any buildings in some way, further look is needed into them
      continue

    poi_reach.append({
      'id': poi.id,
      'geom': poi.geom,
      'subgroup': poi.subgroup,
      'buildings_within_reach': serviced_buildings.shape[0],
      'appartments_within_reach': serviced_buildings['appartments'].sum(),
      'service_distance_polygon': accesibility_polygon,
    })

  gdf_poi_reach = gpd.GeoDataFrame(poi_reach, geometry='geom')
  gdf_poi_reach.set_crs(epsg=7801, inplace=True)

  return gdf_poi_reach

def compute_buildings_reach(pedestrian_network, gdf_residential_buildings, pois, cutoff = 1000, weight = 'length'):
  residentials_reach = []

  for i, residential in tqdm(gdf_residential_buildings.iterrows(), total=gdf_residential_buildings.shape[0], desc="Processing poi"):
    # Try adding a node to the closest edge instead?
    residential_approximation = Point(find_nearest_node(pedestrian_network, residential.geom))
    accesibility_polygon = accesibility_area(pedestrian_network, residential_approximation, cutoff, weight)

    buidling_info = {
      'id': residential.id,
      'geom': residential.geom,
      'floorcount': residential['floors'],
      'appcount': residential['appartments'],
      'accesibility_polygon': accesibility_polygon,
    }

    for gdf_poi_type in pois:
      reachable_pois = within_accesibility_area(accesibility_polygon, gdf_poi_type)
      buidling_info.update(reachable_pois['subgroup'].value_counts().to_dict())

    residentials_reach.append(buidling_info)

  gdf_residentials_reach = gpd.GeoDataFrame(residentials_reach, geometry='geom')
  gdf_residentials_reach.set_crs(epsg=7801, inplace=True)

  return gdf_residentials_reach
