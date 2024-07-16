import numpy as np
import networkx as nx
import scipy
from warehouse_model.graph_tools import gen_graph, gen_pos
from copy import deepcopy
import os

class Layout:
    """
    Class to create a warehouse layout. The layout is represented as a numpy array
    For routing the layout is converted to a graph.
    Takes a number of rows and columns and spreads storage racks with walkalble aisles in between
    Racks can either be standard or double deep
    Alternatively a custo, grid can be specified
    Input
    n_rows: Number of rows 
    n_columns: Number of columns
    n_levels: Height
    double_deep: If racks are standard or double deep storage
    custom_grid: If a custom layout is provided
    grid: The custom layout as a numpy array
    """
    def __init__(self, n_rows, n_columns, n_levels, double_deep, custom_grid, grid) -> None:
        if custom_grid == True:
            self.layout_grid = grid
        else:
            self.layout_grid = self.gen_layout(n_rows, n_columns, n_levels, double_deep)

        self.graph = gen_graph(self.layout_grid, double_deep)
        self.pos_dict = gen_pos(self.graph)
        self.gen_storage_locs()
        self.gen_access_mapping()
        self.all_aisles = self.gen_aisles()
        self.aisles_start_end = self.gen_aisle_start_end()
        self.nodes_list = list(self.graph.nodes)
        self.predecessors = None
        self.dist_mat = None
        self.storage_assignment = None
        

    def gen_layout(self, n_rows=10, n_columns=10, n_levels=3, double_deep=True):

        if double_deep == True:
            layout_grid = np.ones((n_rows, n_columns, n_levels)) * -1
            for i in range(n_levels):
                layout_grid[:, ::3,i] = 0
        elif double_deep == False:
            layout_grid = np.zeros((n_rows, n_columns, n_levels))
            layout_grid[:, ::2] = -1
        layout_grid[0,:] = 0
        layout_grid[n_rows - 1,:] = 0
        return layout_grid

    def gen_storage_locs(self):
        storage_locs = []
        all_locations = np.where(self.layout_grid == -1)
        for loc in range(len(all_locations[0])):
            x_storage = all_locations[0][loc]
            y_storage = all_locations[1][loc]
            z_storage = all_locations[2][loc]

            storage_locs.append((x_storage, y_storage, z_storage))
        self.storage_locs = storage_locs

    def gen_access_mapping(self):
        access_mapping = {}

        all_locations = np.where(self.layout_grid == -1)
        for loc in range(len(all_locations[0])):
            x_storage = all_locations[0][loc]
            y_storage = all_locations[1][loc]
            z_storage = all_locations[2][loc]

            if self.layout_grid[x_storage, y_storage - 1, 0] == 0:
                access = (x_storage, y_storage - 1, 0)
                aisle = access[1]
            elif self.layout_grid[x_storage, y_storage + 1, 0] == 0:
                access = (x_storage, y_storage + 1, 0)
                aisle = access[1]
            access_mapping[(x_storage, y_storage, z_storage)] = {"aisle" : aisle, "access": access}
        
        self.access_mapping = access_mapping

    def gen_aisles(self):   
        all_aisles = []
        for loc in self.access_mapping:
            if self.access_mapping[loc]["aisle"] not in all_aisles:
                all_aisles.append(self.access_mapping[loc]["aisle"])
        return all_aisles

    def gen_aisle_start_end(self):
        aisles_start_end = {i: {"start": 0, "end": 0} for i in self.all_aisles}
        for ailes in self.all_aisles:
            aisles_start_end[ailes]["start"] = (0, ailes, 0)
            aisles_start_end[ailes]["end"] = (self.layout_grid.shape[0] - 1, ailes, 0)
        return aisles_start_end

            
    def gen_dist_mat(self, path):
        #distance_mat = nx.floyd_warshall_numpy(self.graph, self.nodes_list)
        A = nx.adjacency_matrix(self.graph).tolil()
        dist_mat = scipy.sparse.csgraph.floyd_warshall( A, directed=False, unweighted=False)
        self.dist_mat = dist_mat
        #self.predecessors = predecessors
        np.save(path, dist_mat)
        return dist_mat

    def load_dist_mat(self, dist_mat):
        self.dist_mat = dist_mat

    def add_assignment(self, assignment):
        self.storage_assignment = assignment
    
    def get_storage_loc(self, loc):
        return self.nodes_list[loc]