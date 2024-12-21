# -*- coding: utf-8 -*-
'''
GNU LESSER GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007
 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.
'''

# Building and Optimizing an Anti-Cover 2 facility location problem in 
#        Python/Gurobi[gurobipy]

# The ACLP2 maximizes the number of service facilities to be sited
#       while minimum separation distance is constrained.

import numpy as np
import gurobipy as gbp
import time
t1 = time.time()

def GbpACLP2():
    # Cost Matrix
    Dij = np.random.randint(1, 20, 16)
    Dij = Dij.reshape(4,4)
    # Minimum Separation Distance
    r = 10
    service_nodes = range(len(Dij))
    
    #     2. Create Model, Set MIP Focus, Add Variables, & Update Model
    m = gbp.Model(" -- ACLP2 -- ")
    # Set MIP Focus to 2 for optimality
    gbp.setParam('MIPFocus', 2)
    # Add Service Decision Variables
    serv_var = []
    for orig in service_nodes:
        serv_var.append(m.addVar(vtype=gbp.GRB.BINARY,
                                    ub = 1,
                                    name='x'+str(orig+1)))
    
    # Update Model Variables
    m.update()       
    
    #     4. Set Objective Function --> Maximize sited facilities with no overlap (r)
    m.setObjective(gbp.quicksum(serv_var[dest] 
                                for dest in service_nodes), 
                                gbp.GRB.MAXIMIZE)
    
    #    5. Add Constraints 
    #Add Adjacency Pairwise Constraints
    for orig in service_nodes:
        for dest in service_nodes:
            if orig != dest and Dij[orig][dest] < r:
                m.addConstr((serv_var[orig] + serv_var[dest]  <= 1))    
            else:
                pass
    
    #     6. Optimize and Print Results
    try:
        m.optimize()
    except Exception as e:
        print '   ################################################################'
        print ' < ISSUE : ', e, ' >'
        print '   ################################################################'
    
    t2 = time.time()-t1
    print '**********************************************************************'
    selected = []
    for v in m.getVars():
        if v.x > 0:
            var = '%s' % v.VarName
            selected.append(v.x)
            print '    |                                                       ', var
    print '    | Selected Facility Locations ------------------------  ^^^^ '
    print '    | Minimum Distance (r) ------------------------------- ', r
    print '    | Service Nodes -------------------------------------- ', len(service_nodes)
    print '    | Candidate Facilities Sited without (r) overlap ----- ', len(selected)
    print '    | Real Time to Optimize (sec.) ----------------------- ', t2
    print '*****************************************************************************************'
    m.write("path.lp")
    
try:
    GbpACLP2()
    print '\nJames Gaboardi, 2015'
except Exception as e:
    print '   ################################################################'
    print ' < ISSUE : ', e, ' >'
    print '   ################################################################'