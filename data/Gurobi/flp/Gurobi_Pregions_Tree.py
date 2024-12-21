'''
GNU LESSER GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007
 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.
'''

# Building and Optimizing a p-Regions Tree Problem in
#        Python/Gurobi[gurobipy]

'''
    Adapted from:
    
    Duque, Juan C
    Church, Richard L
    Middleton, Richard S
    2011
    The p-Regions Problem
    Geographical Analysis
    43
    104-126
    '''

import numpy as np
import gurobipy as gbp
import time
t1 = time.time()



mPRegT = gbp.Model(' -- p-Regions Tree -- ')

gbp.setParam('MIPFocus', 2)

# T IxJ
t_var = []
for orig in client_nodes:
    t_var.append([])
    for dest in service_nodes:
        t_var[orig].append(mPRegT.addVar(vtype=gbp.GRB.BINARY, 
                                            obj=Sij[orig][dest], 
                                            name='x'+str(orig+1)+'_'+str(dest+1)))


mPRegT.update()
mPRegT.setObjective(gbp.quicksum(Tij[orig][dest]*dij[orig][dest] 
                        for orig in client_nodes for dest in service_nodes), 
                        gbp.GRB.MAXIMIZE)
