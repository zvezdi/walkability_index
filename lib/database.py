import psycopg2
import geopandas as gpd
import geopandas as gpd
from sqlalchemy import create_engine, text


def connect_to_db(connection_string):
  connection = psycopg2.connect(connection_string)
  connection.autocommit = True

  return connection

def get_geodataframe_from_sql(db_connection, sql):
  geodataframe = gpd.GeoDataFrame.from_postgis(sql, db_connection)

  return geodataframe

def close_connection(db_connection):
  db_connection.close()

# Function to convert GeoDataFrame to a SQL command for creating a view
def create_view_sql_from_gdf(gdf, view_name, src = 7801):
  columns = gdf.columns.tolist()
  column_definitions = ", ".join([f'"{col}"' for col in columns if col != 'geom'])
  geometry_definition = 'geom'
  sql = f"""
  CREATE OR REPLACE VIEW {view_name} AS
  SELECT {column_definitions}, ST_GeomFromText('{gdf.geom.to_wkt().iloc[0]}', 4326) AS {geometry_definition}
  FROM (
      VALUES
  """
  for idx, row in gdf.iterrows():
      row_values = ", ".join([f"'{str(row[col])}'" for col in columns if col != 'geom'])
      geom_value = f"ST_GeomFromText('{row.geom.wkt}', {src})"
      sql += f"({row_values}, {geom_value}),"
  sql = sql.rstrip(",")  # Remove the last comma
  sql += ") AS temp_table;"

  return sql

def create_view_from_gdf(connection_string, gdf, view_name):
  engine = create_engine('postgresql+psycopg2://zvezdi:ragis2024zzdftw@34.118.61.196:5432/ragis')
  create_view_sql = create_view_sql_from_gdf(gdf, view_name)
  
  with engine.connect() as conn:
    conn.execute(text(create_view_sql))

  print(f"View '{view_name}' created successfully in the database.")