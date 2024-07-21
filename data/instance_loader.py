import numpy as np
import networkx as nx
import scipy

from collections import defaultdict


class InstanceLoader:
    def __init__(self):
        self.index_node_mapping = None
        self.node_index_mapping = None
        self.general_info = None
        self.articles = None
        self.articles_list = None
        self.skus = None
        self.orders = None
        self.product_frequency = None
        self.graph: nx.graph = None
        self.distance_mat: np.array = None
        self.product_pairs_frequency = None
        self.storage_locations = None

    @staticmethod
    def read_data(path=r"C:\Users\zm0714\Documents\Projekte\beware\data\instances\test"):
        file = open(path, "r")
        content = file.read()
        return content

    def load_instance(self):
        content = self.read_data()
        sections = content.split("SECTION")

        # Extracting and processing each section
        header = sections[0]
        article_data = sections[1].split("\n")[1:-1]
        sku_data = sections[2].split("\n")[1:-1]
        order_data = sections[3].split("\n")[1:-1]

        # Parsing header information
        header_info = {}
        for line in header.split("\n"):
            if line:
                if " : " in line:
                    key, value = line.split(" : ")
                    header_info[key.strip()] = value.strip()

        # Creating article dictionary
        articles = {}
        for line in article_data:
            parts = line.split()
            if " : " not in line:
                articles[int(parts[1])] = {"weight": int(parts[3])}

        # Creating SKU dictionary
        skus = {}
        for line in sku_data:
            parts = line.split()
            if not " : " in line:
                skus[int(parts[1])] = {
                    "aisle": int(parts[3]),
                    "cell": int(parts[5]),
                    "quantity": int(parts[7]),
                    "side": parts[9]
                }

        # Creating orders list
        orders = []
        current_order = []
        for line in order_data:
            line = line.strip()
            if line.startswith("NUM_ARTICLES_IN_ORDER"):
                # If there's a current order being processed, add it to orders
                if current_order:
                    orders.append(current_order)
                    current_order = []
            elif line.startswith("ID"):
                parts = line.split()
                product_id = int(parts[1])
                quantity = int(parts[3])
                current_order.append([product_id, quantity])

        if current_order:
            orders.append(current_order)

        self.general_info = header_info
        self.skus = skus
        self.orders = orders
        self.articles = articles
        self.articles_list = articles.keys()
        self.graph = self.create_graph()
        self.distance_mat = self.gen_dist_mat(self.graph)
        self.product_frequency = self.calc_product_frequency()
        self.product_pairs_frequency = self.calc_product_affinity()
        self.storage_locations = [_ for _ in range(int(header_info["NUM_AISLES"]) * int(header_info["NUM_CELLS"]))]
        self.create_location_mapping()

    def create_graph(self):
        layout_info = self.general_info
        aisles = int(layout_info["NUM_AISLES"])
        locations = int(layout_info["NUM_CELLS"])
        inter_cell_dist = float(layout_info["DISTANCE_CELL_TO_CELL"])
        inter_aisle_dist = float(layout_info["DISTANCE_AISLE_TO_AISLE"])
        G = nx.Graph()

        start = 0
        last_aisle_start = (start, 0, 0)
        last_aisle_end = (start, locations - 1, 0)
        # # Mapping of nodes to indices
        node_index_mapping = {}
        index_node_mapping = []
        #
        index = 0
        for a in range(aisles):
            aisle_start = (start, 0, 0)
            aisle_end = (start, locations - 1, 0)

            if aisle_start not in G:
                G.add_node(aisle_start)
                node_index_mapping[aisle_start] = index
                index_node_mapping.append(aisle_start)
                index += 1

            if aisle_end not in G:
                G.add_node(aisle_end)
                node_index_mapping[aisle_end] = index
                index_node_mapping.append(aisle_end)
                index += 1

            last_node = aisle_start
            for l in range(locations):
                location_node = (start, l, 0)
                if location_node not in G:
                    G.add_node(location_node)
                    node_index_mapping[location_node] = index
                    index_node_mapping.append(location_node)
                    index += 1

                if last_node != location_node:
                    G.add_edge(last_node, location_node, weight=inter_cell_dist)
                last_node = location_node

            if last_node != aisle_end:
                G.add_edge(last_node, aisle_end, weight=1)

            if last_aisle_start is not None and last_aisle_end is not None:
                if last_aisle_start != aisle_start:
                    G.add_edge(last_aisle_start, aisle_start, weight=inter_aisle_dist)
                if last_aisle_end != aisle_end:
                    G.add_edge(last_aisle_end, aisle_end, weight=inter_aisle_dist)

            last_aisle_start = aisle_start
            last_aisle_end = aisle_end
            start += 2

        self.index_node_mapping = index_node_mapping
        self.node_index_mapping = node_index_mapping
        return G

    def gen_dist_mat(self, G):
        A = nx.adjacency_matrix(G, nodelist=self.index_node_mapping).tolil()
        dist_mat = scipy.sparse.csgraph.floyd_warshall(A, directed=False, unweighted=False)
        #self.predecessors = predecessors
        # np.save(path, dist_mat)
        return dist_mat

    def create_location_mapping(self):
        G = self.graph
        pos_dict = {}
        for node in G.nodes():
            pos_dict[node] = np.array([node[0], node[1], node[2]])

    def calc_product_frequency(self):
        product_frequency = {i: 0 for i in self.articles}
        for order in self.orders:
            for orderline in order:
                product_frequency[orderline[0]] += 1
        return product_frequency

    def calc_product_affinity(self):
        product_pairs_frequency = {}

        # Collect all unique products
        unique_products = set()
        for order in self.orders:
            for product in order:
                unique_products.add(product[0])

        # Initialize all possible pairs with zero, including self-pairs
        for product1 in unique_products:
            product_pairs_frequency[product1] = {}
            for product2 in unique_products:
                product_pairs_frequency[product1][product2] = 0

        # Iterate through each order list
        for order in self.orders:
            # Generate all possible pairs of products in the order, including self-pairs
            for i in range(len(order)):
                for j in range(i, len(order)):
                    product1, product2 = order[i][0], order[j][0]

                    # Update the frequency for product1 -> product2
                    product_pairs_frequency[product1][product2] += 1
                    if product1 != product2:
                        # Update the frequency for product2 -> product1, but only if they are different
                        product_pairs_frequency[product2][product1] += 1
        return product_pairs_frequency


    def print_instance(self):
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        print("Header Info:")
        pp.pprint(self.general_info)
        print("\nArticles:")
        pp.pprint(self.articles)
        print("\nSKUs:")
        pp.pprint(self.skus)
        print("\nOrders:")
        pp.pprint(self.orders)
