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

def create_regions_with_service_level(database, type):
  sql = f"""
    DROP TABLE IF EXISTS zvezdi_work.results_gen_adm_regions_service_level;
    CREATE TABLE zvezdi_work.results_gen_adm_regions_service_level AS
    SELECT gar.id,
      gar.obns_lat,
      gar.geom,
      sum(rrsl.service_index) / count(rrsl.id) as service_index,
      sum(rrsl.service_index * rrsl.appcount) / sum(rrsl.appcount) as weighted_service_index,
      sum(rrsl.service_index_pca) / count(rrsl.id) as service_index_pca,
      sum(rrsl.service_index_pca * rrsl.appcount) / sum(rrsl.appcount) as weighted_service_index_pca,
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

def compute_isochron_accesibilities(database, schema, scope, snap_to):
  with database.connect() as db_connection:
    gdf_pedestrian_network = gdf_from_sql(db_connection, pedestrian_network_query(scope))
    gdf_residential_buildings_lozenec = gdf_from_sql(db_connection, residential_buildings_query(scope))
    df_access_weights = pd.read_sql_query("select subgroup_id, sgr_weights, gr_weights from zvezdi_work.access_weights", con=db_connection)
    df_access_weights['gr_weights'] = pd.to_numeric(df_access_weights['gr_weights'])
    df_access_weights['sgr_weights'] = pd.to_numeric(df_access_weights['sgr_weights'])

    pois = {
      'poi_culture': gdf_from_sql(db_connection, poi_query('poi_culture', scope)),
      'poi_health': gdf_from_sql(db_connection, poi_query('poi_health', scope)),
      'poi_kids': gdf_from_sql(db_connection, poi_query('poi_kids', scope)),
      'poi_mobility': gdf_from_sql(db_connection, poi_query('poi_mobility', scope)),
      'poi_others': gdf_from_sql(db_connection, poi_query('poi_others', scope)),
      'poi_parks': gdf_from_sql(db_connection, poi_query('poi_parks', scope)),
      'poi_schools': gdf_from_sql(db_connection, poi_query('poi_schools', scope)),
      'poi_sport': gdf_from_sql(db_connection, poi_query('poi_sport', scope)),
    }

  pedestrian_network = build_network_from_geodataframe(gdf_pedestrian_network, save_as = "lib/saves/pedestrian_network.graph")

  for poi_type, poi_gdf in pois.items():
    gdf_poi_reach = compute_poi_reach(
      pedestrian_network,
      poi_gdf,
      gdf_residential_buildings_lozenec,
      weight_type = 'length',
      max_weight = 1000,
      snap_to = snap_to
    )
    save_gdf_to_db(database, schema, f"results_isochron_{poi_type}_reach", gdf_poi_reach)

  gdf_residentials_reach = compute_buildings_reach(
    pedestrian_network,
    gdf_residential_buildings_lozenec,
    pois.values(),
    weight_type = 'length',
    max_weight = 1000,
    snap_to = snap_to
  )

  gdf_residentials_with_access_index = compute_accessibility_index_weighed_sum(gdf_residentials_reach, df_access_weights, column_name = 'service_index')
  gdf_residentials_with_access_index_and_pca = compute_accessibility_index_pca(gdf_residentials_with_access_index, df_access_weights, column_name = 'service_index_pca')

  save_gdf_to_db(database, schema, 'results_isochron_residentials_service_level', gdf_residentials_with_access_index_and_pca)
  
  create_regions_with_service_level(database)

def compute_absolute_accesibilities(database, schema, scope):
  with database.connect() as db_connection:
    gdf_pedestrian_network = gdf_from_sql(db_connection, pedestrian_network_query(scope))
    gdf_residential_buildings_lozenec = gdf_from_sql(db_connection, residential_buildings_query(scope))
    df_access_weights = pd.read_sql_query("select subgroup_id, sgr_weights, gr_weights from zvezdi_work.access_weights", con=db_connection)
    df_access_weights['gr_weights'] = pd.to_numeric(df_access_weights['gr_weights'])
    df_access_weights['sgr_weights'] = pd.to_numeric(df_access_weights['sgr_weights'])

    pois = {
      'poi_culture': gdf_from_sql(db_connection, poi_query('poi_culture', scope)),
      'poi_health': gdf_from_sql(db_connection, poi_query('poi_health', scope)),
      'poi_kids': gdf_from_sql(db_connection, poi_query('poi_kids', scope)),
      'poi_mobility': gdf_from_sql(db_connection, poi_query('poi_mobility', scope)),
      'poi_others': gdf_from_sql(db_connection, poi_query('poi_others', scope)),
      'poi_parks': gdf_from_sql(db_connection, poi_query('poi_parks', scope)),
      'poi_schools': gdf_from_sql(db_connection, poi_query('poi_schools', scope)),
      'poi_sport': gdf_from_sql(db_connection, poi_query('poi_sport', scope)),
    }

  pedestrian_network = build_network_from_geodataframe(gdf_pedestrian_network, save_as = "lib/saves/pedestrian_network.graph")
  # Extend network with all buildings and pois
  for poi_type, poi_gdf in pois.items():
    extend_network_with(pedestrian_network, poi_gdf)
  extend_network_with(pedestrian_network, gdf_residential_buildings_lozenec)

  nx.write_gml(pedestrian_network, 'lib/saves/pedestrian_network_extended.graph')
  
  for poi_type, poi_gdf in pois.items():
    gdf_poi_reach = compute_poi_absolute_reach(
      pedestrian_network,
      poi_gdf,
      gdf_residential_buildings_lozenec,
      weight_type = 'length',
      max_weight = 1000,
    )
    save_gdf_to_db(database, schema, f"results_absolute_{poi_type}_reach", gdf_poi_reach)

  gdf_residentials_reach = compute_buildings_absolute_reach(
    pedestrian_network,
    gdf_residential_buildings_lozenec,
    pois.values(),
    weight_type = 'length',
    max_weight = 1000,
  )

  gdf_residentials_with_access_index = compute_accessibility_index_weighed_sum(gdf_residentials_reach, df_access_weights, column_name = 'service_index')
  gdf_residentials_with_access_index_and_pca = compute_accessibility_index_pca(gdf_residentials_with_access_index, df_access_weights, column_name = 'service_index_pca')

  save_gdf_to_db(database, schema, 'results_absolute_residentials_service_level', gdf_residentials_with_access_index_and_pca)
  
  create_regions_with_service_level(database, type="isochron")


def main():
  database = db_engine(os.getenv('DB_CONNECTION_STRING'))
  SCOPE = 'Lozenec'
  SCHEMA = 'zvezdi_work'

  # compute_isochron_accesibilities(database, SCHEMA, SCOPE, snap_to = 'edge')
  compute_absolute_accesibilities(database, SCHEMA, SCOPE)

if __name__ == "__main__":
  main()
