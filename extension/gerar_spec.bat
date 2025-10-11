@echo off
echo ========================================
echo    GERADOR SPEC - KeyMovement
echo ========================================
echo.

echo [INFO] Gerando arquivo .spec para analise...

python -m PyInstaller ^
    --onefile ^
    --noconsole ^
    --name "KeyMovement" ^
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
    --specpath "." ^
    --noconfirm ^
    key_movement.py

echo.
echo [INFO] Arquivo KeyMovement.spec gerado!
echo Voce pode editar este arquivo e usar:
echo python -m PyInstaller KeyMovement.spec
echo.
pause