'''
GNU LESSER GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007
 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.
'''

# Building and Optimizing a P-Anti-Center facility location problem in 
#        Python/Gurobi[gurobipy]
#
# Maximizing the Maximum average travel cost from client to service facility 
#        

import numpy as np
import gurobipy as gbp
import time
t1 = time.time()

def GbpApC():
    #           1. Create Data
    # Distance Matrix
    Dij = np.random.randint(100, 1000, 25)
    Dij = Dij.reshape(5,5)
    rows, cols = Dij.shape
    client_nodes = range(rows)
    service_nodes = range(cols)
    
    #     2. Create Model, Set MIP Focus, Add Variables, & Update Model
    mPACP = gbp.Model(" -- P-Anti-Center -- ")
    # Set MIP Focus to 2 for optimality
    gbp.setParam('MIPFocus', 2)
    # Add Client Decision Variables
    client_var = []
    for orig in client_nodes:
        client_var.append([])
        for dest in service_nodes:
            client_var[orig].append(mPACP.addVar(vtype=gbp.GRB.BINARY, 
                                                obj=Dij[orig][dest], 
                                                name='x'+str(orig+1)+'_'+
                                                str(dest+1)))
    # Add Service Decision Variables
    serv_var = []
    for dest in service_nodes:
        serv_var.append([])
        serv_var[dest].append(mPACP.addVar(vtype=gbp.GRB.BINARY, 
                                        name='y'+str(dest+1)))
    # Add Minimized Maximum Average Variable
    W = mPACP.addVar(vtype=gbp.GRB.CONTINUOUS,
                name='W')
    # Update Model Variables
    mPACP.update()       
    
    #     3. Set Objective Function
    mPACP.setObjective(W, gbp.GRB.MAXIMIZE)
    
    #     4. Add Constraints 
    #Add Assignment Constraints
    for orig in client_nodes:
        mPACP.addConstr(gbp.quicksum(client_var[orig][dest] 
                            for dest in service_nodes) == 1)
    # Add Opening Constraints
    for dest in service_nodes:
        for orig in client_nodes:
            mPACP.addConstr((serv_var[dest][0] - client_var[orig][dest] >= 0))
    # Add Facility Constraint -->  [p=2]
    mPACP.addConstr(gbp.quicksum(serv_var[dest][0] for dest in service_nodes) == 2)
    # Add Maximized Maximum Time Constraint
    for orig in client_nodes:
        mPACP.addConstr(gbp.quicksum(Dij[orig][dest]*client_var[orig][dest]
                            for dest in service_nodes) - W >= 0)
    
    #      5. Optimize and Print Results
    try:
        mPACP.optimize()
    except Exception as e:
        print(' < ISSUE : ', e, ' >')
    mPACP.write('path.lp')
    selected = []
    for v in mPACP.getVars():
        if 'x' in v.VarName:
            pass
        elif 'W' in v.VarName:
            pass
        elif v.x > 0:
            var = '%s' % v.VarName
            selected.append(var)
            print('    |                                            ', var)
    print('    | Selected Facility Locations --------------  ^^^^ ')
    print('    | Candidate Facilities [p] ----------------- ', len(selected))
    val = mPACP.objVal
    print('    | Objective Value(miles) ------------------- ', val)
    print('*************************************************************************')


GbpApC()