import multiprocessing
import sys
import os
import json

def parse_instance(filepath):
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    m = int(lines[0])
    n = int(lines[1])
    capacities = list(map(int, lines[2].split()))
    sizes = list(map(int, lines[3].split()))

    # Read distance matrix
    distances = []
    for i in range(4, 4 + n + 1):
        distances.extend(map(int, lines[i].split()))

    # Build distance dict
    dist_matrix = {}
    idx = 0
    for r in range(n + 1):
        for c in range(n + 1):
            dist_matrix[(r, c)] = distances[idx]
            idx += 1

    return {
        'm': m,
        'n': n,
        'capacities': {i: capacities[i] for i in range(m)},
        'sizes': {j: sizes[j] for j in range(n)},
        'distances': dist_matrix,
        'origin_idx': n
    }

def generate_lowerbound(distances, n, origin_idx):
    bounds = []
    for i in range(n):
        to_item = distances.get((origin_idx, i), 0)
        from_item = distances.get((i, origin_idx), 0)
        bounds.append(to_item + from_item)
    return max(bounds)

def model_wrapper(queue, model_func, *args, **kwargs):
    try:
        result = model_func(*args, **kwargs)
        queue.put(result)
    except Exception as e:
        queue.put({'solution_found': False, 'error': str(e)})

def run_with_timeout(timeout, model_func, *args, **kwargs):
    queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=model_wrapper, args=(queue, model_func, *args), kwargs=kwargs)
    p.start()
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        p.join()
        return {'solution_found': False, 'status': 'timeout'}

    return queue.get() if not queue.empty() else {'solution_found': False}

def write_output(results, output_path, solver="mip"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({solver: results}, f, indent=4)

def combine_results(no_symm_dir, symm_dir):
    combined = {}
    
    # Process no symmetry results
    for folder in os.listdir(no_symm_dir):
        if folder.startswith('.'):
            continue
        folder_path = os.path.join(no_symm_dir, folder)
        for file in os.listdir(folder_path):
            if file.startswith('.'):
                continue
            if file not in combined:
                combined[file] = {}
            
            with open(os.path.join(folder_path, file)) as f:
                results = json.load(f)
            
            # Get the solver key
            for solver in ['gurobi', 'highs']:
                if solver in results:
                    combined[file][solver] = results[solver]
                    break

    # Process symmetry breaking results
    for folder in os.listdir(symm_dir):
        if folder.startswith('.'):
            continue
        folder_path = os.path.join(symm_dir, folder)
        for file in os.listdir(folder_path):
            if file.startswith('.'):
                continue
            if file not in combined:
                combined[file] = {}
            
            with open(os.path.join(folder_path, file)) as f:
                results = json.load(f)
            
            # Get the solver key with symbreak suffix
            for solver in ['gurobi', 'highs']:
                if solver in results:
                    combined[file][f"{solver}_symbreak"] = results[solver]
                    break

    # Write combined results
    os.makedirs("res/MIP", exist_ok=True)
    for filename, result in combined.items():
        output_path = os.path.join("res/MIP", filename)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=4)