from ecp.parser import CustomParser as EcpParser, EcpLexer
from parsergen.parser_utils import *
from ecp import _dump
from ast import *

def p(s):
    return EcpParser(TokenStream(EcpLexer().lex_string(s).tokens)).statement()

while True:
    v = p(input("> "))
    if not isinstance(v, AST):
        print(v)
    print(_dump(v, indent=2))
    exec(compile(
        fix_missing_locations(Interactive(body=[v])),
        "<>", "single"))