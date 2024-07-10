import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt 

from layout_utils.layout import Layout

from collections import defaultdict
from copy import deepcopy

def sort_dict(dict_to_sort):
    return dict(sorted(dict_to_sort.items(), key=lambda x:x[1], reverse=True))

def get_products(orders):
    if type(orders) == list:
        products = []
        for order in orders:
            for p in order:
                if p not in products:
                    products.append(p)
        return products
    
    if type(orders) == pd.Series:
        return orders.unique()


def prepare_orders(orders_old, products_mapping):
    new_order = []
    for order in orders_old: 
        orderline = []
        for p in order:
            orderline.append(products_mapping[p])
        new_order.append(orderline)
    return new_order

def calc_product_freq(products, orders):
    product_frequency = {i : 0 for i in products}
    for order in orders:
        for p in order:
            product_frequency[p] += 1
    return product_frequency

def calc_product_affinity(orders):
# Create a dictionary to store the frequency of product pairs
    product_pairs_frequency = defaultdict(lambda: defaultdict(int))

    # Iterate through each order list
    for order in orders:
        # Generate all possible pairs of products in the order
        for i in range(len(order)):
            for j in range(i + 1, len(order)):
                product_pairs_frequency[order[i]][order[j]] += 1
                product_pairs_frequency[order[j]][order[i]] += 1
    return product_pairs_frequency

def render_warehouse(warehouse: Layout, assignment, product_frequency):
    storage_assignment = deepcopy(warehouse.layout_grid)
    walkable_locs = np.where(warehouse.layout_grid == 0)

    for x, y, z in zip(walkable_locs[0], walkable_locs[1], walkable_locs[2]):
        storage_assignment[x,y,z] = -100

    for i, loc in enumerate(assignment):
        storage_assignment[warehouse.nodes_list[loc]] = i 

    storage_frequence = deepcopy(warehouse.layout_grid)
    for i, loc in enumerate(assignment):
        storage_frequence[warehouse.nodes_list[loc]] = product_frequency[i]
    
    node_xyz = np.array([warehouse.pos_dict[v] for v in sorted(warehouse.graph)])
    edge_xyz = np.array([(warehouse.pos_dict[u], warehouse.pos_dict[v]) for u, v in warehouse.graph.edges()])

    data = []
    for x, y, z in zip(node_xyz.T[0], node_xyz.T[1], node_xyz.T[2]):
        data_point = storage_frequence[x,y,z]
        data.append(data_point)

    assignment_plt = []
    for x, y, z in zip(node_xyz.T[0], node_xyz.T[1], node_xyz.T[2]):
        assignment_point = storage_assignment[x,y,z]
        assignment_plt.append(assignment_point)

    trace = go.Scatter3d(customdata=np.stack((data,assignment_plt),axis=-1), hovertemplate = 'x: %{x}<br>y: %{y}<br>z: %{z}<br>Order Frequency: %{customdata[0]}<br>Product: %{customdata[1]}}',
        x = node_xyz.T[0], y = node_xyz.T[1], z = node_xyz.T[2],mode = 'markers', marker = dict(symbol="square",
            size = 12,
            color = data, # set color to an array/list of desired values
            colorscale = 'thermal')
        )
    layout = go.Layout(title = 'Warehouse Visualization')
    fig = go.Figure(data = [trace], layout = layout)
    fig.update_traces(marker_size = 5)
    return fig