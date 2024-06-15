import psycopg2
import geopandas as gpd

def connect_to_db(connection_string):
  connection = psycopg2.connect(connection_string)
  connection.autocommit = True

  return connection

def get_geodataframe_from_sql(db_connection, sql):
  geodataframe = gpd.GeoDataFrame.from_postgis(sql, db_connection)

  return geodataframe

def close_connection(db_connection):
  db_connection.close()
