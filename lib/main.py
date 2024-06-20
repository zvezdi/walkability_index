# import psycopg2
import geopandas as gpd
import pandas as pd
# import networkx as nx
# import matplotlib.pyplot as plt
# import folium

from shapely.geometry import Point, MultiLineString, Polygon

from database import db_engine, gdf_from_sql, create_table_form_dgf, db_execute
from queries import pedestrian_network_query, administrative_regions_query, residential_buildings_query, poi_parks_query, poi_schools_query, poi_query
from network import build_network_from_geodataframe, find_nearest_node, shortest_path, compute_accessibility_isochron
from helpers import crs_transform_coords

import os
from dotenv import load_dotenv
import networkx as nx
from tqdm import tqdm # progressbar
from collections import defaultdict

import folium
from folium.plugins import MarkerCluster

# Load environment variables from a .env file
load_dotenv()

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

def save_gdf_to_db(database, schema, table_name, gdf):
  try:
    create_table_form_dgf(database, gdf, schema = schema, table_name = table_name)
    print(f"Table {schema}.{table_name} created")
  except Exception as e:
    print(f"Table {schema}.{table_name} failed to create wirh {e}")
    exit

def fill_in_access_index(gdf_residentials, df_access_wheights):
  weights_map = df_access_wheights.set_index('subgroup_id')[['gr_weights', 'sgr_weights']].to_dict('index')

  def calculate_service_level(row):
    total = 0
    for col in row.index:
      if col in weights_map:
        gr_weight = weights_map[col]['gr_weights']
        sgr_weight = weights_map[col]['sgr_weights']
        if pd.notna(row[col]) and row[col] > 0:
          total += float(gr_weight) * float(sgr_weight)
    return total

  gdf_residentials['service_index'] = gdf_residentials.apply(calculate_service_level, axis=1)

  return gdf_residentials

def create_regions_with_service_level(database):
  sql = f"""
    DROP TABLE IF EXISTS zvezdi_work.results_gen_adm_regions_service_level;
    CREATE TABLE zvezdi_work.results_gen_adm_regions_service_level AS
    SELECT gar.id,
      gar.obns_lat,
      gar.geom,
      sum(rrsl.service_index) / count(rrsl.id) as service_index,
      sum(rrsl.service_index * rrsl.appcount) / sum(rrsl.appcount) as weighted_service_index,
      sum(rrsl.appcount) as appcount,
      count(rrsl.id) as buildings_count
    FROM zvezdi_work.results_residentials_service_level rrsl, zvezdi_work.gen_adm_regions gar 
    WHERE ST_Contains(gar.geom, rrsl.geom)
    GROUP BY gar.id, gar.obns_lat, gar.geom
  """
  try:
    db_execute(database, sql)
    print(f"Created table zvezdi_work.results_gen_adm_regions_service_level")
  except Exception as e:
    print(f"Could not create, {e}")

def main():
  database = db_engine(os.getenv('DB_CONNECTION_STRING'))

  SCOPE = 'Lozenec'
  SCHEMA = 'zvezdi_work'

  with database.connect() as db_connection:
    gdf_pedestrian_network = gdf_from_sql(db_connection, pedestrian_network_query(SCOPE))
    gdf_residential_buildings_lozenec = gdf_from_sql(db_connection, residential_buildings_query(SCOPE))
    df_access_weights = pd.read_sql_query("select subgroup_id, sgr_weights, gr_weights from zvezdi_work.access_weights", con=db_connection)
    pois = {
      'poi_culture': gdf_from_sql(db_connection, poi_query('poi_culture', SCOPE)),
      'poi_health': gdf_from_sql(db_connection, poi_query('poi_health', SCOPE)),
      'poi_kids': gdf_from_sql(db_connection, poi_query('poi_kids', SCOPE)),
      'poi_mobility': gdf_from_sql(db_connection, poi_query('poi_mobility', SCOPE)),
      'poi_others': gdf_from_sql(db_connection, poi_query('poi_others', SCOPE)),
      'poi_parks': gdf_from_sql(db_connection, poi_query('poi_parks', SCOPE)),
      'poi_schools': gdf_from_sql(db_connection, poi_query('poi_schools', SCOPE)),
      'poi_sport': gdf_from_sql(db_connection, poi_query('poi_sport', SCOPE)),
    }

  pedestrian_network = build_network_from_geodataframe(gdf_pedestrian_network, swap_xy = False, save_as = "lib/saves/pedestrian_network.graph")

  for poi_type, poi_gdf in pois.items():
    gdf_poi_reach = compute_poi_reach(
      pedestrian_network,
      poi_gdf,
      gdf_residential_buildings_lozenec,
      cutoff = 1000,
      weight = 'length'
    )
    save_gdf_to_db(database, SCHEMA, f"results_{poi_type}_reach", gdf_poi_reach)

  gdf_residentials_reach = compute_buildings_reach(
    pedestrian_network,
    gdf_residential_buildings_lozenec,
    pois.values(),
    cutoff = 1000,
    weight = 'length'
  )
  gdf_residentials_with_access_index = fill_in_access_index(gdf_residentials_reach, df_access_weights)
  save_gdf_to_db(database, SCHEMA, 'results_residentials_service_level_v2', gdf_residentials_with_access_index)
  
  create_regions_with_service_level(database)

if __name__ == "__main__":
  main()
