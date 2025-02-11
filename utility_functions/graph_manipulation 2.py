import threading
import networkx as nx
from itertools import combinations
import math
import random

graph_lock = threading.Lock()

def select_vertices(device, N, name):
    """
    Select the best combination of N vertices from the graph based on the color map and connectivity.

    Parameters:
    device : QuantumDevice 
        qdevice that job is assigned.
    N : int
        The number of vertices to select.
    name : str
        The name of the job for logging purposes.

    Returns:
    tuple or None
        The best combination of N vertices that minimizes the number of connected components in the remaining graph,
        or None if no suitable combination is found.
    """
    graph = device.graph
    color_map = device.color_map
    min_subgraphs = float('inf')
    best_combination = None
    i = 0
    with graph_lock:
        
        combin = math.comb(len(graph.nodes), N)       
        
#         print('combinations: ', combin)
        
        for combination in combinations(graph.nodes, N):
            glist = list(graph.nodes)
            skip = False

            for c in combination: 
                if color_map[glist.index(c)] != 'skyblue': 
                    skip = True
            if skip: 
                continue
            subgraph = graph.subgraph(combination)
            if nx.is_connected(subgraph):
                remaining_graph = graph.copy()
                remaining_graph.remove_nodes_from(combination)
                num_subgraphs = nx.number_connected_components(remaining_graph)
                if num_subgraphs < min_subgraphs:
                    min_subgraphs = num_subgraphs
                    best_combination = combination
            i += 1

#         print(f'Job #{name}. The best combination: {best_combination}')

    return best_combination


"""
To modify your code to select one connected subgraph of N vertices without iterating through all combinations, we can use BFS or DFS traversal. Start from any node and expand until you get a connected subgraph of size N.

Filter by the color map during traversal: Ensure that the vertices being considered match the desired color ('skyblue'). In that way, we don't have to iterate all the combination. 

"""

def select_vertices_fast(device, N, name):
    """
    Select a connected subgraph of N vertices from the graph based on the color map and connectivity.

    Parameters:
    device : QuantumDevice 
        qdevice that job is assigned.
    N : int
        The number of vertices to select.
    name : str
        The name of the job for logging purposes.

    Returns:
    list or None
        A connected subgraph of N vertices that match the color criteria, or None if no suitable subgraph is found.
    """
    
    graph = device.graph
    color_map = device.color_map
    # Filter the nodes by color ('skyblue') and create a list of candidate nodes
    candidate_nodes = [node for node in graph.nodes if color_map[list(graph.nodes).index(node)] == 'skyblue']

    if len(candidate_nodes) < N:
#         print(f"Not enough 'skyblue' nodes to form a subgraph of {N} nodes.")
        return None

    # Try to find a connected subgraph of size N using BFS or DFS
    for start_node in candidate_nodes:
        # Perform BFS or DFS starting from the current node
        connected_nodes = list(nx.bfs_edges(graph, start_node))  # You could also use dfs_edges if preferred
        subgraph_nodes = set([start_node])  # Start with the initial node
        
        for edge in connected_nodes:
            if len(subgraph_nodes) >= N:
                break
            # Add both nodes from the edge if they meet the 'skyblue' criteria
            if edge[1] in candidate_nodes:
                subgraph_nodes.add(edge[1])

        # If we have a connected subgraph of N nodes, return it
        if len(subgraph_nodes) == N:
            
#             print(f'Job #{name}. The selected connected subgraph: {subgraph_nodes}')

            return list(subgraph_nodes)
    
#     print(f'Job #{name}. No connected subgraph of {N} vertices found.')

    return None

def remove_connectivity(device, nodes, new_color):
    """
    Remove the connectivity of the specified nodes from the graph and update their colors.

    Parameters:
    device : QuantumDevice 
        qdevice that job is assigned.
    new_color : str
        The new color to assign to the specified nodes.

    Returns:
    list
        A list of edges that were removed from the graph.
    """
    graph = device.graph
    color_map = device.color_map
    
    with graph_lock:
        for i, node in enumerate(graph.nodes):
            if node in nodes: 
                color_map[i] = new_color

        edges_to_remove = []
        for node in nodes:
            for neighbor in list(graph.neighbors(node)):
                if neighbor not in nodes:
                    edges_to_remove.append((node, neighbor))
        graph.remove_edges_from(edges_to_remove)
    return edges_to_remove

def reconnect_nodes(device, selected_vertices):
    """
    Reconnect the specified nodes in the graph and update their colors.

    Parameters:
    device : QuantumDevice 
        qdevice that job is assigned.
    color_map : list
        A list containing colors for each node in the graph.
    edges : list
        The edges to be reconnected.
    selected_vertices : list
        The nodes to be updated and reconnected.

    Returns:
    None
    """
    graph = device.graph
    color_map = device.color_map
    edges = device.nodes
    
    with graph_lock:
        for i, node in enumerate(graph.nodes):
            if node in selected_vertices: 
                color_map[i] = 'skyblue'

        edges_to_reconnect = []    
        glist = list(graph.nodes)
        for e in edges:         
            node1 = e[0]       
            node2 = e[1]
            idx1 = glist.index(node1)
            idx2 = glist.index(node2)
            if color_map[idx1] == 'skyblue' and color_map[idx2] == 'skyblue': 
                edges_to_reconnect.append(e)

        graph.add_edges_from(edges_to_reconnect)
