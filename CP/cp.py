import os
import numpy as np
import datetime
import minizinc
from minizinc import Instance, Model, Solver, Status
from CP.Solutions import *
import time

debug = False

if debug:
    import logging
    logging.basicConfig(filename="minizinc-python.log", level=logging.DEBUG)
    print("Minizinc Python API version:", minizinc.__version__, '\n')
    module_path = os.path.dirname(os.path.realpath(__file__))
    print(module_path)

def cp_model(instance_file:str,
             solver:str = 'chuffed', # gecode   chuffed
             time_limit:int=300000,
             verbose = True,
             symm_break = False
            )->Solutions:

    module_path = os.path.dirname(os.path.realpath(__file__))
    filename = instance_file.split('/')[-1]
    current_solution = Solutions(filename=filename)
    if symm_break:
        cp_model = Model(module_path+'/cp_sb.mzn')
    else:
        cp_model = Model(module_path+'/cp.mzn')
    cp_model.add_file(instance_file, parse_data=True)

    solver_ins = Solver.lookup(solver)
    instance = Instance(solver_ins, cp_model)
    print(filename)
    timedelta = datetime.timedelta(milliseconds=time_limit)
    try:
        #   ⚠⚠⚠ DANGER ZONE ⚠⚠⚠
        start_time = time.time()
        result = instance.solve(timeout=timedelta,
                                intermediate_solutions=False,
                                verbose=False)
        total_time = time.time() - start_time
        if result.solution:
            data = {'max_distance'      :result['max_distance'],
                    'courier_distances' :result['courier_distances'],
                    'node_subset'       :result['node_subset'],
                    'edge_subset'       :result['edge_subset'],
                    'current_load'      :result['current_load'],
                    'status'            :result.status  # OPTIMAL_SOLUTION, SATISFIED, UNSATISFIABLE, UNKNOWN, ALL_SOLUTIONS
                    }
            
            current_solution.set_exec_time(total_time)
            current_solution.set_solution(data)
        else:
            current_solution.set_failed_solution()

    except Exception as e:
        if verbose:
            print("unexpected error-")
            print(e)
        current_solution.set_failed_solution()
        
    return current_solution