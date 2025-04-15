import pulp
import json
import time
import math
import sys
import os
import mip_utils as utils
from collections import defaultdict # Use defaultdict for easier grouping

# def parse_instance(filepath):
#     """Parses the MCP instance file."""
#     try:
#         with open(filepath, 'r') as f:
#             lines = f.readlines()
#             lines = [line.strip() for line in lines if line.strip()] # Remove empty lines and strip whitespace

#             m = int(lines[0])
#             n = int(lines[1])
#             capacities_list = list(map(int, lines[2].split()))
#             sizes_list = list(map(int, lines[3].split()))

#             # Read distance matrix (n+1) x (n+1)
#             distances_flat = []
#             for i in range(4, 4 + n + 1):
#                 if i < len(lines) and lines[i]:
#                     distances_flat.extend(map(int, lines[i].split()))
#                 else:
#                     raise ValueError(f"Missing or empty line for distance matrix row starting at line index {i} (expected {n+1} rows)")

#             if len(capacities_list) != m:
#                 raise ValueError(f"Number of capacities ({len(capacities_list)}) does not match m ({m})")
#             if len(sizes_list) != n:
#                 raise ValueError(f"Number of sizes ({len(sizes_list)}) does not match n ({n})")
#             if len(distances_flat) != (n + 1) * (n + 1):
#                  raise ValueError(f"Distance matrix size incorrect. Expected {(n+1)*(n+1)} elements, got {len(distances_flat)}")

#             # Use dictionaries keyed by 0-based indices
#             capacities = {i: capacities_list[i] for i in range(m)}
#             sizes = {j: sizes_list[j] for j in range(n)}

#             dist_matrix = {}
#             origin_idx_0based = n # The origin is the last index (n+1 in 1-based, n in 0-based)
#             idx = 0
#             for r in range(n + 1): # 0 to n
#                 for c in range(n + 1): # 0 to n
#                     dist_matrix[(r, c)] = distances_flat[idx]
#                     idx += 1

#             params = {
#                 'm': m,
#                 'n': n,
#                 'capacities': capacities, # dict courier_idx -> capacity
#                 'sizes': sizes,          # dict item_idx -> size
#                 'distances': dist_matrix, # dict (from_idx, to_idx) -> distance
#                 'origin_idx': origin_idx_0based # Index of the origin in 0-based system
#             }
#             return params

#     except FileNotFoundError:
#         print(f"Error: Input file not found at {filepath}", file=sys.stderr)
#         sys.exit(1)
#     except Exception as e:
#         print(f"Error parsing instance file {filepath}: {e}", file=sys.stderr)
#         sys.exit(1)

def solve_mcp_mip(params, time_limit_sec=300, add_symmetry_break=False, solver="PULP_CBC_CMD"): # Added flag
    """Builds and solves the MCP MIP model using PuLP, optionally with symmetry breaking."""
    m = params['m']
    n = params['n']
    capacities = params['capacities']
    sizes = params['sizes']
    distances = params['distances']
    origin_idx = params['origin_idx'] # 0-based index for origin

    courier_indices = range(m)
    item_indices = range(n) # 0 to n-1
    all_loc_indices = range(n + 1)

    # --- Identify Identical Couriers (for symmetry breaking) ---
    identical_courier_groups = defaultdict(list)
    if add_symmetry_break:
        for i, cap in capacities.items():
            identical_courier_groups[cap].append(i)
        # Sort indices within each group to have a defined order
        for cap in identical_courier_groups:
            identical_courier_groups[cap].sort()
        print("Identical Courier Groups (for symmetry breaking):")
        for cap, group in identical_courier_groups.items():
            if len(group) > 1:
                print(f"  Capacity {cap}: Couriers {group}")

    # Create the MIP problem
    prob = pulp.LpProblem("MCP_Problem_MIP", pulp.LpMinimize)

    # --- Decision Variables ---
    x = pulp.LpVariable.dicts("x", (courier_indices, item_indices), cat='Binary')
    y = pulp.LpVariable.dicts("y", (courier_indices, all_loc_indices, all_loc_indices), cat='Binary')
    u = pulp.LpVariable.dicts("u", (courier_indices, item_indices), lowBound=1, upBound=n, cat='Integer')
    Z = pulp.LpVariable("Z", lowBound=0, cat='Continuous')

    # --- Objective Function ---
    prob += Z, "Minimize_Max_Distance"

    # --- Constraints ---

    # 1. Each item assigned to exactly one courier
    for j in item_indices:
        prob += pulp.lpSum(x[i][j] for i in courier_indices) == 1, f"Assign_item_{j}"

    # 2. Courier capacity constraint
    for i in courier_indices:
        prob += pulp.lpSum(sizes[j] * x[i][j] for j in item_indices) <= capacities[i], f"Capacity_courier_{i}"

    # 3. Routing Constraints: Link x and y, ensure flow
    for i in courier_indices:
        # Ensure leave origin <= sum(x_ij) (cannot leave if nothing assigned)
        # Using a potentially tighter form: Sum(y_ok) <= 1, and also link to x_ij sum
#        prob += pulp.lpSum(y[i][origin_idx][k] for k in item_indices) <= 1, f"LeaveOriginAtMostOnce_{i}"
        
        # More correct and significantly speedier: Leave origin only if needed
        prob += pulp.lpSum(y[i][origin_idx][k] for k in item_indices) <= pulp.lpSum(x[i][j] for j in item_indices), f"LeaveOriginOnlyIfNeeded_{i}"

        # Ensure cannot leave origin if no items assigned
        # This can be done by linking sum(y_ok) to sum(x_ij), e.g. sum(y_ok) <= sum(x_ij)
        # Or using a Big-M: sum(y_ok) * min_item_size >= sum(x_ij * item_size) / Capacity ? No, simpler:
        # Enforce sum(y_ok) = 0 if sum(x_ij) = 0. Equivalent to sum(y_ok) <= M * sum(x_ij)
        # If sum(x_ij) >= 1, then sum(y_ok) is constrained by the flow (LeaveEqReturnOrigin) and Enter/Exit constraints
        # Let's rely on the combination of constraints to handle the "only leave if needed" logic.


        prob += pulp.lpSum(y[i][origin_idx][k] for k in item_indices) == pulp.lpSum(y[i][k][origin_idx] for k in item_indices), f"LeaveEqReturnOrigin_{i}"

        for j in item_indices:
            prob += pulp.lpSum(y[i][k][j] for k in all_loc_indices if k != j) == x[i][j], f"Enter_item_{i}_{j}"
            prob += pulp.lpSum(y[i][j][k] for k in all_loc_indices if k != j) == x[i][j], f"Exit_item_{i}_{j}"

    for i in courier_indices:
        for j in all_loc_indices:
            prob += y[i][j][j] == 0, f"No_self_loop_{i}_{j}"

    # 4. Subtour Elimination (MTZ formulation)
    for i in courier_indices:
        for j in item_indices:
            for k in item_indices:
                if j != k:
                    prob += u[i][j] - u[i][k] + n * y[i][j][k] <= n - 1, f"MTZ_{i}_{j}_{k}"

    # 5. Objective Function Constraint: Z >= distance for each courier
    for i in courier_indices:
        courier_distance = pulp.lpSum(distances[j, k] * y[i][j][k]
                                      for j in all_loc_indices
                                      for k in all_loc_indices if j != k)
        prob += courier_distance <= Z, f"Max_Dist_Constraint_{i}"

    # --- 6. Symmetry Breaking Constraints (Optional) ---
    if add_symmetry_break:
        print("Adding Symmetry Breaking Constraints...")
        for cap, group in identical_courier_groups.items():
            if len(group) > 1: # Only apply if there are identical couriers
                # Order by total load: courier i load >= courier i+1 load (for i, i+1 in group)
                for idx in range(len(group) - 1):
                    c_i = group[idx]
                    c_i_plus_1 = group[idx+1]
                    load_i = pulp.lpSum(sizes[j] * x[c_i][j] for j in item_indices)
                    load_i_plus_1 = pulp.lpSum(sizes[j] * x[c_i_plus_1][j] for j in item_indices)
                    prob += load_i >= load_i_plus_1, f"SymBreak_LoadOrder_{c_i}_{c_i_plus_1}"
        print("Symmetry Breaking Constraints Added.")


    # --- Solve ---
    chosen_solver = None
    match solver:
        case "PULP_CBC_CMD":
            chosen_solver = pulp.PULP_CBC_CMD(timeLimit=time_limit_sec, msg=True) # Set msg=True to see solver output
        case "GUROBI_CMD":
            chosen_solver = pulp.GUROBI_CMD(timeLimit=time_limit_sec, msg=True) # Set msg=True to see solver output
        case "HiGHS_CMD":
            chosen_solver = pulp.HiGHS_CMD(timeLimit=time_limit_sec, msg=True) # Set msg=True to see solver output
        case _:
            raise ValueError(f"Unsupported solver: {solver}. Supported solvers are 'PULP_CBC_CMD' and 'GUROBI_CMD'.")
        

    solver_name = chosen_solver.name
    print(f"Solving MCP MIP with PuLP (Solver: {solver_name}, Symmetry Break: {add_symmetry_break})...")
    start_time = time.time()
    solver = chosen_solver # Set msg=True to see solver output
    prob.solve(solver)
    end_time = time.time()
    solve_duration = end_time - start_time

    # --- Extract Results ---
    status = pulp.LpStatus[prob.status]
    print(f"Solver Status: {status}")
    print(f"Solve Time: {solve_duration:.2f} seconds")

    results = {
        'time': 0,
        'optimal': False,
        'obj': None,
        'sol': [[] for _ in range(m)]
    }

    results['time'] = math.floor(solve_duration)

    if prob.status == pulp.LpStatusOptimal:
        results['optimal'] = True
        results['obj'] = int(round(pulp.value(prob.objective)))
        print(f"Optimal Objective (Max Distance Z): {results['obj']}")
    elif prob.status in [pulp.LpStatusFeasible, pulp.LpStatusUndefined]: # Undefined often means feasible found but not optimal within time
        results['optimal'] = False
        if prob.objective is not None and pulp.value(prob.objective) is not None:
             results['obj'] = int(round(pulp.value(prob.objective)))
             print(f"Feasible Objective (Max Distance Z): {results['obj']}")
        else:
             print("Warning: No feasible solution found or objective value unavailable.")
             results['obj'] = -1 # Indicator for no solution

        # Ensure time is set to limit if timeout occurred without optimality
        if solve_duration >= time_limit_sec - 1: # Use a small tolerance
             results['time'] = int(time_limit_sec)
             if results['obj'] is None: results['obj'] = -1 # Ensure obj is set if timeout before feasible
    elif prob.status == pulp.LpStatusNotSolved:
         print("Warning: Solver did not run or was interrupted early.")
         results['time'] = int(time_limit_sec)
         results['obj'] = -1 # Indicate no solution found
    elif prob.status == pulp.LpStatusInfeasible:
        print("Error: Model is Infeasible.")
        results['obj'] = -1 # Indicate infeasibility
        results['time'] = math.floor(solve_duration) # Report actual time taken to prove infeasibility
    elif prob.status == pulp.LpStatusUnbounded:
        print("Error: Model is Unbounded.")
        results['obj'] = -2 # Indicate unboundedness
        results['time'] = math.floor(solve_duration)

    # Ensure time is capped at timelimit if solver stops exactly at limit or slightly over but didn't find optimum
    if not results['optimal'] and results['time'] >= time_limit_sec:
         results['time'] = int(time_limit_sec)


    # Reconstruct tours if a feasible/optimal solution exists
    if results['obj'] is not None and results['obj'] >= 0:
        tolerance = 0.001
        active_arcs = {}
        for i in courier_indices:
            active_arcs[i] = {}
            # Check if courier i is used at all
            is_used = any(x[i][j].varValue > tolerance for j in item_indices)
            if not is_used: continue # Skip reconstruction if courier is unused

            for j in all_loc_indices:
                for k in all_loc_indices:
                    if j != k and y[i][j][k].varValue is not None and y[i][j][k].varValue > tolerance:
                        active_arcs[i][j] = k

        for i in courier_indices:
             # Check if courier i actually leaves the origin based on active arcs
            if origin_idx in active_arcs.get(i, {}): # Use .get for safety if courier i had no arcs
                try:
                    current_loc = active_arcs[i][origin_idx]
                    tour_0based = []
                    visited_count = 0 # Safety break for cycles
                    max_visits = n + 2 # Should not visit more nodes than items + origin twice

                    while current_loc != origin_idx and visited_count < max_visits:
                        tour_0based.append(current_loc)
                        if current_loc in active_arcs[i]:
                             current_loc = active_arcs[i][current_loc]
                        else:
                             print(f"Warning: Tour reconstruction broken for courier {i+1} at location {current_loc+1} (0-based {current_loc}). No outgoing arc.", file=sys.stderr)
                             # Attempt to salvage - maybe this node goes directly back to origin? Check y[i][current_loc][origin_idx]
                             if y[i][current_loc][origin_idx].varValue is not None and y[i][current_loc][origin_idx].varValue > tolerance:
                                 print("     (Seems to return directly to origin from here)")
                                 current_loc = origin_idx # Assume it returns to origin
                             else:
                                 tour_0based.append(-99) # Indicate error in tour
                                 break # Avoid infinite loop
                        visited_count += 1

                    if visited_count >= max_visits:
                        print(f"Warning: Tour reconstruction possibly caught in cycle for courier {i+1}. Tour so far: {[idx + 1 for idx in tour_0based]}", file=sys.stderr)
                        tour_0based.append(-999) # Indicate cycle error


                    results['sol'][i] = [item_idx + 1 for item_idx in tour_0based if item_idx >= 0] # Convert to 1-based, filter errors
                except KeyError:
                     print(f"Warning: KeyError during tour reconstruction for courier {i+1}. Active arcs might be inconsistent.", file=sys.stderr)
                     # This might happen if the solver solution has minor inconsistencies or if constraints are slightly off.
                     results['sol'][i] = [-1] # Indicate failure


    return results

# def write_output(results, output_path, approach_name="mip_pulp"): # Allow customizing approach name
#     """Writes the results to a JSON file."""
#     os.makedirs(os.path.dirname(output_path), exist_ok=True)
#     try:
#         with open(output_path, 'w') as f:
#             output_data = {approach_name: results}
#             json.dump(output_data, f, indent=4)
#         print(f"Results written to {output_path}")
#     except Exception as e:
#         print(f"Error writing output file {output_path}: {e}", file=sys.stderr)

# --- Main Execution ---
if __name__ == "__main__":
    # --- Argument Parsing with Flags ---
    import argparse
    parser = argparse.ArgumentParser(description="Solve MCP using MIP with PuLP.")
    parser.add_argument("instance_filepath", help="Path to the MCP instance file.")
    parser.add_argument("output_json_filepath", help="Path to save the output JSON file.")
    parser.add_argument("--nosym", action="store_true", help="Disable symmetry breaking constraints.")
    parser.add_argument("--timelimit", type=int, default=300, help="Time limit for the solver in seconds (default: 300).")
    parser.add_argument("--approach_name", type=str, default=None, help="Name for the approach key in the JSON output (defaults to 'mip_pulp' or 'mip_pulp_symbreak').")
    parser.add_argument("--solver", type=str, default="PULP_CBC_CMD", choices=["PULP_CBC_CMD", "GUROBI_CMD", "HIGHS_CMD"], help="Solver to use (default: PULP_CBC_CMD).")

    args = parser.parse_args()

    instance_file = args.instance_filepath
    output_file = args.output_json_filepath
    time_limit = args.timelimit
    use_symmetry_breaking = not args.nosym
    solver = args.solver

    # Determine the approach name for the JSON output
    if args.approach_name:
        approach_key = args.approach_name
    else:
        approach_key = "mip_pulp"
        if use_symmetry_breaking:
            approach_key += "_symbreak"


    print(f"Loading instance: {instance_file}")
    instance_params = utils.parse_instance(instance_file)

    print("\n" + "="*20 + " Solving MCP " + "="*20)
    results = solve_mcp_mip(instance_params,
                            time_limit_sec=time_limit,
                            add_symmetry_break=use_symmetry_breaking,
                            solver=solver)
    print("="*50 + "\n")

    utils.write_output(results, output_file, approach_name=approach_key)

    print("Script finished.")