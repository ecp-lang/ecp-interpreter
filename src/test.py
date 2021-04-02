from lexer import *
from parse import *
string = """
a ← 1 + 2.2
b ← a + 1
OUTPUT "a is", a, "b is", b

"""

#string = input()
print(string)
l = Lexer()
result = l.lexString(string)

def debugOutput(result):
    table = []
    for i in result:
        table.append([i.value, i.type])
    print(tabulate(table, tablefmt="github", headers=["VALUE", "TYPE"]))

debugOutput(result)

p = Parser(l)
i = Interpreter(p)

i.interpret()
print("global variables:", i.GLOBAL_SCOPE)


