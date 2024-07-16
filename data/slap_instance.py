import numpy as np


class SLAPInstance:
    def __init__(self, source):
        self.source = source

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

        product_frequency = {}
        for i in range(len(storage_locs)):
            product_frequency[i] = product_pairs_frequency[i].sum()

        return (distance_mat, products,
                product_pairs_frequency,
                product_frequency, storage_locs)
