@echo off
echo ========================================
echo    GERADOR DE TESTE - Dependencias
echo ========================================
echo.

echo [INFO] Limpando builds anteriores...
if exist "dist\TestGPython.exe" del /q "dist\TestGPython.exe"

echo [INFO] Gerando executavel de teste...
echo.

python -m PyInstaller ^
    --onefile ^
    --console ^
    --name "TestGPython" ^
    --add-data "../g_python;g_python" ^
    --hidden-import "g_python" ^
    --hidden-import "g_python.gextension" ^
    --hidden-import "g_python.hmessage" ^
    --hidden-import "g_python.hpacket" ^
    --hidden-import "g_python.hparsers" ^
    --hidden-import "g_python.hdirection" ^
    --hidden-import "socket" ^
    --hidden-import "threading" ^
    --hidden-import "time" ^
    --hidden-import "sys" ^
    --hidden-import "os" ^
    --hidden-import "copy" ^
    --hidden-import "enum" ^
    --hidden-import "typing" ^
    --clean ^
    test_g_python.py

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha na compilacao!
    pause
    exit /b 1
)

echo.
echo [INFO] Limpando arquivos temporarios...
if exist "build" rmdir /s /q "build"
if exist "TestGPython.spec" del /q "TestGPython.spec"

echo ========================================
echo      EXECUTAVEL DE TESTE GERADO!
echo ========================================
echo.
echo O arquivo TestGPython.exe foi criado na pasta 'dist'
echo.
echo TESTE:
echo 1. Execute: dist\TestGPython.exe
echo 2. Verifique se todas as dependencias sao carregadas
echo 3. Se houver erros, eles serao mostrados no console
echo.
pause