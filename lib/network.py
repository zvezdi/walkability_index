import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from shapely.geometry import Point, MultiPoint, LineString, MultiLineString, GeometryCollection, MultiPolygon

import numpy as np
from scipy.spatial import Delaunay
from shapely.geometry import MultiPoint, Polygon
from shapely.ops import unary_union

def build_network_from_geodataframe(gdf, save_as = None):
  G = nx.Graph()
  
  for _idx, row in gdf.iterrows():
    geom = row['geom']
    length = row['meters']
    time = row['minutes']
    
    if isinstance(geom, MultiLineString):
      for line in geom.geoms:
        add_line_to_graph(G, line, length, time)
    elif isinstance(geom, LineString):
      add_line_to_graph(G, geom, length, time)
    else:
        raise TypeError(f"Unexpected geometry type: {type(geom)}")
  
  if save_as:
    nx.write_gml(G, save_as)

  return G

def add_line_to_graph(G, line, length, time):
  coords = list(line.coords)
  
  for i in range(len(coords) - 1):
    start = coords[i]
    end = coords[i + 1]
    
    # Add nodes with 'pos' attribute
    if start not in G:
      G.add_node(start, pos=start)
    if end not in G:
      G.add_node(end, pos=end)
    
    # Add edge with length and time as weights
    G.add_edge(start, end, length=length, time=time)

def read_network_from_file(path_to_graph):
  return nx.read_gml(path_to_graph)

def find_nearest_node(G, point):
  """
  Returns a node id in the graph structure
  """
  return min(G.nodes(data=True), key=lambda x: Point(x[1]['pos']).distance(point))[0]

def node_to_point(G, node_id):
  """
  Transforms a node id in the graph to a Point(x, y) object
  """
  if G.has_node(node_id):
    return Point(G.nodes[node_id]['pos'])
  else:
    raise ValueError(f"Node {node_id} does not exist in the graph.")

# Function to compute the shortest path in the graph
def shortest_path(G, start_point, end_point, weight='time'):
  start_node = find_nearest_node(G, start_point)
  end_node = find_nearest_node(G, end_point)

  path = nx.shortest_path(G, source=start_node, target=end_node, weight=weight)
  total_cost = nx.shortest_path_length(G, source=start_node, target=end_node, weight=weight)
  return path, total_cost

def compute_accessibility_boundary_points(network, source_node, weight_type, max_weight):
  # Find all nodes within the max_weight distance and the cost to get to them
  lengths = nx.single_source_dijkstra_path_length(network, source_node, cutoff = max_weight, weight = weight_type)
  reachable_nodes = lengths.keys()
  boundary_points = []

  # Traverse the edges and find boundary points
  for node, _dist in lengths.items():
    for neighbor in network.neighbors(node):
      if neighbor not in reachable_nodes:
        boundary_points.append(node)
        break
  
  return boundary_points, LineString(boundary_points)

def compute_accessibility_isochron(network, source_node, weight_type, max_weight):
  """
  weight_type: string - The name of the edge metric to be used
  max_weight: number - Value in the metric system of the "weight" to stop traversing the graph further when reached
  """
  # Find all nodes within the max_weight distance and the cost to get to them
  lengths = nx.single_source_dijkstra_path_length(network, source_node, cutoff = max_weight, weight = weight_type)

  points_within_distance = [Point(network.nodes[node]['pos']) for node in lengths.keys()]
  multi_point = MultiPoint(points_within_distance)

  return multi_point.convex_hull

def filter_nodes_within_accessibility_isochron(network, accessibility_isochron):
  filtered_nodes = []
  for node in network.nodes:
    point = Point(network.nodes[node]['pos'])
    if point.within(accessibility_isochron):
      filtered_nodes.append(node)
  return filtered_nodes

def find_nearest_edge(network, point):
  nearest_edge = None
  min_dist = float('inf')
  for u, v, data in network.edges(data=True):
    line = LineString([network.nodes[u]['pos'], network.nodes[v]['pos']])
    dist = point.distance(line)
    if dist < min_dist:
      min_dist = dist
      nearest_edge = (u, v, data)
  
  return nearest_edge

def snap_point_to_edge(network, point, length_attr='length', time_attr='time'):
  u, v, data = find_nearest_edge(network, point)

  line = LineString([network.nodes[u]['pos'], network.nodes[v]['pos']])
  proj_point = line.interpolate(line.project(point))

  # Add the new node at the projected point
  new_node = (float(proj_point.x), float(proj_point.y))
  network.add_node(new_node, pos=(proj_point.x, proj_point.y))
  
  # Split the edge (u, v) into (u, new_node) and (new_node, v)
  network.remove_edge(u, v)

  original_length = data[length_attr]
  original_time = data[time_attr]
  
  length1 = Point(network.nodes[u]['pos']).distance(proj_point)
  length2 = proj_point.distance(Point(network.nodes[v]['pos']))

  time1 = original_time * (length1 / original_length)
  time2 = original_time * (length2 / original_length)

  network.add_edge(u, new_node, **{length_attr: float(length1), time_attr: time1})
  network.add_edge(new_node, v, **{length_attr: float(length2), time_attr: time2})

  return new_node