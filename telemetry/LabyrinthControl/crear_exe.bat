@echo off
cd /d "%~dp0"
python -m pip install --upgrade pyinstaller
if errorlevel 1 goto error

python -m PyInstaller --noconfirm --clean --onefile --windowed --name LabyrinthControl app.py
if errorlevel 1 goto error

echo.
echo Ejecutable creado en: dist\LabyrinthControl.exe
pause
exit /b 0

:error
echo.
echo No se pudo crear el ejecutable.
pause
exit /b 1
