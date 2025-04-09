import math

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

    def set_solution(self, result_list:list):
        print(self.filename)
        print(result_list)  # list of Solution obj
        self.solution = result_list
        '''
        OUTPUT EXAMPLE
        [
            Solution(
                objective=16, 
                routes=[[1, 2, 3, 5, 7, 7, 7],
                        [4, 6, 7, 7, 7, 7, 7]],
                _output_item='16\n
                                1 2 3 5 7 7\n
                                4 6 7 7 7 7\n',
                _checker=''
            ),
            Solution(
                objective=15,
                routes=[[1, 2, 5, 4, 7, 7, 7],
                        [3, 6, 7, 7, 7, 7, 7]],
                _output_item='15\n
                                1 2 5 4 7 7\n
                                3 6 7 7 7 7\n',
                _checker=''
            ),
            Solution(
                objective=14,
                routes=[[1, 3, 4, 7, 7, 7, 7],
                        [2, 5, 6, 7, 7, 7, 7]],
                _output_item='14\n
                                1 3 4 7 7 7\n
                                2 5 6 7 7 7\n',
                _checker=''
            )
        ]
        '''
        ...

    def set_failed_solution(self):
        self.failed = True
        self.time = Solutions.MAX_TIME