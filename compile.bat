@echo off
del /Q dist\*
python setup.py sdist
py -m pip install --upgrade build
py -m build