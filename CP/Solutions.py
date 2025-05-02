import math
from minizinc import Status

class Solutions:
    '''
    this class is meant to represent solutions of the solver
    '''
    MAX_TIME = 300  # maximum time allowed, in sec
    def __init__(self, filename:str):
        self.filename = filename
        self.failed = False
        self.solution = None
        self.time = -1

    def set_exec_time(self, time:int=0):
        self.time = time

    def set_solution(self, data):
        print(self.filename)
        print(data)  # list of Solution obj
        self.solution = data
        if self.solution['status'] == Status.UNSATISFIABLE:
            self.set_failed_solution()

    def set_failed_solution(self):
        self.failed = True
        self.time = Solutions.MAX_TIME