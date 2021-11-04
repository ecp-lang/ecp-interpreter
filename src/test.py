from ecp import ecp
import math

class t:
    def __init__(self) -> None:
        self.b = 1

a = t()
a.b = t()

def f(n):
    print(n)

ecp("""
a.b.b := 2
f("function call")
OUTPUT "hi"

SUBROUTINE test(n)
    OUTPUT n + 1
ENDSUBROUTINE

test(2)

IF 1 < 2 < 3 AND True THEN
    OUTPUT "1 < 2 < 3 AND True = True" # lineno property missing? modify code to add actual line numbers
ENDIF

FOR i := 1 TO 3
    OUTPUT "--", str(i)
ENDFOR

OUTPUT math.sqrt(5)
x := 2

""", showAST=True, scope=globals())