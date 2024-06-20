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
  select id, geom, subgroup_i as subgroup from zvezdi_work.poi_parks pp
"""

###### Scoped queries for Lozenec #######

PEDESTRIAN_NETWORK_BUFFERED_LOZENEC_SQL = f"""
  select pn.geom as geom, type, str_class as class, length_m as meters, minutes 
  from zvezdi_work.pedestrian_network pn, zvezdi_work.gen_lezenec_buf buffered_lozenec
  where st_intersects(pn.geom, buffered_lozenec.geom)
"""

RESIDENTIAL_BUILDINGS_LOZENEC_BUFFERED_SQL = f"""
  select id, geom, floorcount as floors, appcount as appartments from zvezdi_work.buildings_res_lozenec_2019
"""

POI_PARKS_BUFFERED_LOZENEC_SQL = f"""
  select pp.id, pp.geom, subgroup_i as subgroup 
  from zvezdi_work.poi_parks pp, zvezdi_work.gen_lezenec_buf buffered_lozenec
  where st_intersects(pp.geom, buffered_lozenec.geom)
"""

POI_SCHOOLS_BUFFERED_LOZENEC_SQL = f"""
  select pp.id, pp.geom, subgroup_i as subgroup 
  from zvezdi_work.poi_schools pp, zvezdi_work.gen_lezenec_buf buffered_lozenec
  where st_intersects(pp.geom, buffered_lozenec.geom)
"""

BUFFER_LOZENEC_SQL = f"""
  select geom from zvezdi_work.gen_lezenec_buf
"""

LOZENEC_RESIDENTIALS_SERVISE_LEVEL_SQL = f"""
  select rrsl.* from zvezdi_work.results_residentials_service_level_v2 rrsl, zvezdi_work.gen_adm_regions gar 
  where gar.obns_lat = 'LOZENEC' and ST_Contains(gar.geom, rrsl.geom)
"""

def pedestrian_network_query(scope):
  if scope == "Lozenec":
    return PEDESTRIAN_NETWORK_BUFFERED_LOZENEC_SQL
  return PEDESTRIAN_NETWORK_SQL

def administrative_regions_query():
  return ADMINISTRATIVE_REGIONS_SQL
 
def residential_buildings_query(scope):
  if scope == "Lozenec":
    return RESIDENTIAL_BUILDINGS_LOZENEC_BUFFERED_SQL
  return RESIDENTIAL_BUILDINGS_SQL

def residential_buildings_with_service_level_query(scope):
  if scope == "Lozenec":
    return LOZENEC_RESIDENTIALS_SERVISE_LEVEL_SQL
  return "Implement me!"

def poi_parks_query(scope):
  if scope == "Lozenec":
    return POI_PARKS_BUFFERED_LOZENEC_SQL
  return POI_PARKS_SQL

def poi_schools_query(scope):
  if scope == "Lozenec":
    return POI_SCHOOLS_BUFFERED_LOZENEC_SQL
  return "Implement me!"

def buffered_region_boundary(scope):
  if scope == "Lozenec":
    return BUFFER_LOZENEC_SQL

def poi_query(table_name, scope):
  if scope == "Lozenec":
    return f"""
      select poi.id, poi.geom, poi.subgroup_i as subgroup 
      from zvezdi_work.{table_name} poi, zvezdi_work.gen_lezenec_buf buffered_lozenec
      where st_intersects(poi.geom, buffered_lozenec.geom)
    """
  return "Implement me!"

def poi_reach_query(table_name, scope):
  if scope == "Lozenec":
    return f"""
      select poi.id, poi.geom, poi.subgroup, poi.buildings_within_reach, poi.appartments_within_reach, poi.service_distance_polygon
      from zvezdi_work.results_{table_name}_reach poi, zvezdi_work.gen_lezenec_buf buffered_lozenec
      where st_intersects(poi.geom, buffered_lozenec.geom)
    """
  return "Implement me!"

def administrative_regions_with_service_level_query():
  return "select * from zvezdi_work.results_gen_adm_regions_service_level"
