import pulp
import time

def build_mcp_model(params, add_symmetry_break=False):
    m = params['m']
    n = params['n']
    capacities = params['capacities']
    sizes = params['sizes']
    distances = params['distances']
    origin_idx = params['origin_idx']

    courier_indices = range(m)
    item_indices = range(n)
    all_loc_indices = range(n + 1)

    prob = pulp.LpProblem("MCP_Problem", pulp.LpMinimize)

    # Variables
    x = pulp.LpVariable.dicts("x", (courier_indices, item_indices), cat='Binary')
    y = pulp.LpVariable.dicts("y", (courier_indices, all_loc_indices, all_loc_indices), cat='Binary')
    u = pulp.LpVariable.dicts("u", (courier_indices, item_indices), lowBound=1, upBound=n, cat='Integer')
    Z = pulp.LpVariable("Z", lowBound=0, cat='Continuous')

    # Objective - minimize max distance per courier
    prob += Z

    # Assign each item to exactly one courier
    for j in item_indices:
        prob += pulp.lpSum(x[i][j] for i in courier_indices) == 1

    # Respect capacity limits
    for i in courier_indices:
        prob += pulp.lpSum(sizes[j] * x[i][j] for j in item_indices) <= capacities[i]

    for i in courier_indices:
        # Courier leaves the depot at most once
        prob += pulp.lpSum(y[i][origin_idx][k] for k in item_indices) <= 1

        # Only leave depot if you have items
        prob += pulp.lpSum(y[i][origin_idx][k] for k in item_indices) <= pulp.lpSum(x[i][j] for j in item_indices)

        # Ensure round trip (same in and out arcs at depot)
        prob += pulp.lpSum(y[i][origin_idx][k] for k in item_indices) == pulp.lpSum(y[i][k][origin_idx] for k in item_indices)

        # Flow conservation
        for j in item_indices:
            prob += pulp.lpSum(y[i][k][j] for k in all_loc_indices if k != j) == x[i][j]
            prob += pulp.lpSum(y[i][j][k] for k in all_loc_indices if k != j) == x[i][j]

        # No self-loops (they mess up MTZ)
        for j in all_loc_indices:
            prob += y[i][j][j] == 0

    # Subtour elimination (MTZ-style)
    for i in courier_indices:
        for j in item_indices:
            for k in item_indices:
                if j != k:
                    prob += u[i][j] - u[i][k] + n * y[i][j][k] <= n - 1

    # Z should bound each courier's total distance
    for i in courier_indices:
        courier_distance = pulp.lpSum(distances[j, k] * y[i][j][k] for j in all_loc_indices for k in all_loc_indices if j != k)
        prob += courier_distance <= Z

    # Optional symmetry breaking
    if add_symmetry_break:
        add_symmetry_breaking(prob, x, courier_indices, item_indices, capacities, sizes)

    return prob, {'x': x, 'y': y, 'u': u, 'Z': Z}

def add_symmetry_breaking(prob, x, courier_indices, item_indices, capacities, sizes):
    identical_groups = {}
    for i in courier_indices:
        cap = capacities[i]
        identical_groups.setdefault(cap, []).append(i)

    for cap, group in identical_groups.items():
        if len(group) > 1:
            group.sort()
            for i in range(len(group) - 1):
                curr, next_courier = group[i], group[i + 1]
                load_curr = pulp.lpSum(sizes[j] * x[curr][j] for j in range(n))
                load_next = pulp.lpSum(sizes[j] * x[next_courier][j] for j in range(n))
                prob += load_curr >= load_next

def solve_model(model, variables, solver_name, time_limit_sec=305):
    solver_map = {
        "PULP_CBC_CMD": pulp.PULP_CBC_CMD(timeLimit=time_limit_sec, msg=True),
        "GUROBI_CMD": pulp.GUROBI_CMD(timeLimit=time_limit_sec, msg=True),
        "HiGHS_CMD": pulp.HiGHS_CMD(timeLimit=time_limit_sec, msg=True),
    }

    if solver_name not in solver_map:
        raise ValueError(f"Unsupported solver: {solver_name}")

    start_time = time.time()
    model.solve(solver_map[solver_name])
    solve_time = time.time() - start_time

    return {
        'status': pulp.LpStatus[model.status],
        'solve_time': int(solve_time) if solve_time < 300 else 300,
        'objective': None if model.status != pulp.LpStatusOptimal else pulp.value(model.objective),
        'is_optimal': True if solve_time < 300 else False,
        'variables': variables
    }

def reconstruct_tours(solution, variables, params):
    if not solution['objective']:
        return [[] for _ in range(params['m'])]

    x, u = variables['x'], variables['u']
    m, n = params['m'], params['n']
    tours = [[] for _ in range(m)]

    # Get assignments - trust the solver
    for i in range(m):
        assigned_items = []
        for j in range(n):
            if x[i][j].value() > 0.5:
                pos = u[i][j].value()
                if pos:
                    assigned_items.append((j + 1, pos))
        
        # Sort by position and build tour
        assigned_items.sort(key=lambda item: item[1])
        tours[i] = [item[0] for item in assigned_items]

    return tours

def solve_mcp_mip(params, time_limit_sec=305, add_symmetry_break=False, solver="PULP_CBC_CMD"):
    model, variables = build_mcp_model(params, add_symmetry_break)
    solution = solve_model(model, variables, solver, time_limit_sec)

    results = {
        'time': solution['solve_time'],
        'optimal': solution['is_optimal'],
        'obj': int(round(solution['objective'])) if solution['objective'] is not None else -1,
        'sol': []
    }

    if solution['objective'] is not None and solution['objective'] >= 0:
        results['sol'] = reconstruct_tours(solution, variables, params)
        verify_objective(results, params)

    return results

def verify_objective(result, params):
    if not result['sol']:
        return

    distances = params['distances']
    depot = params['origin_idx']
    max_dist = 0

    for tour in result['sol']:
        if not tour:
            continue

        dist = 0
        current = depot
        
        for item in tour:
            next_loc = item - 1
            dist += distances.get((current, next_loc), 0)
            current = next_loc
        
        dist += distances.get((current, depot), 0)
        max_dist = max(max_dist, dist)

    if abs(max_dist - result['obj']) > 0.5:
        print(f"Warning: Distance mismatch - calculated: {max_dist}, reported: {result['obj']}")
        result['obj'] = max_dist
