@echo off
echo ========================================
echo    GERADOR DE EXECUTAVEL - KeyMovement
echo ========================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado! Instale o Python primeiro.
    pause
    exit /b 1
)

echo [INFO] Python encontrado!

REM Verificar se PyInstaller está instalado
python -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] PyInstaller nao encontrado. Instalando...
    python -m pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao instalar PyInstaller!
        pause
        exit /b 1
    )
    echo [INFO] PyInstaller instalado com sucesso!
) else (
    echo [INFO] PyInstaller ja esta instalado!
)

echo.
echo [INFO] Limpando builds anteriores...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"

echo [INFO] Gerando executavel...
echo.

REM Gerar executável com configurações otimizadas para evitar conflitos
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
    --hidden-import "g_python.htools" ^
    --hidden-import "g_python.hunityparsers" ^
    --hidden-import "g_python.hunitytools" ^
    --hidden-import "pynput" ^
    --hidden-import "pynput.keyboard" ^
    --hidden-import "pynput.mouse" ^
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
    echo Verifique os erros acima e tente novamente.
    pause
    exit /b 1
)

echo.
echo [INFO] Limpando arquivos temporarios...
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"

echo.
echo ========================================
echo        EXECUTAVEL GERADO COM SUCESSO!
echo ========================================
echo.
echo O arquivo KeyMovement.exe foi criado na pasta 'dist'
echo.
echo INSTALACAO NO G-EARTH:
echo 1. Abra o G-Earth
echo 2. Va em Extensions ^> Install extension
echo 3. Selecione o arquivo: dist\KeyMovement.exe
echo 4. A extensao sera carregada automaticamente
echo.
echo COMO USAR:
echo 1. Entre em um quarto no Habbo
echo 2. A extensao detectara automaticamente as dimensoes
echo 3. Use as SETAS do teclado para mover o avatar
echo 4. A extensao nao interfere com outras teclas
echo 5. Outras aplicacoes funcionam normalmente
echo.
echo Pressione qualquer tecla para sair...
pause >nul