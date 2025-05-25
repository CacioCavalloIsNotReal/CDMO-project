import numpy as np
import threading
import queue
import time
import json
import os
import sys
from z3 import Z3Exception

def read_raw_instances(path:str):
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
    return filename,m,n,l,s,d

def run_z3_with_external_timeout(external_timeout_seconds, model_func, *args, **kwargs):
    result_queue = queue.Queue()
    opt_instance_container = [None] 

    kwargs_for_model = kwargs.copy()
    kwargs_for_model['opt_container'] = opt_instance_container

    def worker():
        try:
            res = model_func(*args, **kwargs_for_model)
            result_queue.put(res)
        except Z3Exception as z3e:
            print(f"Z3Exception in worker: {z3e}")
            result_queue.put({
                'solution_found': False, 
                'status': 'z3_exception_in_worker',
                'error': str(z3e),
                'reason_unknown': 'interrupted' if 'interrupted' in str(z3e).lower() else str(z3e)
            })
        except Exception as e:
            print(f"Generic error in worker: {e}")
            result_queue.put({
                'solution_found': False, 
                'status': 'error_in_worker', 
                'error': str(e)
            })

    thread = threading.Thread(target=worker)
    thread.daemon = True 
    
    start_execution_time = time.time()
    thread.start()
    thread.join(timeout=external_timeout_seconds)
    
    actual_execution_time = time.time() - start_execution_time

    if thread.is_alive():
        print(f"External timeout {external_timeout_seconds} expired. trying to block the z3 solver")
        solver_to_interrupt = opt_instance_container[0]
        interrupted_internally = False
        if solver_to_interrupt:
            try:
                solver_to_interrupt.interrupt()
                interrupted_internally = True
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("no istance found")

        additional_wait_time = 2.0
        thread.join(timeout=additional_wait_time)

        if thread.is_alive():
            return {
                'solution_found': False, 
                'status': 'timeout_external_stuck_after_interrupt',
                'time': actual_execution_time + additional_wait_time,
                'reason_unknown': 'external_timeout_thread_stuck'
            }
        else:
            try:
                result = result_queue.get_nowait()
                if 'time' not in result: result['time'] = actual_execution_time 
                if interrupted_internally and 'status' in result and result['status'] != 'z3_exception_in_worker':
                    if result.get('status') == 'unknown':
                         result['reason_unknown'] = result.get('reason_unknown', '') + '; external_interrupt_attempted'
                    result['status'] += '_after_external_interrupt'

                if result.get('status', '').startswith('unknown') and 'reason_unknown' in result:
                    result['reason_unknown'] = f"External interrupt likely cause: {result['reason_unknown']}"
                elif result.get('status', '').startswith('unknown'):
                     result['reason_unknown'] = "External interrupt likely cause"
                
                return result
            except queue.Empty:
                return {
                    'solution_found': False, 
                    'status': 'timeout_external_interrupted_no_result_in_queue',
                    'time': actual_execution_time,
                    'reason_unknown': 'external_timeout_no_result_after_interrupt'
                }
    else:
        try:
            result = result_queue.get_nowait()
            if 'time' not in result: result['time'] = actual_execution_time
            return result
        except queue.Empty:
            return {
                'solution_found': False, 
                'status': 'thread_completed_no_result_in_queue',
                'time': actual_execution_time,
                'error': 'Worker thread finished but no result was found in the queue.'
            }
        
def write_output(results, output_path):
    """Writes the results to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        with open(output_path, 'w') as f:
            output_data = {"z3": results}
            json.dump(output_data, f, indent=4)
        print(f"Results written to {output_path}")
    except Exception as e:
        print(f"Error writing output file {output_path}: {e}", file=sys.stderr)

def combine_results(result_nosymbreak_dir, result_symbreak_dir):
    
    combined_results = {}
    
    for results_file in sorted(os.listdir(result_nosymbreak_dir)):
        if results_file.startswith('.'):
            continue
        if results_file not in combined_results.keys():
            combined_results[results_file] = {}
        
        updated_results = {}
        results = json.load(open(os.path.join(result_nosymbreak_dir, results_file)))
        updated_results = {'z3': results['z3']}
        combined_results[results_file].update(updated_results)
    
    for results_file in sorted(os.listdir(result_symbreak_dir)):
        if results_file.startswith('.'):
            continue
        if results_file not in combined_results.keys():
            combined_results[results_file] = {}
        
        updated_results = {}
        results = json.load(open(os.path.join(result_symbreak_dir, results_file)))
        updated_results = {'z3_symbreak': results['z3']}
        combined_results[results_file].update(updated_results)
    
    os.makedirs("res/SMT", exist_ok=True)

    for file_name, result in combined_results.items():
        output_path = os.path.join("res/SMT", file_name)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=4)
        print(f"Combined results written to {output_path}")