import random

import gurobipy as gp
from gurobipy import GRB


class SLAP:
    def __init__(self, dist_mat, products, product_frequency, storage_locs, depot):
        self.assignment = None
        self.dist_mat = dist_mat
        self.products = products
        self.product_frequency = product_frequency
        self.storage_locs = storage_locs
        self.depot = depot
        self.model = None
        self.solved = False
        self.y_i_j = None

    def build_model(self):
        pass

    def solve(self):
        pass

    def report(self):
        pass


class SLAPDIST(SLAP):
    def build_model(self):
        # decision variables
        self.model = gp.Model("SLAP")
        self.y_i_j = {}
        self.products = list(self.products)
        for i in range(len(self.storage_locs)):
            if i >= len(self.products):
                self.product_frequency[i] = 0
        self.products = [i for i in range(len(self.storage_locs))]

        for i in self.products:
            for j in self.storage_locs:
                self.y_i_j[i, j] = self.model.addVar(vtype=GRB.BINARY, name=f"Produkt{i}_an_LP_{j}")

        self.model.setObjective(gp.quicksum(self.y_i_j[i,j] * self.dist_mat[self.depot, j] * self.product_frequency[i] for i in self.products for j in self.storage_locs))

        for j in self.storage_locs:
            self.model.addConstr(gp.quicksum(self.y_i_j[i, j] for i in self.products) == 1, name=f"Lagerplatz_{i}_constraint")

        for i in self.products:
            self.model.addConstr(gp.quicksum(self.y_i_j[i, j] for j in self.storage_locs) == 1, name=f"Produkt_{j}_constraint")
    
    def solve(self):
        self.build_model()
        self.model.optimize()
        self.solved = True

    def report(self):
        assignment = []
        if not self.solved:
            self.solve()

        # Print the optimal solution
        if self.model.status == GRB.OPTIMAL:
            print("Optimal Solution Found:")
            for i in self.products:
                for loc, j in enumerate(self.storage_locs):
                    if self.y_i_j[i, j].x > 0.5:  # Check if the variable is assigned to 1 (approximately)
                        print(f"Item {i} stored at storage location {j}")
                        assignment.append(j) 
            self.assignment = assignment
        else:
            print("No optimal solution found.")
            

class SLAP_PA(SLAP):
    """
    Class to solve the SLAP with product affinity objective.
    """
    def build_model(self):
        # decision variables
        self.model = gp.Model("SLAP_PA")
        self.y_i_j = {}
        for i in self.products:
            for j in self.storage_locs:
                self.y_i_j[i, j] = self.model.addVar(vtype=GRB.BINARY, name=f"Product{i}_at_SL_{j}")

        self.model.setObjective(
            gp.quicksum(
                self.y_i_j[h, j] * self.y_i_j[i, k] * self.dist_mat[j, k] * self.product_pairs_frequency[h][i]
                for h in self.products 
                for i in self.products 
                for j in self.storage_locs 
                for k in self.storage_locs
                ) + gp.quicksum(
                    self.y_i_j[i,j] * self.dist_mat[0, j] * self.product_frequency[i] 
                    for i in self.products 
                    for j in self.storage_locs),  
                    GRB.MINIMIZE)
        for j in self.storage_locs: 
            self.model.addConstr(gp.quicksum(self.y_i_j[i, j] for i in self.products) == 1, name=f"Storage Location{i}_constraint")

        for i in self.products:
            self.model.addConstr(gp.quicksum(self.y_i_j[i, j] for j in self.storage_locs) == 1, name=f"Product{j}_constraint")
    
    def solve(self):
        self.build_model()
        self.model.optimize()
        self.solved = True

    def report(self):
        if not self.solved:
            self.solve()

        # Print the optimal solution
        if self.model.status == GRB.OPTIMAL:
            print("Optimal Solution Found:")
            for i in self.products:
                for loc, j in enumerate(self.storage_locs):
                    if self.y_i_j[i, j].x > 0.5:  # Check if the variable is assigned to 1 (approximately)
                        print(f"Item {i} stored at storage location {j}")
        else:
            print("No optimal solution found.")

class SLAP_QA(SLAP):
    """
    Class to solve the SLAP with product affinity objective.
    """
    def build_model(self):
        # decision variables
        self.model = gp.Model("SLAP_QA")
        self.y_i_j = {}
        for i in self.products:
            for j in self.storage_locs:
                self.y_i_j[i, j] = self.model.addVar(vtype=GRB.BINARY, name=f"Product{i}_at_SL_{j}")

        self.model.setObjective(
            gp.quicksum(
                self.y_i_j[h, j] * self.y_i_j[i, k] * self.dist_mat[j, k] * self.product_pairs_frequency[h][i]
                for h in self.products 
                for i in self.products 
                for j in self.storage_locs 
                for k in self.storage_locs
                ), GRB.MINIMIZE)
        for j in self.storage_locs: 
            self.model.addConstr(gp.quicksum(self.y_i_j[i, j] for i in self.products) == 1, name=f"Storage Location{i}_constraint")

        for i in self.products:
            self.model.addConstr(gp.quicksum(self.y_i_j[i, j] for j in self.storage_locs) == 1, name=f"Product{j}_constraint")
    
    def solve(self):
        self.build_model()
        self.model.optimize()
        self.solved = True

    def report(self):
        if not self.solved:
            self.solve()

        # Print the optimal solution
        if self.model.status == GRB.OPTIMAL:
            print("Optimal Solution Found:")
            for i in self.products:
                for loc, j in enumerate(self.storage_locs):
                    if self.y_i_j[i, j].x > 0.5:  # Check if the variable is assigned to 1 (approximately)
                        print(f"Item {i} stored at storage location {j}")
        else:
            print("No optimal solution found.")


class SLAPRAND(SLAP):
    def build_model(self):
        self.products = list(self.products)
        for i in range(len(self.storage_locs)):
            if i >= len(self.products):
                self.product_frequency[i] = 0
        self.products = [i for i in range(len(self.storage_locs))]

    def solve(self):
        self.build_model()
        random.shuffle(self.storage_locs)
        self.assignment = [storage_loc for storage_loc in self.storage_locs]

    def report(self):
        self.solve()

