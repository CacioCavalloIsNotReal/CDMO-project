from z3.z3 import Solver, sat, unsat, Int, Bool, Sum, If, And, Or, Not, Implies, BoolVal, is_true, Z3Exception, unknown
import time
from collections import defaultdict

def solve_mcp_smt(m, n, capacities, sizes, dist_dict, # Changed parameter name
                  timeout_sec=300, use_symmetry_breaking=False):
    # N = n + 1 (number of points including origin n)
    N = n + 1
    points = list(range(N)) # 0..n
    items = list(range(n)) # 0..n-1
    couriers = list(range(m)) # 0..m-1
    origin = n

    # --- Find Bounds for Binary Search ---
    max_single_dist = 0
    if n > 0:
        try:
             # Access distances using dictionary keys
             max_single_dist = max(dist_dict.get((origin, j), 0) + dist_dict.get((j, origin), 0) for j in items) if items else 0
        except KeyError as e:
             print(f"Warning: Missing distance key during LB calculation: {e}. Check instance data.")
             max_single_dist = 0 # Default if keys are missing

    # Rough upper bound using max distance in the dictionary
    max_dist_val = max(dist_dict.values()) if dist_dict else 0
    # Simple UB: max edge distance * number of items (very rough)
    ub = (max_dist_val * n) if n > 0 else 0 
    # A slightly better UB could be max_dist_val * N, assuming a path could visit all nodes
    # ub = max_dist_val * N 
    # A much better UB requires a heuristic solution. Using the rough one for now.
    lb = max_single_dist
    
    print(f"Initial Bounds: LB={lb}, UB={ub}")

    best_model = None
    # Initialize higher than UB, handle UB=0 case
    optimal_max_dist = ub + 1 if ub >= 0 else 1 

    start_time = time.time()

    while lb <= ub:
        # Handle potential infinite loop if lb/ub aren't changing correctly
        if time.time() - start_time >= timeout_sec + 5: # Add buffer
             print("Timeout likely exceeded, breaking search loop.")
             break
             
        mid_dist = lb + (ub - lb) // 2
        print(f"Checking MaxDist = {mid_dist} (Bounds: [{lb}, {ub}]) Symmetry: {use_symmetry_breaking}")

        s = Solver()
        remaining_time_ms = max(1000, int((timeout_sec - (time.time() - start_time)) * 1000))
        s.set("timeout", remaining_time_ms) 

        # --- Variables ---
        assign = [Int(f"assign_{j}") for j in items]
        use_edge = [[[Bool(f"use_{i}_{p}_{q}") for q in points] for p in points] for i in couriers]
        u = [[Int(f"u_{i}_{p}") for p in points] for i in couriers]
        courier_dist = [Int(f"dist_{i}") for i in couriers]
        courier_load = [Int(f"load_{i}") for i in couriers]

        # --- Constraints ---
        # (C1, C2, C3, C4, C5, C6 remain the same logically, check implementation details)

        # C1: Assignment Domain
        for j in items:
            s.add(assign[j] >= 0, assign[j] < m)

        # Intermediate Load Calculation
        for i in couriers:
            load_expr = Sum([If(assign[j] == i, sizes[j], 0) for j in items])
            s.add(courier_load[i] == load_expr)

        # C2: Capacity
        for i in couriers:
            s.add(courier_load[i] <= capacities[i])

        # C3 & C4: Tour Flow and Assignment Linking (check carefully)
        active_couriers = [Bool(f"active_{i}") for i in couriers]
        for i in couriers:
             is_active_cond = Or([assign[j] == i for j in items]) if n > 0 else BoolVal(False)
             s.add(active_couriers[i] == is_active_cond)
             
             # Origin flow for active couriers
             num_leaving_origin = Sum([If(use_edge[i][origin][q], 1, 0) for q in items]) # Only items possible targets from origin
             num_entering_origin = Sum([If(use_edge[i][p][origin], 1, 0) for p in items]) # Only items possible sources to origin
             s.add(Implies(active_couriers[i], num_leaving_origin == 1))
             s.add(Implies(active_couriers[i], num_entering_origin == 1))
             # If not active, ensure no edges leave/enter origin involving items
             s.add(Implies(Not(active_couriers[i]), num_leaving_origin == 0))
             s.add(Implies(Not(active_couriers[i]), num_entering_origin == 0))
             # Also ensure no edges between origin and itself or unused points if inactive
             s.add(Implies(Not(active_couriers[i]), Not(use_edge[i][origin][origin])))


             # Item flow linked to assignment
             for j in items:
                 in_degree_j = Sum([If(use_edge[i][p][j], 1, 0) for p in points if p != j]) 
                 s.add(Implies(assign[j] == i, in_degree_j == 1))
                 s.add(Implies(assign[j] != i, in_degree_j == 0))

                 out_degree_j = Sum([If(use_edge[i][j][q], 1, 0) for q in points if q != j]) 
                 s.add(Implies(assign[j] == i, out_degree_j == 1))
                 s.add(Implies(assign[j] != i, out_degree_j == 0))
             
             # Ensure no edges used AT ALL if inactive (important)
             s.add(Implies(Not(active_couriers[i]), And([Not(use_edge[i][p][q]) for p in points for q in points])))

        # C5: No Self-Loops
        for i in couriers:
            for p in points:
                s.add(Not(use_edge[i][p][p]))

        # C6: Sub-tour Elimination (MTZ)
        for i in couriers:
            s.add(u[i][origin] == 0)
            for j in items:
                 s.add(Implies(assign[j] == i, u[i][j] >= 1))
                 s.add(Implies(assign[j] == i, u[i][j] <= n)) 
                 s.add(Implies(assign[j] != i, u[i][j] == 0)) # Keep u=0 if not assigned

            for p in points:
                for q in items: # MTZ main constraint applies to edges ending at items
                    s.add(Implies(use_edge[i][p][q], u[i][q] >= u[i][p] + 1))

        # C7: Calculate Courier Distance using dist_dict
        for i in couriers:
            # Use dist_dict.get() for safety within the Summation over all possible edges
            dist_expr = Sum([If(use_edge[i][p][q], dist_dict.get((p, q), 0), 0) 
                             for p in points for q in points])
            s.add(courier_dist[i] == dist_expr)

        # C8: Objective Constraint
        for i in couriers:
            s.add(courier_dist[i] <= mid_dist)

        # --- Symmetry Breaking (Optional - logic remains the same) ---
        if use_symmetry_breaking:
            # (Code for symmetry breaking based on courier_load is unchanged)
            print("  Adding Symmetry Breaking Constraints...")
            symmetric_groups = defaultdict(list)
            for i in couriers:
                symmetric_groups[capacities[i]].append(i)
            for capacity, group in symmetric_groups.items():
                if len(group) > 1:
                    sorted_group = sorted(group) 
                    for idx1 in range(len(sorted_group)):
                        for idx2 in range(idx1 + 1, len(sorted_group)):
                            courier1 = sorted_group[idx1]
                            courier2 = sorted_group[idx2]
                            print(f"    SymBreak: load_{courier1} >= load_{courier2}")
                            s.add(courier_load[courier1] >= courier_load[courier2])


        # --- Check Satisfiability ---
        result = s.check()
        elapsed_time = time.time() - start_time

        # (Rest of the SAT/UNSAT/UNKNOWN logic and binary search update is the same)
        # ... (omitted for brevity - same as previous version) ...
        if result == sat:
            print(f"  SAT (Found solution with MaxDist <= {mid_dist})")
            optimal_max_dist = mid_dist
            try:
                 best_model = s.model()
            except Z3Exception as e:
                 print(f"  Error getting model: {e}")
                 result = unknown 
                 best_model = None 
                 lb = mid_dist + 1 # Treat as unknown/timeout case
                 if elapsed_time >= timeout_sec:
                     print("Timeout reached during binary search (model extraction error).")
                     break
                 continue # Skip to next iteration

            ub = mid_dist - 1 # Try for better
            
        elif result == unsat:
            print(f"  UNSAT (No solution with MaxDist <= {mid_dist})")
            lb = mid_dist + 1 # Need larger distance
        else: # unknown (timeout or error)
            print(f"  UNKNOWN (Timeout or error at MaxDist = {mid_dist})")
            # Increase LB cautiously when unknown, as mid_dist *might* be feasible
            lb = mid_dist + 1 
            if elapsed_time >= timeout_sec:
                 print("Timeout reached during binary search.")
                 break
                 
        if elapsed_time >= timeout_sec and result != sat: 
             print("Timeout reached during binary search.")
             break


    # --- Process Result ---
    total_time = time.time() - start_time
    is_optimal = (best_model is not None) and (lb > ub) # Optimal if search finished normally AND found a solution

    if best_model:
        try:
            final_assign = {j: best_model.eval(assign[j]).as_long() for j in items}
            final_tours = [[] for _ in couriers]
            final_obj = 0 
            calculated_dists = [0] * m # Track distances accurately

            for i in couriers:
                tour_i = []
                is_courier_active = any(final_assign.get(j, -1) == i for j in items)
                
                if is_courier_active:
                    current = origin
                    visited_count = 0 
                    
                    while visited_count <= n: 
                        found_next = False
                        for q in points:
                            # Check if edge is used in the solution model
                            use = best_model.eval(use_edge[i][current][q], model_completion=True) 
                            if is_true(use):
                                # Use dist_dict.get() for safety, though key should exist if edge is used
                                edge_dist = dist_dict.get((current, q), 0) 
                                if edge_dist is None: # Should not happen if dict is complete
                                     print(f"Warning: Missing distance for used edge ({current}, {q}) in final calculation!")
                                     edge_dist = 0
                                calculated_dists[i] += edge_dist # Add distance for used edge
                                
                                if q == origin: 
                                    current = q 
                                    found_next = True 
                                    break # Finished tour segment
                                else: # q must be an item
                                    tour_i.append(q) 
                                    current = q
                                    found_next = True
                                    break # Move to next point
                        
                        visited_count += 1
                        # Break if back at origin or if no outgoing edge found (shouldn't happen in valid solution)
                        if current == origin or not found_next: 
                            if not found_next and current != origin:
                                print(f"Warning: Tour reconstruction error for courier {i}. Dead end at point {current}.")
                            break 
                
                final_tours[i] = tour_i
                # Use the calculated distance for accuracy
                final_obj = max(final_obj, calculated_dists[i])
                
            # Ensure reported obj doesn't exceed the proven feasible bound
            final_obj = min(final_obj, optimal_max_dist) 

            # Report final time, ensuring it's <= 300 if timeout occurred during search
            report_time = int(total_time) if total_time < timeout_sec else 300
            # Optimal only if search completed fully (lb > ub) AND didn't timeout finding the *best* solution
            report_optimal = is_optimal and (total_time < timeout_sec)

            return {
                "time": report_time, 
                "optimal": report_optimal, 
                "obj": final_obj, 
                "sol": final_tours
            }
        except Z3Exception as e:
             print(f"Error extracting solution from model: {e}")
             report_time = int(total_time) if total_time < timeout_sec else 300
             return {
                "time": report_time,
                "optimal": False,
                 # Report best feasible bound found, or -1 if none found
                "obj": optimal_max_dist if best_model else -1, 
                "sol": [] 
            }
            
    else: # No model found at all
         print("No feasible solution found within the time limit or bounds.")
         final_time = 300 if total_time >= timeout_sec else int(total_time)
         return {
            "time": final_time,
            "optimal": False,
            "obj": -1, 
            "sol": [] 
        }