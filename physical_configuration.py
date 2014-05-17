#!/usr/bin/python


#
# num_servers                   is the number of servers
# num_racks                     is the number of racks
# which_rack                    is a list indicating which rack each server belongs to
#                               e.g.    [0, 0, 1, 1, 2, 2]  server_0 and server_1 on rack_0
# traffic_cost_matrix           * can be ignored for now
# constraint_cpu                is a list indicating the number of cpus each server has
# constraint_memory             is a list indicating how much memory (MB) each server has
# constraint_disk               is a list indication how much disk (GB) each server has
# num_links                     is the number of all physical links (out of racks)
# link_capacity                 is the traffic capacity (MB) of each link
# link_occupation_matrix        can be ignored for now
#                               is a 3-dimension list and meanwhile a symmetric matrix, indication which links each pair of racks use
#                               e.g.    [[ [], [0, 1], [0, 2] ], [ [0, 1], [], [1, 2] ], [ [0, 2], [1, 2], [] ]]    rack_0 and rack_1 use link [0, 1], rack_0 and rack_0 use link []
# link_user_racks               * can be ignored for now
#
class PhysicalConfig(object):
    def __init__(self, num_servers = 0, num_racks = 0, which_rack = [], traffic_cost_matrix = [], constraint_cpu = [], constraint_memory = [], constraint_disk = [], num_links = 0, link_capacity = [], link_occupation_matrix = [], link_user_racks = [], constraint_rack_cpu = [], constraint_rack_memory = [], constraint_rack_disk = []):
        self.num_servers = num_servers
        self.num_racks = num_racks
        self.which_rack = which_rack
        self.traffic_cost_matrix = traffic_cost_matrix
        self.constraint_cpu = constraint_cpu
        self.constraint_memory = constraint_memory
        self.constraint_disk = constraint_disk
        self.num_links = num_links
        self.link_capacity = link_capacity
        self.link_occupation_matrix = link_occupation_matrix
        self.link_user_racks = link_user_racks
        self.constraint_rack_cpu = constraint_rack_cpu
        self.constraint_rack_memory = constraint_rack_memory
        self.constraint_rack_disk = constraint_rack_disk


        # compute rack users using which_rack
        self.rack_user_servers = [ [] for k in range(num_racks) ]
        for k in range(num_servers):
            self.rack_user_servers[which_rack[k]].append(k)

        #print self.rack_user_servers
        #print self.link_user_racks
    def compute_available_rack_resource(self):
        self.constraint_rack_cpu = [0 for k in range(self.num_racks)]
        self.constraint_rack_memory = [0 for k in range(self.num_racks)]
        self.constraint_rack_disk = [0 for k in range(self.num_racks)]
        for server in range(self.num_servers):
            self.constraint_rack_cpu[self.which_rack[server]] += self.constraint_cpu[server]
            self.constraint_rack_memory[self.which_rack[server]] += self.constraint_memory[server]
            self.constraint_rack_disk[self.which_rack[server]] += self.constraint_disk[server]

        #print "cpu resource of each rack: ", self.constraint_rack_cpu
        #print "memory resource of each rack: ", self.constraint_rack_memory
