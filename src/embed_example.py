from ecp import ecp

ecp("""
SUBROUTINE TotalOut(a, b)
    c ← a + b
    WHILE a < c
        a ← a + 1
        b ← b - a
    ENDWHILE
    RETURN b
ENDSUBROUTINE
""", scope=globals())

print(TotalOut(3, 4))

