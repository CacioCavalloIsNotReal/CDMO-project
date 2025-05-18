

def my_model0(m,n,l,s,d):
    '''
    <3<3<3
    '''
    opt = Optimize()
    # deliver   -> courier i deliver item j
    deliver = Function('deliver', IntSort(), IntSort(), BoolSort())

    # item_order   -> courier i deliver item j with order "value"
    item_order = Function('item_order', IntSort(), IntSort(), IntSort())

    # travels   -> courier i travels from j to k
    travels = Function('deliver', IntSort(), IntSort(), IntSort(), BoolSort())


    courier_load = [
        Sum(
            [If(deliver(i,j), s[j], 0) for j in range(n)]
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
                [If(deliver(c, i), 1, 0) for c in range(m)]
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
                ) == If(deliver(i,j), 1, 0)
            )
            opt.add(
                Sum(
                    # the number of times the courier i arrives to j is only once
                    [If(travels(i,k,j), 1, 0) for k in range(n+1)]
                ) == If(deliver(i,j), 1, 0)
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
                    Not(deliver(i, j)),
                    item_order(i, j) == -1
                )
            )

    for i in range(m):
        # Distinct(item_order)
        for j1 in range(n):
            for j2 in range(j1 + 1, n):
                opt.add(
                    Implies(    # if the courier deliver both j1 and j2, then their value must be different
                        And(deliver(i, j1), deliver(i, j2)),
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
    # symm break  DA RIVEDERE

    # first_item = [Int(f"first_item_{i}") for i in range(m)]

    # for i in range(m):
    #     opt.add(
    #         Or(
    #             [And(deliver(i, j), first_item[i] == j) for j in range(n)]
    #         )
    #     )

    # for i in range(m - 1):
    #     opt.add(
    #         first_item[i] <= first_item[i + 1]
    #     )

    for i in range(m-1):
        opt.add(    # load of the first courier is bigger than the load of the second courier and so on
            And(
                courier_load[i] >= courier_load[i+1]
            )
        )
    max_load_idx = np.argmax(s)
    opt.add(
        deliver(0, max_load_idx) == True
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
    if opt.check() == sat:
        out = opt.model()
        print("potete sucarmelo tutti", out)

        print("Consegne (deliver):")
        for i in range(m):
            for j in range(n):
                if is_true(out.evaluate(deliver(i, j))):
                    print(f"Corriere {i} consegna item {j}")
        print("\nSpostamenti (travels):")
        for i in range(m):
            for j in range(n + 1):      # incluso n perché hai usato anche `n` come origine/destinazione
                for k in range(n + 1):
                    if is_true(out.evaluate(travels(i, j, k))):
                        print(f"Corriere {i} va da {j} a {k}")
        print("\nOrdine di consegna (item_order):")
        for i in range(m):
            for j in range(n):
                val = out.evaluate(item_order(i, j))
                if val is not None:
                    print(f"Corriere {i} consegna item {j} in posizione {val}")
        print('distances')
        for i in range(len(distances)):
            print(out.evaluate(distances[i]))
        print(f"max_dist = {out.evaluate(max_dist)}")


def lex_le(xs, ys):
    # arr1 <=_lex arr2 IFF
    # (arr1[0] < arr2[0]) OR
    # ...
    # (arr1[0] == arr2[0] AND arr1[1] == arr2[1] AND arr1[2] < arr2[2])
    # assert len(xs) == len(ys)
    return Or(
            [And(
                *[xs[k] == ys[k] for k in range(i)],
                xs[i] <= ys[i]
            )
            for i in range(len(xs))]
        )

def my_model_old(m,n,l,s,d,symm_break=False):
    opt = Optimize()

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
    if opt.check() == sat:
        out = opt.model()
        print("potete sucarmelo tutti", out)

        print("\nSpostamenti (travels):")
        for i in range(m):
            for j in range(n + 1):      # incluso n perché hai usato anche `n` come origine/destinazione
                for k in range(n + 1):
                    if is_true(out.evaluate(travels(i, j, k))):
                        print(f"Corriere {i} va da {j} a {k}")
        print("\nOrdine di consegna (item_order):")
        for i in range(m):
            for j in range(n):
                val = out.evaluate(item_order(i, j))
                if val is not None:
                    print(f"Corriere {i} consegna item {j} in posizione {val}")
        print('distances')
        for i in range(len(distances)):
            print(out.evaluate(distances[i]))
        print(f"max_dist = {out.evaluate(max_dist)}")

