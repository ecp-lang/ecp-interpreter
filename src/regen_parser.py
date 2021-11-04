from parsergen.parsergen import Generator

HEADER = """from .parser_helpers import *

"""

with open("ecp/grammar.gram") as f:
    grammar = f.read()

result = Generator().generate(grammar)

with open("ecp/parser.py", "w") as f:
    f.write(HEADER + result)