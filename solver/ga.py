from typing import List, Tuple, Literal
from layout_utils.simulation import s_shape, stichgang
from copy import deepcopy
from collections import Counter 
from dataclasses import dataclass
import random
import numpy as np

from layout_utils.layout import Layout

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def create_data_model(dist_mat):
    """Stores the data for the problem."""
    data = {}
    data['distance_matrix'] = dist_mat
    data['num_vehicles'] = 1
    data['depot'] = 0
    return data


def print_solution(manager, routing, solution):
    """Prints solution on console."""
    print('Objective: {} miles'.format(solution.ObjectiveValue()))
    index = routing.Start(0)
    plan_output = 'Route for vehicle 0:\n'
    route_distance = 0
    while not routing.IsEnd(index):
        plan_output += ' {} ->'.format(manager.IndexToNode(index))
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    plan_output += ' {}\n'.format(manager.IndexToNode(index))
    print(plan_output)
    plan_output += 'Route distance: {}miles\n'.format(route_distance)

def fitness_qa(individual, dist_mat, product_affinity):
    affinity_score = 0
    for p in range(len(individual)):
        for p2 in range(len(individual)):
            if p == p2 or product_affinity[p][p2] == 0:
                continue
            else:
                affinity_score += product_affinity[p][p2] * dist_mat[individual[p]][individual[p2]]
    return affinity_score

def fitness_pf_pa(individual, dist_mat, product_frequency, product_affinity):
    affinity_score = 0
    for p in range(len(individual)):
        for p2 in range(len(individual)):
            if p == p2 or product_affinity[p][p2] == 0:
                continue
            else:
                affinity_score += product_affinity[p][p2] * dist_mat[individual[p]][individual[p2]]
    return sum(dist_mat[0][individual] * np.array(product_frequency)) + affinity_score

def fitness_vrp(individual, dist_mat, orders):
    costs = 0
    for order in orders:
        storage_locs_orders = np.array(individual)[order].tolist()
        storage_locs_orders.insert(0, 0)
        dist_mat_order = np.take(np.take(dist_mat, storage_locs_orders, 0), storage_locs_orders, 1)
        dist_mat_order = dist_mat_order.astype(int).tolist()

        data = create_data_model(dist_mat_order)

        # Create the routing index manager.
        manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                                data['num_vehicles'], data['depot'])

        # Create Routing Model.
        routing = pywrapcp.RoutingModel(manager)


        def distance_callback(from_index, to_index):
            """Returns the distance between the two nodes."""
            # Convert from routing variable Index to distance matrix NodeIndex.
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['distance_matrix'][from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)

        # Define cost of each arc.
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Setting first solution heuristic.
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

        # Solve the problem.
        solution = routing.SolveWithParameters(search_parameters)

        # Print solution on console.
        # if solution:
        #     print_solution(manager, routing, solution)
        costs += solution.ObjectiveValue()
    return costs

def find_duplicates(l):
    counts = dict(Counter(l))
    duplicates = {key:value for key, value in counts.items() if value > 1}
    return duplicates

def generate_genome(products, layout: Layout):
    chromosome = []
   
    locations_list = layout.storage_locs
    random.shuffle(locations_list)
    for i in range(len(products)):
        storage_loc = locations_list[i]
        chromosome.append(layout.nodes_list.index(storage_loc))
    return chromosome

def selection(population, scores, n=2):
    best_score = np.inf
    scores_np = np.array(scores)
    #print(scores_np)
    index_min = np.argpartition(scores_np, n)[:n]
    selected = [] 
    #print(index_min)
    for i in range(n):
        if scores[index_min[i]] < best_score:
            selected.append(population[index_min[i]])
    return selected

def naive_conflict_resolver(child, parents):
    duplicates = find_duplicates(child)
    present_locs = set(child)
    all_locs = set(parents[0])
    not_present = list(all_locs - present_locs)
    for dup in duplicates.keys():
        child[child.index(dup)] = not_present.pop(0)
    return child

def local_search_resolver(child, parents):
    #TODO
    pass

def random_point_crossover(parents):
    i = random.randint(0,len(parents[0]))
    child = parents[0][:i] + parents[1][i:]
    return child

def crossover(parents, x_method="random-point", conflict_resolver="naive"):
    if x_method == "random-point":
        child = random_point_crossover(parents)
    
    if conflict_resolver == "naive":
        child = naive_conflict_resolver(child, parents)
    return child


def mutation(to_mutate):
    idx_1, idx_2 = random.sample(range(0, len(to_mutate)-1), 2)
    node1 = to_mutate[idx_1]
    node2 = to_mutate[idx_2]
    to_mutate[idx_1] = node2
    to_mutate[idx_2] = node1
    return to_mutate

def mutation_move(to_mutate, n_products):
    idx_1, idx_2 = random.sample(range(0, len(to_mutate)-1), 2)
    node1 = to_mutate[idx_1]
    node2 = to_mutate[idx_2]
    to_mutate[idx_1] = node2
    to_mutate[idx_2] = node1
    all_products = [i for i in range(n_products)]
    to_draw = [x for x in all_products if x not in to_mutate]
    idx = random.randint(0, len(to_mutate)-1)
    new_product = random.sample(to_draw, 1)
    to_mutate[idx] = new_product[0]

    return to_mutate

def fitness_move(genome, assignment_prev, assignment_new, orders, warehouse: Layout, start: tuple[Literal, Literal, Literal]):
    assignment_prev = np.array(assignment_prev)
    assignment_test = deepcopy(assignment_prev)
    assignment_new = np.array(assignment_new)
    assignment_test[genome] = assignment_new[genome]

    warehouse.storage_assignment = list(assignment_test)
    
    orders_sim = []
    for order in orders:
        order_s_shaped = stichgang(order, warehouse)
        orders_sim.append(order_s_shaped)

    distance = 0
    for order in orders_sim:
        source = deepcopy(start)
        for sku in order:
            loc = warehouse.nodes_list[warehouse.storage_assignment[sku]] 
            distance += warehouse.dist_mat[warehouse.nodes_list.index(source)][warehouse.nodes_list.index(loc)]
            source = loc
        distance += warehouse.dist_mat[warehouse.nodes_list.index(source)][warehouse.nodes_list.index(start)]
    return distance

def generate_genome_move(n, n_products):
    to_choose = [i for i in range(n_products)]
    genome = random.sample(to_choose, n)
    return genome


def render(warehouse, child, cool_storage, cool_products, product_frequency, product_weight):
    storage_assignment = deepcopy(warehouse.layout_grid)
    walkable_locs = np.where(warehouse.layout_grid == 0)

    for i, loc in enumerate(child):
        storage_assignment[warehouse.nodes_list[loc]] = i 

    storage_frequence = deepcopy(warehouse.layout_grid)
    for i, loc in enumerate(child):
        storage_frequence[warehouse.nodes_list[loc]] = product_frequency[i]

    for x, y, z in zip(walkable_locs[0], walkable_locs[1], walkable_locs[2]):
        storage_assignment[x,y,z] = -100
        storage_frequence[x,y,z] = -100


    storage_cool = deepcopy(warehouse.layout_grid)
    # for i in cool_products:
    #     loc = np.where(storage_assignment == i) 
    #     storage_cool[loc[0],loc[1]] = 100
    # for loc in cool_storage:
    #     storage_cool[loc[0],loc[1]] = -100

    storage_weight = deepcopy(warehouse.layout_grid)
    for i, loc in enumerate(child):
        storage_weight[warehouse.nodes_list[loc]] = product_weight[i]

    return storage_assignment, storage_frequence, storage_cool, storage_weight

def simulate_orders(product_frequency, n_orders, ub, lb):
    #random.seed(42)
    products = list(product_frequency.keys()) 
    frequency = list(product_frequency.values())
    orders = [random.choices(products, weights=frequency, k=random.randint(lb, ub)) for i in range(n_orders)]
    return orders

def run_ga(n_g, fitness_func, dist_mat, orders, initial_population, product_frequency, product_pair_frequency, n_orders, ub, lb):
    min_fitness = np.inf
    for g in range(n_g):
        if g % 100 == 0:
            print("Generation:",g)
        new_pop = []
        pop_results = []
        
        if orders == None:
            orders_sim = simulate_orders(product_frequency, n_orders, ub, lb)
        else:
            orders_sim = orders
        #fitness_result = [fitness(pop, only_d, product_frequency, product_weight, z_idx) for pop in initial_population]
        if fitness_func == "fitness_vrp":
            fitness_result = [fitness_vrp(pop, dist_mat, orders_sim) for pop in initial_population]
        elif fitness_func == "fitness_pf_pa":
            fitness_result = [fitness_pf_pa(pop, dist_mat, product_frequency, product_pair_frequency) for pop in initial_population]
        #print(fitness_result)
        for _ in range(100):
            selected = selection(initial_population, fitness_result)
            child = crossover(selected)
            mutated = mutation(child)
            new_pop.append(mutated)
        initial_population = new_pop
        print(min(fitness_result))
        if min(fitness_result) < min_fitness:
            min_fitness = min(fitness_result)
            min_child = initial_population[fitness_result.index(min_fitness)]
    
    return min_child

def heuristic_solution(warehouse: Layout, product_frequency: dict, n_products: int, source: tuple[Literal, Literal, Literal]):
    idx_storage = []
    for loc in warehouse.storage_locs:
        idx = warehouse.nodes_list.index(loc)
        idx_storage.append(idx)

    idx_source = warehouse.nodes_list.index(source)
    only_storage = warehouse.dist_mat[idx_source][idx_storage]

    storage_mapping = {}
    for idx, dist in zip(idx_storage, only_storage):
        storage_mapping[idx] = dist

    storage_dist_srtd = dict(sorted(storage_mapping.items(), key=lambda item: item[1]))

    products_srtd = dict(sorted(product_frequency.items(), key=lambda item: item[1], reverse=True))

    heuristic_assignment = [0 for i in range(n_products)]
    storage_keys = storage_dist_srtd.keys()
    i = 0 
    for product in products_srtd.keys():
        heuristic_assignment[product] = list(storage_keys)[i]
        i+=1

    return heuristic_assignment