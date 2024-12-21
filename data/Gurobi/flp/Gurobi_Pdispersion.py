#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
GNU LESSER GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007
 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.
'''
'''
Adapted from:   
    M. J. Kuby. 
    1988. 
    Programming models for facility dispersion: the p-dispersion 
            and maxisum dispersion problems. 
    Mathematical and Computer Modelling. 
    10 (4):316-329.
'''

# Maximizing the minimum distance bewteen facilities (generally noxious)

# Terminology & General Background for Facility Location and Summation Notation:

#   *   [i][j] - matrix dimensions
#   *   [dij] - matrix of travel costs between nodes
#   *   [M] - largest value in dij
#   *   [D] - Maximized minimum distance between facilities
#   *	[yi] - each service facility
#   *   [p] - the number of facilities to be sited
##########################################################################################


# Imports
import numpy as np
import gurobipy as gbp
import time
np.random.seed(352)

def Gurobi_pDispersion(dij, p_facilities, total_facilities):
    
    t1 = time.time()
    
    facility_range = range(total_facilities)     # range of total facilities
    M = np.amax(dij)                             # Max Value in dij
    
    mPDP = gbp.Model(" -- p-Dispersion -- ")    # Instantiate a model
    gbp.setParam('MIPFocus', 2)                 # Set MIP Focus to 2 for optimality
    
    # Add Decision Variables
    facility_variable = []
    for destination in facility_range:
        facility_variable.append(mPDP.addVar(vtype=gbp.GRB.BINARY,
                                                lb=0,
                                                ub=1,
                                              name='y'+str(destination+1)))
    # Add Maximized Minimum Variable
    D = mPDP.addVar(vtype=gbp.GRB.CONTINUOUS,
                       lb=0,
                       ub=gbp.GRB.INFINITY,
                     name='D')
    # Update Model Variables
    mPDP.update()       
    
    #  Set Objective Function
    mPDP.setObjective(D, gbp.GRB.MAXIMIZE)
    
    # Add Facility Constraint
    mPDP.addConstr(gbp.quicksum(facility_variable[destination]                         \
                                                    for destination in facility_range) \
                                                    == p_facilities)                        
    
    # Add Inter-Facility Distance Constraints ==> n(n-1)/2
    for origin in facility_range:
        for destination in facility_range:
            if destination > origin:
                mPDP.addConstr(
                                dij[origin][destination]               \
                                + M * 2                                \
                                - M * facility_variable[origin]        \
                                - M * facility_variable[destination]   \
                                >= D)
            else:
                pass
    
    #  Optimize and Print Results
    mPDP.optimize()
    mPDP.write('path.lp')
    t2 = round(round(time.time()-t1, 3)/60, 5)
    selected_facilities = []
    for v in mPDP.getVars():
        if 'D' in v.VarName:
            pass
        elif v.x > 0:
            var = '%s' % v.VarName
            selected_facilities.append(var)
            print('    |                                            ', var)
    print('    | Selected Facility Locations -------------  ^^^^ ')
    print('    | Candidate Facilities [p] ---------------- ', len(selected_facilities))
    print('    | Largest Value in dij (M) ---------------- ', M)
    print('    | Objective Value (D) --------------------- ', mPDP.objVal)
    print('    | Matrix Dimensions ----------------------- ', dij.shape)
    print('    | Real Time to Solve (minutes)------------- ', t2)
##########################################################################################
# Data can be read-in or simulated

#  Total Number of Facilities  
Service = matrix_vector = 200       # matrix_vector * matrix_vector for total facilities

P = candidate_facilities = 2

# Cost Matrix
Cost_Matrix = np.random.randint(3, 
                                50, 
                                matrix_vector*matrix_vector)
Cost_Matrix = Cost_Matrix.reshape(matrix_vector,matrix_vector)

# Call Function   
Gurobi_pDispersion(
                    dij=Cost_Matrix, 
                    p_facilities=P, 
                    total_facilities=Service)
