@echo off
echo ========================================
echo    GERADOR DE EXECUTAVEL - KeyMovement
echo ========================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python nao encontrado no PATH
    echo Por favor, instale o Python e adicione ao PATH
    pause
    exit /b 1
)

echo [INFO] Python encontrado!

REM Verificar se PyInstaller está instalado
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [INFO] PyInstaller nao encontrado. Instalando...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Falha ao instalar PyInstaller
        pause
        exit /b 1
    )
)

echo [INFO] PyInstaller disponivel!

REM Limpar builds anteriores
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del "*.spec"

echo [INFO] Gerando executavel...

REM Gerar executável com PyInstaller
python -m PyInstaller ^
    --onefile ^
    --noconsole ^
    --name "KeyMovement" ^
    --distpath "." ^
    --workpath "build" ^
    --specpath "build" ^
    key_movement.py

if errorlevel 1 (
    echo [ERROR] Falha na compilacao
    pause
    exit /b 1
)

REM Limpar arquivos temporários
if exist "build" rmdir /s /q "build"

echo.
echo [SUCCESS] Compilacao concluida!
echo.
echo Arquivo gerado: KeyMovement.exe
echo.
echo INSTRUCOES DE INSTALACAO:
echo 1. Copie o arquivo KeyMovement.exe para a pasta de extensoes do G-Earth
echo 2. Abra o G-Earth
echo 3. Va em Extensoes e clique em "Instalar extensao"
echo 4. Selecione o arquivo KeyMovement.exe
echo 5. A extensao sera carregada automaticamente
echo.
echo COMO USAR:
echo - Use as setas do teclado ou WASD para mover o avatar
echo - Clique no quarto para definir posicao inicial
echo - A extensao detecta automaticamente as dimensoes do quarto
echo.
pause