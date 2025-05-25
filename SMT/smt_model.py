from z3 import *
import time

def Iff(A, B):
    return And(
            Implies(A,B),
            Implies(B,A)
        )
    
def my_model(m,n,l,s,d,symm_break=False,timeout=None, opt_container=None):
    start_time = time.time()
    opt = Optimize()
    if timeout:
        opt.set("timeout", timeout*1000) 

    # item_order   -> courier i deliver item j with order "value"
    item_order = Function('item_order', IntSort(), IntSort(), IntSort())

    # travels   -> courier i travels from j to k
    travels = Function('travels', IntSort(), IntSort(), IntSort(), BoolSort())

    courier_load = [
        Sum(
            [If(item_order(i,j)>=1,s[j], 0)
            for j in range(n)]
        )
        for i in range(m)
    ]

    # load constraint
    for i in range(m):
        opt.add(
            courier_load[i] <= l[i]
        )
    
    # each item is assigned to only one courier
    for i in range(n):
        opt.add(
            Sum(
                [If(item_order(c, i) >= 1, 1, 0) for c in range(m)]
            ) == 1
        )
    
    # each courier path must start/end at the origin
    for i in range(m):
        opt.add(
            Sum(
                # the courier i start from n and end only in one j
                [If(travels(i,n,j), 1, 0) for j in range(n)]
            ) == 1
        )
        opt.add(
            Sum(
                # the courier i start from one j and end in n
                [If(travels(i,j,n), 1, 0) for j in range(n)]
            ) == 1
        )

    # courier must deliver the item and leave
    for i in range(m):
        for j in range(n):
            opt.add(
                Sum(
                    # the number of times the courier i leaves from point j is once
                    [If(travels(i,k,j), 1, 0) for k in range(n+1)]
                ) == If(item_order(i,j)>=1,1, 0)
            )

    for i in range(m):
        for j in range(n):
            # this combined with the fact that a courier can't come back in the same item/point is sufficient
            opt.add(
                    Not(travels(i, j,j))
                )


    # value constraints
    for i in range(m):
        for j in range(n):
            opt.add(
                And(
                        item_order(i, j) >= 0, item_order(i, j) <= n,   # domain 
                    )
            )
        
        for j in range(n):
            opt.add(
                # default value, if the item j is not delivered by courier i, then its value is 0
                Iff(
                    item_order(i, j) == 0,
                    And(
                        Sum(
                            [If(travels(i,j,k), 1, 0) for k in range(n+1)]
                        )==0, 
                        Sum(
                            [If(travels(i,k,j), 1, 0) for k in range(n+1)]
                        )==0
                    )
                ),
            )
    
    for i in range(m):
        # Distinct(item_order)
        for j1 in range(n):
            for j2 in range(n):
                opt.add(
                    Implies(    # if the courier deliver both j1 and j2, then their value must be different
                        And(
                            j1!=j2,
                            item_order(i,j1)>=1,
                            item_order(i,j2)>=1
                        ),
                        item_order(i, j1) != item_order(i, j2)
                    )
                )

    for i in range(m):
        for k in range(n):
            opt.add(
                Implies(    # if the courier i goes from the origin elsewhere, then this is the first item to be delivered
                    travels(i, n, k), item_order(i, k) == 1
                )
            )

    for i in range(m):
        for j in range(n):
            for k in range(n + 1):
                if j != k:
                    opt.add(
                        Implies(    # the order of the current item is past item + 1 
                            travels(i, j, k),
                            item_order(i, k) == item_order(i, j) + 1
                        )
                    )

    # the courier c deliver as last item j and then com eback to the origin
    courier_last_item = Function('courier_last_item', IntSort(), IntSort() )
    for c in range(m):
        tmp = Int(f"tmp_{c}")
        for k in range(n):
            opt.add(
                And(
                    item_order(c, tmp)>=item_order(c, k),
                    tmp >= 0,
                    tmp < n # NB. n is the origin, not an item
                )
            )
        opt.add(
            courier_last_item(c)==tmp
        )

    for c in range(m):
        opt.add(
            travels(c, courier_last_item(c), n) == True
        )

    if symm_break:
        for c1 in range(m):
            for c2 in range(c1 + 1, m):
                # aggiungere if
                opt.add(
                    Implies(
                        # if the work of c1 can be swapped with the work of c2
                        If( # the max of the current load
                            courier_load[c1]>=courier_load[c2], courier_load[c1], courier_load[c2]
                        )<=
                        If( # the minimum of the couriers capacity
                            l[c1]<=l[c2], l[c1], l[c2]
                        ),
                        # then lexicographic order
                        # logic:
                        #  arr1 <=_lex arr2 IFF
                        # (arr1[0] < arr2[0]) OR
                        # ...
                        # (arr1[0] == arr2[0] AND arr1[1] == arr2[1] AND arr1[2] < arr2[2])
                        Or(
                            [And(
                                *[
                                    [item_order(c1, j) for j in range(n)][k] == [item_order(c2, j) for j in range(n)][k] 
                                    for k in range(i)
                                ],
                                [item_order(c1, j) for j in range(n)][i] <= [item_order(c2, j) for j in range(n)][i]
                            )
                            for i in range(len([item_order(c1, j) for j in range(n)]))]
                        )
                    )
                )

    # cost
    distances = []
    for i in range(m):
        distances.append(
            Sum(
                [If(travels(i, j, k), d[j][k], 0) for j in range(n+1) for k in range(n+1)]
            )
        )

    max_dist = Int("max_dist")
    for distance in distances:
        opt.add(
            max_dist>=distance
        )
    opt.add(
        Or(
            [max_dist == dist for dist in distances]
        )  
    )

    opt.minimize(max_dist)
    
    if opt_container is not None:
        opt_container[0] = None

    result = opt.check()
    solution = {
            'time' : time.time() - start_time,
            'solution_found' : True,
            'status': str(result), 
            'travels': [],
            'item_order': [],
            'distances': [],
            'max_distance': 0
        }
    
    if result == sat:
        model = opt.model()
        solution['max_distance'] = model.evaluate(max_dist).as_long()

        for i in range(m):
            for j in range(n + 1):
                for k in range(n + 1):
                    if is_true(model.evaluate(travels(i, j, k))):
                        solution['travels'].append((i, j, k))

        for i in range(m):
            for j in range(n):
                val = model.evaluate(item_order(i, j))
                if val is not None and val.as_long() >= 0:
                    solution['item_order'].append((i, j, val.as_long()))

        for i in range(m):
            solution['distances'].append(model.evaluate(distances[i]).as_long())

        return solution
    elif result == unknown:
        solution['solution_found'] = False
        return solution
    else: 
        solution['solution_found'] = False
        return solution