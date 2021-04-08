__version__ = "1.0.0-alpha"
from lexer import *
from parse import *
import argparse
from traceback import print_exc

parser = argparse.ArgumentParser(description="ECP interpreter")
parser.add_argument("inputfile", type=argparse.FileType("r", encoding="utf-8"), nargs="?")
parser.add_argument("--debug", action="store_true")
parser.add_argument("--pause", action="store_true")
parser.add_argument('--version', action='version', version='%(prog)s v'+__version__)

options = parser.parse_args()
#print(options)
if options.inputfile:
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

else:
    # Live console
    print(f"ECP {__version__}")
    string = ""
    multiple_line = False
    prompt = ">>> "
    l = Lexer()
    result = l.lexString("")
    p = Parser(l)
    i = Interpreter(p)
    i.interpret()
    while True:
        if not multiple_line:
            string = input(">>> ")
            multiple_line = string.endswith("\\")
            if multiple_line:
                string = string[:-1]
                string += "\n"
        
        while multiple_line:
            string += input("... ")
            multiple_line = string.endswith("\\")
            if multiple_line:
                string = string[:-1]
                string += "\n"
        
        try:
            l = Lexer()
            p = Parser(l)
            i.parser = p
            result = l.lexString(string)
            tree = i.parser.parse()
            i.visit(tree)
        except:
            print_exc(0)