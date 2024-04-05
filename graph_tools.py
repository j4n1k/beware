import networkx as nx
import numpy as np

def gen_graph(layout: np.array, double_deep):
    G = nx.Graph()

    walkable_pos = np.where(layout == 0)
    xs_walk = walkable_pos[0]
    ys_walk = walkable_pos[1]

    storage_pos = np.where(layout == -1)
    xs_store = storage_pos[0]
    ys_store = storage_pos[1]
    zs_store = storage_pos[2]

    for x, y in zip(xs_walk, ys_walk):
        G.add_node((x,y,0))
        links = (x-1,y,0)
        rechts = (x+1,y,0)
        oben = (x,y+1,0)
        unten = (x, y-1,0)
        if links[0]>= 0:
            if layout[links] == 0:
                G.add_edge((x,y,0),links, weight=1)
            # elif layout[links] == -1:
            #     G.add_edge((x,y),links, weight=1)
        if rechts[0] < layout.shape[0]:
            if layout[rechts] == 0:
                G.add_edge((x,y,0),rechts, weight=1)
            # elif layout[rechts] == -1:
            #     G.add_edge((x,y),rechts, weight=1)
            
        if oben[1] < layout.shape[1]:
            if layout[oben] == 0:
                G.add_edge((x,y,0),oben, weight=1)
            elif layout[oben] == -1:
                G.add_edge((x,y,0),oben, weight=1)
                for i in range(1,layout.shape[2]):
                    G.add_edge(oben, (oben[0], oben[1], oben[2] +i))
                    G.add_edge(oben, (oben[0], oben[1], oben[2] +i))

        if unten[1] >= 0:
            if layout[unten] == 0:
                G.add_edge((x,y,0),unten, weight=1) 
            elif layout[unten] == -1:
                G.add_edge((x,y,0),unten, weight=1)
                for i in range(1,layout.shape[2]):
                    G.add_edge(unten, (unten[0], unten[1], unten[2] +i))
                    G.add_edge(unten, (unten[0], unten[1], unten[2] +i))
    
    for x, y, z in zip(xs_store, ys_store, zs_store):
        G.add_node((x, y, z))



    
    return G

# def gen_pos(G: nx.Graph):
#     pos_dict = {}
#     for node in G.nodes():
#         pos_dict[node] = node
#     return pos_dict

def gen_pos(G: nx.Graph):
    pos_dict = {}
    for node in G.nodes():
        pos_dict[node] = np.array([node[0], node[1], node[2]])
    return pos_dict

def get_nodes (orders, start, storage, products):
    list_of_nodes_lists = []

    for i in orders:
        node_list = []
        node_list.append(start)
        for p in orders[i]:
            loc = np.where(storage == p)
            node_list.append((loc[0][0], loc[1][0]+1))
        list_of_nodes_lists.append(node_list)
    return list_of_nodes_lists

def get_route_lenght(G, list_of_nodes_lists):
    lenghts = []
    tsp = nx.approximation.traveling_salesman_problem
    for order in list_of_nodes_lists:
        result = tsp(G, nodes=order)
        lenghts.append(len(result))
    return lenghts

def viz_graph(G, pos_dict):
    import matplotlib.pyplot as plt

    node_xyz = np.array([pos_dict[v] for v in sorted(G)])
    edge_xyz = np.array([(pos_dict[u], pos_dict[v]) for u, v in G.edges()])
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    #plot nodes
    ax.scatter(node_xyz.T[0], node_xyz.T[1], node_xyz.T[2], s=10)

    # Plot the edges
    for vizedge in edge_xyz:
        ax.plot(*vizedge.T, color="tab:gray")

    ax.set_box_aspect([1,1,1])
    ax.set_title("3D plot")
    ax.set_xlabel('x-axis')
    ax.set_ylabel('y-axis')
    ax.set_zlabel('z-axis')
    plt.show()