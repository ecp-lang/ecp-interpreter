from lexer import *
from parse import *
string = """
a ← 1 + 2.2
OUTPUT " this is a string "

"""

string = input()
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
p.parse()

print(p.nodes)