# Create a simple example
from data.instance_loader import InstanceLoader
from env.slap_env import SLAPEnv
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


def mask_fn(env: SLAPEnv):
    return env.get_action_mask()


def main():
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


if __name__ == "__main__":
    main()
