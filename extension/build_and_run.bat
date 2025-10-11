@echo off
echo ========================================
echo    KeyMovement Extension - Build & Run
echo ========================================
echo.

REM Verificar se Python está disponível
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Python não encontrado no PATH
    echo    Instale Python ou adicione ao PATH
    pause
    exit /b 1
)

REM Verificar se PyInstaller está instalado
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  PyInstaller não encontrado. Instalando...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ ERRO: Falha ao instalar PyInstaller
        pause
        exit /b 1
    )
)

echo 🔧 Limpando arquivos antigos...
if exist "dist\KeyMovement*.exe" del /q "dist\KeyMovement*.exe"
if exist "build" rmdir /s /q "build"

echo 📦 Compilando extensão...
pyinstaller --onefile --name "KeyMovement-Debug" key_movement.py

if errorlevel 1 (
    echo ❌ ERRO: Falha na compilação
    pause
    exit /b 1
)

echo ✅ Compilação concluída!
echo.
echo 📁 Arquivo gerado: dist\KeyMovement-Debug.exe
echo.
echo 🚀 Para testar:
echo    1. Abra o G-Earth
echo    2. Vá em Extensions
echo    3. Adicione: dist\KeyMovement-Debug.exe
echo    4. Entre em um quarto do Habbo
echo    5. Teste as setas do teclado
echo.

REM Opção para executar diretamente (modo debug)
echo 🔍 Deseja executar em modo debug local? (s/n)
set /p choice=
if /i "%choice%"=="s" (
    echo.
    echo 🐛 Executando em modo debug...
    echo    Pressione Ctrl+C para parar
    echo.
    python key_movement.py -p 9092
)

echo.
echo ✨ Processo concluído!
pause