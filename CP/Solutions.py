import math
import numpy as np
from minizinc import Status

class Solutions:
    '''
    this class is meant to represent solutions of the solver
    '''
    MAX_TIME = 300  # maximum time allowed, in sec
    def __init__(self, filename:str, solver_type:str):
        self.filename = filename
        self.solver_type = solver_type
        self.failed = False
        self.solution = {solver_type : {
                    "time":-1,
                    "optimal":False,
                    "obj":-1,
                    "sol":[]
                }
            }
        self.data = None

    def convert_solution(self, data):
        data = np.array(data)
        out = []

        for row in data:
            row = np.array(row)
            max_val = np.max(row)

            valid_indices = [i for i, val in enumerate(row) if val > 1 and val < max_val]
            
            sorted_indices = sorted(valid_indices, key=lambda i: row[i])
            out.append([valore +1 for valore in sorted_indices])

        return out

    def set_exec_time(self, time:int=0):
        self.solution[self.solver_type]["time"] = time

    def set_solution(self, data):
        self.data = data
        if (self.data['status'] == Status.UNSATISFIABLE or
            self.data['status'] == Status.UNKNOWN or
            self.data['status'] == Status.ERROR):
            self.set_failed_solution()
        self.solution[self.solver_type]["time"] = int(data["time"]) if data["time"]<300 else 300
        self.solution[self.solver_type]["optimal"] = True if data['status'] == Status.OPTIMAL_SOLUTION else False
        self.solution[self.solver_type]["obj"] = data['max_distance']

        self.solution[self.solver_type]["sol"] = self.convert_solution(data['path'])

    def set_failed_solution(self):
        self.failed = True
        self.time = Solutions.MAX_TIME
        self.solution[self.solver_type]["time"] = Solutions.MAX_TIME
        self.solution[self.solver_type]["optimal"] = False

    def get_solution(self):
        return self.solution
            