import os
from tqdm import tqdm
from .smt_utils import *
from .smt_model import *
import numpy as np

MAX_TIME = 300

def execute_smt(symbreak: bool = False, instance_name: str = "all"):
    os.makedirs("./SMT/result_symbreak", exist_ok=True)
    os.makedirs("./SMT/result_nosymbreak", exist_ok=True)

    module_path = os.path.dirname(os.path.realpath(__file__))
    outpath = "/".join(module_path.split('/')[:-1]+['res', 'SMT'])
    os.makedirs(outpath, exist_ok=True)

    instances_folder =  "/".join(module_path.split('/')[:-1]+['instances'])
    file_names = sorted(os.listdir(instances_folder) )
    if instance_name == "all":
        print("Running on all instances...")
        pbar = tqdm(file_names)
        for name in pbar:
            for sb in [True, False]:
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
                    lower = generate_lowerbound(d, n),
                    symm_break=sb,
                    timeout=MAX_TIME
                )
                if sb:
                    write_output(prepare_solution(result_dict), f'./SMT/result_symbreak/{filename}.json')
                else:
                    write_output(prepare_solution(result_dict), f'./SMT/result_nosymbreak/{filename}.json')

                combine_results(
                    result_nosymbreak_dir="./SMT/result_nosymbreak",
                    result_symbreak_dir="./SMT/result_symbreak"
                )

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
                lower = generate_lowerbound(d, n),
                symm_break=symbreak,
                timeout=MAX_TIME 
            )
        if symbreak:
            write_output(prepare_solution(result_dict), f'./SMT/result_symbreak/{filename}.json')
        else:
            write_output(prepare_solution(result_dict), f'./SMT/result_nosymbreak/{filename}.json')

    combine_results(
        result_nosymbreak_dir="./SMT/result_nosymbreak",
        result_symbreak_dir="./SMT/result_symbreak"
    )
    
