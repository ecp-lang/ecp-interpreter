__version__ = "1.0.0-alpha"
from lexer import *
from parse import *
import argparse

parser = argparse.ArgumentParser(description="ECP interpreter")
parser.add_argument("inputfile", type=argparse.FileType("r", encoding="utf-8"))
parser.add_argument("--debug", action="store_true")
parser.add_argument("--pause", action="store_true")
parser.add_argument('--version', action='version', version='%(prog)s v'+__version__)

options = parser.parse_args()
#print(options)

string = options.inputfile.read()
options.inputfile.close()

l = Lexer()
result = l.lexString(string)

def debugOutput(result):
    table = []
    for i in result:
        table.append([i.value, i.type])
    print(tabulate(table, tablefmt="github", headers=["VALUE", "TYPE"]))

if options.debug:
    debugOutput(result)

p = Parser(l)
i = Interpreter(p)

i.interpret()
#print("global variables:", i.current_scope)
if options.pause:
    input("Press enter to exit...")