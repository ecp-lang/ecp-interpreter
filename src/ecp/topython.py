"""Converts a list of ECP tokens into a python AST and provides the environment for execution."""
from parsergen import *
from parsergen.pyparse import Statement
from .lexer import *
from .tracker import Tracer
import sys, os
try:
    import astor
except ImportError:
    print("astor module not found - will not be able to convert ECP to python source code")
    astor = None
from math import gamma, sqrt
from random import randint, uniform
from ast import *
import ast
_List = ast.List
_Dict = ast.Dict

BUILTIN_IMPORT = "from ecp.topython import *\n"

TOKEN_TO_OP = {
    "ADD":     Add,
    "SUB":     Sub,
    "MUL":     Mult,
    "DIV":     Div,
    "INT_DIV": FloorDiv,
    "POW":     Pow,
    "MOD":     Mod,
    "LT":      Lt,
    "LE":      LtE,
    "EQ":      Eq,
    "NE":      NotEq,
    "GT":      Gt,
    "GE":      GtE,
    "AND":     And,
    "OR":      Or,
    "NOT":     Not,
}

def _dump(node, annotate_fields=True, include_attributes=False, *, indent=None):
    """
    Return a formatted dump of the tree in node.  This is mainly useful for
    debugging purposes.  If annotate_fields is true (by default),
    the returned string will show the names and the values for fields.
    If annotate_fields is false, the result string will be more compact by
    omitting unambiguous field names.  Attributes such as line
    numbers and column offsets are not dumped by default.  If this is wanted,
    include_attributes can be set to true.  If indent is a non-negative
    integer or string, then the tree will be pretty-printed with that indent
    level. None (the default) selects the single line representation.
    """
    def _format(node, level=0):
        if indent is not None:
            level += 1
            prefix = '\n' + indent * level
            sep = ',\n' + indent * level
        else:
            prefix = ''
            sep = ', '
        if isinstance(node, AST):
            cls = type(node)
            args = []
            allsimple = True
            keywords = annotate_fields
            for name in node._fields:
                try:
                    value = getattr(node, name)
                except AttributeError:
                    keywords = True
                    continue
                if value is None and getattr(cls, name, ...) is None:
                    keywords = True
                    continue
                value, simple = _format(value, level)
                allsimple = allsimple and simple
                if keywords:
                    args.append('%s=%s' % (name, value))
                else:
                    args.append(value)
            if include_attributes and node._attributes:
                for name in node._attributes:
                    try:
                        value = getattr(node, name)
                    except AttributeError:
                        continue
                    if value is None and getattr(cls, name, ...) is None:
                        continue
                    value, simple = _format(value, level)
                    allsimple = allsimple and simple
                    args.append('%s=%s' % (name, value))
            if allsimple and len(args) <= 3:
                return '%s(%s)' % (node.__class__.__name__, ', '.join(args)), not args
            return '%s(%s%s)' % (node.__class__.__name__, prefix, sep.join(args)), False
        elif isinstance(node, list):
            if not node:
                return '[]', True
            return '[%s%s]' % (prefix, sep.join(_format(x, level)[0] for x in node)), False
        return repr(node), True

    if not isinstance(node, AST):
        raise TypeError('expected AST, got %r' % node.__class__.__name__)
    if indent is not None and not isinstance(indent, str):
        indent = ' ' * indent
    return _format(node)[0]

"""
Grammar for ECP


program                 :  compound
compound                :  statement_list
statement_list          :  NEWLINE* (statement NEWLINE*)*
statement               :  magic_function
                        |  if_statement | for_loop | while_loop | repeat_until_loop | record_definition | try_catch | suboroutine_definition | class_definition | import_statement | assignment_statement
                        |  expr
assignment_statement    :  variable (COLON ID)? ASSIGN expr
variable                :  CONSTANT? ID indexing
attr_index              :  DOT ID
subscript_index         :  LS_PAREN expr RS_PAREN
call                    :  LPAREN (expr (COMMA expr)* COMMA?)? RPAREN
indexing                :  (attr_index | subscript_index | call)*
factor                  :  factor_part indexing
factor_part             :  PLUS factor
                        |  SUB factor
                        |  NOT factor
                        |  INT
                        |  FLOAT
                        |  BOOLEAN
                        |  STRING
                        |  NONE
                        |  LPAREN expr RPAREN
                        |  array | dictionary | magic_function | variable
term                    :  factor (POW term)?
term2                   :  term ((MUL | DIV | INT_DIV | MOD) term)*
term3                   :  term2 ((ADD | SUB) term2)*
term4                   :  term3 ((LT | GT | LE | GE | EQ | NE) term3)*
term5                   :  term4 ((AND | OR) term4)*
expr                    :  term5
magic_function          :  MAGIC (expr (COMMA expr)* COMMA?)?
param_definition        :  ID (COLON ID)?
_                       :  NEWLINE*
suboroutine_definition  :  SUBROUTINE ID LPAREN (param_definition (COMMA param_definition)* COMMA?)? RPAREN compound END
if_statement            :  IF expr _ THEN compound (elseif_statement | else_statement)? END
elseif_statement        :  ELSE if_statement
else_statement          :  ELSE compound
while_loop              :  WHILE expr _ compound END
repeat_until_loop       :  REPEAT _ compound _ UNTIL expr
array                   :  LS_PAREN (_ expr (_ COMMA _ expr)* _ COMMA?)? _ RS_PAREN
dictionary              :  LC_BRACE (_ expr _ COLON _ expr (_ COMMA _ expr _ COLON _ expr)* _ COMMA?)? _ RC_BRACE
for_loop                :  FOR variable ASSIGN expr TO expr (STEP expr)? _ compound _ END
                        |  FOR variable IN expr _ compound _ END
record_definition       :  RECORD ID (_ variable (COLON ID)?)* _ END
try_catch               :  TRY compound CATCH compound END
class_definition        :  CLASS variable compound END
import_statement        :  IMPORT expr (AS expr)?

"""




class ParseToPython(Parser):
    tokens = EcpLexer.tokens
    starting_point = "program"
    
    #def error(self):
    #    raise ParseError(
    #        f"Unexpected token {self.current_token.error_format()}", 
    #        *self.current_token.pos,
    #        lineText=self.lexer.lines[self.current_token.lineno-1]
    #    )

    @property
    def loc(self):
        return {"lineno": self.current_token.lineno, "col_offset": self.current_token.column}

    @grammar("compound")
    def program(self, p):
        return Module(body=p[0], type_ignores=[])
    
    @grammar("statement_list")
    def compound(self, p):
        nodes = p[0]
        if len(nodes) == 0:
            nodes.append(Pass(**self.loc))
        return nodes
    
    @grammar("NEWLINE* (statement NEWLINE*)*")
    def statement_list(self, p):
        results = [s[0] for s in p[1] if s[0]]
        return results
    
    @grammar("magic_function")
    def statement(self, p):
        node = p[0]
        if isinstance(node, expr):
            return Expr(value=node, lineno=node.lineno, col_offset=node.col_offset)
        return node
        
    @grammar("if_statement | for_loop | while_loop | repeat_until_loop | record_definition | try_catch | suboroutine_definition | class_definition | import_statement | assignment_statement")
    def statement(self, p):
        return p[0]
    
    @grammar("expr")
    def statement(self, p):
        value = p[0]
        if isinstance(value, expr):
            return Expr(value=value, lineno=value.lineno, col_offset=value.col_offset)
        return value
    
    @grammar("variable (COLON ID)? ASSIGN expr")
    def assignment_statement(self, p):
        left = p[0]
        left.ctx = Store()
        right = p[3]
        node = Assign(targets=[left], value=right, **self.loc)
        return node
    
    @grammar("CONSTANT? ID indexing")
    def variable(self, p):
        node = Name(id=p[1], ctx=Load(), **self.loc)
        return self.process_indexing(node, p[2])

    @grammar("DOT ID")
    def attr_index(self, p):
        return "attr", p[1]
    
    @grammar("LS_PAREN expr RS_PAREN")
    def subscript_index(self, p):
        return "subscript", p[1]

    @grammar("LPAREN (expr (COMMA expr)* COMMA? )? RPAREN")
    def call(self, p):
        params = []
        if p[1] != None and len(p[1]) > 1:
            params.append(p[1][0])
            for _, param in p[1][1]:
                params.append(param)
        
        return "call", params
    
    @grammar("(attr_index | subscript_index | call)*")
    def indexing(self, p):
        return [s[0] for s in p[0]]

    def process_indexing(self, node, indexing):
        rv = node
        for t, v in indexing:
            if t == "attr":
                rv = Attribute(value=rv, attr=v, ctx=Load(), **self.loc)
            elif t == "subscript":
                rv = Subscript(value=rv, slice=Index(value=v), ctx=Load(), **self.loc)
            elif t == "call":
                rv = Call(func=rv, args=v, keywords=[], **self.loc)
        return rv
    
    def empty(self):
        return Pass()

    @grammar("factor_part indexing")
    def factor(self, p):
        return self.process_indexing(p[0], p[1])
    
    @grammar("PLUS factor")
    def factor_part(self, p):
        return UnaryOp(op=UAdd(), operand=p[1], lineno=p[1].lineno, col_offset=p[1].col_offset)

    @grammar("SUB factor")
    def factor_part(self, p):
        return UnaryOp(op=USub(), operand=p[1], lineno=p[1].lineno, col_offset=p[1].col_offset)

    @grammar("NOT factor")
    def factor_part(self, p):
        return UnaryOp(op=Not(), operand=p[1], lineno=p[1].lineno, col_offset=p[1].col_offset)
    
    @grammar("INT")
    def factor_part(self, p):
        return Constant(value=int(p[0]), **self.loc)
    
    @grammar("FLOAT")
    def factor_part(self, p):
        return Constant(value=float(p[0]), **self.loc)

    @grammar("BOOLEAN")
    def factor_part(self, p):
        return Constant(value=False if p[0] == "False" else True, **self.loc)
    
    @grammar("STRING")
    def factor_part(self, p):
        return Constant(value=str(p[0]), **self.loc)
    
    @grammar("NONE")
    def factor_part(self, p):
        return Constant(value=None, **self.loc)
    
    @grammar("LPAREN expr RPAREN")
    def factor_part(self, p):
        return p[1]
    
    @grammar("array | dictionary | magic_function | variable")
    def factor_part(self, p):
        return p[0]

    @grammar("factor (POW term)?")
    def term(self, p):
        node = p[0]
        if p[1]:
            node = BinOp(left=node, op=Pow(), right=p[1][1], lineno=p[1][1].lineno, col_offset=p[1][1].col_offset)
        
        return node
    
    @grammar("term ( (MUL | DIV | INT_DIV | MOD) term )*")
    def term2(self, p):
        node = p[0]
        for [op], t in p[1]:
            node = BinOp(left=node, op=TOKEN_TO_OP[op](), right=t, lineno=t.lineno, col_offset=t.col_offset)
        
        return node
    
    @grammar("term2 ( (ADD | SUB) term2 )*")
    def term3(self, p):
        node = p[0]
        for [op], t in p[1]:
            node = BinOp(left=node, op=TOKEN_TO_OP[op](), right=t, lineno=t.lineno, col_offset=t.col_offset)
        
        return node
    
    @grammar("term3 ( (LT | GT | LE | GE | EQ | NE) term3)*")
    def term4(self, p):
        node = p[0]
        for [op], t in p[1]:
            if not isinstance(node, Compare):
                node = Compare(left=node, ops=[TOKEN_TO_OP[op]()], comparators=[t], lineno=t.lineno, col_offset=t.lineno)
            else:
                node.ops.append(TOKEN_TO_OP[op]())
                node.comparators.append(t)
        
        return node
    
    @grammar("term4 ( (AND | OR) term4)*")
    def term5(self, p):
        node = p[0]
        for [op], t in p[1]:
            if not isinstance(node, BoolOp):
                node = BoolOp(op=TOKEN_TO_OP[op](), values=[node, t], lineno=t.lineno, col_offset=t.lineno)
            else:
                node.values.append(t)
        
        return node
        
    @grammar("term5")
    def expr(self, p):
        return p[0]
        
    @grammar("MAGIC (expr (COMMA expr)* COMMA? )?")
    def magic_function(self, p):
        parameters = []
        if p[1] != None and len(p[1]) > 0:
            parameters.append(p[1][0])
            if len(p[1]) > 1:
                for _, param in p[1][1]:
                    parameters.append(param)
        name = p[0]
        
        if name == "RETURN":
            if len(parameters) == 1:
                return Return(value=parameters[0])
            if len(parameters > 1):
                return Return(value=Tuple(elts=parameters, ctx=Load()))
            return Return()
        elif name == "CONTINUE":
            return Continue()
        elif name == "BREAK":
            return Break()

        return Call(func=Name(id="_MAGIC_"+name, ctx=Load()), args=parameters, keywords=[], **self.loc)
    

    @grammar("ID (COLON ID)?")
    def param_definition(self, p):
        node = arg(arg=p[0], annotation=None, **self.loc)
        return node
    
    @grammar("NEWLINE*")
    def _(self, p):
        pass

    @grammar("SUBROUTINE ID LPAREN (param_definition (COMMA param_definition)* COMMA? )? RPAREN compound END")
    def suboroutine_definition(self, p):
        parameters = []
        if p[3] != None and len(p[3]) > 0: # maybe broken
            parameters.append(p[3][0])
            for _, param in p[3][1]:
                parameters.append(param)
        name = p[1]
        compound = p[5]
        return FunctionDef(
            name=name, 
            args=arguments(args=parameters, posonlyargs=[], kwonlyargs=[], kw_defaults=[], defaults=[], kwarg=None, vararg=None), 
            body=compound, 
            decorator_list=[], 
            returns=None, 
            type_comment=None, 
            lineno=self.current_token.lineno, 
            col_offset=self.current_token.lineno
        )
 
    @grammar("IF expr _ THEN compound ( elseif_statement | else_statement )? END")
    def if_statement(self, p):
        condition = p[1]
        consequence = p[4]
        alternative = p[5] if p[5] is not None else []
        return If(test=condition, body=consequence, orelse=alternative, **self.loc)

    @grammar("ELSE if_statement")
    def elseif_statement(self, p):
        return [p[1]]
    
    @grammar("ELSE compound")
    def else_statement(self, p):
        return p[1]
    
    @grammar("WHILE expr _ compound END")
    def while_loop(self, p):
        token = self.current_token
        condition = p[1]
        consequence = p[3]
        return While(test=condition, body=consequence, orelse=[], lineno=token.lineno, col_offset=token.column)
        # TODO: implement else after while and for loops
    
    @grammar("REPEAT _ compound _ UNTIL expr")
    def repeat_until_loop(self, p):
        token = self.current_token
        consequence = p[2]
        condition = p[-1]

        check = If(
            test=condition,
            body=[Break()],
            orelse=[]
        )

        node = While(test=Constant(value=True), body=consequence + [check], orelse=[], lineno=token.lineno, col_offset=token.column)

        return node
    
    @grammar("LS_PAREN (_ expr ( _ COMMA _ expr)* _ COMMA? )? _ RS_PAREN")
    def array(self, p):
        values = []
        if p[1] is not None and len(p[1]) > 1:
            values = [p[1][1]]
            for [_, _, _, v] in p[1][2]:
                values.append(v)
        return List(elts=values, ctx=Load(), **self.loc)
    
    @grammar("LC_BRACE (_ expr _ COLON _ expr ( _ COMMA _ expr _ COLON _ expr)* _ COMMA? )? _ RC_BRACE")
    def dictionary(self, p):
        keys = []
        values = []
        if p[1] is not None:
            keys, values = [p[1][1]], [p[1][5]]
            if len(p[1][6]) > 6:
                for [_, _, _, k, _, _, v] in p[1][6]:
                    keys.append(k)
                    values.append(v)
        return _Dict(keys=keys, values=values, **self.loc)
    
    @grammar("FOR variable ASSIGN expr TO expr (STEP expr)? _ compound _ END")
    def for_loop(self, p):
        variable = p[1]
        variable.ctx = Store()
        step = Constant(value=1, **self.loc)

        start = p[3]
        end = p[5]
        if p[6]:
            step = p[6][1]

        body = p[8]
        f = For(
            target=variable,
            iter=Call(
                func=Name(id='range', ctx=Load(), **self.loc),
                args=[
                  start,
                  BinOp(left=end, op=Add(), right=Constant(value=1, **self.loc), **self.loc),
                  step
                ],
                keywords=[], **self.loc
            ),
            body=body,
            orelse=[],
            lineno=self.current_token.lineno,
            col_offset=self.current_token.column
        )
            
        return f
    
    @grammar("FOR variable IN expr _ compound _ END")
    def for_loop(self, p):
        variable = p[1]
        variable.ctx = Store()
        iterator = p[3]
        body = p[5]
        
        f = For(
            target=variable,
            iter=iterator,
            body=body,
            orelse=[],
            lineno=self.current_token.lineno,
            col_offset=self.current_token.column
        )
        return f
    
    @grammar("RECORD ID ( _ variable (COLON ID)? )* _ END")
    def record_definition(self, p):
        name = p[1]
        parameters = []
        for [_, variable, *_] in p[2]: # maybe broken
            parameters.append(variable.id)

        # class something:
        #   def __init__(self, a, b, c, ...):
        #       self.a = a
        #       self.b = b
        #       self.c = c
        #       ...  = ...
        return ClassDef(
            name=name,
            bases=[],
            keywords=[],
            body=[
                FunctionDef(
                    name="__init__", 
                    args=arguments(args=[arg(arg='self', annotation=None)]+[arg(arg=p, annotation=None) for p in parameters], posonlyargs=[], kwonlyargs=[], kw_defaults=[], defaults=[], kwarg=None, vararg=None), 
                    body=[
                        Assign(
                            targets=[
                                Attribute(
                                    value=Name(
                                        id='self', 
                                        ctx=Load()
                                    ),
                                    attr=p,
                                    ctx=Store()
                                )
                            ],
                            value=Name(
                                id=p,
                                ctx=Load()
                            )
                        ) for p in parameters
                    ], 
                    decorator_list=[], 
                    returns=None, 
                    type_comment=None, 
                    lineno=self.current_token.lineno, 
                    col_offset=self.current_token.lineno
                )
            ],
            decorator_list=[],
            lineno=self.current_token.lineno,
            col_offset=self.current_token.column
        )
        
    
    @grammar("TRY compound CATCH compound END")
    def try_catch(self, p):
        try_compound = p[1]
        catch_compound = p[3]
        
        return Try(
            body=try_compound,
            handlers=[
                ExceptHandler(
                    type=None,
                    name=None,
                    body=catch_compound
                )
            ],
            orelse=[],
            finalbody=[]
        )
    
    @grammar("CLASS variable compound END")
    def class_definition(self, p):
        variable = p[1]
        body = p[2]
        
        return ClassDef(
            name=variable.id,
            bases=[],
            keywords=[],
            body=body,
            decorator_list=[],
            lineno=self.current_token.lineno,
            col_offset=self.current_token.column
        )
    
    @grammar("IMPORT expr (AS expr)?")
    def import_statement(self, p):
        location = p[1]
        target = Constant(value=None)
        if p[2] is not None:
            target = p[2][1]
        
        return Expr(
            value=Call(
                func=Name(id='_ECP_IMPORT', ctx=Load()),
                args=[location, target, Call(func=Name(id='globals', ctx=Load()), args=[], keywords=[])],
                keywords=[]
            )
        )

    #def parse(self):
    #    node = self.program()
    #    if self.current_token.type != TokenType.EOF:
    #        self.error()
    #    return node 

class Namespace:
    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


def fix_line_and_column(node):
    for child in walk(node):
        if 'lineno' in child._attributes:
            child.lineno = getattr(child, 'lineno', 0)
        if 'end_lineno' in child._attributes:
            child.end_lineno = getattr(child, 'end_lineno', 0)
        if 'col_offset' in child._attributes:
            child.col_offset = getattr(child, 'col_offset', 0)
        if 'end_col_offset' in child._attributes:
            child.end_col_offset = getattr(child, 'end_col_offset', 0)
    return fix_missing_locations(node)

def parse_ecp(text: str):
    return fix_line_and_column(ParseToPython().parse(EcpLexer().lex_string(text)))

def to_py_source(text: Union[str, Module]):
    code = text
    if isinstance(text, str):
        code = parse_ecp(text)
    if astor is not None:
        return BUILTIN_IMPORT + astor.to_source(code)
    raise Exception("astor module not found - cannot convert ecp to python source code")

def ecp(text: str=None, *, file: str=None, name="<unkown>", showAST=False, scope=None, trace=None, tracecompact=False):
    if text is None:
        with open(file, encoding="utf-8") as f:
            text = f.read()
    if scope is None:
        scope = {}
    if isinstance(scope, Namespace):
        scope = vars(scope)
    if trace is None:
        trace = []
    scope.update(globals())
    r = parse_ecp(text)
    if showAST:
        print(_dump(r, indent=2))
    if len(trace) > 0:
        with Tracer(trace, compact=tracecompact):
            exec(compile(parse(r, mode="exec"), name, "exec"), scope)
    else:
        exec(compile(parse(r, mode="exec"), name, "exec"), scope)

    return Namespace(**scope)

def _ECP_IMPORT(location: str, target: str, scope=None):
    m = None
    for p in sys.path:
        if os.path.exists(p + location + ".ecp"):
            s = ecp(file=p + location + ".ecp", scope=globals())
            scope[target] = s
            return
    raise ImportError(name=location, path=p + location + ".ecp")


# ECP BUILTINS

_MAGIC_OUTPUT = print
_MAGIC_USERINPUT = input
INPUT = input
LEN = len
Integer = int
Int = int
Real = float
Bool = bool
String = str
Array = list
Dictionary = dict

def POSITION(string: str, to_match: str) -> int:
    try:
        return string.index(to_match)
    except:
        return -1

def SUBSTRING(start: int, end: int, string: str):
    return string[start:end+1]

STRING_TO_INT = int
STRING_TO_REAL = float
INT_TO_STRING = REAL_TO_STRING = str
CHAR_TO_CODE = ord
CODE_TO_CHAR = chr
RANDOM_INT = randint
SQRT = sqrt

PY = exec