###### Full data #######

PEDESTRIAN_NETWORK_SQL = f"""
  SELECT id, ST_Transform(geom, 4283) as geom, type, str_class as class, length_m as meters, minutes FROM zvezdi_work.pedestrian_network pn
"""

ADMINISTRATIVE_REGIONS_SQL = f"""
  select id, geom, obns_cyr as municipality from zvezdi_work.gen_adm_regions gar
"""

RESIDENTIAL_BUILDINGS_SQL = f"""
  select id, geom, floorcount as floors, appcount as appartments from zvezdi_work.buildings_res_all_2023
"""

POI_PARKS_SQL = f"""
  select id, ST_Transform(geom, 4283) as geom, subgroup_i as subgroup from zvezdi_work.poi_parks pp
"""

###### Scoped queries for Lozenec #######

PEDESTRIAN_NETWORK_BUFFERED_LOZENEC_SQL = f"""
  select pn.geom as geom, type, str_class as class, length_m as meters, minutes 
  from zvezdi_work.pedestrian_network pn, zvezdi_work.gen_lezenec_buf buffered_lozenec
  where st_intersects(pn.geom, buffered_lozenec.geom)
"""

RESIDENTIAL_BUILDINGS_LOZENEC_SQL = f"""
  select id, geom, floorcount as floors, appcount as appartments from zvezdi_work.buildings_res_lozenec_2019
"""

POI_PARKS_BUFFERED_LOZENEC_SQL = f"""
  select pp.geom, subgroup_i as subgroup 
  from zvezdi_work.poi_parks pp, zvezdi_work.gen_lezenec_buf buffered_lozenec
  where st_intersects(pp.geom, buffered_lozenec.geom)
"""

def pedestrian_network_query(scope):
  if scope == "Lozenec":
    return PEDESTRIAN_NETWORK_BUFFERED_LOZENEC_SQL
  return PEDESTRIAN_NETWORK_SQL

def administrative_regions_query():
  return ADMINISTRATIVE_REGIONS_SQL
 
def residential_buildings_query(scope):
  if scope == "Lozenec":
    return RESIDENTIAL_BUILDINGS_LOZENEC_SQL
  return RESIDENTIAL_BUILDINGS_SQL

def poi_parks_query(scope):
  if scope == "Lozenec":
    return POI_PARKS_BUFFERED_LOZENEC_SQL
  return POI_PARKS_SQL
