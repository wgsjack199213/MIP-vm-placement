#!/usr/bin/python

import random
from physical_configuration import PhysicalConfig
import numpy
from MIP_rack_interface import migrate_policy

# num_racks is the number of racks
# num_server_per_rack in the number of servers in each rack
num_racks = 12
num_server_per_rack = 15
num_servers = num_racks * num_server_per_rack 

# num_links is the number of links (out of racks). 
# Suppos all racks are linked to a single switch, then num_links is the same with the number of R
num_links = num_racks

num_vms_per_server = 4

num_vms = num_vms_per_server * num_servers

vm_memory_scale = [512, 1024, 2048, 4096, 8192, 16384, 32768, 65536]
vm_cpu_scale = [1, 2, 4, 8, 11]

random_bandwidth_upper_bound = 200



# create a traffic matrix
def create_traffic_matrix():
    t = []
    for k in range(num_vms):
        row = []
        busy_flag = random.random() < 0.5
        for i in range(num_vms):
            if i < k:
                row.append(t[i][k])
            elif i == k:
                row.append(0)
            else:
                if busy_flag:
                    row.append(random.randint(random_bandwidth_upper_bound * 3 / 4, random_bandwidth_upper_bound))
                else:
                    row.append(random.randint(0, random_bandwidth_upper_bound / 4))
        t.append(row)

    #f=open('traffic_matrix.txt', 'a')
    #f.write(t)
    #f.close()

    #print "the traffic matrix: "
    #print t
    return t

def create_physical_config_instance():
    which_rack = []
    for k in range(num_racks):
        for i in range(num_server_per_rack):
            which_rack.append(k)
    #print "which rack", which_rack

    constraint_cpu = [12 for k in range(num_servers)]
    #print "constraint on cpus", constraint_cpu

    constraint_memory = [128000 for k in range(num_servers)]
    #print "constraint on memory", constraint_memory

    link_capacity = [10000 for k in range(num_links)]
    #print "link capacity", link_capacity
    
    config = PhysicalConfig(num_servers = num_servers, num_racks = num_racks, which_rack = which_rack, constraint_cpu = constraint_cpu, constraint_memory = constraint_memory, num_links = num_links, link_capacity = link_capacity)
    return config


# num_servers = 0, num_racks = 0, which_rack = [], traffic_cost_matrix = [], constraint_cpu = [], constraint_memory = [], num_links = 0, link_capacity = [], link_occupation_matrix = [], link_user_racks = []):

def generate_vm_consumption():
    vm_consumption = []
    for k in range(num_vms):
        cpu = vm_cpu_scale[random.randint(0, 2)]
        memory = vm_memory_scale[random.randint(0, 6)]
        vm_consumption.append([cpu, memory])
    #print "vm consumption", vm_consumption
    return vm_consumption

def generate_original_placement():
    original_placement = []
    for k in range(num_servers):
        for i in range(num_vms_per_server):
            original_placement.append(k)
    #print "original placement", original_placement
    return original_placement

if __name__ == "__main__":
    traffic = create_traffic_matrix()
    #traffic = [[0, 190, 19, 134, 155, 154, 125, 164, 120, 168, 52, 37], [190, 0, 104, 45, 198, 117, 158, 199, 93, 96, 129, 84], [19, 104, 0, 175, 12, 126, 93, 140, 200, 152, 184, 17], [134, 45, 175, 0, 106, 182, 129, 172, 43, 44, 184, 85], [155, 198, 12, 106, 0, 125, 184, 108, 100, 32, 116, 171], [154, 117, 126, 182, 125, 0, 9, 155, 59, 186, 104, 79], [125, 158, 93, 129, 184, 9, 0, 184, 139, 190, 9, 168], [164, 199, 140, 172, 108, 155, 184, 0, 83, 117, 39, 180], [120, 93, 200, 43, 100, 59, 139, 83, 0, 148, 63, 81], [168, 96, 152, 44, 32, 186, 190, 117, 148, 0, 115, 8], [52, 129, 184, 184, 116, 104, 9, 39, 63, 115, 0, 122], [37, 84, 17, 85, 171, 79, 168, 180, 81, 8, 122, 0]]

     
    all_vm_consumption = generate_vm_consumption()
    all_original_placement = generate_original_placement()


    test_config = create_physical_config_instance()
    
    print "migrate_policy is being called..."
    migrate_policy(num_vms, all_vm_consumption, traffic, all_original_placement, test_config)
