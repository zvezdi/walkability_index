import pandas as pd
import os
from dotenv import load_dotenv

from database import db_engine, gdf_from_sql, save_gdf_to_db, db_execute
from queries import pedestrian_network_query, residential_buildings_query, poi_query
from network import build_network_from_geodataframe, extend_network_with
from compute_accessibility_index import compute_accessibility_index_weighed_sum, compute_accessibility_index_pca
from compute_location_reach import compute_poi_reach, compute_buildings_reach, compute_poi_absolute_reach, compute_buildings_absolute_reach
import networkx as nx

# Load environment variables from a .env file
load_dotenv()

def create_regions_with_service_level(database, tables_sufix):
  sql = f"""
    DROP TABLE IF EXISTS zvezdi_work.results_gen_adm_regions_service_level_{tables_sufix};
    CREATE TABLE zvezdi_work.results_gen_adm_regions_service_level_{tables_sufix} AS
    SELECT gar.id,
      gar.obns_lat,
      gar.geom,
      sum(rrsl.service_index) / count(rrsl.id) as service_index,
      sum(rrsl.service_index * rrsl.appcount) / sum(rrsl.appcount) as weighted_service_index,
      sum(rrsl.service_index_pca) / count(rrsl.id) as service_index_pca,
      sum(rrsl.service_index_pca * rrsl.appcount) / sum(rrsl.appcount) as weighted_service_index_pca,
      sum(rrsl.appcount) as appcount,
      count(rrsl.id) as buildings_count
    FROM zvezdi_work.results_residentials_service_level_{tables_sufix} rrsl, zvezdi_work.gen_adm_regions gar 
    WHERE ST_Contains(gar.geom, rrsl.geom)
    GROUP BY gar.id, gar.obns_lat, gar.geom
  """
  try:
    db_execute(database, sql)
    print(f"Created table zvezdi_work.results_gen_adm_regions_service_level_{tables_sufix}")
  except Exception as e:
    print(f"Could not create, {e}")

def create_ge_with_service_level(database, tables_sufix):
  sql = f"""
    DROP TABLE IF EXISTS zvezdi_work.results_ge_service_level_{tables_sufix};
    CREATE TABLE zvezdi_work.results_ge_service_level_{tables_sufix} AS
    SELECT ge.id,
      ge.regname,
      ge.rajon,
      ge.geom,
      sum(rrsl.service_index) / count(rrsl.id) as service_index,
      COALESCE(sum(rrsl.service_index * rrsl.appcount) / NULLIF(sum(rrsl.appcount), 0), 0) as weighted_service_index,
      sum(rrsl.service_index_pca) / count(rrsl.id) as service_index_pca,
      COALESCE(sum(rrsl.service_index_pca * rrsl.appcount) / NULLIF(sum(rrsl.appcount), 0), 0) as weighted_service_index_pca,
      sum(rrsl.appcount) as appcount,
      count(rrsl.id) as buildings_count
    FROM zvezdi_work.results_residentials_service_level_{tables_sufix} rrsl, ge_2020 ge 
    WHERE ST_Contains(ge.geom, rrsl.geom)
    GROUP BY ge.id, ge.regname, ge.rajon, ge.geom
  """
  try:
    db_execute(database, sql)
    print(f"Created table zvezdi_work.results_ge_service_level_{tables_sufix}")
  except Exception as e:
    print(f"Could not create, {e}")

def compute_isochron_accesibilities(gdf_pedestrian_network, pois, gdf_residentials, df_access_weights, snap_to: None, save_network_as = None, database = None, schema = None, tables_sufix = None):
  """
  Compute the accesible items by creating isochron (convex hull around the points that are within the specified distance).
  This add some small error to the 'max_weight' but is fast to do and pretty.
  """
  pedestrian_network = build_network_from_geodataframe(gdf_pedestrian_network, save_as = save_network_as)

  # Create tables for each POI with the number of buildings/appartments within reach
  for poi_type, poi_gdf in pois.items():
    print(f"Working on {poi_type}")
    gdf_poi_reach = compute_poi_reach(
      pedestrian_network,
      poi_gdf,
      gdf_residentials,
      weight_type = 'length',
      max_weight = 1000,
      snap_to = snap_to,
    )
    save_gdf_to_db(database, schema, f"results_{poi_type}_reach_{tables_sufix}", gdf_poi_reach)

  # Create table for residentials service level - compute the index both systematically and with PCA
  gdf_residentials_reach = compute_buildings_reach(
    pedestrian_network,
    gdf_residentials,
    pois.values(),
    weight_type = 'length',
    max_weight = 1000,
    snap_to = snap_to,
  )
  gdf_residentials_with_access_index = compute_accessibility_index_weighed_sum(gdf_residentials_reach, df_access_weights, column_name = 'service_index')
  gdf_residentials_with_access_index_and_pca = compute_accessibility_index_pca(gdf_residentials_with_access_index, df_access_weights, column_name = 'service_index_pca')
  save_gdf_to_db(database, schema, f"results_residentials_service_level_{tables_sufix}", gdf_residentials_with_access_index_and_pca)

def compute_absolute_accesibilities(gdf_pedestrian_network, pois, gdf_residentials, df_access_weights, save_network_as = None, database = None, schema = None, tables_sufix = None):
  """
  Compute the accesible items by adding each point to the network and computing all points within 'max_weight' distance from the origin point.
  The point is added by snapping the original to the closest edge and spliting it in two (weights are split proportionally).
  The process of adding the nodes is quite slow and not idempotent(if you snap the same point after adding some other edges,
  the resultion node might be different as the graph has changes),
  hence I preserve the node I've assosiated with a Point when adding it and use that preserved when computing accesible items 
  """
  pedestrian_network = build_network_from_geodataframe(gdf_pedestrian_network)

  # Extend network with all buildings and pois
  for poi_type, poi_gdf in pois.items():
    extend_network_with(pedestrian_network, poi_gdf)
  extend_network_with(pedestrian_network, gdf_residentials)
  nx.write_gml(pedestrian_network, 'lib/saves/pedestrian_network_extended.graph')
  
  # Create tables for each POI with the number of buildings/appartments within reach
  for poi_type, poi_gdf in pois.items():
    print(f"Working on {poi_type}")
    gdf_poi_reach = compute_poi_absolute_reach(
      pedestrian_network,
      poi_gdf,
      gdf_residentials,
      weight_type = 'length',
      max_weight = 1000,
    )
    save_gdf_to_db(database, schema, f"results_{poi_type}_reach_{tables_sufix}", gdf_poi_reach)

  # Create table for residentials service level - compute the index both systematically and with PCA
  gdf_residentials_reach = compute_buildings_absolute_reach(
    pedestrian_network,
    gdf_residentials,
    pois.values(),
    weight_type = 'length',
    max_weight = 1000,
  )
  gdf_residentials_with_access_index = compute_accessibility_index_weighed_sum(gdf_residentials_reach, df_access_weights, column_name = 'service_index')
  gdf_residentials_with_access_index_and_pca = compute_accessibility_index_pca(gdf_residentials_with_access_index, df_access_weights, column_name = 'service_index_pca')
  save_gdf_to_db(database, schema, f"results_residentials_service_level_{tables_sufix}", gdf_residentials_with_access_index_and_pca)

def main():
  database = db_engine(os.getenv('DB_CONNECTION_STRING'))
  SCOPE = 'Lozenec'
  SCHEMA = 'zvezdi_work'

  with database.connect() as db_connection:
    gdf_pedestrian_network = gdf_from_sql(db_connection, pedestrian_network_query(SCOPE))
    gdf_residential_buildings_lozenec = gdf_from_sql(db_connection, residential_buildings_query(SCOPE))
    df_access_weights = pd.read_sql_query("select subgroup_id, sgr_weights, gr_weights from zvezdi_work.access_weights", con=db_connection)
    df_access_weights['gr_weights'] = pd.to_numeric(df_access_weights['gr_weights'])
    df_access_weights['sgr_weights'] = pd.to_numeric(df_access_weights['sgr_weights'])

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

  compute_isochron_accesibilities(
    gdf_pedestrian_network,
    pois,
    gdf_residential_buildings_lozenec,
    df_access_weights,
    snap_to = 'edge',
    save_network_as = "lib/saves/pedestrian_network.graph",
    database = database,
    schema = SCHEMA,
    tables_sufix = "isochron",
  )
  create_regions_with_service_level(database, "isochron")
  create_ge_with_service_level(database, "isochron")

  compute_absolute_accesibilities(
    gdf_pedestrian_network,
    pois,
    gdf_residential_buildings_lozenec,
    df_access_weights,
    save_network_as = "lib/saves/pedestrian_network_extended.graph",
    database = database,
    schema = SCHEMA,
    tables_sufix = "absolute",
  )
  create_regions_with_service_level(database, "absolute")
  create_ge_with_service_level(database, "absolute")

if __name__ == "__main__":
  main()
