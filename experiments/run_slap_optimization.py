from warehouse_model.layout import Layout
import numpy as np
from solver.slap_models import SLAP, SLAP_PA, SLAP_QA

# Params
depot = 0
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

slap = SLAP_QA(d, products, w, storage_locs, depot)

slap.report()
