import numpy as np
from data.slap_instance import SLAPInstance
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

instance = SLAPInstance(params.instance)
(distance_mat, products, product_pairs_frequency,
 product_frequency, storage_locs) = instance.load_data()

depot = params.depot_location

if params.slap_model == "QA":
    slap = SLAP_QA(distance_mat, products, product_pairs_frequency, storage_locs, depot)
    slap.report()

elif params.slap_model == "PA":
    slap = SLAP_PA(distance_mat, products, product_frequency, product_pairs_frequency, storage_locs, depot)
    slap.report()
