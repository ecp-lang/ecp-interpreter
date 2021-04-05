@echo off
copy /Y ..\src\ecp.py .
copy /Y ..\src\lexer.py .
copy /Y ..\src\parse.py .
pyinstaller ^
 --onefile ^
 --icon=icon.ico ^
 --exclude tkinter ^
 --exclude multiprocessing ^
 --exclude unittest ^
 --exclude urllib ^
 ecp.py
pyinstaller --onefile --windowed --icon=icon.ico ECPUser.py
copy /Y dist\* ..\executables
pause