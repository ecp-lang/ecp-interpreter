import os
from lexer import *
from parse import *

completed = 0
total = 0
failed = 0
print(os.getcwd())
for (dirpath, dirnames, filenames) in os.walk("../examples"):
    total = len(filenames)
    for f in filenames:
        print(f"[#] Testing {f}...")
        path = os.path.join(dirpath, f)
        with open(path, encoding="utf-8") as file:
            data = file.read()
        try:
            l = Lexer()
            result = l.lexString(data)
            p = Parser(l)
            i = Interpreter(p)
            i.interpret()
        except:
            failed += 1
            print(f"[!] An error occured in {f}")
        finally:
            completed += 1
    break

print(f"Complete.")
print(f"Success: {total-failed}/{total}")
print(f"Failed: {failed}/{total}")
if failed > 0:
    raise Exception("Some examples failed.")