# pseudocode-interpreter
CC BY-SA 2021 Alfred Taylor & Conqu3red 

# **Extended Computer-Friendly Pseudocode V1.0  (CP/ECP/ECFP/EECP)**

## `PLEASE EXPECT LIMITED FUNCTIONALITY.`

## Introduction:

This is an adaptation of the pseudocode used by the AQA GCSE testing body (found [here](https://filestore.aqa.org.uk/resources/computing/AQA-8525-TG-PC.PDF)) that has had its syntax tweaked for use in a compiler and had some additional functionality added. The language will be fully Turing complete. Pseudocode found in tests is compatible with ECP. It is procedurally based, and shares similarities with python (It is programmed on python, after all.) It is intended as a scripting language, that is separate from python, but has the same basic functionality, whilst maintaining some resemblance of simplicity. Considering it is entirely written in python, it is not for use in situations where speed is a priority.

**Other Language Support:**

We're designing the language to be more like a set of rules than a specific piece of software, although the software bundled in this repo is supported by us. It can be interpreted, compiled, based off C, based off python, based off java , and more, if you can write the software to execute it.

**How it works**

ECP code is analysed and then parsed into a python AST (Abstract Syntax Tree). This can then be executed by the python interpreter. This allows near seamless integration with python and almost identical speed and behaviour.

# Usage
## Command Line arguments
```
usage: python -m ecp [-h] [--debug] [--trace [TRACE [TRACE ...]]] [--tracecompact] [--pause] [--version] [inputfile]

ECP interpreter

positional arguments:
  inputfile

optional arguments:
  -h, --help            show this help message and exit
  --debug               show debug information like token list
  --trace [TRACE [TRACE ...]]
                        space seperated names of the variables to be traced
  --tracecompact        trace compactly
  --pause               pause on completion
  --version             show program's version number and exit
```

# Installation
```
pip install py-ecp
```
## Running
```
python -m ecp path/to/ecp/file.ecp
```

## Embedding ecp code in python files
```python
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
```

## Converting ECp to python source code
```
python -m ecp path/to/ecp/file.ecp --topython
```
or:
```python
from ecp import to_py_source
text = """
SUBROUTINE DoSomething(a, b)
    RETURN a + b
ENDSUBROUTINE
"""

print(to_py_source(text))
```
# MORE COMING SOON!


