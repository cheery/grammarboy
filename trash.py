# bunch of stuff that didn't work.

#costs, seq = shortest_sequences(grammar)
#print(costs)
#print(seq)
#print(rules)

##results = grammar.parse(tokenize("hello plus ppe"))

##print("count:", len(results))
##print("shortest:", results.shortest)
##tot = 0
##for result in results:
##    print(list(result))
##    if result.ambiguity == 1:
##        print(result.traverse())
##    print(result.explain())
##    tot += 1
##print("redesign", tot)

#matcher = difflib.SequenceMatcher(None)
#matches = []
#for result in islice(results, 0, 10):
#    matcher.set_seq1(list(result))
#    print(list(result), result.ambiguity)
#    for rule in grammar.bi:
#        if rule.row:
#            matcher.set_seq2(list(rule))
#            ratio = matcher.ratio()
#            if ratio > 0.0:
#                matches.append((ratio, rule, list(result)))
#matches.sort(key=lambda x: -x[0])
#print_table(matches)

#def propose(results, goals, count=50):
#    matcher = difflib.SequenceMatcher(None)
#    matches = []
#    for result in results:
#        if len(result) == 1 and result[0] in goals:
#            raise Exception("has solution")
#        if result.ambiguity > 1:
#            print("ambiguous", *result)
#            continue
#        matcher.set_seq1(list(result))
#        for rule in grammar.rules:
#            if len(rule) == 1:
#                continue
#            matcher.set_seq2(rule.row)
#            ratio = matcher.ratio()
#            if ratio > 0.0:
#                matches.append((ratio, rule, result))
#                if len(matches) >= count:
#                    return sorted(matches, key=lambda x: -x[0])
#    return sorted(matches, key=lambda x: -x[0])

#def test(result, rule):
#    result = iter(result)
#    rule  = iter(rule)
#    for a in result:
#        for b in rule:
#            if a == b:
#                yield True
#                break
#            else:
#                yield False
#
#def propose(results, goals):
#    print("mintab")
#    for row in results.mintab:
#        print(*row)
#    #print("shortest result", results.shortest)
#    count = 5
#    for result in results:
#        print("result", *result)
#        count -= 1
#        if count <= 0:
#            break
#    no_results = True
#    shortest   = results.shortest
#    while no_results:
#        for result in results.just(shortest):
#            print("trying result", *result)
#            for rule in grammar.rules:
#                if len(rule) <= 1:
#                    continue
#                match = tuple(test(result, rule))
#                if sum(match) >= 2:
#                    yield result, rule, match
#                    no_results = False
#        shortest += 1

#    for x in results:
#        print(*x)
#        if i >= 5:
#            break
#        i += 1
