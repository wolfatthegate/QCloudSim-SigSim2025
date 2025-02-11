# utility_functions/graph_viz.py

import networkx as nx
import matplotlib.pyplot as plt

def display_graph(QDevice, figsize=(5, 3), title = '', node_size=700, font_size=8, with_labels=True):
    """
    Visualize the connectivity of qubits.

    Parameters:
    QDevice : object
        The quantum device object containing topology information.
    figsize : tuple, optional
        The size of the figure for the plot (default is (5, 3)).
    """
    complete_title = f'{QDevice.name} - {QDevice.number_of_qubits} qubits'
    if title != '': 
        complete_title += f'\n{title}'
    
    plt.figure(figsize=figsize)
    nx.draw_networkx(QDevice.graph, QDevice.pos, node_color=QDevice.color_map, with_labels=with_labels, node_size=node_size, font_size=font_size)
    plt.title(complete_title)
    plt.show()