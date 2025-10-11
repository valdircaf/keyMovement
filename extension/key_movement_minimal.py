import sys
import os
import time
import threading
from g_python.gextension import Extension
from g_python.hmessage import Direction
from g_python.hpacket import HPacket

# Detectar se está rodando como executável PyInstaller
RUNNING_AS_EXE = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

# Import classes individually to avoid circular import issues
try:
    from g_python.hdirection import Direction
except ImportError:
    try:
        from g_python.hmessage import Direction
    except ImportError:
        class Direction:
            TO_CLIENT = 0
            TO_SERVER = 1

# Configurar informações da extensão
extension_info = {
    "title": "KeyMovement Minimal Test",
    "description": "Versão mínima para teste de compatibilidade",
    "version": "1.0.0",
    "author": "Test"
}

# Inicializar extensão
ext = Extension(extension_info, sys.argv)

print(" [INIT] Extensão mínima iniciada")
if RUNNING_AS_EXE:
    print(" [INIT] Detectado: Executando como executável PyInstaller")
else:
    print(" [INIT] Detectado: Executando como script Python local")

print(" [STATUS] Extensão mínima carregada - SEM interceptadores")
print(" [INFO] Esta versão não intercepta nenhum packet")
print(" [INFO] Teste: Entre e saia de quartos para verificar se há problemas")

# Manter a extensão rodando
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print(" [SHUTDOWN] Extensão finalizada")