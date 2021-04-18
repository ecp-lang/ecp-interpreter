@echo off
copy /Y ..\src\ecp.py .
copy /Y ..\src\tracker.py .
copy /Y ..\src\lexer.py .
copy /Y ..\src\parse.py .
del /Q dist\ecp\*
rmdir dist\ecp
pyinstaller ^
 --icon=icon.ico ^
 --exclude tkinter ^
 --exclude multiprocessing ^
 --exclude unittest ^
 --exclude urllib ^
 --noconfirm ^
 ecp.py
xcopy /E /I /Y dist ..\executables
iscc ..\installers\compileiss.iss
pause