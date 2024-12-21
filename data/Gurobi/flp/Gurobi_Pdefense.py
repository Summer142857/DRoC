'''
GNU LESSER GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007
 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.
'''

# Building and Optimizing a p-Defense-Sum facility location problem in 
#        Python/Gurobi[gurobipy]
#
# Maximizing the total distance bewteen facilities (generally noxious)

# Terminology & General Background for Facility Location and Summation Notation:

#   *   The objective of the p-Defense-Sum Facility Location Problem is to 
#        maximize the minimum distance bewteen facilities (generally noxious).

#   *   [i] - a specific origin
#   *   [j] - a specifc destination
#   *   [n] - the set of origins
#   *   [m] - the set of destinations
#   *   [Cij] - matrix of travel costs between nodes
#   *	[yi] - each service facility
#   *   [p] - the number of facilities to be sited

#    1. Imports and Data Creation
# Imports
import numpy as np
import gurobipy as gbp
import time
t1 = time.time()   

def GbpPdefSum():    
    # Distance Matrix --> 20x20
    Cij = np.random.randint(100, 1000, 400)
    Cij = Cij.reshape(20,20)
    # Service Nodes
    service_nodes = range(len(Cij))
    
    
    #     2. Create Model, Set MIP Focus, Add Variables, & Update Model
    mPDPsum = gbp.Model(' -- p-Defense-Sum -- ')
    # Set MIP Focus to 2 for optimality
    gbp.setParam('MIPFocus', 2)
    
    #     3. Add Variables
    # Add Decision Variables
    # Service Facility IxJ
    serv_var = []
    for dest in service_nodes:
        serv_var.append(mPDPsum.addVar(vtype=gbp.GRB.BINARY,
                                    ub = 1,
                                    name='y'+str(dest+1)))
    
    # Update Model Variables
    mPDPsum.update()
    
    #     4. Set Objective --> Maximize Sum of Distance        
    mPDPsum.setObjective(gbp.quicksum(Cij[orig][dest]*serv_var[orig] 
                                    for orig in service_nodes 
                                    for dest in service_nodes), 
                                    gbp.GRB.MAXIMIZE)            
    
    #     5. Add Constriants         
    # Add Facility Constraint --> [p=2]
    mPDPsum.addConstr(gbp.quicksum(serv_var[dest] for dest in service_nodes) == 2)                        
    
    #     6. Optimize and Print Results
    try:
        mPDPsum.optimize()
    except Exception as e:
        print(' < ISSUE : ', e, ' >')
    t2 = time.time() - t1
    mPDPsum.write('path.lp')
    selected = []
    for v in mPDPsum.getVars():
        if v.x > 0:
            var = '%s' % v.VarName
            selected.append(var)
            print('    |                                            ', var)
    print('    | Selected Facility Locations --------------  ^^^^ ')
    print('    | Candidate Facilities [p] ----------------- ', len(selected))
    val = mPDPsum.objVal
    print('    | Objective Value -------------------------- ', val)
    print('    | Real Time to Optimize (sec.) ------------- ', t2)
    
GbpPdefSum()
