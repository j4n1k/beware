from copy import deepcopy
from typing import Mapping, List

import gymnasium as gym
from gymnasium import spaces
import networkx as nx
import numpy as np
from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
from sb3_contrib.common.wrappers import ActionMasker

from stable_baselines3 import PPO, DQN, SAC, A2C

from sb3_contrib import MaskablePPO
from sb3_contrib.common.envs import InvalidActionEnvDiscrete
from sb3_contrib.common.maskable.evaluation import evaluate_policy
from sb3_contrib.common.maskable.utils import get_action_masks
# This is a drop-in replacement for EvalCallback
from sb3_contrib.common.maskable.callbacks import MaskableEvalCallback
from stable_baselines3.common.vec_env import DummyVecEnv

from torch import nn
import torch as th

from render import create_layout_array, create_viz_arrays, render_warehouse
from solver.order_picking import Routing  # Make sure you have this module available
from data.instance_loader import InstanceLoader
import plotly.express as px


class SLAPEnv(gym.Env):
    def __init__(self,locations, aisles, inter_cell_dist, inter_aisle_dist,
                 graph: nx.Graph,
                 dist_mat: np.array,
                 products: List,
                 product_frequency: Mapping,
                 storage_locs: List,
                 depot: tuple,
                 orders: List,
                 index_node_mapping,
                 node_index_mapping):
        super(SLAPEnv, self).__init__()

        self.locations = locations
        self.aisles = aisles
        self.inter_cell_dist = inter_cell_dist
        self.inter_aisle_dist = inter_aisle_dist
        self.max_steps = 100
        self.current_step = 0
        self.graph = graph
        self.dist_mat = dist_mat
        #self.products = list(products)
        self.product_frequency = product_frequency
        self.storage_locs = storage_locs
        for i in range(len(self.storage_locs)):
            if i >= len(products):
                self.product_frequency[i] = 0
        self.products = [i for i in range(len(self.storage_locs))]
        self.depot = depot
        self.orders = orders
        self.index_node_mapping = index_node_mapping
        self.node_index_mapping = node_index_mapping
        #self.state = self.products
        self.state = [-1] * len(self.products)
        self.routing_solver = Routing(
            self.graph,
            self.depot,
            self.dist_mat,
            self.state,
            self.index_node_mapping,
            self.node_index_mapping)

        # Define the action space and observation space
        self.action_space = self.action_space = spaces.MultiDiscrete([len(self.products), len(self.storage_locs)])
        #self.action_space = spaces.MultiDiscrete([len(self.storage_locs), len(self.storage_locs)])
        # self.observation_space = spaces.Box(low=0, high=len(self.storage_locs) - 1,
        #                                     shape=(len(self.storage_locs),), dtype=np.int32)
        self.observation_space = spaces.Box(
            low=0,
            high=max(self.product_frequency.values()),
            shape=(len(self.storage_locs) + len(self.product_frequency),),
            dtype=np.int32
        )

    def get_state(self):
        state = np.concatenate([self.state, list(self.product_frequency.values())])
        return state

    def step(self, action):
        # assign all products until no products are left
        # terminates if all products are assigned
        product_idx, location_idx = action
        reward = 0
        if self.state[product_idx] != -1 or location_idx in self.state:
            reward = -1  # Penalty for reassigning an already assigned product
            done = False
            info = {"error": "Product already assigned"}
            return self.get_state(), reward, done, info

            # Assign the product to the selected location
        self.state[product_idx] = location_idx

        self.current_step += 1

        # Check if all products have been assigned or max steps reached
        done = all(location != -1 for location in self.state)
        info = {}
        if done:
            reward = self.reward()
        # old_state = deepcopy(self.state)
        # new_state = deepcopy(self.state)
        #
        # idx_1, idx_2 = action
        # location_1 = new_state[idx_1]
        # location_2 = new_state[idx_2]
        #
        # new_state[idx_1] = location_2
        # new_state[idx_2] = location_1
        #
        # self.state = new_state
        # reward = self.reward()
        # info = {}  # Additional info
        # self.current_step += 1
        #done = self.current_step >= self.max_steps
        truncated = False
        return self.get_state(), reward, done, truncated, info

    def reset(self, seed=None, options=None):
        # Reset to a random assignment or any initial state you define
        # np.random.shuffle(self.products)
        # self.state = self.products.copy()
        self.state = [-1] * len(self.products)
        self.current_step = 0
        info = {}
        return self.get_state(), info

    def reward(self):
        rs = self.routing_solver
        rs.assignment = self.state
        total_reward = 0
        for order in self.orders:
            try:
                tour_length = rs.tsp_approximation(order)
            except:
                pass
            total_reward += tour_length
        return -total_reward  # Assuming a lower tour length is better

    def render(self, mode='human'):
        layout_array = create_layout_array(self.inter_aisle_dist,
                                           self.inter_cell_dist,
                                           self.node_index_mapping,
                                           self.aisles,
                                           self.locations)

        storage_assignment, storage_frequency = create_viz_arrays(layout_array,
                                                                  self.index_node_mapping,
                                                                  self.state,
                                                                  self.product_frequency)

        warehouse_heatmap = px.imshow(storage_assignment)
        warehouse_heatmap = px.imshow(storage_frequency)

        warehouse_heatmap.show()
        # print(storage_frequency)
        # print(storage_assignment)


    def close(self):
        # Cleanup if needed
        pass

    def get_action_mask(self):
        mask_1 = np.ones((len(self.products)), dtype=bool)
        mask_2 = np.ones((len(self.storage_locs)), dtype=bool)
        for product_idx, location in enumerate(self.state):
            if location != -1:
                mask_1[product_idx] = False  # Product already assigned, can't be assigned again
        for location_idx in range(len(self.storage_locs)):
            if location_idx in self.state:
                mask_2[location_idx] = False  # Location already occupied
        return np.concatenate([mask_1, mask_2])

def mask_fn(env: SLAPEnv):
    return env.get_action_mask()

# Example usage
if __name__ == "__main__":
    # Create a simple example
    instance = InstanceLoader()
    instance.load_instance()
    instance.print_instance()
    dist_mat = instance.distance_mat
    products = instance.articles_list
    product_pairs_frequency = instance.product_pairs_frequency
    product_frequency = instance.product_frequency
    storage_locs = instance.storage_locations

    layout_info = instance.general_info
    aisles = int(layout_info["NUM_AISLES"])
    locations = int(layout_info["NUM_CELLS"])
    inter_cell_dist = float(layout_info["DISTANCE_CELL_TO_CELL"])
    inter_aisle_dist = float(layout_info["DISTANCE_AISLE_TO_AISLE"])

    env = SLAPEnv(locations, aisles, inter_cell_dist, inter_aisle_dist, instance.graph, dist_mat, products,
                  product_frequency,
                  storage_locs, (0, 0, 0), instance.orders,
                  instance.index_node_mapping,
                  instance.node_index_mapping)

    print(env.action_space)
    print(env.action_space)
    env = ActionMasker(env, action_mask_fn=mask_fn)

    #model = PPO('MlpPolicy', env, verbose=1)
    # model = MaskablePPO(MaskableActorCriticPolicy, env, verbose=1)
    # model.learn(total_timesteps=5000000, tb_log_name="./ppo_slap")
    # model.save("masked_ppo_slap_env")

    # To reload the model and continue training or evaluation
    model = MaskablePPO.load("masked_ppo_slap_env")

    # Evaluate the trained model
    obs, _ = env.reset()
    done = False
    while not done:
        action_masks = get_action_masks(env)
        action, _states = model.predict(obs, action_masks=action_masks)
        obs, reward, done, truncated, info = env.step(action)
        if done:
            print(reward)
            env.render()
