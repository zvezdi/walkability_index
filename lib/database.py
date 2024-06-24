import geopandas as gpd
from sqlalchemy import create_engine, text

def db_engine(connection_string):
  return create_engine(f'postgresql+psycopg2://{connection_string}')

def db_execute(engine, sql):
  with engine.connect() as conn:
    conn.execute(text(sql))
    conn.commit()

def gdf_from_sql(connection, query, geom_column = 'geom'):
  return gpd.read_postgis(query, connection, geom_col=geom_column)

def create_table_form_dgf(engine, gdf, schema, table_name):
  gdf.to_postgis(name=table_name, con=engine, schema = schema, if_exists='replace')

def save_gdf_to_db(database, schema, table_name, gdf):
  try:
    create_table_form_dgf(database, gdf, schema = schema, table_name = table_name)
    print(f"Table {schema}.{table_name} created")
  except Exception as e:
    print(f"Table {schema}.{table_name} failed to create wirh {e}")
    exit
