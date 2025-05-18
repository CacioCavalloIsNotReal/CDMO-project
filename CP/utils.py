from CP.CP_file_instance import *
import numpy as np
import json

def read_raw_instances(path:str) -> CP_file_instance:
    filename = "".join(path.split('/')[-1].split('.')[:-1])
    with open(path, 'r') as f:
        matrix = ''
        for i, line in enumerate(f):
            if i == 0:
                m = int(line)
            elif i == 1:
                n = int(line)
            elif i == 2:
                l = [int(x) for x in line.split() if x.strip()]   # load
            elif i == 3:
                s = [int(x) for x in line.split() if x.strip()]   # item size
            else:
                matrix += line[:-1] + '; '
    d = np.matrix(matrix[:-2]).tolist()
    instance = CP_file_instance(filename,m,n,l,s,d)
    return instance

def save_solutions(output_dict, path):
    """
    file 1.json
        nome solver:...
        nome solver:...
    """
    for filename in output_dict.keys():
        result = output_dict[filename]
        # if len(result)==0: continue
        # with open(path+'/'+filename, 'w') as file:
        #     json.dump(result, file, indent=4)
        save_result(result, path+'/'+filename)
            
def save_result(data, path):
    if not len(data)==0:
        with open(path, 'w') as file:
            json.dump(data, file, indent=4)
    