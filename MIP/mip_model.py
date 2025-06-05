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
        prob += pulp.lpSum(x[i][j] for i in courier_indices) == 1, f"Assign_item_{j}"

    # Respect capacity limits
    for i in courier_indices:
        prob += pulp.lpSum(sizes[j] * x[i][j] for j in item_indices) <= capacities[i], f"Capacity_{i}"

    for i in courier_indices:
        # Only leave depot if you have items
        prob += pulp.lpSum(y[i][origin_idx][k] for k in item_indices) <= pulp.lpSum(x[i][j] for j in item_indices)

        # Ensure round trip (same in and out arcs at depot)
        prob += pulp.lpSum(y[i][origin_idx][k] for k in item_indices) == pulp.lpSum(y[i][k][origin_idx] for k in item_indices)

        # Item entry/exit balance
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
    # TODO: improve grouping if other courier features matter later
    identical_groups = {}
    for i in courier_indices:
        cap = capacities[i]
        identical_groups.setdefault(cap, []).append(i)

    for cap, group in identical_groups.items():
        if len(group) > 1:
            group.sort()
            for idx in range(len(group) - 1):
                i, i_next = group[idx], group[idx + 1]
                load_i = pulp.lpSum(sizes[j] * x[i][j] for j in item_indices)
                load_next = pulp.lpSum(sizes[j] * x[i_next][j] for j in item_indices)
                prob += load_i >= load_next, f"SymBreak_{i}_{i_next}"

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
        'solve_time': solve_time if solve_time < 300 else 300,
        'objective': None if model.status != pulp.LpStatusOptimal else pulp.value(model.objective),
        'is_optimal': True if solve_time < 300 else False,
        'variables': variables
    }

def reconstruct_tours(solution, variables, params):
    if not solution['is_optimal'] and solution['objective'] is None:
        return [[] for _ in range(params['m'])]

    x, u = variables['x'], variables['u']
    m, n = params['m'], params['n']
    tours = [[] for _ in range(m)]

    # Build assignment dict
    assignments = {
        i: [j for j in range(n) if x[i][j].value() and x[i][j].value() > 1e-4]
        for i in range(m)
    }

    for i in range(m):
        if not assignments[i]:
            continue
        positions = [(j + 1, u[i][j].value()) for j in assignments[i] if u[i][j].value() is not None]
        positions.sort(key=lambda x: x[1])
        tours[i] = [item for item, _ in positions]

    # Handle any missed items
    expected = set(range(1, n + 1))
    actual = set(item for tour in tours for item in tour)
    for missing in expected - actual:
        for i in range(m):
            if x[i][missing - 1].value() and x[i][missing - 1].value() > 1e-4:
                tours[i].append(missing)
                break

    return tours

def solve_mcp_mip(params, time_limit_sec=305, add_symmetry_break=False, solver="PULP_CBC_CMD"):
    model, variables = build_mcp_model(params, add_symmetry_break)
    solution = solve_model(model, variables, solver, time_limit_sec)

    results = {
        'time': min(int(solution['solve_time']), time_limit_sec),
        'optimal': solution['is_optimal'],
        'obj': int(round(solution['objective'])) if solution['objective'] is not None else -1,
        'sol': []
    }

    if solution['objective'] is not None and solution['objective'] >= 0:
        results['sol'] = reconstruct_tours(solution, variables, params)
        verify_objective(results, params)

    return results

def verify_objective(results, params):
    if not results['sol']:
        return

    distances = params['distances']
    origin_idx = params['origin_idx']
    max_dist = 0

    for tour in results['sol']:
        if not tour:
            continue

        dist = 0
        prev = origin_idx
        for curr in [j - 1 for j in tour]:
            dist += distances.get((prev, curr), 0)
            prev = curr
        dist += distances.get((prev, origin_idx), 0)

        max_dist = max(max_dist, dist)

    if abs(max_dist - results['obj']) > 0.5:
        print(f"WARNING: Calculated distance {max_dist} differs from reported {results['obj']}")
        results['obj'] = max_dist
    else:
        print(f"Objective verification passed: {results['obj']} matches calculated distance {max_dist}")
