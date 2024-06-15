from pyproj import Transformer
from shapely.geometry import Point

def point_xy_to_4326_lat_long(point):
  """ In the database we have point in 7801 (x, y) which translates to 4326 (lon, lat),
  however plotting libraries use 4326 (lat, lon)

  >>> point_xy_to_4326_lat_long(Point(321812.94252381043, 4731192.267176171))
  <POINT (42.696 23.325)>
  """
  transformer = Transformer.from_crs("EPSG:7801", "EPSG:4326", always_xy=True)
  lon, lat = transformer.transform(point.x, point.y)

  return Point(lat, lon)

def xy_to_4326_lat_long(x, y, toPoint = False):
  """ In the database we have point in 7801 (x, y) which translates to 4326 (lon, lat),
  however plotting libraries use 4326 (lat, lon)

  >>> xy_to_4326_lat_long(321812.94252381043, 4731192.267176171)
  (42.69556468222738, 23.325072705320427)

  >>> xy_to_4326_lat_long(321812.94252381043, 4731192.267176171, toPoint = True)
  <POINT (42.696 23.325)>
  """
  transformer = Transformer.from_crs("EPSG:7801", "EPSG:4326", always_xy=True)
  lon, lat = transformer.transform(x, y)

  if toPoint:
    return Point(lat, lon)
  
  return (lat, lon)
