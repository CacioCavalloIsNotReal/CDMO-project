import os
from tqdm import tqdm
from .smt_utils import *
from .smt_model import *
import numpy as np

MAX_TIME = 300

def choose_instance(instance_name):
    if int(instance_name) in range(1, 9):
        instance = f"inst0{instance_name}.dat"
    elif int(instance_name) in range(10, 21):
        instance = f"inst{instance_name}.dat"
    return instance

def prepare_solution(input):
    # NB sta cosa va calcolata soltanto se è stata trovata una soluzione!
    item_order = np.array(input['item_order']).T
    couriers = np.unique(item_order[0])

    percorso = []
    for courier in couriers:
        mask = item_order[0] == courier
        courier_m = item_order[:, mask]
        positions = np.argsort(courier_m[2])
        n_zeros = sum(courier_m[2]==0)
        m_idxs = positions[n_zeros:]
        trip = [int(courier_m[1][idx]+1) for idx in m_idxs]
        percorso.append(trip)

    print(input)
    output = {
        'time' : int(input['time']) if  input['time']<=300 else 300 ,
        'optimal' : input['solution']  ,    # non ne sono completamente sicuro
        'obj' : input['max_distance'] ,
        'sol': percorso
        }

    print(output)
    return output

def execute_smt(symbreak: bool = False, instance_name: str = "all"):
    os.makedirs("./SMT/result_symbreak", exist_ok=True)
    os.makedirs("./SMT/result_nosymbreak", exist_ok=True)

    module_path = os.path.dirname(os.path.realpath(__file__))
    outpath = "/".join(module_path.split('/')[:-1]+['res', 'SMT'])

    instances_folder =  "/".join(module_path.split('/')[:-1]+['instances'])
    file_names = sorted(os.listdir(instances_folder) )
    if instance_name == "all":
        print("Running on all instances...")
        pbar = tqdm(file_names)
        for name in pbar:
            pbar.set_description(f"solving problem {name}")
            path=instances_folder+f'/{name}'
            filename,m,n,l,s,d = read_raw_instances(path)
            result_dict = run_z3_with_external_timeout(
                external_timeout_seconds=MAX_TIME,
                model_func=my_model,
                m=m, 
                n=n, 
                l=l, 
                s=s, 
                d=d,
                symm_break=symbreak, # Prova con True o False
                timeout=MAX_TIME # Timeout interno per Z3 (in ms)
            )
            if symbreak:
                write_output(prepare_solution(result_dict), f'./SMT/result_symbreak/{filename}.json')
            else:
                write_output(prepare_solution(result_dict), f'./SMT/result_nosymbreak/{filename}.json')

    else:
        instance_name = choose_instance(instance_name)
        pbar = tqdm([instance for instance in file_names if instance == instance_name])
        for name in pbar:
            pbar.set_description(f"solving problem {name}")
            path=instances_folder+f'/{name}'
            filename,m,n,l,s,d = read_raw_instances(path)
            result_dict = run_z3_with_external_timeout(
                external_timeout_seconds=MAX_TIME,
                model_func=my_model,
                m=m, 
                n=n, 
                l=l, 
                s=s, 
                d=d,
                symm_break=symbreak, # Prova con True o False
                timeout=MAX_TIME # Timeout interno per Z3 (in ms)
            )
        if symbreak:
            write_output(prepare_solution(result_dict), f'./SMT/result_symbreak/{filename}.json')
        else:
            write_output(prepare_solution(result_dict), f'./SMT/result_nosymbreak/{filename}.json')

    combine_results(
        result_nosymbreak_dir="./SMT/result_nosymbreak",
        result_symbreak_dir="./SMT/result_symbreak"
    )
    
