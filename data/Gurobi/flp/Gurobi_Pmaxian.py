'''
GNU LESSER GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007
 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.
'''

# Building and Optimizing a p-Maxian facility location problem in 
#        Python/Gurobi[gurobipy]

# Maximizing the sum of total weighted travel cost for all clients


import numpy as np
import gurobipy as gbp
import time
t1 = time.time()


def GbpPmax():
    #     1. Data
    # Weighted Costs
    # Cost Matrix
    Cij = np.random.randint(100, 1000, 25)
    Cij = Cij.reshape(5,5)
    # Weights Matrix
    Ai = np.random.randint(1, 100, 5)
    Ai = Ai.reshape(1,len(Ai))
    # Demand Sum
    AiSum = np.sum(Ai)
    # Weighted Cost Coefficients for Decision Variables
    Sij = Ai * Cij
    client_nodes = range(len(Sij))
    service_nodes = range(len(Sij[0]))
    
    mPMaxP = gbp.Model(' -- p-Maxian -- ')
    
    gbp.setParam('MIPFocus', 2)
    
    # Client IxJ
    client_var = []
    for orig in client_nodes:
        client_var.append([])
        for dest in service_nodes:
            client_var[orig].append(mPMaxP.addVar(vtype=gbp.GRB.BINARY, 
                                                obj=Sij[orig][dest], 
                                                name='x'+str(orig+1)+'_'+str(dest+1)))
    #J
            serv_var = []
    for dest in service_nodes:
        serv_var.append([])
        serv_var[dest].append(mPMaxP.addVar(vtype=gbp.GRB.BINARY, 
                                        name='y'+str(dest+1)))
    mPMaxP.update()
    mPMaxP.setObjective(gbp.quicksum(Sij[orig][dest]*client_var[orig][dest] 
                            for orig in client_nodes for dest in service_nodes), 
                            gbp.GRB.MINIMIZE)
    for orig in client_nodes:
        mPMaxP.addConstr(gbp.quicksum(client_var[orig][dest] 
                            for dest in service_nodes) == 1)
    for orig in service_nodes:
        for dest in client_nodes:
            mPMaxP.addConstr((serv_var[orig][0] - client_var[dest][orig] >= 0))
    mPMaxP.addConstr(gbp.quicksum(serv_var[dest][0] for dest in service_nodes) == 2)
    try:
        mPMaxP.optimize()
    except Exception as e:
        print(' < ISSUE : ', e, ' >')
    mPMaxP.write('path.lp')
    selected = []
    for v in mPMaxP.getVars():
        if 'x' in v.VarName:
            pass
        elif v.x > 0:
            var = '%s' % v.VarName
            selected.append(var)
            print('    |                                            ', var)
    val = mPMaxP.objVal
    print('    | Objective Value(miles) ------------------- ', val)
    avg = float(mPMaxP.objVal)/float(AiSum)
    print('    | Avg. Value / Client(miles) --------------- ', avg)
    
GbpPmax()