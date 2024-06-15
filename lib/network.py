import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from shapely.geometry import Point, MultiLineString

def build_network_from_geodataframe(gdf, swap_xy = True, save_as = None):
  """
  EPSG:7801(our calcualtions crs) is denoted in (x, y) and EPSG:4326(the visualization crs) is denoted with (longitude, latitude)
  Most map visualization libraries use (latitude, longitude) style coordinates in EPSG:4326
  swap_xy = False will add the edges as they are in the gdf aka for edge Linestring((x1, y1), (x2,y2)) will add an edge (x1, y1) -> (x2, y2) 
  swap_xy = True will swap the coordinates aka for edge Linestring((x1, y1), (x2,y2)) will add an edge (y1, x1) -> (y2, x2)
  """
  G = nx.Graph()
  for _idx, row in gdf.iterrows():
    geom = row['geom']
    length = row['meters']
    time = row['minutes']

    if isinstance(geom, MultiLineString):
      lines = geom.geoms
    else:
      lines = [geom]

    for line in lines:
      coords = list(line.coords)

      for i in range(len(coords) - 1):
          u = coords[i]
          v = coords[i + 1]
          if swap_xy:
            # Add edges with swaped (latitude/y, longitude/x) if input was (x, y)
            G.add_edge((u[1], u[0]), (v[1], v[0]), length=length, time=time)
          else:
            # Add edges as they are in the input, presumably (x, y)
            G.add_edge((u[0], u[1]), (v[0], v[1]), length=length, time=time)

  if save_as:
    nx.write_gml(G, save_as)

  return G

def read_network_from_file(path_to_graph):
  return nx.read_gml(path_to_graph)

def visualize_network(G, save_as = None):
  pos = {node: (node[0], node[1]) for node in G.nodes()}
  
  plt.figure(figsize=(12, 8))
  nx.draw(G, pos, with_labels=False, node_size=10, font_size=8, edge_color="gray")
  plt.title('Pedestrian Network Graph')
  plt.xlabel('Longitude')
  plt.ylabel('Latitude')
  if save_as:
    plt.savefig(save_as)
  plt.show()

# Function to find the nearest node in the graph to a given point
def find_nearest_node(G, point):
  nearest_node = None
  min_dist = float('inf')

  for node in G.nodes:
      dist = Point(node).distance(point)
      if dist < min_dist:
          min_dist = dist
          nearest_node = node

  return nearest_node

def visualize_nearest_node(G, original_point, nearest_node, save_as = None):
  pos = {node: (node[0], node[1]) for node in G.nodes()}
  
  plt.figure(figsize=(12, 8))
  nx.draw(G, pos, with_labels=False, node_size=10, font_size=8, edge_color="gray")

  # Add the original point
  plt.scatter(original_point.x, original_point.y, color='red', s=20, marker='s')  # s is the size, marker='s' is for square shape
  plt.text(original_point.x, original_point.y, "original", horizontalalignment='center', verticalalignment='center', color='black', fontsize=12)
  # Add the nearest node
  plt.scatter(nearest_node.x, nearest_node.y, color='green', s=20, marker='s')  # s is the size, marker='s' is for square shape
  plt.text(nearest_node.x, nearest_node.y, "nearest", horizontalalignment='center', verticalalignment='center', color='black', fontsize=12)

  # Define the zoom region (adjust these values to fit your region of interest)
  x_min = min(original_point.x, nearest_node.x) - 500
  x_max = max(original_point.x, nearest_node.x) + 500
  y_min = min(original_point.y, nearest_node.y) - 500
  y_max = max(original_point.y, nearest_node.y) + 500

  # Set the axis limits to zoom in on the region of interest
  plt.xlim(x_min, x_max)
  plt.ylim(y_min, y_max)

  plt.title('Pedestrian Network Graph')
  plt.xlabel('Longitude')
  plt.ylabel('Latitude')
  if save_as:
    plt.savefig(save_as)
  plt.show()

# Function to compute the shortest path in the graph
def shortest_path(G, start_point, end_point, weight='time'):
    start_node = find_nearest_node(G, start_point)
    end_node = find_nearest_node(G, end_point)

    path = nx.shortest_path(G, source=start_node, target=end_node, weight=weight)
    total_cost = nx.shortest_path_length(G, source=start_node, target=end_node, weight=weight)
    return path, total_cost

def visualize_path(G, original_source, original_destination, path_time = None, path_length = None, save_as = None):
  pos = {node: (node[0], node[1]) for node in G.nodes()}
  
  plt.figure(figsize=(12, 8))
  # Draw the graph
  nx.draw(G, pos, with_labels=False, node_size=10, font_size=8, edge_color="gray")

  # Draw the paths
  if path_time:
    path_edges = list(zip(path_time, path_time[1:]))
    nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='green', width=4)
  if path_length:
    path_edges = list(zip(path_length, path_length[1:]))
    nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='purple', width=2)

  # Add the original point
  plt.scatter(original_source.x, original_source.y, color='red', s=20, marker='s')  # s is the size, marker='s' is for square shape
  plt.text(original_source.x, original_source.y, "source", horizontalalignment='center', verticalalignment='center', color='black', fontsize=12)
  # Add the destination point
  plt.scatter(original_destination.x, original_destination.y, color='green', s=20, marker='s')  # s is the size, marker='s' is for square shape
  plt.text(original_destination.x, original_destination.y, "destination", horizontalalignment='center', verticalalignment='center', color='black', fontsize=12)

  # Define the zoom region (adjust these values to fit your region of interest)
  x_min = min(original_source.x, original_destination.x) - 100
  x_max = max(original_source.x, original_destination.x) + 100
  y_min = min(original_source.y, original_destination.y) - 100
  y_max = max(original_source.y, original_destination.y) + 100

  # Set the axis limits to zoom in on the region of interest
  plt.xlim(x_min, x_max)
  plt.ylim(y_min, y_max)

  # Other config
  plt.title('Pedestrian Network Graph')
  plt.xlabel('Longitude')
  plt.ylabel('Latitude')

  legend_elements = [
    Line2D([0], [0], color='green', lw=2, label='Shortest by Time'),
    Line2D([0], [0], color='purple', lw=2, label='Shortest by Length')
  ]
  plt.legend(handles=legend_elements, loc='best')

  if save_as:
    plt.savefig(save_as)
  plt.show()
