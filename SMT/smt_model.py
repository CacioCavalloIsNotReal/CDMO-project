from z3 import *
import time
from collections import defaultdict


def solve_mcp_smt(params, timeout_sec=300, use_symmetry_breaking=False):
    start_time = time.time()

    # Extract parameters
    m = params['m']
    n = params['n']
    capacities_dict = params['capacities'] # courier_idx -> capacity
    sizes_dict = params['sizes']           # item_idx -> size
    dist_dict = params['distances']      # (from, to) -> distance
    origin = params['origin_idx']        # 0-based index for origin (which is 'n')

    N_points = n + 1 # Total number of points including origin
    points = list(range(N_points)) # Indices 0 to n (0..n-1 for items, n for origin)
    items = list(range(n))         # Indices 0 to n-1
    couriers = list(range(m))      # Indices 0 to m-1

    opt = Optimize()
    opt.set("timeout", timeout_sec * 1000)

    # --- Variables ---
    assign = [Int(f"assign_{j}") for j in items] # For item j
    use_edge = [[[Bool(f"use_{i}_{p}_{q}") for q in points] for p in points] for i in couriers]
    u = [[Int(f"u_{i}_{p}") for p in points] for i in couriers] # MTZ variables
    courier_dist_vars = [Int(f"dist_{i}") for i in couriers]
    courier_load_vars = [Int(f"load_{i}") for i in couriers]

    max_courier_distance_obj = Int("max_courier_distance_obj")

    # --- Constraints ---

    # C1: Assignment Domain
    for j_idx in items: # j_idx is 0 to n-1
        opt.add(assign[j_idx] >= 0, assign[j_idx] < m)

    # Intermediate Load Calculation
    for i_idx in couriers: # i_idx is 0 to m-1
        # sizes_dict keys are item indices (0 to n-1)
        load_expr = Sum([If(assign[j_idx] == i_idx, sizes_dict[j_idx], 0) for j_idx in items])
        opt.add(courier_load_vars[i_idx] == load_expr)

    # C2: Capacity
    for i_idx in couriers:
        # capacities_dict keys are courier indices (0 to m-1)
        opt.add(courier_load_vars[i_idx] <= capacities_dict[i_idx])

    # C3 & C4: Tour Flow and Assignment Linking
    active_couriers = [Bool(f"active_{i}") for i in couriers]
    for i_idx in couriers:
        is_active_cond = Or([assign[j_idx] == i_idx for j_idx in items]) if n > 0 else BoolVal(False)
        opt.add(active_couriers[i_idx] == is_active_cond)

        # Edges from origin go to items; edges to origin come from items
        num_leaving_origin = Sum([If(use_edge[i_idx][origin][q_item_idx], 1, 0) for q_item_idx in items])
        num_entering_origin = Sum([If(use_edge[i_idx][p_item_idx][origin], 1, 0) for p_item_idx in items])
        
        opt.add(Implies(active_couriers[i_idx], num_leaving_origin == 1))
        opt.add(Implies(active_couriers[i_idx], num_entering_origin == 1))
        opt.add(Implies(Not(active_couriers[i_idx]), num_leaving_origin == 0))
        opt.add(Implies(Not(active_couriers[i_idx]), num_entering_origin == 0))
        # If not active, no edge from origin to origin either
        opt.add(Implies(Not(active_couriers[i_idx]), Not(use_edge[i_idx][origin][origin])))


        for j_item_idx in items: # j_item_idx is 0 to n-1 (an item)
            # In-degree for item j_item_idx by courier i_idx
            # p can be another item or the origin
            in_degree_j = Sum([If(use_edge[i_idx][p_idx][j_item_idx], 1, 0) for p_idx in points if p_idx != j_item_idx])
            opt.add(Implies(assign[j_item_idx] == i_idx, in_degree_j == 1))
            opt.add(Implies(assign[j_item_idx] != i_idx, in_degree_j == 0))

            # Out-degree for item j_item_idx by courier i_idx
            # q can be another item or the origin
            out_degree_j = Sum([If(use_edge[i_idx][j_item_idx][q_idx], 1, 0) for q_idx in points if q_idx != j_item_idx])
            opt.add(Implies(assign[j_item_idx] == i_idx, out_degree_j == 1))
            opt.add(Implies(assign[j_item_idx] != i_idx, out_degree_j == 0))

        # If a courier is not active, no edges should be used by them AT ALL.
        opt.add(Implies(Not(active_couriers[i_idx]), And([Not(use_edge[i_idx][p_idx][q_idx]) for p_idx in points for q_idx in points])))

    # C5: No Self-Loops
    for i_idx in couriers:
        for p_idx in points: # p_idx can be an item or origin
            opt.add(Not(use_edge[i_idx][p_idx][p_idx]))

    # C6: Sub-tour Elimination (MTZ)
    for i_idx in couriers:
        opt.add(u[i_idx][origin] == 0) # u for origin is 0
        for j_item_idx in items: # For each item
            opt.add(Implies(assign[j_item_idx] == i_idx, u[i_idx][j_item_idx] >= 1))
            opt.add(Implies(assign[j_item_idx] == i_idx, u[i_idx][j_item_idx] <= n)) # Max position can be n
            opt.add(Implies(assign[j_item_idx] != i_idx, u[i_idx][j_item_idx] == 0)) # If not assigned, u is 0

        # MTZ core constraint: applies to edges from any point p to an item q
        for p_idx in points:
            for q_item_idx in items: # q is an item
                opt.add(Implies(use_edge[i_idx][p_idx][q_item_idx], u[i_idx][q_item_idx] >= u[i_idx][p_idx] + 1))

    # C7: Calculate Courier Distance & Link to Objective
    for i_idx in couriers:
        dist_expr = Sum([If(use_edge[i_idx][p_idx][q_idx], dist_dict.get((p_idx, q_idx), 999999), 0) # Large default if key missing
                         for p_idx in points for q_idx in points])
        opt.add(courier_dist_vars[i_idx] == dist_expr)
        opt.add(max_courier_distance_obj >= courier_dist_vars[i_idx])

    # --- Symmetry Breaking (Optional) ---
    if use_symmetry_breaking:
        print("  Adding Symmetry Breaking Constraints...")
        symmetric_groups = defaultdict(list)
        # Group couriers by their capacity values
        for courier_idx_val in couriers: # 0 to m-1
            symmetric_groups[capacities_dict[courier_idx_val]].append(courier_idx_val)
        
        for capacity_val, group_of_courier_indices in symmetric_groups.items():
            if len(group_of_courier_indices) > 1:
                sorted_group = sorted(group_of_courier_indices)
                for k1_idx_in_sorted in range(len(sorted_group)):
                    for k2_idx_in_sorted in range(k1_idx_in_sorted + 1, len(sorted_group)):
                        c1_actual_idx = sorted_group[k1_idx_in_sorted]
                        c2_actual_idx = sorted_group[k2_idx_in_sorted]
                        # Add load ordering constraint: load[c1] >= load[c2]
                        opt.add(courier_load_vars[c1_actual_idx] >= courier_load_vars[c2_actual_idx])

    # --- Minimize the objective ---
    h_obj = opt.minimize(max_courier_distance_obj)

    print(f"Starting Z3 Optimize check (Timeout: {timeout_sec}s, Symmetry: {use_symmetry_breaking})...")
    result_status = opt.check()
    total_time = time.time() - start_time

    final_obj_val = -1
    final_tours = []
    is_solution_optimal = False # Standard Z3 optimal means provably optimal

    if result_status == sat:
        print("  SAT (Z3 Optimize found a solution)")
        model = opt.model()
        # If Z3 Optimize finishes *before* timeout, it has found the provable optimum.
        # If it times out and gives a solution, it's the best found so far.
        is_solution_optimal = (total_time < timeout_sec) 

        try:
            final_obj_val = model.eval(max_courier_distance_obj).as_long()
            final_assign = {j_idx: model.eval(assign[j_idx]).as_long() for j_idx in items}
            final_tours = [[] for _ in couriers] # Initialize empty tours for all m couriers

            for i_courier_idx in couriers:
                tour_i = []
                # Check if this courier is actually assigned any items
                is_courier_active_in_sol = any(final_assign.get(j_idx, -1) == i_courier_idx for j_idx in items)
                
                if is_courier_active_in_sol:
                    current_point_idx = origin
                    visited_count_in_tour = 0 # Safety break for tour reconstruction
                    
                    # Max N_points edges in a simple tour starting and ending at origin
                    while visited_count_in_tour <= N_points : 
                        found_next_edge = False
                        for q_next_point_idx in points: 
                            edge_is_used = model.eval(use_edge[i_courier_idx][current_point_idx][q_next_point_idx], model_completion=True)
                            if is_true(edge_is_used):
                                if q_next_point_idx == origin: # Returned to origin
                                    current_point_idx = q_next_point_idx 
                                    found_next_edge = True 
                                    break # This segment of the tour is complete
                                else: # q_next_point_idx must be an item
                                    tour_i.append(q_next_point_idx) # Add item_idx to tour
                                    current_point_idx = q_next_point_idx
                                    found_next_edge = True
                                    break # Move to the next point in the tour
                        
                        visited_count_in_tour += 1
                        # Break if back at origin or if no outgoing edge found (should not happen in valid solution)
                        if current_point_idx == origin or not found_next_edge:
                            if not found_next_edge and current_point_idx != origin:
                                print(f"Warning: Z3Opt Tour reconstruction error for courier {i_courier_idx}. Dead end at point {current_point_idx}.")
                            break 
                final_tours[i_courier_idx] = tour_i
        
        except Z3Exception as e:
            print(f"  Error extracting solution from model: {e}")
            final_obj_val = -1 
            final_tours = []
            is_solution_optimal = False # Error in extraction means not reliable
        
    elif result_status == unsat:
        print("  UNSAT (Problem has no solution)")
        is_solution_optimal = True # Provably no solution is an optimal determination
    else: # unknown (likely timeout)
        print("  UNKNOWN (Z3 Optimize timed out or encountered an issue)")
        is_solution_optimal = False # Not proven optimal if unknown

    # Per project spec: if timeout, time is 300, optimal is false
    report_time = int(total_time) if total_time < timeout_sec else 300
    if total_time >= timeout_sec: # If actual time hits timeout, not optimal for project
        is_solution_optimal = False 

    # If Z3 status is not 'sat', no valid objective or tours
    if result_status != sat:
        final_obj_val = -1 
        final_tours = [[] for _ in range(m)] # Empty tours if no solution

    return {
        "time": report_time,
        "optimal": is_solution_optimal,
        "obj": final_obj_val, 
        "sol": final_tours
    }

