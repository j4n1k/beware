import numpy as np
from solver.slap_models import SLAP, SLAP_PA, SLAP_QA
import argparse

parser = argparse.ArgumentParser()
# params
parser.add_argument('--depot_location', default=0, type=int,
                    help='Depot Location')
parser.add_argument('--slap_model', default="QA", type=str,
                    help='SLAP model used for optimization: PA/QA')
parser.add_argument('--instance', default="test", type=str)

params = parser.parse_args()
# Params
depot = params.depot_location
d = None
products = None
w = None
storage_locs = None

if params.instance == "test":
    products = [0, 1, 2, 3]
    storage_locs = [0, 1, 2, 3]

    # Flow matrix (between assignees)
    w = np.array([[0, 3, 0, 2],
                  [3, 0, 0, 1],
                  [0, 0, 0, 4],
                  [2, 1, 4, 0]])

    # Distance matrix (between assignments)
    d = np.array([[0, 22, 53, 53],
                  [22, 0, 40, 62],
                  [53, 40, 0, 55],
                  [53, 62, 55, 0]])

if params.slap_model == "QA":
    slap = SLAP_QA(d, products, w, storage_locs, depot)
    slap.report()

# elif params.slap_model == "PA":
    # slap = SLAP_PA(d, products, w, product_pairs_frequency, storage_locs, depot)
