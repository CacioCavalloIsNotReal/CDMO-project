import pulp
import json
import time
import math
import sys
import os

def parse_instance(filepath):
    """Parses the MCP instance file."""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            lines = [line.strip() for line in lines if line.strip()] # Remove empty lines and strip whitespace

            m = int(lines[0])
            n = int(lines[1])
            capacities = list(map(int, lines[2].split()))
            sizes = list(map(int, lines[3].split()))

            # Read distance matrix (n+1) x (n+1)
            distances_flat = []
            for i in range(4, 4 + n + 1):
                 # Check if line exists and is not empty
                if i < len(lines) and lines[i]:
                    distances_flat.extend(map(int, lines[i].split()))
                else:
                    raise ValueError(f"Missing or empty line for distance matrix row starting at line index {i} (expected {n+1} rows)")


            if len(capacities) != m:
                raise ValueError(f"Number of capacities ({len(capacities)}) does not match m ({m})")
            if len(sizes) != n:
                raise ValueError(f"Number of sizes ({len(sizes)}) does not match n ({n})")
            if len(distances_flat) != (n + 1) * (n + 1):
                 raise ValueError(f"Distance matrix size incorrect. Expected {(n+1)*(n+1)} elements, got {len(distances_flat)}")

            # Reshape flat list into matrix (dictionary format recommended for PuLP)
            # Using 0-based indexing internally: items 0 to n-1, origin n
            # Input file uses 1-based: items 1 to n, origin n+1
            dist_matrix = {}
            origin_idx_0based = n # The origin is the last index (n+1 in 1-based, n in 0-based)
            idx = 0
            for r in range(n + 1): # 0 to n (representing 1 to n+1)
                for c in range(n + 1): # 0 to n (representing 1 to n+1)
                    # Map 1-based input description to 0-based internal indices
                    # Input row r+1, col c+1 corresponds to internal r, c
                    dist_matrix[(r, c)] = distances_flat[idx]
                    idx += 1

            # Create 0-based parameter lists/dicts for convenience
            params = {
                'm': m,
                'n': n,
                'capacities': {i: capacities[i] for i in range(m)}, # dict courier_idx -> capacity
                'sizes': {j: sizes[j] for j in range(n)}, # dict item_idx -> size
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


def solve_mcp_mip(params, time_limit_sec=300):
    """Builds and solves the MCP MIP model using PuLP."""
    m = params['m']
    n = params['n']
    capacities = params['capacities']
    sizes = params['sizes']
    distances = params['distances']
    origin_idx = params['origin_idx'] # 0-based index for origin

    courier_indices = range(m)
    item_indices = range(n) # 0 to n-1
    # All locations including origin: 0 to n-1 (items), n (origin)
    all_loc_indices = range(n + 1)

    # Create the MIP problem
    prob = pulp.LpProblem("MCP_Problem_MIP", pulp.LpMinimize)

    # --- Decision Variables ---
    # x_ij = 1 if item j is assigned to courier i
    x = pulp.LpVariable.dicts("x", (courier_indices, item_indices), cat='Binary')

    # y_ijk = 1 if courier i travels from location j to location k
    y = pulp.LpVariable.dicts("y", (courier_indices, all_loc_indices, all_loc_indices), cat='Binary')

    # u_ij = Auxiliary variable for MTZ subtour elimination (position/load) for item nodes
    # Needs to accommodate up to n stops
    u = pulp.LpVariable.dicts("u", (courier_indices, item_indices), lowBound=1, upBound=n, cat='Integer') # Or Continuous? Integer is safer for MTZ logic.

    # Z = Maximum distance traveled by any courier
    Z = pulp.LpVariable("Z", lowBound=0, cat='Continuous') # Or Integer if distances are integers

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
        # - Must leave origin if assigned any items
        prob += pulp.lpSum(y[i][origin_idx][k] for k in item_indices) <= pulp.lpSum(x[i][j] for j in item_indices), f"LeaveOriginOnlyIfNeeded_{i}"
        # Big M version (alternative): Ensure leave if assigned >= 1 item
        # M_items = n + 1
        # prob += pulp.lpSum(x[i][j] for j in item_indices) <= M_items * pulp.lpSum(y[i][origin_idx][k] for k in item_indices), f"MustLeaveOriginIfAssigned_{i}"


        # - Must return to origin if leaves origin
        prob += pulp.lpSum(y[i][origin_idx][k] for k in item_indices) == pulp.lpSum(y[i][k][origin_idx] for k in item_indices), f"LeaveEqReturnOrigin_{i}"

        for j in item_indices:
            # - If item j assigned to courier i, it must be entered and exited by i
            prob += pulp.lpSum(y[i][k][j] for k in all_loc_indices if k != j) == x[i][j], f"Enter_item_{i}_{j}"
            prob += pulp.lpSum(y[i][j][k] for k in all_loc_indices if k != j) == x[i][j], f"Exit_item_{i}_{j}"

    # Ensure no self-loops
    for i in courier_indices:
        for j in all_loc_indices:
            prob += y[i][j][j] == 0, f"No_self_loop_{i}_{j}"

    # 4. Subtour Elimination (MTZ formulation)
    # u_i - u_j + n * y_ijk <= n - 1 for i -> j -> k where i,j are items
    # This prevents subtours among item nodes not involving the origin.
    # Note: This formulation assumes y[i][j][k] implies x[i][j] and x[i][k] are active (handled by linking constraints above)
    for i in courier_indices:
        for j in item_indices:
            for k in item_indices:
                if j != k:
                    # If courier i goes from item j to item k, u[k] must be at least u[j]+1
                    # u[j] - u[k] + n * y[i][j][k] <= n - 1
                    prob += u[i][j] - u[i][k] + n * y[i][j][k] <= n - 1, f"MTZ_{i}_{j}_{k}"

    # Bounds for u variables (only meaningful if x[i][j]=1)
    # Linking u with x more explicitly (can sometimes help, but adds complexity)
    # M_u_link = n
    # for i in courier_indices:
    #     for j in item_indices:
    #          prob += u[i][j] >= 1 - M_u_link * (1 - x[i][j]), f"u_min_link_{i}_{j}"
    #          prob += u[i][j] <= n + M_u_link * (1 - x[i][j]), f"u_max_link_{i}_{j}"
    # The lowBound=1, upBound=n on variable definition might suffice if solver is good.


    # 5. Objective Function Constraint: Z >= distance for each courier
    for i in courier_indices:
        courier_distance = pulp.lpSum(distances[j, k] * y[i][j][k]
                                      for j in all_loc_indices
                                      for k in all_loc_indices if j != k)
        prob += courier_distance <= Z, f"Max_Dist_Constraint_{i}"

    # --- Solve ---
    print(f"Solving MCP MIP with PuLP (Solver: {pulp.PULP_CBC_CMD().name})...")
    start_time = time.time()
    # Use default CBC solver provided with PuLP, set time limit
    # You can replace PULP_CBC_CMD with GUROBI_CMD, CPLEX_CMD etc. if installed and configured
    solver = pulp.PULP_CBC_CMD(timeLimit=time_limit_sec, msg=True)
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
        'sol': [[] for _ in range(m)] # Initialize empty tours for each courier
    }

    # Use math.floor for runtime as requested
    results['time'] = math.floor(solve_duration)

    if prob.status == pulp.LpStatusOptimal:
        results['optimal'] = True
        results['obj'] = int(round(pulp.value(prob.objective))) # Round obj value if needed
        print(f"Optimal Objective (Max Distance Z): {results['obj']}")
    elif prob.status == pulp.LpStatusNotSolved:
         print("Warning: Solver did not run or was interrupted.")
         results['time'] = int(time_limit_sec) # Per spec, use 300 if timeout/no solution found
    elif prob.status == pulp.LpStatusInfeasible:
        print("Error: Model is Infeasible.")
        results['obj'] = -1 # Indicate infeasibility
        # You might want to return/handle this differently
    elif prob.status == pulp.LpStatusUnbounded:
        print("Error: Model is Unbounded.")
        results['obj'] = -2 # Indicate unboundedness
    else: # Feasible solution found but not proven optimal within time limit
        results['optimal'] = False
        if prob.objective is not None and pulp.value(prob.objective) is not None:
             results['obj'] = int(round(pulp.value(prob.objective)))
             print(f"Feasible Objective (Max Distance Z): {results['obj']}")
        else:
             print("Warning: No feasible solution found within time limit.")
             results['obj'] = -1 # Or another indicator for no solution found

        # If timeout without optimality, set time to 300
        if solve_duration >= time_limit_sec - 1: # Use a small tolerance for time limit check
             results['time'] = int(time_limit_sec)


    # Reconstruct tours if a feasible/optimal solution exists
    if results['obj'] is not None and results['obj'] >= 0:
        # Tolerate small deviations from 1.0 for binary variables
        tolerance = 0.001
        active_arcs = {} # Store active arcs for easier lookup: courier -> {from: to}
        for i in courier_indices:
            active_arcs[i] = {}
            for j in all_loc_indices:
                for k in all_loc_indices:
                    if j != k and y[i][j][k].varValue is not None and y[i][j][k].varValue > (1 - tolerance):
                        active_arcs[i][j] = k

        for i in courier_indices:
            if origin_idx in active_arcs[i]: # Check if courier i actually leaves the origin
                current_loc = active_arcs[i][origin_idx]
                tour_0based = []
                while current_loc != origin_idx:
                    # Append item index (which is current_loc as it's 0 to n-1)
                    tour_0based.append(current_loc)
                    if current_loc in active_arcs[i]:
                         current_loc = active_arcs[i][current_loc]
                    else:
                         print(f"Warning: Tour reconstruction broken for courier {i} at location {current_loc+1}", file=sys.stderr)
                         break # Avoid infinite loop

                # Convert 0-based item indices to 1-based for output
                results['sol'][i] = [item_idx + 1 for item_idx in tour_0based]

    return results

# def write_output(results, output_path):
#     """Writes the results to a JSON file."""
#     # Ensure the output directory exists
#     os.makedirs(os.path.dirname(output_path), exist_ok=True)

#     try:
#         with open(output_path, 'w') as f:
#             # Use approach name 'mip_pulp' or similar - consistent with project spec
#             output_data = {"mip_pulp": results} # Wrap results under a key
#             json.dump(output_data, f, indent=4)
#         print(f"Results written to {output_path}")
#     except Exception as e:
#         print(f"Error writing output file {output_path}: {e}", file=sys.stderr)

# --- Main Execution ---
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python solve_mcp_mip.py <instance_filepath> <output_json_filepath>")
        sys.exit(1)

    instance_file = sys.argv[1]
    output_file = sys.argv[2]
    time_limit = 300 # Seconds, as per project spec

    print(f"Loading instance: {instance_file}")
    instance_params = parse_instance(instance_file)

    print("Instance Parameters Loaded:")
    print(f"  Couriers (m): {instance_params['m']}")
    print(f"  Items (n): {instance_params['n']}")
    # print(f"  Capacities: {instance_params['capacities']}") # Might be long
    # print(f"  Sizes: {instance_params['sizes']}")         # Might be long
    # print(f"  Origin Index (0-based): {instance_params['origin_idx']}")

    results = solve_mcp_mip(instance_params, time_limit_sec=time_limit)

    write_output(results, output_file)

    print("Script finished.")