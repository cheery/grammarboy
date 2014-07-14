from . import cyk

def main():
    grammar = Grammar()
    grammar.terminal('sym')
    grammar.rule("term", "sym")
    grammar.rule("expr", "term")
    grammar.rule("expr", "expr", keyword("plus"), "term")
    grammar.rule("stmt", keyword("return"), "expr")
    lengths, seqs   = shortest_sequences(grammar)
    groups = rules_by_nonterminal(grammar)


    print(seqs)

    distances = completion_distance_to(grammar, lengths, groups, {"stmt"})

    for key, item in distances.items():
        print(key, item)

def intervals(results):
    iv = set()
    for result in results.just(results.shortest):
        interval = []
        for var, length, count in result.trees:
            interval.append(length)
        iv.add(tuple(interval))
    return iv

def visualize_intervals(results):
    tokens = results.tab[0]
    for interval in sorted(intervals(results)):
        offset = 0
        s = ''
        for length in interval:
            start = tokens[offset].pos % 1000
            tok = tokens[offset+length-1]
            stop = tok.pos % 1000 + tok.length
            s += " " * (start - len(s))
            if tok.length > 1:
                s += "|"
                s += "-" * (stop - start - 2)
                s += "|"
            else:
                s += "'"
            offset += length
        yield s

def relevant_ruleset(results):
    inversions = rule_inversions(results.grammar)
    ruleset = set()
    for result in results.just(results.shortest):
        inv = []
        for cell in result:
            for index, rule in inversions.get(cell, ()):
                if len(rule) > 1:
                    ruleset.add(rule)
    return ruleset 

def rule_inversions(grammar):
    inversions = {}
    for rule in grammar.rules:
        for index, cell in enumerate(rule):
            if cell not in inversions:
                inversions[cell] = []
            inversions[cell].append((index, rule))
    return inversions

def completion_distance_to(grammar, lengths, groups, goals):
    distance = {}
    queue = []
    for goal in goals:
        distance[goal] = 0
        queue.append(goal)
    while queue:
        current   = queue.pop(0)
        d_current = distance[current]
        for rule in groups.get(current, ()):
            weight = sum(lengths[cell] for cell in rule)
            for cell in rule:
                d = weight - lengths[cell] + d_current
                if cell in distance:
                    distance[cell] = min(distance[cell], d)
                else:
                    queue.append(cell)
                    distance[cell] = d
        queue.sort(key=lambda cell: distance[cell])
    return distance

def shortest_sequences(grammar):
    lengths = {}
    sequences = {}
    for term in grammar.terminals:
        lengths[term] = 1
        sequences[term] = [term]
    for term in grammar.cnf.specifiers:
        lengths[term] = 1
        sequences[term] = [term]

    def price_sum(rule):
        price = 0
        for cell in rule:
            if cell not in lengths:
                return None
            price += lengths[cell]
        return price

    unrelaxed = True
    while unrelaxed:
        unrelaxed = False
        for rule in grammar.rules:
            p = price_sum(rule)
            if p:
                cat = []
                for cell in rule:
                    cat += sequences[cell]
                was = lengths.get(rule.var, p+1)
                lengths[rule.var] = min(p,was)
                if p < was:
                    sequences[rule.var] = cat
                unrelaxed |= p < was

    rule_sequences = {}
    for rule in grammar.rules:
        cat = []
        for cell in rule:
            cat += sequences[cell]
        rule_sequences[rule] = cat
    return lengths, rule_sequences

def rules_by_nonterminal(grammar):
    nonterminals = {}
    for rule in grammar.rules:
        if rule.var not in nonterminals:
            nonterminals[rule.var] = []
        nonterminals[rule.var].append(rule)
    return nonterminals

class Grammar:
    def __init__(self, rules=None, terminals=None):
        self.rules = rules or set()
        self.terminals = terminals or set()
        self._cnf = None

    @property
    def cnf(self):
        if self._cnf is None:
            self._cnf = cyk.cnf(self.rules, self.terminals)
        return self._cnf
        
    def rule(self, var, *sequence):
        rule = Rule(var, sequence)
        self.rules.add(rule)
        return rule

    def terminal(self, sym):
        self.terminals.add(sym)
    
    def __add__(self, other):
        return Grammar(self.rules | other.rules, self.terminals | other.terminals)

    def parse(self, tokens):
        tokens = list(tokens)
        tab, apl, mintab = cyk.cyk(tokens, self.cnf)
        return Table(self, tab, apl, mintab)

class Rule:
    def __init__(self, var, row):
        self.var = var
        self.row = row

    def __getitem__(self, index):
        return self.row[index]

    def __len__(self):
        return len(self.row)

    def __iter__(self):
        return iter(self.row)

    def __repr__(self):
        return "{} <- {}".format(self.var, ' '.join(map(str,self.row)))

class Table:
    def __init__(self, grammar, tab, apl, mintab):
        self.grammar = grammar
        self.tab    = tab
        self.apl    = apl
        self.mintab = mintab
        self._length = None
        self.shortest = mintab[0][0]
    
    def __len__(self):
        if self._length is None:
            self._length = cyk.count(self.tab)
        return self._length

    def just(self, length):
        assert length >= 1
        yield from iter_results(self, length)

    def __iter__(self):
        for i in range(1, len(self.tab)):
            yield from iter_results(self, i)

def iter_results(table, size=1, index=0, prefix=[], ambiguity=1):
    n = len(table.tab[0])
    if size == 0 and index == n:
        yield Result(table, ambiguity, prefix)
    elif size > 0:
        for length in range(1+n-size-index, 0, -1):
            for var, count in table.tab[length][index].items():
                if isinstance(var, cyk.Implicit):
                    continue
                yield from iter_results(table, size - 1, index+length, prefix + [(var,length,count)], ambiguity*count)

class Result:
    def __init__(self, table, ambiguity, trees):
        self.table     = table
        self.ambiguity = ambiguity
        self.trees     = trees

    def traverse(self, visitor=None, *args):
        if self.ambiguity > 1:
            raise TypeError("Ambiguous result does not produce unambiguous traversal")
        return traverse(self.table, self.trees, visitor, args)

    def explain(self):
        return explain(self.table, self.trees)

    def __iter__(self):
        for var, length, count in self.trees:
            yield var

    def __len__(self):
        return len(self.trees)

    def __getitem__(self, index):
        return self.trees[index][0]

def traverse(table, trees, visitor, args):
    index = 0
    output = []
    if visitor is None:
        visitor = lambda rule, lst: [rule] + lst
    for var, length, _ in trees:
        output.append(traverse_item(table, var, length, index, visitor, args))
        index += length
    return output

def traverse_item(table, var, length, index, visitor, args):
    if length == 1:
        obj = None
        for obj, k in table.apl[length][index]:
            if obj.var == var:
                break
            obj = None
        if isinstance(obj, cyk.Lead):
            return visitor(obj.rule, [traverse_item(table, obj.node, length, index, visitor, args)], *args)
        if obj and not isinstance(obj.var, cyk.Specifier):
            return visitor(obj.rule, [table.tab[0][index]], *args)
        else:
            return table.tab[0][index]

    for obj, k in table.apl[length][index]:
        if obj.var == var:
            break
    
    if isinstance(obj, cyk.Lead):
        return visitor(obj.rule, [traverse_item(table, obj.node, length, index, visitor, args)], *args)

    lhs_length, lhs_index = cyk.lhs_coords(length, index, k)
    rhs_length, rhs_index = cyk.rhs_coords(length, index, k)

    left  = traverse_item(table, obj.lhs, lhs_length, lhs_index, visitor, args)
    right = traverse_item(table, obj.rhs, rhs_length, rhs_index, visitor, args)
    if isinstance(obj.var, cyk.Implicit):
        return [left, right]
    if isinstance(obj.rhs, cyk.Implicit):
        return visitor(obj.rule, [left] + right, *args)
    return visitor(obj.rule, [left, right], *args)

def explain(table, trees):
    index  = 0
    output = []
    for var, length, _ in trees:
        rules = []
        for obj, k in table.apl[length][index]:
            if obj.var == var and not isinstance(obj, cyk.InitSpecifier):
                rules.append(Explanation(obj.rule, index, length, k))
        index += length
        output.append(rules)
    return output

class Explanation:
    def __init__(self, rule, index, length, middle):
        self.rule   = rule
        self.index  = index
        self.middle = middle 
        self.length = length

    def __repr__(self):
        return "{0.rule}:{0.index}:{0.middle}:{0.length}".format(self)

class near(cyk.Specifier):
    def __init__(self, sym):
        self.sym = sym

    def match(self, token):
        if isinstance(self.sym, cyk.Specifier):
            return (not token.near) and self.sym.match(token)
        return token.near and token.type == self.sym

    def __eq__(self, other):
        return type(self) == type(other) and self.sym == other.sym

    def __hash__(self):
        return hash((type(self), self.sym))

    def __repr__(self):
        return "near({})".format(self.sym)

    def validate(self, terminals):
        if isinstance(self.sym, cyk.Specifier):
            return self.sym.validate(terminals)
        if self.sym not in terminals:
            raise Exception("{} of {} is not a terminal or a specifier".format(self.sym, self))

class far(cyk.Specifier):
    def __init__(self, sym):
        self.sym = sym

    def match(self, token):
        if isinstance(self.sym, cyk.Specifier):
            return (not token.near) and self.sym.match(token)
        return (not token.near) and token.type == self.sym

    def __eq__(self, other):
        return type(self) == type(other) and self.sym == other.sym

    def __hash__(self):
        return hash((type(self), self.sym))

    def __repr__(self):
        return "far({})".format(self.sym)

    def validate(self, terminals):
        if isinstance(self.sym, cyk.Specifier):
            return self.sym.validate(terminals)
        if self.sym not in terminals:
            raise Exception("{} of {} is not a terminal".format(self.sym, self))

class keyword(cyk.Specifier):
    def __init__(self, val):
        self.val  = val

    def match(self, token):
        return self.val == token.val

    def __eq__(self, other):
        return type(self) == type(other) and self.val == other.val

    def __hash__(self):
        return hash((type(self), self.val))

    def __repr__(self):
        return "keyword({})".format(self.val)

    def validate(self, terminals):
        pass

def tokenize(text, keywords, location=1000):
    ch  = None
    pos = location - 2
    near = True
    def advance():
        nonlocal ch, text, pos
        last = ch
        ch   = text[:1]
        text = text[1:]
        pos += 1
        if last == '\n':
            pos = 1000 + pos // 1000 * 1000
        return last
    def token(type, val):
        nonlocal near
        w = near
        near  = True
        return Token(pos - len(string) + 1, len(string), type, val, w)
    advance()
    while ch:
        string = ""
        if issym(ch):
            while issym(ch):
                string += advance()
            if string in keywords:
                yield token("keyword", string)
            else:
                yield token("sym", string)
        elif ch == " ":
            while ch == " ":
                string += advance()
            near = False
        elif isnum(ch):
            while isnum(ch):
                string += advance()
            yield token("num", int(string))
        else:
            string += advance()
            yield token("unk", string)

issym   = lambda text: text.isalpha()
isnum   = lambda text: text.isdigit()
isspace = lambda text: text.isspace()

class Token:
    def __init__(self, pos, length, type, val, near):
        self.pos    = pos
        self.length = length
        self.type   = type
        self.val    = val
        self.near   = near

    def __repr__(self):
        return "{0.type} {0.val!r} at {0.pos}".format(self)

if __name__=='__main__':
    main()
