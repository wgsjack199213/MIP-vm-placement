#!/usr/bin/python

import random
from physical_configuration import PhysicalConfig
import numpy
from MIP_interface import migrate_policy


# num_racks is the number of racks
# num_server_per_rack in the number of servers in each rack
num_racks = 3
num_server_per_rack = 2
num_servers = num_racks * num_server_per_rack 

# num_links is the number of links (out of racks). 
# Suppos all racks are linked to a single switch, then num_links is the same with the number of R
num_links = num_racks

num_vms_per_server = 2

num_vms = num_vms_per_server * num_servers

vm_memory_scale = [512, 1024, 2048, 4096, 8192, 16384, 32768, 65536]
vm_cpu_scale = [1, 2, 4, 8, 11]

# create a traffic matrix
def create_traffic_matrix():
    t = []
    for k in range(num_vms):
        row = []
        for i in range(num_vms):
            if i < k:
                row.append(t[i][k])
            elif i == k:
                row.append(0)
            else:
                row.append(random.randint(1, 1000))
        t.append(row)

    #f=open('traffic_matrix.txt', 'a')
    #f.write(t)
    #f.close()

    print "the traffic matrix: "
    print t
    return t

def create_physical_config_instance():
    which_rack = []
    for k in range(num_racks):
        for i in range(num_server_per_rack):
            which_rack.append(k)
    print "which rack", which_rack

    constraint_cpu = [12 for k in range(num_servers)]
    print "constraint on cpus", constraint_cpu

    constraint_memory = [128000 for k in range(num_servers)]
    print "constraint on memory", constraint_memory

    link_capacity = [10000 for k in range(num_links)]
    print "link capacity", link_capacity
    
    config = PhysicalConfig(num_servers = num_servers, num_racks = num_racks, which_rack = which_rack, constraint_cpu = constraint_cpu, constraint_memory = constraint_memory, num_links = num_links, link_capacity = link_capacity)
    return config


# num_servers = 0, num_racks = 0, which_rack = [], traffic_cost_matrix = [], constraint_cpu = [], constraint_memory = [], num_links = 0, link_capacity = [], link_occupation_matrix = [], link_user_racks = []):

def generate_vm_consumption():
    vm_consumption = []
    for k in range(num_vms):
        cpu = vm_cpu_scale[random.randint(0, 3)]
        memory = vm_memory_scale[random.randint(0, 7)]
        vm_consumption.append([cpu, memory])
    print "vm consumption", vm_consumption
    return vm_consumption

def generate_original_placement():
    original_placement = []
    for k in range(num_servers):
        for i in range(num_vms_per_server):
            original_placement.append(k)
    print "original placement", original_placement
    return original_placement

if __name__ == "__main__":
    #traffic = create_traffic_matrix()
    traffic = [[0, 409, 819, 470, 185, 277, 752, 908, 397, 82, 703, 795], [409, 0, 838, 616, 453, 125, 626, 280, 60, 225, 633, 669], [819, 838, 0, 439, 705, 737, 445, 323, 281, 97, 413, 340], [470, 616, 439, 0, 708, 547, 316, 889, 661, 607, 774, 924], [185, 453, 705, 708, 0, 34, 940, 939, 136, 908, 288, 112], [277, 125, 737, 547, 34, 0, 578, 559, 603, 342, 594, 752], [752, 626, 445, 316, 940, 578, 0, 393, 194, 983, 867, 648], [908, 280, 323, 889, 939, 559, 393, 0, 818, 416, 320, 902], [397, 60, 281, 661, 136, 603, 194, 818, 0, 209, 325, 675], [82, 225, 97, 607, 908, 342, 983, 416, 209, 0, 838, 787], [703, 633, 413, 774, 288, 594, 867, 320, 325, 838, 0, 132], [795, 669, 340, 924, 112, 752, 648, 902, 675, 787, 132, 0]]

    vm_consumption = generate_vm_consumption()

    original_placement = generate_original_placement()

    test_config = create_physical_config_instance()

    migrate_policy(num_vms, vm_consumption, traffic, original_placement, test_config)
