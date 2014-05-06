#!/usr/bin/python
# OpenStack virtual machine placement
# try to solve the mixed integer programming problem with NO quadratic opjection

import sys
sys.path.append('/Users/wgs/projects/IBM/ILOG/CPLEX_Studio126/cplex/python/x86-64_osx/')
import cplex
import random

M = 4
N = 2

def set_problem_data(p):
    p.set_problem_name("OpenStack VM placement")
    p.objective.set_sense(p.objective.sense.minimize)

    # ====================
    # objective
    # ====================
    
    # the objectiv is to be refined
    # TODO
    objective = [k for k in range(M*N+M*(M-1)/2*N*N)]


    # ====================
    # variables
    # ====================

    # http://www-01.ibm.com/support/knowledgecenter/api/content/SSSA5P_12.6.0/ilog.odms.cplex.help/refcallablelibrary/mipapi/copyctype.html?locale=en
    # CBISN     coninuous binary integer semi-continuous semi-integer 
    variable_types = 'B' * ((M*N) + (M*(M-1)*N*N/2))
    
    upper_bound = [1 for k in range(M*N)] + [1 for k in range(M*(M-1)*N*N/2)]
    lower_bound = [0 for k in range(M*N)] + [0 for k in range(M*(M-1)*N*N/2)]

    names = []
    for k in range(M):
        for i in range(N):
            names.append("x_{0}_{1}".format(k, i))
    for i in range(M):
        for j in range(i+1, M):
            for u in range(N):
                for v in range(N): 
                    names.append("y_{0}_{1}_{2}_{3}".format(i, j, u, v))

    # for debugging
    print "obj: ", len(objective), objective
    print "ub: ", len(upper_bound), upper_bound
    print "lb: ", len(lower_bound), lower_bound
    print "types: ", len(variable_types), variable_types
    print "names: ", len(names), names

    p.variables.add(obj = objective, lb = lower_bound, ub = upper_bound, types = variable_types, names = names)



    # ====================
    # constraints
    # ====================
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

    print "\n"
    print "rows: ", rows

  
    placement_constraints = [1 for k in range(M)]
    for k in range (M*(M-1)*N*N/2):
        placement_constraints += [0, 0, 1]
    placement_senses = 'E' * M + 'GGL' * (M*(M-1)*N*N/2)       # E means 'equal'   
    
    print placement_constraints
    print placement_senses

    p.linear_constraints.add(lin_expr = rows, rhs = placement_constraints, senses = placement_senses)



    print "the problem data has been set!"


if __name__ == "__main__":
    
    placement = cplex.Cplex()
    set_problem_data(placement)
    
    # try to tune
    placement.parameters.timelimit.set(1200.0)
    #placement.parameters.threads.set(1)
    placement.parameters.emphasis.mip.set(1)
    placement.parameters.emphasis.memory.set(1)

    
    print "begin solving..."
    placement.solve()

    sol = placement.solution

    # solution.get_status() returns an integer code
    print "Solution status = " , sol.get_status(), ":",
    # the following line prints the corresponding string
    print sol.status[sol.get_status()]
    print "Solution value  = ", sol.get_objective_value()

    numrows = placement.linear_constraints.get_num()

    for i in range(numrows):
        print "Row %d:  Slack = %10f" % (i, sol.get_linear_slacks(i))

    numcols = placement.variables.get_num()

    for j in range(numcols):
        print "Column %d:  Value = %10f" % (j, sol.get_values(j))

    placement.write("openstack_output.txt")
