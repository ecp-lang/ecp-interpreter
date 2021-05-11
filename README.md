# pseudocode-interpreter
CC BY-SA 2021 Alfred Taylor & Conqu3red 

# **Extended Compiler-Friendly Pseudocode V1.0  (CP/ECP/ECFP/EECP)**

## Introduction:

This is an adaptation of the pseudocode used by the AQA GCSE testing body (found [here](https://filestore.aqa.org.uk/resources/computing/AQA-8525-TG-PC.PDF)) that has had its syntax tweaked for use in a compiler and had some additional functionality added. The language will be fully Turing complete. Pseudocode found in tests is compatible with ECP. It is procedurally based, and shares similarities with python.

#### Unique Features/Future Features:

Apart from its basis in real pseudocode, there are multiple non-standard features, such as:

**Headers:**

Headers are pieces of code that can directly address the interpreter, negating the need for a CLI. They can be used to import libraries, set the folder of execution, and more. They take advantage of interpreter code.

**Magic Snippets:**

Magic snippets are built-in functions, classes and libraries that can run interpreter code, libraries written in the interpreter language, and other functions that can be added onto with libraries.

**Other Language Support:**

We're designing the language to be more like a set of rules than a specific piece of software, although the software bundled in this repo is supported by us. It can be interpreted, compiled, based off C, based, off python, and more, if you can write the software to run it. That's why "interpreter code" is used, for future proofing and cross compatibility.

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
A live version of the interpreter can be found at http://conqu3red.pythonanywhere.com/

# Installation

```
pip install py-ecp
```
## Running
```
python -m ecp path/to/ecp/file.ecp
```
# MORE COMING SOON!


