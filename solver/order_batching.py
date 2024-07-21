# n_orders = len(instance.orders)
# n_batches = 2
# #capacity = int(instance.general_info["PICKER_CAPACITY"])
# capacity = 3
# aisles = int(instance.general_info["NUM_AISLES"])
# inter_aisle_dist = float(instance.general_info["DISTANCE_AISLE_TO_AISLE"])
# aisle_length = (int(instance.general_info["NUM_CELLS"]) *
#                 int(instance.general_info["DISTANCE_CELL_TO_CELL"]))

import pyomo.environ as pyo

class Batching:
    def __init__(self, aisles,
                 orders,
                 n_batches,
                 capacity,
                 inter_aisle_dist,
                 aisle_length,
                 order_weights,
                 skus, articles):
        self.n_orders = len(orders)
        self.orders = orders
        self.n_batches = n_batches
        self.capacity = capacity
        self.aisles = aisles
        self.inter_aisle_dist = inter_aisle_dist
        self.aisle_length = aisle_length
        self.order_weights = order_weights
        self.articles = articles
        self.skus = skus

    def build_model(self):
        pass

    def solve(self):
        pass

    def report(self):
        pass


class BatchingSShape(Batching):
    def __init__(self, aisles, orders, n_batches, capacity, inter_aisle_dist, aisle_length):
        super().__init__(aisles, orders, n_batches, capacity, inter_aisle_dist, aisle_length)

    def build_model(self):
        max_aisle_dist = {}
        order_weights = {}
        for order_idx, order in enumerate(self.orders):
            max_aisle_dist[order_idx + 1] = {}
            order_weights[order_idx + 1] = []
            for line in order:
                item = line[0]
                quantity = line[1]
                aisle = self.skus[item]["aisle"]
                cell = self.skus[item]["cell"]
                side = self.skus[item]["side"]
                if aisle not in max_aisle_dist[order_idx + 1].keys():
                    max_aisle_dist[order_idx + 1][aisle] = []
                max_aisle_dist[order_idx + 1][aisle].append(cell)
                order_weights[order_idx + 1].append(self.articles[item]["weight"])

        model = pyo.ConcreteModel("BATCHING_TRAVERSAL")
        model.Aisles = pyo.RangeSet(0, self.aisles-1)
        model.Orders = pyo.RangeSet(1, self.n_orders)
        model.Batches = pyo.RangeSet(1, self.n_batches)
        dik = {}
        for order in max_aisle_dist.keys():
            for aisle in max_aisle_dist[order].keys():
                max_dist = max(max_aisle_dist[order][aisle])
                dik[(order, aisle)] = max_dist

        weights = []
        for order in self.order_weights.keys():
            weights.append(sum(self.order_weights[order]))
        items_per_order = []
        for order in self.order_weights.keys():
            items_per_order.append(len(self.order_weights[order]))
        model.mi = pyo.Param(model.Orders, initialize=dict(enumerate(items_per_order, start=1)))
        model.dik = pyo.Param(model.Orders, model.Aisles, initialize=dik)
        model.M = pyo.Param(within=pyo.NonNegativeReals, initialize=1000)
        model.vj = pyo.Var(model.Batches, domain=pyo.Integers)

        model.yjk = pyo.Var(model.Batches, model.Aisles, domain=pyo.Binary)
        model.pjk = pyo.Var(model.Batches, model.Aisles, domain=pyo.Binary)

        model.cj = pyo.Var(model.Batches, domain=pyo.Binary)

        model.xij = pyo.Var(model.Orders, model.Batches, domain=pyo.Binary)
        model.hjR = pyo.Var(model.Batches, domain=pyo.PositiveReals)
        model.hjL = pyo.Var(model.Batches, domain=pyo.PositiveReals)
        model.ujk = pyo.Var(model.Batches, model.Aisles, domain=pyo.PositiveReals)

        M = 1000

        def objective(model):
            return 2 * pyo.quicksum(
                model.ujk[j,k] for j in model.Batches for k in model.Aisles
        )
        + 2 * pyo.quicksum(
            model.hjR[j] * model.hjL[j] for j in model.Batches
        )
        + 2 * self.aisle_length * pyo.quicksum(
            model.vj[j] - model.cj[j] for j in model.Batches
        )

        model.obj = pyo.Objective(rule=objective, sense=pyo.minimize)

        def constraint_batch_assignment(model, i_order):
            return pyo.quicksum(model.xij[i_order,j] for j in model.Batches) == 1
        model.constraint_batch_assignment = pyo.Constraint(model.Orders, rule=constraint_batch_assignment)

        def constraint_batch_capacity(model, i_order):
            return pyo.quicksum(model.mi[i_order]*model.xij[i_order,j] for j in model.Batches) <= self.capacity
        model.constraint_batch_capacity = pyo.Constraint(model.Orders, rule=constraint_batch_capacity)

        def constraint_batch_guarantee(model, i_order, j):
            return model.xij[i_order,j] <= model.xij[j,j]
        model.constraint_batch_guarantee = pyo.Constraint(model.Orders, model.Batches, rule=constraint_batch_guarantee)

        def constraint_1_1(model, j, k, i):
            return model.yjk[j,k] <= pyo.quicksum(
                model.dik[i,k] * model.xij[i,j]
                for j in model.Batches
                for k in model.Aisles)
        model.constraint_1_1 = pyo.Constraint(model.Batches, model.Aisles, model.Orders, rule=constraint_1_1)

        def constraint_1_2(model, j, k, i):
            return pyo.quicksum(
                model.dik[i,k] * model.xij[i,j]
                for j in model.Batches
                for k in model.Aisles) <= M*model.yjk[j,k]
        model.constraint_1_2 = pyo.Constraint(model.Batches, model.Aisles, model.Orders, rule=constraint_1_2)

        def constraint_2(model, k, j):
            return ((k+1)-k) * self.inter_aisle_dist * model.yjk[j,k] <= model.hjR[j]
        model.constraint_2 = pyo.Constraint(model.Aisles, model.Batches, rule=constraint_2)

        def constraint_3(model, k, j):
            return ((k+1)-k) * self.inter_aisle_dist * model.yjk[j,k] <= model.hjL[j]
        model.constraint_3 = pyo.Constraint(model.Aisles, model.Batches, rule=constraint_3)

        def constraint_4(model, j):
            return pyo.quicksum(model.yjk[j,k] + model.cj[j] for k in model.Aisles) == 2 * model.vj[j]
        model.constraint_4 = pyo.Constraint(model.Batches, rule=constraint_4)

        def constraint_5(model, j, k, i):
            return pyo.quicksum(
                model.dik[i,k] * model.xij[i,j]
                for j in model.Batches
                for k in model.Aisles) <= model.M*model.yjk[j,k]
        model.constraint_5 = pyo.Constraint(model.Batches, model.Aisles, model.Orders, rule=constraint_5)

        # def constraint_6(model):
        #     return model.yjk[j,k] - pyo.quicksum()
        # model.constraint_6 = pyo.Constraint(rule=constraint_6)