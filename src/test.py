from lexer import *
from parse import *
string = """
a: Real ← 1 + 2.2
b ← a + 1
OUTPUT "a is", a, "b is", b


"""

string = """
SUBROUTINE func(a, b)
    result ← a * b + b
    RETURN result
ENDSUBROUTINE

SUBROUTINE t()
    OUTPUT "e"
ENDSUBROUTINE

OUTPUT func(1,func(2,3))
a ← 1 > 0 < -1
OUTPUT a
t()

a := "a"

IF a = "a" THEN 
    OUTPUT "AAAA"
ELSE IF a = "b" THEN
    OUTPUT "BBBB"
ELSE IF a = "c" THEN
    OUTPUT "CCCC"
ELSE
    IF a = "d" THEN
        OUTPUT "a is d"
    ELSE
        OUTPUT "e"
    ENDIF
ENDIF

OUTPUT NOT (True AND False)
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


