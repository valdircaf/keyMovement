@echo off
echo ========================================
echo    GERADOR DEBUG - KeyMovement
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
if exist "dist\KeyMovementDebug.exe" del /q "dist\KeyMovementDebug.exe"
if exist "build" rmdir /s /q "build"

echo [INFO] Gerando executavel DEBUG (com console)...
echo.

python -m PyInstaller ^
    --onefile ^
    --console ^
    --name "KeyMovementDebug" ^
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
    --debug "all" ^
    --log-level "DEBUG" ^
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
if exist "KeyMovementDebug.spec" del /q "KeyMovementDebug.spec"

echo ========================================
echo    EXECUTAVEL DEBUG GERADO!
echo ========================================
echo.
echo O arquivo KeyMovementDebug.exe foi criado na pasta 'dist'
echo.
echo TESTE DEBUG:
echo 1. Execute: dist\KeyMovementDebug.exe
echo 2. O console mostrara todos os erros e logs
echo 3. Copie qualquer mensagem de erro que aparecer
echo 4. Teste tambem no G-Earth para ver erros especificos
echo.
pause