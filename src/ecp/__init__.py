"""ECP programming language

An implementation of the ECP programming language. Includes a Lexer and Parser for generating a python AST from
ECP code.
"""
__version__ = "1.5.0"
from .lexer import EcpLexer
from .topython import EcpParser, ecp, parse_ecp, to_py_source, _dump, get_more