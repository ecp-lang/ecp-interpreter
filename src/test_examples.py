import os
from ecp.lexer import *
from ecp.topython import *
import sys
completed = 0
total = 0
failed = 0
_failed = []
print(os.getcwd())
for (dirpath, dirnames, filenames) in os.walk("../examples"):
    total = len(filenames)
    for f in filenames:
        if not f.endswith(".ecp"): continue
        print(f"[#] Testing {f}...")
        path = os.path.join(dirpath, f)
        with open(path, encoding="utf-8") as file:
            data = file.read()
        try:
            loc = os.path.dirname(os.path.abspath(path))
            sys.path.insert(0, loc)
            ecp(data, name=f, scope=globals())
        except Exception as e:
            failed += 1
            _failed.append(f)
            print(f"[!] An error occured in {f}")
        finally:
            completed += 1
            del sys.path[0]
    break

print(f"Complete.")
print(f"Success: {total-failed}/{total}")
print(f"Failed: {failed}/{total}")
if failed > 0:
    print("tests which failed:")
    for t in _failed:
        print("\t", t)
    raise Exception("Some examples failed.")