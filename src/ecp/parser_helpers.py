"""Helper functions for creating the creating python AST via the ECP parser"""

from collections import namedtuple
from parsergen import *
from parsergen.parser import ParseError
from parsergen.parser_utils import Filler, GeneratedParser
from .lexer import *
from ast import *
from typing import *
import ast
_List = ast.List
_Dict = ast.Dict

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

TOKEN_TO_UOP = {
    "ADD": UAdd,
    "SUB": USub,
    "NOT": Not
}

TYPE_CONVERSIONS = {
    "INT": int,
    "FLOAT": float,
    "BOOLEAN": lambda v: True if v == "True" else False,
    "STRING": str,
    "NONE": lambda v: None
}

def loc(self: GeneratedParser):
    tok = self.peek_token()
    return {"lineno": tok.lineno, "col_offset": tok.column}

GeneratedParser.loc = property(loc) # add loc property so we can get location


def PyECP_Compound(c: list, l):
    if len(c) == 0:
        return [Pass(**l)]
    return c

def PyECP_Constant(t: Token, l):
    return Constant(TYPE_CONVERSIONS[t.type](t.value), **l)

def PyECP_UnaryOp(op: Token, operand):
    op_class = TOKEN_TO_UOP[op.type]()
    return UnaryOp(op=op_class, operand=operand, lineno=operand.lineno, col_offset=operand.col_offset)

def PyECP_BinOp(left, right, op: Token, l):
    return BinOp(left=left, op=TOKEN_TO_OP[op.type](), right=right, **l)

def PyECP_BoolOp(base, op, others, l):
    return BoolOp(op=TOKEN_TO_OP[op](), values=[base] + [v for _, v in others], **l)

def PyECP_Comparison(base, others, l):
    ops = [TOKEN_TO_OP[op.value]() for op, _ in others]
    comparators = [v for _, v in others]
    return Compare(left=base, ops=ops, comparators=comparators, **l)

def PyECP_ExprStatement(value):
    if isinstance(value, expr):
        return Expr(value=value, lineno=value.lineno, col_offset=value.col_offset)
    return value

def PyECP_ProcessIndexing(rv, indexes, l):
    for t, v in indexes:
        if t == "attr":
            rv = Attribute(value=rv, attr=v, ctx=Load(), **l)
        elif t == "subscript":
            rv = Subscript(value=rv, slice=Index(value=v), ctx=Load(), **l)
        elif t == "call":
            args, kwargs = v
            rv = Call(func=rv, args=args, keywords=kwargs, **l)
    return rv

def PyECP_Variable(name: Token, indexes, l):
    return PyECP_ProcessIndexing(Name(id=name.value, ctx=Load(), **l), indexes, l)

def PyECP_Assign(target, value, l):
    # TODO: allow unpacking like a,b = 1,2 (need tuple without bracket support)
    target.ctx = Store()
    return Assign(targets=[target], value=value, **l)

def PyECP_Parameters(p):
    # p: (expr (COMMA expr)* COMMA?)?
    params = []
    if not isinstance(p, Filler):
        params.append(p[0])
        for _, param in p[1]:
            params.append(param)
    return params

def PyECP_KwParameters(p):
    # p: (ID ASSIGN expr (COMMA ID ASSIGN expr)* COMMA?)?
    kw_params = []
    if not isinstance(p, Filler):
        kw_params.append(keyword(arg=p[0].value, value=p[2]))
        for _, *param in p[3]:
            kw_params.append(keyword(arg=param[0].value, value=param[2]))
    return kw_params

def PyECP_Factor(factor, indexes, l):
    rv = factor
    return PyECP_ProcessIndexing(rv, indexes, l)

def PyECP_Magic(name: str, parameters, l):
    if name == "RETURN":
        if len(parameters) == 1:
            return Return(value=parameters[0])
        if len(parameters) > 1:
            return Return(value=Tuple(elts=parameters, ctx=Load()))
        return Return()
    elif name == "CONTINUE":
        return Continue()
    elif name == "BREAK":
        return Break()
    elif name == "OUTPUT":
        name = "print"
    elif name == "USERINPUT":
        name = "input"

    return Call(func=Name(id=name, ctx=Load()), args=parameters, keywords=[], **l)


def PyECP_Tuple(values, l):
    return ast.Tuple(elts=values, ctx=Load(), **l)

def PyECP_Array(values, l):
    return ast.List(elts=values, ctx=Load(), **l)

def PyECP_Dictionary(kv_pairs, l):
    # kv_pairs: (expr COLON expr (COMMA expr COLON expr)* COMMA?)?
    keys = []
    values = []
    if not isinstance(kv_pairs, Filler):
        keys, values = [kv_pairs[0]], [kv_pairs[2]]
        for _, k, _, v in kv_pairs[3]:
            keys.append(k)
            values.append(v)
    return ast.Dict(keys=keys, values=values, **l)

def PyECP_IfStatement(condition, block, other, l):
    if isinstance(other, Filler):
        other = []
    return If(test=condition, body=block, orelse=other, **l)

def PyECP_SubroutineDef(name: Token, params, block, l):
    # params: (param_definition (COMMA param_definition)* COMMA?)?
    # TODO: keyword arguments
    parameters = []
    if not isinstance(params, Filler):
        parameters.append(params[0])
        for _, param in params[1]:
            parameters.append(param)
    return FunctionDef(
        name=name.value, 
        args=arguments(args=parameters, posonlyargs=[], kwonlyargs=[], kw_defaults=[], defaults=[], kwarg=None, vararg=None), 
        body=block, 
        decorator_list=[], 
        returns=None, 
        type_comment=None, 
        **l
    )

def PyECP_While(condition, block, l):
    return While(test=condition, body=block, orelse=[], **l)
    # TODO: implement else after while and for loops

def PyECP_RepeatUntil(condition, block, l):
    check = If(
        test=condition,
        body=[Break()],
        orelse=[],
        **l
    )

    return While(test=Constant(value=True), body=block + [check], orelse=[], **l)

def PyECP_ForTo(variable, start, end, step, block, l):
    variable.ctx = Store()
    if isinstance(step, Filler):
        step = Constant(value=1, **l)
    else:
        step = step[1]
    return For(
        target=variable,
        iter=Call(
            func=Name(id='range', ctx=Load(), **l),
            args=[
              start,
              BinOp(left=end, op=Add(), right=Constant(value=1, **l), **l),
              step
            ],
            keywords=[], **l
        ),
        body=block,
        orelse=[],
        **l
    )

def PyECP_ForIn(variable, iterator, block, l):
    variable.ctx = Store()
    return For(
        target=variable,
        iter=iterator,
        body=block,
        orelse=[],
        **l
    )

def PyECP_Record(name: Token, values, l):
    # values: (variable (COLON ID)?)*
    parameters = [v.id for v, *_ in values]
    return ClassDef(
        name=name.value,
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
                **l
            )
        ],
        decorator_list=[],
        **l
    )

def PyECP_Try(try_block, catch_block, l):
    return Try(
        body=try_block,
        handlers=[
            ExceptHandler(
                type=None,
                name=None,
                body=catch_block
            )
        ],
        orelse=[],
        finalbody=[],
        **l
    )
    # TODO: add support for finally and else

def PyECP_Class(name: Name, body, l):
    return ClassDef(
        name=name.id,
        bases=[],
        keywords=[],
        body=body,
        decorator_list=[],
        **l
    )

def PyECP_Import(location, target, l):
    if isinstance(target, Filler):
        target = Constant(value=None)
    else:
        target = target[1]
    
    return Expr(
        value=Call(
            func=Name(id='_ECP_IMPORT', ctx=Load()),
            args=[location, target, Call(func=Name(id='globals', ctx=Load()), args=[], keywords=[])],
            keywords=[]
        )
    )