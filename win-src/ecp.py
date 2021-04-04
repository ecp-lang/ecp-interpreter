from lexer import *
from parse import *
import argparse
import os

parser = argparse.ArgumentParser(description="ECP interpreter")
parser.add_argument("inputfile", type=argparse.FileType("r", encoding="utf-8"))
parser.add_argument("--debug", action="store_true")

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
os.system("pause")