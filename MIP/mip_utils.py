import sys
import os
import json

def parse_instance(filepath):
    """Parses the MCP instance file."""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            lines = [line.strip() for line in lines if line.strip()] # Remove empty lines and strip whitespace

            m = int(lines[0])
            n = int(lines[1])
            capacities_list = list(map(int, lines[2].split()))
            sizes_list = list(map(int, lines[3].split()))

            # Read distance matrix (n+1) x (n+1)
            distances_flat = []
            for i in range(4, 4 + n + 1):
                if i < len(lines) and lines[i]:
                    distances_flat.extend(map(int, lines[i].split()))
                else:
                    raise ValueError(f"Missing or empty line for distance matrix row starting at line index {i} (expected {n+1} rows)")

            if len(capacities_list) != m:
                raise ValueError(f"Number of capacities ({len(capacities_list)}) does not match m ({m})")
            if len(sizes_list) != n:
                raise ValueError(f"Number of sizes ({len(sizes_list)}) does not match n ({n})")
            if len(distances_flat) != (n + 1) * (n + 1):
                 raise ValueError(f"Distance matrix size incorrect. Expected {(n+1)*(n+1)} elements, got {len(distances_flat)}")

            # Use dictionaries keyed by 0-based indices
            capacities = {i: capacities_list[i] for i in range(m)}
            sizes = {j: sizes_list[j] for j in range(n)}

            dist_matrix = {}
            origin_idx_0based = n # The origin is the last index (n+1 in 1-based, n in 0-based)
            idx = 0
            for r in range(n + 1): # 0 to n
                for c in range(n + 1): # 0 to n
                    dist_matrix[(r, c)] = distances_flat[idx]
                    idx += 1

            params = {
                'm': m,
                'n': n,
                'capacities': capacities, # dict courier_idx -> capacity
                'sizes': sizes,          # dict item_idx -> size
                'distances': dist_matrix, # dict (from_idx, to_idx) -> distance
                'origin_idx': origin_idx_0based # Index of the origin in 0-based system
            }
            return params

    except FileNotFoundError:
        print(f"Error: Input file not found at {filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing instance file {filepath}: {e}", file=sys.stderr)
        sys.exit(1)

def write_output(results, output_path, approach_name="mip_pulp"): # Allow customizing approach name
    """Writes the results to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        with open(output_path, 'w') as f:
            output_data = {approach_name: results}
            json.dump(output_data, f, indent=4)
        print(f"Results written to {output_path}")
    except Exception as e:
        print(f"Error writing output file {output_path}: {e}", file=sys.stderr)

def combine_results(result_nosymbreak_dir, result_symbreak_dir):
    combined_results = {}
    for subfolder in os.listdir(result_nosymbreak_dir):
        if subfolder.startswith('.'):
            # Skip hidden folders.
            continue
        folder = os.path.join(result_nosymbreak_dir, subfolder)
        for results_file in sorted(os.listdir(folder)):
            if results_file.startswith('.'):
                # Skip hidden folders.
                continue
            if results_file not in combined_results.keys():
                combined_results[results_file] = {}
            
            results = json.load(open(os.path.join(folder, results_file)))
            if 'PULP_CBC_CMD' in results.keys():
                updated_results = {'cbc': results['PULP_CBC_CMD']}
            elif 'GUROBI_CMD' in results.keys():
                updated_results = {'gurobi': results['GUROBI_CMD']}
            elif 'HiGHS_CMD' in results.keys():
                updated_results = {'highs': results['HiGHS_CMD']}
            else:
                print("ERROR")

            combined_results[results_file].update(updated_results)
    for subfolder in os.listdir(result_symbreak_dir):
        if subfolder.startswith('.'):
            # Skip hidden folders.
            continue
        folder = os.path.join(result_symbreak_dir, subfolder)
        for results_file in sorted(os.listdir(folder)):
            if results_file.startswith('.'):
                # Skip hidden folders.
                continue
            if results_file not in combined_results.keys():
                combined_results[results_file] = {}

            results = json.load(open(os.path.join(folder, results_file)))
            if 'PULP_CBC_CMD' in results.keys():
                updated_results = {'cbc_symbreak': results['PULP_CBC_CMD']}
            elif 'GUROBI_CMD' in results.keys():
                updated_results = {'gurobi_symbreak': results['GUROBI_CMD']}
            elif 'HiGHS_CMD' in results.keys():
                updated_results = {'highs_symbreak': results['HiGHS_CMD']}
            else:
                print("ERROR")

            combined_results[results_file].update(updated_results)

    os.makedirs("res/MIP", exist_ok=True)

    for file_name, result in combined_results.items():
        output_path = os.path.join("res/MIP", file_name)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=4)
        print(f"Combined results written to {output_path}")