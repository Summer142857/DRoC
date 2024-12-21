'''
GNU LESSER GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007
 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.
'''

# Building and Optimizing a p-Center facility location problem in
#        Python/Gurobi[gurobipy]
# Change dimensions of Cij and the Facility Constraint for varying
#        spatial extents
# The dimension of the problem are SERVICExCLIENT (rowXcolumn)
#        unlike equation formulation CLIENTxSERVICE (rowXcolumn)

import numpy as np
import gurobipy as gbp
import time
t1 = time.time()

#           1. Read In (or Create) Data
'''
# Cost Matrix
Cij = np.fromfile('path.txt', dtype=float, sep='\n')
Cij = Cij.reshape(#,#)
'''
# Cost Matrix
Cij = np.random.randint(100, 1000, 25)
Cij = Cij.reshape(5,5)

client_nodes = range(len(Cij[0]))
service_nodes = range(len(Cij))

#           2. Create Model, Set MIP Focus, Add Variables, & Update Model
m = gbp.Model(' -- P-Center -- ')
# Set MIP Focus to 2 for optimality
gbp.setParam('MIPFocus', 2)
# Add Client Decision Variables
client_var = []
for orig in service_nodes:
    client_var.append([])
    for dest in client_nodes:
        client_var[orig].append(m.addVar(vtype=gbp.GRB.BINARY, 
                                            obj=Cij[orig][dest], 
                                            name='x'+str(orig+1)+'_'+str(dest+1)))
# Add Service Decision Variables
serv_var = []
for dest in service_nodes:
    serv_var.append([])
    serv_var[dest].append(m.addVar(vtype=gbp.GRB.BINARY, 
                                    name='y'+str(dest+1)))
# Add Minimized Maximum Average Variable
W = m.addVar(vtype=gbp.GRB.CONTINUOUS,
            name='W')
# Update Model Variables
m.update()       

#           3. Set Objective Function
m.setObjective(W, gbp.GRB.MINIMIZE)

#           4. Add Constraints
#Add Assignment Constraints
for orig in client_nodes:
    m.addConstr(gbp.quicksum(client_var[dest][orig] 
                        for dest in service_nodes) == 1, 
                        'Assignment_Constraint_%d' % orig)
# Add Opening Constraints
for dest in service_nodes:
    for orig in client_nodes:
        m.addConstr((serv_var[dest][0] - client_var[dest][orig] >= 0), 
                        'Opening_Constraint_%d_%d' % (dest, orig))
# Add Facility Constraint --> [p=2]
m.addConstr(gbp.quicksum(serv_var[dest][0] for dest in service_nodes) == 2, 
                        'Facility_Constraint')

# Add Minimized Maximum Time Constraint
for orig in client_nodes:
    m.addConstr(gbp.quicksum(Cij[dest][orig]*client_var[dest][orig]
                        for dest in service_nodes) - W <= 0,
                        'Max_Time_Constraint_%d' % orig)

#           5. Optimize and Print Results
m.optimize()
t2 = time.time()-t1
selected = []
for v in m.getVars():
    if 'x' in v.VarName:
        pass
    elif 'W' in v.VarName:
        pass
    elif v.x > 0:
        var = '%s' % v.VarName
        selected.append(var)
        print('    |                                            ', var)
print('    | Candidate Facilities [p] ----------------- ', len(selected))
val = m.objVal
print('    | Objective Value -------------------------- ', val)
print('    | Real Time to Optimize (sec.) ------------- ', t2)