# converts rules into chomsky normal form.
# 
def cnf(rules, terminals):
    leads = []
    inits = []
    pairs = []
    specifiers = set()
    implicits = {}
    nonterminals = set()
    def decompose(var, rule, sequence):
        if len(sequence) <= 1:
            rhs = sequence[0]
            if var == rhs:
                raise Exception("degenerate rule {}".format(rule))
            if rhs in terminals:
                inits.append(InitSym(rule.var, rule, rhs))
            else:
                leads.append(Lead(rule.var, rule, rhs))
        elif len(sequence) == 2:
            pairs.append(Pair(var, rule, *sequence))
        else:
            lhs, *rhs = sequence
            rhs = tuple(rhs)
            if rhs in implicits:
                imp = implicits[rhs]
            else:
                imp = implicits[rhs] = Implicit(len(implicits))
                decompose(imp, None, rhs)
                pairs.append(Pair(var, rule, lhs, imp))
    for rule in rules:
        if rule.var in terminals:
            raise Exception("{} is both a terminal and a nonterminal, remove the rules or the terminal of this name.".format(rule.var))
        else:
            nonterminals.add(rule.var)
    for rule in rules:
        for arg in rule:
            if isinstance(arg, Specifier):
                if arg not in implicits:
                    specifiers.add(arg)
                    implicits[arg] = arg
                    inits.append(InitSpecifier(arg))
                    arg.validate(terminals)
            elif arg in nonterminals:
                pass
            elif arg in terminals:
                pass
            else:
                raise Exception("{} of {} neither in terminals or nonterminals".format(arg, rule))
        decompose(rule.var, rule, rule)

    leadtab = dict((v, set()) for v in specifiers | nonterminals)

    for lead in leads:
        leadtab[lead.node].add(lead)
    changed = True
    while changed:
        changed = False
        for var, row in leadtab.items():
            merge = set()
            for lead in row:
                merge |= leadtab[lead.var]
            k = len(row)
            row.update(merge)
            changed |= len(row) > k

    return CNF(leadtab, inits, pairs)

class CNF:
    def __init__(self, leads, inits, pairs):
        self.leads = leads
        self.inits = inits
        self.pairs = pairs

class Lead:
    def __init__(self, var, rule, node):
        self.var  = var
        self.rule = rule
        self.node = node

    def __repr__(self):
        if self.rule is None:
            return "{0.node} leads to {0.var}".format(self)
        else:
            return "{0.node} leads to {0.var} {{{0.rule}}}".format(self)

class InitSym:
    def __init__(self, var, rule, terminal):
        self.var      = var
        self.rule     = rule
        self.terminal = terminal

    def match(self, token):
        return token.type == self.terminal

    def __repr__(self):
        if self.rule is None:
            return "{0.var} <- {0.terminal}".format(self)
        else:
            return "{0.var} <- {0.terminal} {{{0.rule}}}".format(self)

class InitSpecifier:
    def __init__(self, specifier):
        self.var       = specifier
        self.specifier = specifier

    def match(self, token):
        return self.specifier.match(token)

    def __repr__(self):
        return "initspec {0.specifier}".format(self)

class Pair:
    def __init__(self, var, rule, lhs, rhs):
        self.var  = var
        self.rule = rule
        self.lhs  = lhs
        self.rhs  = rhs

    def __repr__(self):
        if self.rule is None:
            return "{0.var} <- {0.lhs} {0.rhs}".format(self)
        else:
            return "{0.var} <- {0.lhs} {0.rhs} {{{0.rule}}}".format(self)

class Implicit:
    def __init__(self, num):
        self.num = num

    def __repr__(self):
        return "imp{}".format(self.num)

# The CYK algorithm that powers this thing.
# There's plenty of information about this algorithm,
# The grammar is given in Chomsky normal form.
# Produces every interpretation that is possible with the grammar.
def cyk(tokens, cnf):
    tab = [tokens] # cyk       table
    apl = [None]   # structure table
    for cols in range(len(tokens), 0, -1):
        tab.append([{} for _ in range(cols)])
        apl.append([[] for _ in range(cols)])
    def increment(cell, key, count=1):
        cell[key] = cell.get(key, 0) + count
    for i, token in enumerate(tokens):
        cell  = tab[1][i]
        acell = apl[1][i]
        increment(cell, token.type)
        for init in cnf.inits:
            if init.match(token):
                increment(cell, init.var)
                acell.append((init, 1))
                for lead in cnf.leads.get(init.var, ()):
                    increment(cell, lead.var)
                    acell.append((lead, 1))
    for length in range(2, len(tab)):
        row  = tab[length]
        arow = apl[length]
        for i in range(len(tokens) - length + 1):
            cell  = row[i]
            acell = arow[i]
            for k in range(1, length):
                lcell = lhs_cell(tab, length, i, k)
                rcell = rhs_cell(tab, length, i, k)
                for pair in cnf.pairs:
                    if pair.lhs in lcell and pair.rhs in rcell:
                        lc = lcell[pair.lhs]
                        rc = rcell[pair.rhs]
                        increment(cell, pair.var, lc*rc)
                        acell.append((pair, k))
                        for lead in cnf.leads.get(pair.var, ()):
                            increment(cell, lead.var)
                            acell.append((lead, k))

    return tab, apl, build_mintab(tab)

# length, k - the length of the left-side.
# this way the k and the length is the only thing needed to traverse the parsing result.
def lhs_cell(tab, length, i, k):
    return tab[k][i]

def rhs_cell(tab, length, i, k):
    return tab[length - k][i+k]

def lhs_coords(length, i, k):
    return k, i

def rhs_coords(length, i, k):
    return length-k, i+k

def count(tab):
    """
    Counts the available permutations of parse forests that cover the whole result.
    """
    n     = len(tab[0])
    count = [1] * (n+1)
    for i in range(n-1, -1, -1):
        score = 0
        for length in range(1, 1+n-i):
            if tab[length][i]:
                mult = count[i+length]
                for var in tab[length][i]:
                    if not isinstance(var, Implicit):
                        score += mult
        count[i] = score
    return count[0]

def build_mintab(tab):
    """
    Calculates a map to produce the most concise match first.
    Reveals the shortest match too.
    """
    n   = len(tab[0])
    nom = n+1
    shortest = [nom] * (n+1)
    mintab   = [shortest]
    for cols in range(n, 0, -1):
        mintab.append([nom for _ in range(cols)])
    shortest[n]  = 0
    for i in range(n-1, -1, -1):
        score = nom
        for length in range(1, 1+n-i):
            solution = False
            for var in tab[length][i]:
                if not isinstance(var, Implicit):
                    solution = True
                    break
            if solution:
                s = shortest[i+length] + 1
                mintab[length][i] = s
                score = min(score, length)
        shortest[i] = score
    return mintab

# Specifiers extend the capabilities of the engine.
class Specifier:
    pass
