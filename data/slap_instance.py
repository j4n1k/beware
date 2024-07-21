import numpy as np
import networkx as nx


class SLAPInstance:
    def __init__(self, params):
        self.source = params.instance
        self.n_locations = params.n_locations
        self.n_aisles = params.n_aisles
        self.n_products = params.n_products
        self.depot = params.depot_location
        self.inter_cell_dist = params.inter_cell_dist
        self.inter_aisle_dist = params.inter_aisle_dist

    def load_data(self):
        distance_mat = None
        products = None
        product_pairs_frequency = None
        storage_locs = None

        if self.source == "test":
            products = [0, 1, 2, 3]
            storage_locs = [0, 1, 2, 3]

            # Flow matrix (between assignees)
            product_pairs_frequency = np.array([[0, 3, 0, 2],
                                                [3, 0, 0, 1],
                                                [0, 0, 0, 4],
                                                [2, 1, 4, 0]])

            # Distance matrix (between assignments)
            distance_mat = np.array([[0, 22, 53, 53],
                                    [22, 0, 40, 62],
                                    [53, 40, 0, 55],
                                    [53, 62, 55, 0]])

        if self.source == "generated":
            G = self.generate_graph()
            distance_mat = self.gen_dist_mat(G)

        product_frequency = {}
        for i in range(len(storage_locs)):
            product_frequency[i] = product_pairs_frequency[i].sum()

        return (distance_mat, products,
                product_pairs_frequency,
                product_frequency, storage_locs)

    def generate_graph(self):
        aisles = self.n_aisles
        locations = self.n_locations
        inter_cell_dist = self.inter_cell_dist
        inter_aisle_dist = self.inter_aisle_dist
        G = nx.Graph()
        depot = self.depot_location
        G.add_node(depot)  # depot

        start = 1
        last_aisle_start = (start, 1, 0)
        last_aisle_end = (start, 2 + locations, 0)
        G.add_edge(depot, (7, 1, 0), weight=1.5)
        for a in range(aisles):
            aisle_start = (start, 1, 0)
            aisle_end = (start, 2 + locations, 0)
            G.add_node(aisle_start)
            G.add_node(aisle_end)
            # if a > 0:
            last_mid = aisle_start
            for l in range(locations):
                location_left = (start - 1, l + 2, 0)
                location_right = (start + 1, l + 2, 0)
                location_mid = (start, l + 2, 0)

                G.add_node(location_left)
                G.add_node(location_right)
                G.add_node(location_mid)

                G.add_edge(location_left, location_mid, weight=1)
                G.add_edge(location_right, location_mid, weight=1)

                G.add_edge(last_mid, location_mid, weight=inter_cell_dist)
                last_mid = location_mid

            G.add_edge(last_mid, aisle_end, weight=1)

            G.add_edge(last_aisle_start, aisle_start, weight=inter_aisle_dist)
            G.add_edge(last_aisle_end, aisle_end, weight=inter_aisle_dist)
            last_aisle_start = aisle_start
            last_aisle_end = aisle_end
            start += 3
        return G

    def gen_dist_mat(self, G):
        A = nx.adjacency_matrix(G).tolil()
        dist_mat = scipy.sparse.csgraph.floyd_warshall(A, directed=False, unweighted=False)
        #self.predecessors = predecessors
        # np.save(path, dist_mat)
        return dist_mat

    def create_graph(self):
        layout_info = instance.general_info
        aisles = int(layout_info["NUM_AISLES"])
        locations = int(layout_info["NUM_CELLS"])
        inter_cell_dist = float(layout_info["DISTANCE_CELL_TO_CELL"])
        inter_aisle_dist = float(layout_info["DISTANCE_AISLE_TO_AISLE"])
        G = nx.Graph()
        depot = (int(layout_info["DEPOT_AISLE"]), 0, 0)
        G.add_node(depot)  # depot

        start = 1
        last_aisle_start = (start, 1, 0)
        last_aisle_end = (start, 2 + locations, 0)
        G.add_edge(depot, (7, 1, 0), weight=1.5)
        for a in range(aisles):
            aisle_start = (start, 1, 0)
            aisle_end = (start, 2 + locations, 0)
            G.add_node(aisle_start)
            G.add_node(aisle_end)
            # if a > 0:
            last_mid = aisle_start
            for l in range(locations):
                location_left = (start - 1, l + 2, 0)
                location_right = (start + 1, l + 2, 0)
                location_mid = (start, l + 2, 0)

                G.add_node(location_left)
                G.add_node(location_right)
                G.add_node(location_mid)

                G.add_edge(location_left, location_mid, weight=1)
                G.add_edge(location_right, location_mid, weight=1)

                G.add_edge(last_mid, location_mid, weight=inter_cell_dist)
                last_mid = location_mid

            G.add_edge(last_mid, aisle_end, weight=1)

            G.add_edge(last_aisle_start, aisle_start, weight=inter_aisle_dist)
            G.add_edge(last_aisle_end, aisle_end, weight=inter_aisle_dist)
            last_aisle_start = aisle_start
            last_aisle_end = aisle_end
            start += 3