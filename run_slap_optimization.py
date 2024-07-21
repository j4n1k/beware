from copy import deepcopy
import heapq
from typing import List

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from data.slap_instance import SLAPInstance
from data.instance_loader import InstanceLoader

from render import create_layout_array, create_viz_arrays, render_warehouse
from solver.order_picking import Routing
from solver.slap_models import SLAPDIST, SLAP_PA, SLAP_QA, SLAPRAND, SLAP

import argparse



parser = argparse.ArgumentParser()
# params
parser.add_argument('--depot_location', default=0, type=int,
                    help='Depot Location')
parser.add_argument('--slap_model', default="ABC", type=str,
                    help='SLAP model used for optimization: PA/QA')
parser.add_argument('--instance', default="test", choices=['test', 'generated', 'henn'], type=str)

parser.add_argument('--n_locations', default=5, type=int,
                    help='Number of storage locations')

parser.add_argument('--n_aisles', default=5, type=int,
                    help='Number of aisles')

parser.add_argument('--n_products', default=5, type=int,
                    help='Number of articles')

parser.add_argument('--inter_cell_dist', default=1, type=int,
                    help='inter_cell_dist')

parser.add_argument('--inter_aisle_dist', default=2, type=int,
                    help='inter_aisle_dist')
params = parser.parse_args()

# instance = SLAPInstance(params)
# (distance_mat, products, product_pairs_frequency,
#  product_frequency, storage_locs) = instance.load_data()

instance = InstanceLoader()
instance.load_instance()
instance.print_instance()
distance_mat = instance.distance_mat
products = instance.articles_list
product_pairs_frequency = instance.product_pairs_frequency
product_frequency = instance.product_frequency
storage_locs = instance.storage_locations
layout_info = instance.general_info
aisles = int(layout_info["NUM_AISLES"])
locations = int(layout_info["NUM_CELLS"])
inter_cell_dist = float(layout_info["DISTANCE_CELL_TO_CELL"])
inter_aisle_dist = float(layout_info["DISTANCE_AISLE_TO_AISLE"])

depot = params.depot_location
slap = SLAP(distance_mat, products, product_frequency, storage_locs, depot)
if params.slap_model == "ABC":
    slap = SLAPDIST(distance_mat, products, product_frequency, storage_locs, depot)
    slap.report()

if params.slap_model == "QA":
    slap = SLAP_QA(distance_mat, products, product_pairs_frequency, storage_locs, depot)
    slap.report()

elif params.slap_model == "PA":
    slap = SLAP_PA(distance_mat, products, product_frequency, product_pairs_frequency, storage_locs, depot)
    slap.report()

elif params.slap_model == "random":
    slap = SLAPRAND(distance_mat, products, product_frequency, storage_locs, depot)
    slap.report()

routing_solver = Routing(instance.graph,
                         (0, 0, 0),
                         instance.distance_mat,
                         slap.assignment,
                         instance.index_node_mapping,
                         instance.node_index_mapping)
route_cost = 0
for order in instance.orders:
    tour_length = routing_solver.tsp_approximation(order)
    route_cost += tour_length

print(route_cost)

layout_array = create_layout_array(inter_aisle_dist,
                                   inter_cell_dist,
                                   instance.node_index_mapping,
                                   aisles,
                                   locations)


storage_assignment, storage_frequency = create_viz_arrays(layout_array,
                                                          instance.index_node_mapping,
                                                          slap.assignment,
                                                          instance.product_frequency)


fig = render_warehouse(instance.graph, storage_frequency, storage_assignment)
fig.show()

warehouse_heatmap = px.imshow(storage_frequency)
warehouse_heatmap.show()
