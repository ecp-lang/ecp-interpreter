"""Converts a list of ECP tokens into a python AST and provides the environment for execution."""
from parsergen import *
from parsergen.parser import ParseError
from .lexer import *
from .tracker import Tracer
import sys, os
try:
    import astor
except ImportError:
    print("astor module not found - will not be able to convert ECP to python source code")
    astor = None
from math import sqrt
from random import randint
from ast import *
import ast
from ecp.parser import EcpParser
from parsergen.parser_utils import *
_List = ast.List
_Dict = ast.Dict

BUILTIN_IMPORT = "from ecp.topython import *\n"

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

def parse_ecp(text: str, mode="exec"):
    p = EcpParser(TokenStream(EcpLexer().lex_string(text)))
    rv = p.program()
    error = p.error()
    if rv is None and error is not None:
        raise error
    rv = fix_line_and_column(rv)
    if mode == "single":
        rv = Interactive(body=rv.body)
    return rv

def get_more(text: str) -> bool:
    code = None
    
    try:
        code = compile(parse_ecp(text, mode="single"), "<interactive>", "single")
    except ParseError as e:
        pass
    
    if code or text.endswith("\n"):
        return False
    else:
        return True
    

def to_py_source(text: Union[str, Module]):
    code = text
    if isinstance(text, str):
        code = parse_ecp(text)
    if astor is not None:
        return BUILTIN_IMPORT + astor.to_source(code)
    raise Exception("astor module not found - cannot convert ecp to python source code")

def ecp(text: str=None, *, file: str=None, name="<unkown>", showAST=False, scope=None, trace=None, tracecompact=False, mode="exec"):
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
    r = parse_ecp(text, mode=mode)
    if showAST:
        print(_dump(r, indent=2))
    if len(trace) > 0:
        with Tracer(trace, compact=tracecompact):
            exec(compile(parse(r, mode=mode), name, mode), scope)
    else:
        exec(compile(parse(r, mode=mode), name, mode), scope)

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