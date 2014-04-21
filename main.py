#!/usr/bin/python

#import markov_migration
from markov_migration import migrate_policy
from physical_configuration import PhysicalConfig
import numpy


def construct_a_physical_config():
    #
    #   rack 012 is connected to the switch S
    #   rack 0      link0 = 2          
    #   rack 1      link1 = 2.5
    #   rack 2      link2 = 3
    #
    num_servers = 6
    num_racks = 3
    which_rack = [0, 0, 1, 1, 2, 2]
    traffic_cost_matrix = [[0, 0, 4.5, 4.5, 5, 5], [0, 0, 4.5, 4.5, 5, 5], [4.5, 4.5, 0, 0, 5.5, 5.5], [4.5, 4.5, 0, 0, 5.5, 5.5], [5, 5, 5.5, 5.5, 0, 0], [5, 5, 5.5, 5.5, 0, 0]]
    constraint_cpu = []
    constraint_memory = []
    num_links = 3
    link_capacity = []
    link_occupation_matrix = [[ [], [0, 1], [0, 2] ], [ [0, 1], [], [1, 2] ], [ [0, 2], [1, 2], [] ]]
    
    # how to determine the set of vms who are using a certain link?
    # currently we assume that the topology is a star (tree), and each link corresponds to a certain rack
    link_user_racks = [[0], [1], [2]]

    config = PhysicalConfig(num_servers, num_racks, which_rack, traffic_cost_matrix, constraint_cpu, constraint_memory, num_links, link_capacity, link_occupation_matrix, link_user_racks)
    
    return config


if __name__ == "__main__":

    test_config = construct_a_physical_config()
    
    num_vms = 3
    vm_consumption = []
    vm_traffic_matrix = [[0, 7.2, 2], [7.2, 0, 3], [2, 3, 0]]
    original_placement = [0, 2, 4]
    
    migrate_policy(num_vms, vm_consumption, vm_traffic_matrix, original_placement, test_config)
