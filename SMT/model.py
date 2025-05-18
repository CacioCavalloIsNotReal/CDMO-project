from z3 import *
import time

def my_model(m,n,l,s,d,symm_break=False,timeout=None, opt_container=None):
    start_time = time.time()
    opt = Optimize()
    if timeout:
        opt.set("timeout", timeout*1000) 

    # item_order   -> courier i deliver item j with order "value"
    item_order = Function('item_order', IntSort(), IntSort(), IntSort())

    # travels   -> courier i travels from j to k
    travels = Function('deliver', IntSort(), IntSort(), IntSort(), BoolSort())

    courier_load = [
        Sum(
            [If(item_order(i,j)>=0,s[j], 0)
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
                [If(item_order(c, i) >= 0, 1, 0) for c in range(m)]
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
                    [If(travels(i,j,k), 1, 0) for k in range(n+1)]
                ) == If(item_order(i,j)>=0,1, 0)
            )
            opt.add(
                Sum(
                    # the number of times the courier i arrives to j is only once
                    [If(travels(i,k,j), 1, 0) for k in range(n+1)]
                ) == If(item_order(i,j)>=0,1, 0)
            )

    for i in range(m):
        for j in range(n):
            for k in range(j,n):
                for z in range(j,n):
                    opt.add(
                        Implies(    # if a courier arrives at k, then it can never comeback to that point k
                            travels(i, j, k), Not(travels(i, z, k))
                        )
                    )

    # value constraints
    for i in range(m):
        for j in range(n + 1):
            opt.add(
                Or(
                    And(
                        item_order(i, j) >= 1, item_order(i, j) <= n,   # domain if item is delivered
                    ),
                    item_order(i, j) == -1   # domain if item is not delivered
                )
            )
        
        for j in range(n + 1):
            opt.add(
                Implies(    # default value, if the item j is not delivered by courier i, then its value is -1
                    If(item_order(i,j)>=0,False, True),
                    item_order(i, j) == -1
                )
            )

    for i in range(m):
        # Distinct(item_order)
        for j1 in range(n):
            for j2 in range(j1 + 1, n):
                opt.add(
                    Implies(    # if the courier deliver both j1 and j2, then their value must be different
                        And(
                            If(item_order(i,j1)>=0,True, False),
                            If(item_order(i,j2)>=0,True, False)
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

    '''
    ragioniamo
    in questo problema la simmetria avviene quando due corrieri possono fare lo stesso lavoro.
    se due corrieri sono capaci di fare un certo lavoro, occorre imporre l'ordine.
    due corrieri possono fare lo stesso lavoro quando
    max(current_load_i)<min(load_capacity)

    se avviene questo noi possiamo scambiare la soluzione senza problemi, ed è quello che vogliamo evitare.
    lo swap è possibile nel seguente modo:
        - item_order il corriere i consegna l'item j con ordine valore
            -> item_order(c1,j) = item_order(c2,j)
            -> item_order(c2,j) = item_order(c1,j)
        - travels con significato corriere i viaggia da j a k
            -> travels(c1,j,k) = travels(c2,j,k)
            -> travels(c2,j,k) = travels(c1,j,k)
        dove va imposto l'ordinamento? sulle variabili che introducono simmetria -> item_order
    '''
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
    
    result_status = opt.check()
    
    if opt_container is not None: # Pulisci il riferimento
        opt_container[0] = None

    # Preparazione del dizionario di output
    solution = {
        'time' : time.time() - start_time,
        'solution_found' : False, # Cambiato da 'solution' a 'solution_found' per chiarezza
        'status': str(result_status), # Aggiungiamo lo status Z3 (sat, unsat, unknown)
        'travels': [],
        'item_order': [],
        'distances': [],
        'max_distance': None # Inizializzato a None
    }
    
    if result_status == sat:
        solution['solution_found'] = True
        model = opt.model()

        solution['max_distance'] = model.evaluate(max_dist).as_long()

        for i in range(m):
            for j_node in range(n + 1): # j_node può essere un item o l'origine
                for k_node in range(n + 1): # k_node può essere un item o l'origine
                    if j_node != k_node and model.evaluate(travels(i, j_node, k_node)) is True: # is_true non serve se confrontiamo con True
                        solution['travels'].append((i, j_node, k_node))

        for i in range(m):
            for j_item_idx in range(n): # j_item_idx è l'indice dell'item
                val_expr = model.evaluate(item_order(i, j_item_idx))
                if val_expr is not None: # Dovrebbe sempre esserlo se sat
                    val_long = val_expr.as_long()
                    if val_long >= 0: # Consideriamo solo ordini validi (non -1)
                        solution['item_order'].append((i, j_item_idx, val_long))

        for i in range(m):
            dist_val = model.evaluate(distances[i])
            solution['distances'].append(dist_val.as_long() if dist_val is not None else 0)

        return solution
    
    elif result_status == unknown:
        # solution['solution_found'] è già False
        # solution['status'] è già 'unknown'
        # Potremmo voler registrare perché è unknown (es. timeout interno di Z3)
        reason_unknown = opt.reason_unknown()
        if reason_unknown:
             solution['reason_unknown'] = reason_unknown
        return solution
    else: # unsat
        # solution['solution_found'] è già False
        # solution['status'] è già 'unsat'
        return solution


    # result = opt.check()
    # solution = {
    #         'time' : time.time() - start_time,
    #         'solution' : True,
    #         'travels': [],
    #         'item_order': [],
    #         'distances': [],
    #         'max_distance': 0
    #     }
    
    # if result == sat:
    #     model = opt.model()

    #     solution['max_distance'] = model.evaluate(max_dist).as_long()

    #     for i in range(m):
    #         for j in range(n + 1):
    #             for k in range(n + 1):
    #                 if is_true(model.evaluate(travels(i, j, k))):
    #                     solution['travels'].append((i, j, k))

    #     for i in range(m):
    #         for j in range(n):
    #             val = model.evaluate(item_order(i, j))
    #             if val is not None and val.as_long() >= 0:
    #                 solution['item_order'].append((i, j, val.as_long()))

    #     for i in range(m):
    #         solution['distances'].append(model.evaluate(distances[i]).as_long())

    #     return solution
    # elif result == unknown:
    #     solution['solution'] = False
    #     return {'solution' : False,}
    # else: 
    #     solution['solution'] = False
    #     return {'solution' : False,}