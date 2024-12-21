'''
GNU LESSER GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007
 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.
'''

# Building and Optimizing a Capacitated P-Anti-Center facility location problem in 
#        Python/Gurobi[gurobipy]
#
# Maximizing the Maximum average travel cost from client to service facility 
#        while constraining for demand capacity at service facilities 

import numpy as np
import gurobipy as gbp
import time
t1 = time.time()

#           1. Create Data
# Distance Matrix
Dij = np.random.randint(100, 1000, 25)
Dij = Dij.reshape(5,5)
# Demand
qi = np.random.randint(1, 100, 5)
# Capacity
Qj = np.random.randint(200, 300, 5)
rows, cols = Dij.shape
client_nodes = range(rows)
service_nodes = range(cols)

#     2. Create Model, Set MIP Focus, Add Variables, & Update Model
mCPACP = gbp.Model(" -- Capacitated P-Anti-Center -- ")
# Set MIP Focus to 2 for optimality
gbp.setParam('MIPFocus', 2)
# Add Client Decision Variables
client_var = []
for orig in client_nodes:
    client_var.append([])
    for dest in service_nodes:
        client_var[orig].append(mCPACP.addVar(vtype=gbp.GRB.BINARY, 
                                            obj=Dij[orig][dest], 
                                            name='x'+str(orig+1)+'_'+
                                            str(dest+1)))
# Add Service Decision Variables
serv_var = []
for dest in service_nodes:
    serv_var.append([])
    serv_var[dest].append(mCPACP.addVar(vtype=gbp.GRB.BINARY, 
                                    name='y'+str(dest+1)))
# Add Minimized Maximum Average Variable
W = mCPACP.addVar(vtype=gbp.GRB.CONTINUOUS,
            name='W')
# Update Model Variables
mCPACP.update()       

#     3. Set Objective Function
mCPACP.setObjective(W, gbp.GRB.MAXIMIZE)

#     4. Add Constraints 
#Add Assignment Constraints
for orig in client_nodes:
    mCPACP.addConstr(gbp.quicksum(client_var[orig][dest] 
                        for dest in service_nodes) == 1)
# Add Opening Constraints
for dest in service_nodes:
    for orig in client_nodes:
        mCPACP.addConstr((serv_var[dest][0] - client_var[orig][dest] >= 0))
# Add Facility Constraint -->  [p=2]
mCPACP.addConstr(gbp.quicksum(serv_var[dest][0] for dest in service_nodes) == 2)
# Add Maximized Maximum Time Constraint
for orig in client_nodes:
    mCPACP.addConstr(gbp.quicksum(Dij[orig][dest]*client_var[orig][dest]
                        for dest in service_nodes) - W >= 0)
# Add Capacity Constraints
for dest in service_nodes:
    mCPACP.addConstr(gbp.quicksum(qi[orig]*client_var[orig][dest]
                        for orig in client_nodes) - 
                        Qj[dest]*serv_var[dest][0] <= 0)

#      5. Optimize and Print Results
mCPACP.optimize()
mCPACP.write('path.lp')
print('\n*************************************************************************')
selected = []
for v in mCPACP.getVars():
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
val = mCPACP.objVal
print('    | Objective Value(miles) ------------------- ', val)