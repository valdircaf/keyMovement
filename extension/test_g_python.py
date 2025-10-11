import sys
import os
import time

# Detectar se está rodando como executável PyInstaller
RUNNING_AS_EXE = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

print(f" [TEST] Executando como executável: {RUNNING_AS_EXE}")
print(f" [TEST] sys.argv: {sys.argv}")
print(f" [TEST] Diretório atual: {os.getcwd()}")

if RUNNING_AS_EXE:
    print(f" [TEST] _MEIPASS: {sys._MEIPASS}")

# Testar imports da biblioteca g_python
try:
    print(" [TEST] Testando import g_python.gextension...")
    from g_python.gextension import Extension
    print(" [SUCCESS] g_python.gextension importado com sucesso!")
except Exception as e:
    print(f" [ERROR] Falha ao importar g_python.gextension: {e}")

try:
    print(" [TEST] Testando import g_python.hmessage...")
    from g_python.hmessage import Direction, HMessage
    print(" [SUCCESS] g_python.hmessage importado com sucesso!")
except Exception as e:
    print(f" [ERROR] Falha ao importar g_python.hmessage: {e}")

try:
    print(" [TEST] Testando import g_python.hpacket...")
    from g_python.hpacket import HPacket
    print(" [SUCCESS] g_python.hpacket importado com sucesso!")
except Exception as e:
    print(f" [ERROR] Falha ao importar g_python.hpacket: {e}")

# Testar criação da extensão
try:
    print(" [TEST] Testando criação da extensão...")
    extension_info = {
        "title": "Test Extension",
        "description": "Teste de dependências",
        "version": "1.0.0",
        "author": "Test"
    }
    
    # Simular argumentos do G-Earth
    test_args = ["-p", "9092"] if len(sys.argv) < 2 else sys.argv
    
    ext = Extension(extension_info, test_args)
    print(" [SUCCESS] Extensão criada com sucesso!")
    
    # NÃO chamar ext.start() para evitar tentar conectar com G-Earth
    print(" [INFO] Teste concluído - extensão não foi iniciada (apenas testada)")
    
except Exception as e:
    print(f" [ERROR] Falha ao criar extensão: {e}")
    import traceback
    traceback.print_exc()

print(" [TEST] Teste de dependências concluído!")
print(" [INFO] Pressione Ctrl+C para sair...")

# Manter rodando para teste
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print(" [SHUTDOWN] Teste finalizado")