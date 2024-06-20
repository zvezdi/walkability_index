from pyproj import Transformer
from shapely.geometry import Point, LineString, Polygon, MultiPolygon

BGS2005 = "EPSG:7801"
WGS84 = "EPSG:4326"

def crs_transform_point(point, swap_coords = False, source_crs = BGS2005, target_crs = WGS84):
  """ In the database we have point in 7801 (x, y) which translates to 4326 (lon, lat),
  however plotting libraries use 4326 (lat, lon)

  >>> crs_transform_point(Point(321812.94252381043, 4731192.267176171), swap_coords = True)
  <POINT (42.696 23.325)>
  >>> crs_transform_point(Point(321812.94252381043, 4731192.267176171), swap_coords = False)
  <POINT (23.325 42.696)>
  """
  transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
  lon, lat = transformer.transform(point.x, point.y)

  return Point(lat, lon) if swap_coords else Point(lon, lat)

def crs_transform_coords(x, y, swap_coords = False, toPoint = False, source_crs = BGS2005, target_crs = WGS84):
  """ In the database we have point in 7801 (x, y) which translates to 4326 (lon, lat),
  however plotting libraries use 4326 (lat, lon)

  >>> crs_transform_coords(321812.94252381043, 4731192.267176171)
  (23.325072705320427, 42.69556468222738)
  >>> crs_transform_coords(321812.94252381043, 4731192.267176171, swap_coords = True)
  (42.69556468222738, 23.325072705320427)
  >>> crs_transform_coords(321812.94252381043, 4731192.267176171, toPoint = True)
  <POINT (23.325 42.696)>
  >>> crs_transform_coords(321812.94252381043, 4731192.267176171, toPoint = True, swap_coords = True)
  <POINT (42.696 23.325)>
  """

  transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
  lon, lat = transformer.transform(x, y)

  if swap_coords:
    return Point(lat, lon) if toPoint else (lat, lon)
  
  return Point(lon, lat) if toPoint else (lon, lat)

def crs_transform_linestring(linestring, swap_coords = False, source_crs = BGS2005, target_crs = WGS84):
  """ In the database we have point in 7801 (x, y) which translates to 4326 (lon, lat),
  however plotting libraries use 4326 (lat, lon)

  >>> crs_transform_linestring(LineString([(320960.4910, 4728848.5264), (320844.2254, 4728875.6080), (320794.2176, 4729493.6845)]))
  <LINESTRING (23.315 42.674, 23.314 42.674, 23.313 42.68)>
  >>> crs_transform_linestring(LineString([(320960.4910, 4728848.5264), (320844.2254, 4728875.6080), (320794.2176, 4729493.6845)]), swap_coords = True)
  <LINESTRING (42.674 23.315, 42.674 23.314, 42.68 23.313)>
  """
  
  transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
  transformed_coords = [transformer.transform(x, y) for x, y in linestring.coords]

  if swap_coords:
    transformed_coords = [(lat, lon) for lon, lat in transformed_coords]

  return LineString(transformed_coords)

def crs_transform_polygon(polygon, swap_coords = False, source_crs = BGS2005, target_crs = WGS84):
  """ In the database we have point in 7801 (x, y) which translates to 4326 (lon, lat),
  however plotting libraries use 4326 (lat, lon)

  >>> crs_transform_polygon(Polygon([(320960.4910, 4728848.5264), (320844.2254, 4728875.6080), (320794.2176, 4729493.6845), (320960.4910, 4728848.5264)]))
  <POLYGON ((23.315 42.674, 23.314 42.674, 23.313 42.68, 23.315 42.674))>
  >>> crs_transform_polygon(Polygon([(320960.4910, 4728848.5264), (320844.2254, 4728875.6080), (320794.2176, 4729493.6845), (320960.4910, 4728848.5264)]), swap_coords = True)
  <POLYGON ((42.674 23.315, 42.674 23.314, 42.68 23.313, 42.674 23.315))>
  """
  
  transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
  transformed_coords = [transformer.transform(x, y) for x, y in polygon.exterior.coords]

  if swap_coords:
    transformed_coords = [(lat, lon) for lon, lat in transformed_coords]

  return Polygon(transformed_coords)

def crs_transform_multipolygon(multipolygon, swap_coords=False, source_crs=BGS2005, target_crs=WGS84):
  transformed_polygons = [
    crs_transform_polygon(polygon, swap_coords, source_crs, target_crs) for polygon in multipolygon.geoms
  ]
    
  return MultiPolygon(transformed_polygons)