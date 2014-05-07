# OpenStack virtual machine placement
# try to solve the mixed integer programming problem with NO quadratic opjection

import sys
sys.path.append('/Users/wgs/projects/IBM/ILOG/CPLEX_Studio126/cplex/python/x86-64_osx/')
import cplex
import random


# ====================
# constraints
# ====================
def add_constraints(problem, num_vms, vm_consumption, vm_traffic_matrix, link_capacity_consumed, physical_config):
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
        for i in range(M):
            variables.append("x_{0}_{1}".format(i, j))
            cpu_coefficient.append(vm_consumption[i][0])
            memory_coefficient.append(vm_consumption[i][1])

        rows.append([variables, cpu_coefficient])
        rows.append([variables, memory_coefficient])

    # computation of l variables (traffic on each link)
    for i in range(physical_config.num_links):
        variables = []
        coefficient = []
        for p in range(M):
            # to avoid duplicately adding y variable into rows, we consider pair by pair
            # switching p and q
            for q in range(p+1, M):
                # now p < q 
                for j in range(N): 
                    for s in range(j+1, N):
                        if s == j:
                            continue
                        variables.append("y_{0}_{1}_{2}_{3}".format(p, q, j, s))
                        variables.append("y_{0}_{1}_{2}_{3}".format(p, q, s, j))
                        coefficient.append(vm_traffic_matrix[p][q])
                        coefficient.append(vm_traffic_matrix[p][q])
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
    # TODO
        placement_constraints += [physical_config.constraint_rack_cpu[k], physical_config.constraint_rack_memory[k]]

    if link_capacity_consumed == []:
        link_capacity_consumed = [0 for k in range(physical_config.num_links)]
    for k in range(physical_config.num_links):
        placement_constraints += [ -link_capacity_consumed[k] ]

    # to minimize the max
    for k in range(physical_config.num_links):
        placement_constraints += [0]



    placement_senses = 'E' * M + 'GGL' * (M*(M-1)*N*N/2)       # E means 'equal'  
    placement_senses += 'L' * (2*N)
    placement_senses += 'E' * physical_config.num_links
    placement_senses += 'L' * physical_config.num_links
    #print placement_constraints
    #print placement_senses

    problem.linear_constraints.add(lin_expr = rows, rhs = placement_constraints, senses = placement_senses)




def set_problem_data(p, num_vms, vm_consumption, vm_traffic_matrix, physical_config, link_capacity_consumed):
    p.set_problem_name("OpenStack VM placement")
    p.objective.set_sense(p.objective.sense.minimize)

    M = num_vms
    N = physical_config.num_racks

    # ====================
    # objective
    # ====================
    
    # the objectiv is to be refined
    # TODO
    objective = [0 for k in range(M*N+M*(M-1)/2*N*N+physical_config.num_links*2)]
    objective.append(1)


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

    add_constraints(p, M, vm_consumption, vm_traffic_matrix, link_capacity_consumed, physical_config)

    print "the problem data has been set!"



# the main interface
def migrate_policy(num_vms, vm_consumption, vm_traffic_matrix, original_placement, physical_config, link_capacity_consumed = []):
    M = num_vms
    N = physical_config
    
    placement = cplex.Cplex()
    set_problem_data(placement, M, vm_consumption, vm_traffic_matrix, physical_config, link_capacity_consumed)
    
    # try to tune
    placement.parameters.timelimit.set(1500.0)
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

    sol = placement.solution

    # solution.get_status() returns an integer code
    print "Solution status = " , sol.get_status(), ":",
    # the following line prints the corresponding string
    print sol.status[sol.get_status()]
    print "Solution value  = ", sol.get_objective_value()

    numrows = placement.linear_constraints.get_num()

#    for i in range(numrows):
#        print "Row %d:  Slack = %10f" % (i, sol.get_linear_slacks(i))
#
#    numcols = placement.variables.get_num()

#    for j in range(numcols):
#        print "Column %d:  Value = %10f" % (j, sol.get_values(j))

    placement.write("openstack_output.txt")
    print "THE END"
