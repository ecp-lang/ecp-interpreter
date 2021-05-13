import time, os
file = "temp.ecp"
NUMBER_OF_RUNS = 5

def cs_benchmark():
    start = time.time()
    os.system(f"bin\\Debug\\netcoreapp3.1\\ecp-csharp.exe ..\\..\\examples\\{file}")
    end = time.time()
    return end - start

def py_benchmark():
    os.chdir("..")
    start = time.time()
    os.system(f"python ecp.py ..\\examples\\{file}")
    end = time.time()
    os.chdir("csharp")
    return end - start

def pypy_benchmark():
    os.chdir("..")
    start = time.time()
    os.system(f"pypy3 ecp.py ..\\examples\\{file}")
    end = time.time()
    os.chdir("csharp")
    return end - start

cs_runs = []
py_runs = []
pypy_runs = []

for i in range(NUMBER_OF_RUNS):
    cs_time = cs_benchmark()
    py_time = py_benchmark()
    pypy_time = pypy_benchmark()
    print(f"C# ecp: {cs_time}s")
    print(f"Python ecp: {py_time}s")
    print(f"PyPy ecp: {pypy_time}s")
    cs_runs.append(cs_time)
    py_runs.append(py_time)
    pypy_runs.append(pypy_time)

print("AVERAGE:")
print(f"C# ecp: {sum(cs_runs)/NUMBER_OF_RUNS}s")
print(f"Python ecp: {sum(py_runs)/NUMBER_OF_RUNS}s")
print(f"PyPy ecp: {sum(pypy_runs)/NUMBER_OF_RUNS}s")