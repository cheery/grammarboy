from grammarboy import Grammar, keyword, near, far, tokenize, relevant_ruleset, visualize_intervals

# keywords for the tokenizer, could be derived from the grammar itself.
keywords = {'return', 'and', 'or'}

# stores the guidance strings
guide = {}

# to evaluate the few rules defined here.
interpreter = {}
def interp(rule):
    def _impl(fn):
        interpreter[rule] = fn
        return fn
    return _impl

def interpret(rule, pattern, env):
    if rule in interpreter:
        return interpreter[rule](pattern, env)
    elif len(rule) == 1:
        return pattern[0]
    else:
        raise Exception(repr(rule))

# here's the grammar understood by the engine
grammar = Grammar()
grammar.terminal("num")
grammar.terminal("unk")
grammar.rule("expr",   "expr90")
grammar.rule("expr90", "term")

_return = grammar.rule("stmt", keyword("return"), "expr")
guide[_return] = "return from function"

_number = grammar.rule("term",   "num")
@interp(_number)
def i_number(expr, env):
    return expr[0].val

_add = grammar.rule("expr90", "expr90", keyword("+"), "term")
guide[_add] = "addition"
@interp(_add)
def i_add(expr, env):
    return expr[0] + expr[2]

_sub = grammar.rule("expr90", "expr90", keyword("-"), "term")
guide[_sub] = "subtract"
@interp(_sub)
def i_sub(expr, env):
    return expr[0] - expr[2]

_and = grammar.rule("expr", "expr90", keyword("and"), "expr")
guide[_and] = "logical and"
@interp(_and)
def i_and(expr, env):
    return expr[0] and expr[2]

_or  = grammar.rule("expr", "expr90", keyword("or"),  "expr")
guide[_or]  = "logical or"
@interp(_or)
def i_or(expr, env):
    return expr[0] or expr[2]

while True:
    text = input("> ")
    results = grammar.parse(list(tokenize(text, keywords)))
    success = False
    goals = {'expr'}
    for result in results.just(1):
        if result.ambiguity == 1 and result[0] in goals:
            print(result.traverse(interpret, {})[0])
            success = True
    if not success:
        for string in visualize_intervals(results):
            print("  " + string)
        for rule in sorted(relevant_ruleset(results), key=lambda rule: rule.var):
            out = []
            for cell in rule:
                if isinstance(cell, keyword):
                    out.append(cell.val)
                else:
                    out.append("<"+cell+">")
            print("{:>8} := {:30} # {:30}".format(rule.var, ' '.join(out), guide.get(rule, '')))
        print()
