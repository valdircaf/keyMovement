@echo off
echo ========================================
echo        GERANDO EXECUTAVEL MINIMAL
echo ========================================

echo [INFO] Limpando builds anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del "*.spec"

echo [INFO] Gerando executavel minimal...
pyinstaller --onefile --windowed --name KeyMovementMinimal key_movement_minimal.py

echo [INFO] Limpando arquivos temporarios...
if exist "build" rmdir /s /q "build"
if exist "*.spec" del "*.spec"

echo ========================================
echo       EXECUTAVEL MINIMAL GERADO!
echo ========================================
echo.
echo O arquivo KeyMovementMinimal.exe foi criado na pasta 'dist'
echo.
echo TESTE:
echo 1. Instale no G-Earth: dist\KeyMovementMinimal.exe
echo 2. Entre em um quarto
echo 3. Saia e reentrar no quarto
echo 4. Verifique se NÃO há tela preta
echo.
pause