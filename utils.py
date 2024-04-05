import pandas as pd
from collections import defaultdict

def sort_dict(dict_to_sort):
    return dict(sorted(dict_to_sort.items(), key=lambda x:x[1], reverse=True))

def get_products(orders):
    if type(orders) == list:
        products = []
        for order in orders:
            for p in order:
                if p not in products:
                    products.append(p)
        return products
    
    if type(orders) == pd.Series:
        return orders.unique()


def prepare_orders(orders_old, products_mapping):
    new_order = []
    for order in orders_old: 
        orderline = []
        for p in order:
            orderline.append(products_mapping[p])
        new_order.append(orderline)
    return new_order

def calc_product_freq(products, orders):
    product_frequency = {i : 0 for i in products}
    for order in orders:
        for p in order:
            product_frequency[p] += 1
    return product_frequency

def calc_product_affinity(orders):
# Create a dictionary to store the frequency of product pairs
    product_pairs_frequency = defaultdict(lambda: defaultdict(int))

    # Iterate through each order list
    for order in orders:
        # Generate all possible pairs of products in the order
        for i in range(len(order)):
            for j in range(i + 1, len(order)):
                product_pairs_frequency[order[i]][order[j]] += 1
                product_pairs_frequency[order[j]][order[i]] += 1
    return product_pairs_frequency