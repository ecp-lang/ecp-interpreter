# pseudocode-interpreter
CC BY-SA 2021 Alfred Taylor & Conqu3red 

# **Extended Compiler-Friendly Pseudocode V1.0  (CP/ECP/ECFP/EECP)**

## `THIS CODE IS IN A VERY INCOMPLETE STATE, PLEASE EXPECT LIMITED FUNCTIONALITY.`

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
usage: ecp.py [-h] [--debug] [--trace [TRACE [TRACE ...]]] [--tracecompact] [--pause] [--version] [inputfile]

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
## Using the installer
Go the the [latest release](https://github.com/Conqu3red/pseudocode-interpreter/releases/latest) and download `ECPSetup.exe`, this is the installer which will install the ECP interpreter. The installer will setup the association with the ecp file type so that you can just double click on ecp files to run them.
## Downloading the latest build
Iy you don't want to use the installer you can download the zip file called `ecp.zip` from the latest release, this contains the interpreter executable. It is reccomended that you add the folder with this exe to your PATH so that you can execute ecp files using ecp from any location.
## Running the source python code
if you don't want to use the exe then you can also just use the source python code. You will require python 3.7+ for it to work. Download this repository and to run ecp files change directory to src and run `python ecp.py <file_path>` or omit the file path to see other parameters.
## Building from source
to build the exe and installer first clone this repo. Then navigate to `win-src` and execute `compile.bat`. The installer file will be placed in `installer/Output` and the exe and its requirements will be located in `executables/ecp`
# MORE COMING SOON!


