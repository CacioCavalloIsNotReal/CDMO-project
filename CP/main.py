from CP.utils import read_raw_instances
from CP.CP_file_instance import *
from CP.cp import *
from tqdm import tqdm
     
def run_cp():
    convert_files=False
    solvers = ['gecode', 'chuffed']

    module_path = os.path.dirname(os.path.realpath(__file__))
    savepath = module_path+'/instances/'
    instances_path = "/".join(module_path.split('/')[:-1]+['instances'])
    instances_names = os.listdir(instances_path)

    if convert_files:
        for name in tqdm(instances_names, desc="Converting instances into .dzn files"):
            # creating the .dzn file
            path = instances_path+'/'+name
            istc = read_raw_instances(path)
            cp_path = istc.to_file(savepath, raw=False)

    solutions = {solver:[] for solver in solvers}
    dzn_names = os.listdir(savepath)    # list of dzn contained into CP/instances
    for solver in solvers:
        print(f"************************************using {solver} solver************************************")
        for name in dzn_names[:1]:

            path = savepath+'/'+name
            solutions[solver].append(cp_model(path, verbose=True, symm_break=True)) 

    print("ayos")
    # for solution in solutions:
    #     print(solution.failed)

if __name__ == '__main__':
    run_cp()