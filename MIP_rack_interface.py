# OpenStack virtual machine placement
# try to solve the mixed integer programming problem with NO quadratic opjection

import sys
sys.path.append('/Users/wgs/projects/IBM/ILOG/CPLEX_Studio126/cplex/python/x86-64_osx/')
import cplex
import random


def compute_two_kinds_of_traffic(M, rack, vm_mobile, physical_config, num_all_vms, most_noisy_vms, original_placement, vm_traffic_matrix):
    traffic_fixed_on_rack, traffic_fixed_out_of_rack = 0, 0
    
    for j in range(num_all_vms):
        if j in most_noisy_vms:
            continue
        if physical_config.which_rack[original_placement[j]] == rack:
            traffic_fixed_on_rack += vm_traffic_matrix[most_noisy_vms[vm_mobile]][j]
        else:
            traffic_fixed_out_of_rack += vm_traffic_matrix[most_noisy_vms[vm_mobile]][j]
        
    return traffic_fixed_on_rack, traffic_fixed_out_of_rack


# ====================
# constraints
# ====================
def add_constraints(problem, num_vms, vm_consumption, original_placement, vm_traffic_matrix, link_capacity_consumed, physical_config, num_all_vms, most_noisy_vms):
    M = num_vms
    N = physical_config.num_racks

    # Populate by rows
    rows = []
    # constraint of vm placement
    for i in range(M):
        variables = []
        for k in range(N):
            variables.append("x_{0}_{1}".format(i, k))

        rows.append([variables, [1 for j in range(N)]])
   
   # constraint of y
    for i in range(M):
        for j in range(i+1, M):
            for u in range(N):
                for v in range(N): 
                    x_1, x_2 = "x_{0}_{1}".format(i, u), "x_{0}_{1}".format(j, v)
                    y = "y_{0}_{1}_{2}_{3}".format(i, j, u, v)
                    rows.append([[x_1, y], [1, -1]])
                    rows.append([[x_2, y], [1, -1]])
                    rows.append([[x_1, x_2, y], [1, 1, -1]])

    # constraint of resources
    for j in range(N):
        variables = []
        cpu_coefficient = []
        memory_coefficient = []
        disk_coefficient = []
        for i in range(M):
            variables.append("x_{0}_{1}".format(i, j))
            cpu_coefficient.append(vm_consumption[i][0])
            memory_coefficient.append(vm_consumption[i][1])
            disk_coefficient.append(vm_consumption[i][2])

        rows.append([variables, cpu_coefficient])
        rows.append([variables, memory_coefficient])
        rows.append([variables, disk_coefficient])


    # computation of l variables (traffic on each link)
    constant_term_mobile_and_fixed_list = [0 for k in range(physical_config.num_links)]

    for i in range(physical_config.num_links):
        variables = []
        coefficient = []

        coefficient_list_for_x_pi = [0 for ii in range(M)]

        # between "can move" and "can move"
#        for p in range(M):
#            # to avoid duplicately adding y variable into rows, we consider pair by pair
#            # switching p and q
#            for q in range(p+1, M):
#                # now p < q 
#                for j in range(N): 
#                    for s in range(j+1, N):
#                        if s == j:
#                            continue
#                        variables.append("y_{0}_{1}_{2}_{3}".format(p, q, j, s))
#                        variables.append("y_{0}_{1}_{2}_{3}".format(p, q, s, j))
#                        coefficient.append(vm_traffic_matrix[p][q])
#                        coefficient.append(vm_traffic_matrix[p][q])

        for p in range(M):
            # to avoid duplicately adding y variable into rows, we consider pair by pair
            for q in range(p+1, M):
                # now p < q
                variables.append("y_{0}_{1}_{2}_{3}".format(p, q, i, i))     
                traffic =  vm_traffic_matrix[most_noisy_vms[p]][most_noisy_vms[q]]
                
                coefficient.append(-2*traffic) 
                coefficient_list_for_x_pi[p] += traffic
                coefficient_list_for_x_pi[q] += traffic
                


        # between "can move" and "fixed"
        for p in range(M):
            # compute two kinds of traffic
            traffic_j_on_i, traffic_j_out_of_i = compute_two_kinds_of_traffic(M, i, p, physical_config, num_all_vms, most_noisy_vms, original_placement, vm_traffic_matrix)
            variables.append("x_{0}_{1}".format(p, i))
            coefficient.append(traffic_j_out_of_i - traffic_j_on_i + coefficient_list_for_x_pi[p])

            constant_term_mobile_and_fixed_list[i] += traffic_j_on_i



        variables.append("l_{0}".format(i))
        coefficient.append(-1)
        rows.append([variables, coefficient])

    # to minimize the heavest link
    for k in range(physical_config.num_links):
        rows.append([["l_{0}".format(k), "heavest_link"], [1, -1]])

    
  
    placement_constraints = [1 for k in range(M)]
    for k in range(M*(M-1)*N*N/2):
        placement_constraints += [0, 0, 1]
    for k in range(N):
        placement_constraints += [physical_config.constraint_rack_cpu[k], physical_config.constraint_rack_memory[k], physical_config.constraint_rack_disk[k]]

    if link_capacity_consumed == []:
        link_capacity_consumed = [0 for k in range(physical_config.num_links)]

    # the rhs of traffic on each link
    for k in range(physical_config.num_links):
        placement_constraints += [ -link_capacity_consumed[k]-constant_term_mobile_and_fixed_list[k] ]

    # to minimize the max
    for k in range(physical_config.num_links):
        placement_constraints += [0]



    placement_senses = 'E' * M + 'GGL' * (M*(M-1)*N*N/2)       # E means 'equal'  
    placement_senses += 'L' * (3*N)     #resources
    placement_senses += 'E' * physical_config.num_links
    placement_senses += 'L' * physical_config.num_links
    #print placement_constraints
    #print placement_senses

    problem.linear_constraints.add(lin_expr = rows, rhs = placement_constraints, senses = placement_senses)



def set_problem_data(p, num_vms, vm_consumption, vm_traffic_matrix, original_placement, physical_config, link_capacity_consumed, cost_migration, num_all_vms, most_noisy_vms):
    p.set_problem_name("OpenStack VM placement")
    p.objective.set_sense(p.objective.sense.minimize)

    M = num_vms
    N = physical_config.num_racks

    # ====================
    # objective
    # ====================
    
    # the objectiv is to be refined
    objective = [0 for k in range(M*N+M*(M-1)/2*N*N+physical_config.num_links*2)]
    objective.append(1)
    for k in range(M):
        rack = original_placement[most_noisy_vms[k]]
        objective[N*k + rack] = -cost_migration[most_noisy_vms[k]]


    # ====================
    # variables
    # ====================

    # http://www-01.ibm.com/support/knowledgecenter/api/content/SSSA5P_12.6.0/ilog.odms.cplex.help/refcallablelibrary/mipapi/copyctype.html?locale=en
    # CBISN     coninuous binary integer semi-continuous semi-integer 
    variable_types = 'B' * ((M*N) + (M*(M-1)*N*N/2))
    # l (all traffic over a link) and z (phi(l))
    variable_types += 'C' * (2*physical_config.num_links)

    variable_types += 'C'
    
    upper_bound = [1 for k in range(M*N)] + [1 for k in range(M*(M-1)*N*N/2)] + [cplex.infinity for k in range(physical_config.num_links)] + [cplex.infinity for k in range(physical_config.num_links)] + [cplex.infinity]
    lower_bound = [0 for k in range(M*N)] + [0 for k in range(M*(M-1)*N*N/2)] + [0 for k in range(physical_config.num_links)] + [0 for k in range(physical_config.num_links)] + [0]

    names = []
    for k in range(M):
        for i in range(N):
            names.append("x_{0}_{1}".format(k, i))
    for i in range(M):
        for j in range(i+1, M):
            for u in range(N):
                for v in range(N): 
                    names.append("y_{0}_{1}_{2}_{3}".format(i, j, u, v))
    for k in range(physical_config.num_links):
        names.append("l_{0}".format(k))
    for k in range(physical_config.num_links):
        names.append("z_{0}".format(k))

    names.append("heavest_link")

    # for debugging
    #print "obj: ", len(objective)#, objective
    #print "ub: ", len(upper_bound)#, upper_bound
    #print "lb: ", len(lower_bound)#, lower_bound
    #print "types: ", len(variable_types)#, variable_types
    #print "names: ", len(names)#, names

    p.variables.add(obj = objective, lb = lower_bound, ub = upper_bound, types = variable_types, names = names)

    add_constraints(p, M, vm_consumption, original_placement, vm_traffic_matrix, link_capacity_consumed, physical_config, num_all_vms, most_noisy_vms)

    print "the problem data has been set!"



# the second main interface
def set_and_solve_problem(num_vms, vm_consumption, vm_traffic_matrix, original_placement, physical_config, cost_migration, num_all_vms, most_noisy_vms, link_capacity_consumed = []):
    M = num_vms
    N = physical_config
    
    placement = cplex.Cplex()
    set_problem_data(placement, M, vm_consumption, vm_traffic_matrix, original_placement, physical_config, link_capacity_consumed, cost_migration, num_all_vms, most_noisy_vms)
    
    # try to tune
    placement.parameters.timelimit.set(60.0)
    #placement.parameters.threads.set(1)
    placement.parameters.emphasis.mip.set(1)
    placement.parameters.emphasis.memory.set(1)

#    print "begin to add the start solution"
#    for k in range(M):
#        indices = list(range(k*N, (k+1)*N))
#        values = [0 for i in range(N)]
#        values[original_placement[k]] = 1
        #print indices
        #print values
#        placement.MIP_starts.add(cplex.SparsePair(ind = indices, val = values), placement.MIP_starts.effort_level.solve_MIP)

    #return 
    
    print "begin solving..."
    placement.solve()

    placement.write("openstack_output.txt")
    print "Get the solution"

    return placement




def select_most_noisy_vms(num_vms, traffic_matrix, original_placement, physical_config, num_top_noisy_vms, fixed_vms):
    #return [0, 1]

    traffic = [0 for k in range(num_vms)]
    for k in range(num_vms):
        for i in range(num_vms):
            if physical_config.which_rack[original_placement[k]] == physical_config.which_rack[original_placement[i]]:
                continue
            traffic[k] += traffic_matrix[k][i]
    # the list traffic is INDEED the traffic each vm contributes on each link
    ans = []
    indice = []
    traffic_copy, traffic_copy_for_search_index = traffic[:], traffic[:]

    loop_variable = num_top_noisy_vms
    while loop_variable > 0 and traffic_copy != []:
        tmp_max = max(traffic_copy)
        index_max = traffic_copy_for_search_index.index(tmp_max)
        traffic_copy.remove(tmp_max)
        traffic_copy_for_search_index[index_max] = -1

        if index_max in fixed_vms:     # we do not count(choose) the vms that should be fixed
            # TODO
            #print index_max, "can not be moved!========================================="
            continue
        ans.append(tmp_max)
        indice.append(index_max)
        
        loop_variable -= 1

    #print ans, indice
    return indice

# for debug
def compute_link_used_capacity(num_vms, original_placement, traffic, most_noisy_vms, config):
    link_used = [0 for k in range(config.num_links)]
    # enumerate vm pair k and i, check if they are in the same rack
    for k in range(num_vms):
        if k in most_noisy_vms:
            continue
        for i in range(num_vms):
            if i in most_noisy_vms:
                continue
            rack_of_k, rack_of_i = config.which_rack[original_placement[k]], config.which_rack[original_placement[i]]
            if rack_of_k == rack_of_i:
                continue
            link_used[rack_of_k] += traffic[k][i]
    #print "link capacity that has been used: ", link_used
    return link_used


# get the migration operations from the result
def process_result(placement, num_top_noisy_vms, most_noisy_vms, original_placement, num_racks):
    migration_operations = []

    sol = placement.solution


# TODO this is debugging
#    numcols = placement.variables.get_num()
#    numrows = placement.linear_constraints.get_num()
#    slack = sol.get_linear_slacks()
#    x     = sol.get_values()
#
#
#    for j in range(numcols):
#        print "Column %d:  Value = %10f" % (j, x[j])




    # solution.get_status() returns an integer code
    print "Solution status = " , sol.get_status(), ":",
    # the following line prints the corresponding string
    print sol.status[sol.get_status()]
    print "Solution value  = ", sol.get_objective_value()

    print "number of top noisy vms: ", num_top_noisy_vms
    print most_noisy_vms
    for k in range(num_top_noisy_vms):
        vm = most_noisy_vms[k]
        if 1 == sol.get_values(original_placement[vm] + k*num_racks):
            print vm, ": stays in ", original_placement[vm]
        else:
            for i in range(num_racks):
                #print sol.get_values(k*num_racks + i)
                if 1 == sol.get_values(k*num_racks + i):
                    print vm, ": originally in ", original_placement[vm], ", now moves to", i
                    migration_operations.append([vm, i])
                    break

    return migration_operations 


def choose_server_in_rack(migrate_to_rack, vm_consumption, physical_config):
    operations = []
    for migration in migrate_to_rack:
        vm, rack = migration[0], migration[1]
        candidate_servers = []
        for server in physical_config.rack_user_servers[rack]:
            if physical_config.constraint_cpu[server] > vm_consumption[vm][0] and physical_config.constraint_memory[server] > vm_consumption[vm][1] and physical_config.constraint_disk[server] > vm_consumption[vm][2]:
                candidate_servers.append(server)

        server_with_most_memory, most_memory = 0, 0
        for s in candidate_servers:
            if physical_config.constraint_memory[s] > most_memory:
                server_with_most_memory, most_memory = s, physical_config.constraint_memory[s]
                
        physical_config.constraint_cpu[server_with_most_memory] -= vm_consumption[vm][0]
        physical_config.constraint_memory[server_with_most_memory] -= vm_consumption[vm][1]
        physical_config.constraint_disk[server_with_most_memory] -= vm_consumption[vm][2]
        operations.append([vm, server_with_most_memory])

        
    print "final operations", operations
    return operations
        


# the firt main interface
def migrate_policy(num_vms, vm_consumption, vm_traffic_matrix, original_placement, physical_config, num_top_noisy_vms = 2, fixed_vms = [], cost_migration = []):
    # adjustable parameters
    #num_top_noisy_vms = 2
    if cost_migration == []:
        cost_migration = [0 for k in range(num_vms)]

    most_noisy_vms = select_most_noisy_vms(num_vms, vm_traffic_matrix, original_placement, physical_config, num_top_noisy_vms, fixed_vms)
    if len(most_noisy_vms) < num_vms:
        num_top_noisy_vms = len(most_noisy_vms)

    # only consider the most busiest vms
    busy_vm_consumption = []
    for k in range(num_top_noisy_vms):
        busy_vm_consumption.append(vm_consumption[most_noisy_vms[k]])
        #busy_original_placement.append(original_placement[most_noisy_vms[k]])

    for k in range(num_vms):
        if k in most_noisy_vms:
            continue
        physical_config.constraint_cpu[original_placement[k]] -= vm_consumption[k][0]
        physical_config.constraint_memory[original_placement[k]] -= vm_consumption[k][1]
        physical_config.constraint_disk[original_placement[k]] -= vm_consumption[k][2]
    #print "constraint on cpus", physical_config.constraint_cpu
    #print "constraint on memory", physical_config.constraint_memory
    physical_config.compute_available_rack_resource()

    # compute how much capacity has been used in each link
    link_capacity_consumed = compute_link_used_capacity(num_vms, original_placement, vm_traffic_matrix, most_noisy_vms, physical_config)
    print "link_capacity_consumed:", link_capacity_consumed

    # compute current state of each link
    no_vms = []
    link_state = compute_link_used_capacity(num_vms, original_placement, vm_traffic_matrix, no_vms, physical_config)
    print "traffic on each link: ", link_state

    print "begin set_and_solve_problem"
    placement = set_and_solve_problem(num_top_noisy_vms, busy_vm_consumption, vm_traffic_matrix, original_placement, physical_config, cost_migration, num_vms, most_noisy_vms, link_capacity_consumed)

    migrate_to_rack = process_result(placement, num_top_noisy_vms, most_noisy_vms, original_placement, physical_config.num_racks)
    #print migrate_to_rack
    migrate_to_server = choose_server_in_rack(migrate_to_rack, vm_consumption, physical_config)
    
    return migrate_to_server
