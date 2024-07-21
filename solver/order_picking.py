import heapq
from typing import List

import networkx as nx
import numpy as np


class Routing:
    def __init__(self,
                 graph,
                 start,
                 dist_mat,
                 assignment,
                 index_node_mapping,
                 node_index_mapping):
        self.graph: nx.Graph = graph
        self.dist_mat: np.array = dist_mat
        self.assignment = assignment
        self.index_node_mapping = index_node_mapping
        self.node_index_mapping = node_index_mapping
        self.start = start

    def build_ordered_list(self, order: List[List[int]]):
        aisle_queue = []
        for line in order:
            item = line[0]
            qty = line[1]
            storage_index = self.assignment[item]
            storage_node = self.index_node_mapping[storage_index]
            heapq.heappush(aisle_queue, storage_node)
        return aisle_queue

    def aisle_order(self, start: tuple[int, int, int]):
        aisle_queue = []
        G = self.graph
        x_coords = [node[0] for node in G.nodes]
        unique_x_coords = list(set(x_coords))
        for coord in unique_x_coords:
            location = (coord, start[1], 0)
            source = self.node_index_mapping[start]
            target = self.node_index_mapping[location]
            dist = self.dist_mat[source][target]
            pos = (dist, coord)
            heapq.heappush(aisle_queue, pos)
        return aisle_queue

    def calculate_tour_length(self, path: List):
        tour_length = 0
        for i in range(len(path) - 1):
            tour_length += self.graph[path[i]][path[i + 1]]['weight']
        return tour_length

    def s_shape_routing(self, order: List[List[int]], node_index_mapping):
        distance = 0
        route = []

        order_queue = self.build_ordered_list(order)
        ordered = []
        for pos in range(len(order_queue)):
            ordered.append(heapq.heappop(order_queue))
        aisle_queue = self.aisle_order(self.start)

        while order_queue:
            location = heapq.heappop(order_queue)
            x_coord = self.node_index_mapping[self.start]
            y_coord = self.node_index_mapping[location]
            dist = self.dist_mat[x_coord, y_coord]
            distance += dist
            start = location
        return distance

    def tsp_approximation(self, order):
        order_nodes = self.build_ordered_list(order)
        tsp_path = nx.approximation.traveling_salesman_problem(self.graph, nodes=order_nodes)
        tour_length = self.calculate_tour_length(tsp_path)
        return tour_length
