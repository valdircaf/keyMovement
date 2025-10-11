@echo off
echo ========================================
echo    GERADOR ONEDIR - KeyMovement
echo ========================================
echo.

echo [INFO] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    pause
    exit /b 1
)

echo [INFO] Limpando builds anteriores...
if exist "dist\KeyMovementDir" rmdir /s /q "dist\KeyMovementDir"
if exist "build" rmdir /s /q "build"

echo [INFO] Gerando executavel ONEDIR (pasta)...
echo.

python -m PyInstaller ^
    --onedir ^
    --noconsole ^
    --name "KeyMovementDir" ^
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
    --exclude-module "tkinter" ^
    --exclude-module "matplotlib" ^
    --exclude-module "numpy" ^
    --exclude-module "scipy" ^
    --exclude-module "PIL" ^
    --exclude-module "cv2" ^
    --clean ^
    key_movement.py

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha na compilacao!
    pause
    exit /b 1
)

echo.
echo [INFO] Limpando arquivos temporarios...
if exist "build" rmdir /s /q "build"
if exist "KeyMovementDir.spec" del /q "KeyMovementDir.spec"

echo ========================================
echo    EXECUTAVEL ONEDIR GERADO!
echo ========================================
echo.
echo A pasta KeyMovementDir foi criada em 'dist'
echo O executavel esta em: dist\KeyMovementDir\KeyMovementDir.exe
echo.
echo TESTE ONEDIR:
echo 1. Va para: dist\KeyMovementDir\
echo 2. Execute: KeyMovementDir.exe
echo 3. Teste no G-Earth usando este executavel
echo.
echo VANTAGEM: Todas as bibliotecas ficam visiveis na pasta
echo Isso pode resolver problemas de empacotamento do onefile
echo.
pause