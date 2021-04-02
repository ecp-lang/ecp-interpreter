from lexer import *
from parse import *
string = """
a: Real ← 1 + 2.2
b ← a + 1
OUTPUT "a is", a, "b is", b


"""

string = """
SUBROUTINE add(a, b)
    result ← a + b
    RETURN result
ENDSUBROUTINE

OUTPUT "1 + 2 =", add(1,2)
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
print("global variables:", i.current_scope)


