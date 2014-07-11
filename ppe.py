import cyk

def main():
    grammar = Grammar()
    grammar.terminal('sym')
    grammar.rule("term", "sym")
    grammar.rule("expr", "term")
    grammar.rule("expr", "expr", keyword("plus"), "term")

    results = grammar.parse(tokenize("hello plus ppe"))

    print("count:", len(results))
    print("shortest:", results.shortest)
    tot = 0
    for result in results:
        print(list(result))
        if result.ambiguity == 1:
            print(result.traverse())
        print(result.explain())
        tot += 1

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

    print("redesign", tot)

class Grammar:
    def __init__(self, rules=None, terminals=None):
        self.rules = rules or set()
        self.terminals = terminals or set()
        self.cnf = None
        
    def rule(self, var, *sequence):
        rule = Rule(var, sequence)
        self.rules.add(rule)
        return rule

    def terminal(self, sym):
        self.terminals.add(sym)
    
    def __add__(self, other):
        return Grammar(self.rules | other.rules, self.terminals | other.terminals)

    def parse(self, tokens):
        if self.cnf is None:
            self.cnf = cyk.cnf(self.rules, self.terminals)
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
        return token.near and token.type == self.sym

    def __eq__(self, other):
        return type(self) == type(other) and self.sym == other.sym

    def __hash__(self):
        return hash((type(self), self.sym))

    def __repr__(self):
        return "near({})".format(self.sym)

    def validate(self, terminals):
        if self.sym not in terminals:
            raise Exception("{} of {} is not a terminal".format(self.sym, self))

class far(cyk.Specifier):
    def __init__(self, sym):
        self.sym = sym

    def match(self, token):
        return (not token.near) and token.type == self.sym

    def __eq__(self, other):
        return type(self) == type(other) and self.sym == other.sym

    def __hash__(self):
        return hash((type(self), self.sym))

    def __repr__(self):
        return "far({})".format(self.sym)

    def validate(self, terminals):
        if self.sym not in terminals:
            raise Exception("{} of {} is not a terminal".format(self.sym, self))

class keyword(cyk.Specifier):
    def __init__(self, val, type="sym"):
        self.val  = val
        self.type = type

    def match(self, token):
        return self.val == token.val and self.type == token.type

    def __eq__(self, other):
        return type(self) == type(other) and self.val == other.val and self.type == other.type

    def __hash__(self):
        return hash((type(self), self.val, self.type))

    def __repr__(self):
        return "keyword({}, {})".format(self.val, self.type)

    def validate(self, terminals):
        if self.type not in terminals:
            raise Exception("{} of {} is not a terminal".format(self.type, self))

def tokenize(text, location=1000):
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
        return Token(pos, type, val, w)
    advance()
    while ch:
        string = ""
        if issym(ch):
            while issym(ch):
                string += advance()
            yield token("sym", string)
        elif ch == " ":
            while ch == " ":
                string += advance()
            near = False
        elif isnum(ch):
            while isnum(ch):
                string += advance()
            yield token("num", int(string))

issym   = lambda text: text.isalpha()
isnum   = lambda text: text.isdigit()
isspace = lambda text: text.isspace()

class Token:
    def __init__(self, pos, type, val, near):
        self.pos  = pos
        self.type = type
        self.val  = val
        self.near = near

    def __repr__(self):
        return "{0.type} {0.val!r} at {0.pos}".format(self)

if __name__=='__main__':
    main()
