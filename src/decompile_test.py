from ecp import ecp, parse_ecp, to_py_source

text = """
SUBROUTINE TotalOut(a, b)
    c ← a + b
    WHILE a < c
        a ← a + 1
        b ← b - a
    ENDWHILE
    RETURN b
ENDSUBROUTINE
"""
print("---- ECP ----\n"+text)
print("---- PYTHON ----\n"+to_py_source(text))