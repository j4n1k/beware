from copy import deepcopy
from warehouse_model.graph_tools import gen_pos
import numpy as np
import plotly.graph_objects as go

class Render:
    def __init__(self, inter_aisle_dist,
                        inter_cell_dist,
                        node_index_mapping,
                        aisles, locations):
        self.inter_aisle_dist = inter_aisle_dist
        self.inter_cell_dist = inter_cell_dist
        self.node_index_mapping = node_index_mapping
        self.aisles = aisles
        self.locations = locations

def create_layout_array(inter_aisle_dist,
                        inter_cell_dist,
                        node_index_mapping,
                        aisles, locations):
    layout_array = np.full((aisles * int(inter_aisle_dist), locations * int(inter_cell_dist)), -1)

    for node, index in node_index_mapping.items():
        x = node[0]
        y = node[1]
        layout_array[x, y] = index
    return layout_array


def create_viz_arrays(layout_array,
                      index_node_mapping,
                      assignment,
                      product_frequency):
    storage_assignment = deepcopy(layout_array)
    walkable_locs = np.where(layout_array == -1)

    for x, y, in zip(walkable_locs[0], walkable_locs[1]):
        storage_assignment[x, y] = -100

    for i, loc in enumerate(assignment):
        storage_assignment[
            index_node_mapping[loc][0],
            index_node_mapping[loc][1]] = i

    storage_frequency = deepcopy(layout_array)
    for i, loc in enumerate(assignment):
        storage_frequency[
            index_node_mapping[loc][0],
            index_node_mapping[loc][1]] = product_frequency[i]
    return storage_assignment, storage_frequency


def render_warehouse(graph,
                     storage_frequency,
                     storage_assignment):
    pos_dict = gen_pos(graph)
    node_xyz = np.array([pos_dict[v] for v in sorted(graph)])
    edge_xyz = np.array([(pos_dict[u], pos_dict[v]) for u, v in graph.edges()])

    data = []
    for x, y in zip(node_xyz.T[0], node_xyz.T[1]):
        data_point = storage_frequency[x, y]
        data.append(data_point)

    assignment_plt = []
    for x, y in zip(node_xyz.T[0], node_xyz.T[1]):
        assignment_point = storage_assignment[x, y]
        assignment_plt.append(assignment_point)

    trace = go.Scatter(customdata=np.stack((data, assignment_plt), axis=-1),
                         hovertemplate='x: %{x}<br>y: %{y}<br>z: %{z}<br>Order Frequency: %{customdata[0]}<br>Product: %{customdata[1]}}',
                         x=node_xyz.T[0], y=node_xyz.T[1], mode='markers', marker=dict(symbol="square",
                                                                                                        size=12,
                                                                                                        color=data,
                                                                                                        # set color to an array/list of desired values
                                                                                                        colorscale='thermal')
                         )
    layout = go.Layout(title='Warehouse Visualization')
    fig = go.Figure(data=[trace], layout=layout)
    fig.update_traces(marker_size=5)
    return fig
