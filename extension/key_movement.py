import sys
import os
import time
import threading
from g_python.gextension import Extension
from g_python.hmessage import Direction, HMessage
from g_python.hpacket import HPacket

# Detectar se está rodando como executável PyInstaller
RUNNING_AS_EXE = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

# Import classes individually to avoid circular import issues
try:
    from g_python.hparsers import HHeightMap, HUserUpdate, HEntity, HEntityType
except ImportError:
    # Fallback: define minimal classes if import fails
    class HHeightMap:
        def __init__(self, packet):
            try:
                self.width, tileCount = packet.read('ii')
                self.height = int(tileCount / self.width)
                self.tiles = [packet.read_short() for _ in range(tileCount)]
            except:
                self.width = 60
                self.height = 60
                self.tiles = []
        
        def index_to_coords(self, index):
            y = int(index % self.width)
            x = int((index - y) / self.width)
            return x, y
        
        def is_room_tile(self, x, y):
            return 0 <= x < self.width and 0 <= y < self.height
    
    class HUserUpdate:
        def __init__(self, packet):
            pass
    class HEntityType:
        HABBO = 1
    class HEntity:
        def __init__(self, packet):
            self.name = ""
            self.entity_type = HEntityType.HABBO
            self.tile = type("Tile", (), {"x": 0, "y": 0})()
        @classmethod
        def parse(cls, packet):
            return [HEntity(packet)]

# Configuração de ambiente e disponibilidade de pynput
if RUNNING_AS_EXE:
    print(" [INIT] Detectado: Executando como executável PyInstaller")
    print(" [INIT] Aplicando configurações específicas para .exe")
else:
    print(" [INIT] Detectado: Executando como script Python local")

# Tentar importar pynput tanto no executável quanto no script local
try:
    from pynput import keyboard, mouse
    PYNPUT_AVAILABLE = True
    print(" [INIT] pynput importado com sucesso")
except ImportError:
    PYNPUT_AVAILABLE = False
    print(" [ERROR] pynput não encontrado - instale com: pip install pynput")

extension_info = {
    "title": "KeyMovement",
    "description": "Movimento livre com setas",
    "version": "1.0.0",
    "author": "Valdir"
}

# Inicialização específica para executável vs script local
if RUNNING_AS_EXE:
    print(" [INIT] Inicializando extensão como executável...")
    print(f" [DEBUG] sys.argv recebido: {sys.argv}")
    # Para executáveis, sempre usar sys.argv (G-Earth passa os argumentos corretos)
    ext = Extension(extension_info, sys.argv)
else:
    print(" [INIT] Inicializando extensão como script local...")
    ext = Extension(extension_info, sys.argv)

try:
    ext.start()
    print(" [SUCCESS] Extensão iniciada com sucesso!")
except Exception as e:
    print(f" [FATAL] Falha ao iniciar extensão: {e}")
    sys.exit(1)

current_x = None
current_y = None
avatar_position_updated = False
key_pressed = None
last_move_time = 0

# Controle de estado da extensão (play/stop)
extension_active = True  # Extensão inicia ativa por padrão

# Configuração de múltiplos cliques
MULTIPLE_CLICKS_COUNT = 1  # Desativar múltiplos envios para evitar anti-flood
CLICK_DELAY = 0.03  # Delay entre cliques em segundos (30ms)
MOVE_THROTTLE_MS = 0  # Sem atraso: enviar movimentos imediatamente

# Modificador para evitar capturar todas as teclas: exigir Alt pressionado
MOVEMENT_REQUIRE_ALT = False
alt_pressed = False

room_width = 0  # Será detectado automaticamente
room_height = 0  # Será detectado automaticamente
room_detected = False
my_id = None  # Id do usuário atual (para mensagens no jogo)

def initial_position(message):
    """Captura a posição inicial do avatar quando entra no quarto (via Users)."""
    global current_x, current_y, avatar_position_updated, my_id

    try:
        entities = HEntity.parse(message.packet)
        # Log reduzido: não imprimir quantidade de entidades

        # Seleciona o primeiro HABBO como posição inicial (fallback razoável)
        selected = None
        for ent in entities:
            if getattr(ent, "entity_type", None) == HEntityType.HABBO:
                selected = ent
                break

        if selected is not None and hasattr(selected, "tile"):
            current_x = selected.tile.x
            current_y = selected.tile.y
            avatar_position_updated = True
            if hasattr(selected, "id"):
                my_id = selected.id
            # print(f" [SUCCESS] Posição inicial capturada: ({current_x}, {current_y})")
        else:
            # print(" [INFO] Nenhum HABBO encontrado no Users; aguardando UserUpdate")
            avatar_position_updated = False

    except Exception as e:
        # print(f"✗ [ERROR] Erro ao processar Users: {e}")
        avatar_position_updated = False

def capture_move_position(message):
    """Captura TODOS os movimentos enviados ao servidor e atualiza posição atual (não bloqueia)."""
    global current_x, current_y, avatar_position_updated, room_width, room_height

    try:
        packet = message.packet
        packet.reset()
        (x, y) = packet.read('ii')

        current_x = x
        current_y = y
        avatar_position_updated = True
        # Logs mínimos para não afetar desempenho
        # if room_width > 0 and room_height > 0:
        #     if 0 <= x < room_width and 0 <= y < room_height:
        #         print(f" [POS] Atualizado: ({x}, {y})")
        #     else:
        #         print(f" [POS] Atualizado: ({x}, {y}) fora dos limites {room_width}x{room_height}")
        # else:
        #     print(f" [POS] Atualizado: ({x}, {y}) (dimensões ainda não detectadas)")

    except Exception as e:
        # print(f"✗ [ERROR] Erro ao capturar MoveAvatar: {e}")
        pass

def intercept_all_packets(message):
    """Intercepta TODOS os packets para debug"""
    try:
        packet = message.packet
        header_id = packet.header_id()
        packet_length = len(packet.bytearray)
        
        # Log packets com tamanho significativo que podem ser HeightMap
        if packet_length > 20:  # HeightMap geralmente tem dados substanciais
            print(f" [ALL_PACKETS] Header ID: {header_id}, Length: {packet_length}")
            
            # Analisar TODOS os packets grandes para encontrar o correto
            packet.reset()
            try:
                # Tentar ler como diferentes estruturas
                first_int = packet.read_int()
                second_int = packet.read_int()
                
                # Verificar se pode ser width, height (ao invés de width, tileCount)
                if first_int > 5 and first_int <= 200 and second_int > 5 and second_int <= 200:
                    # Pode ser width, height diretamente
                    print(f" [POSSIBLE_ROOM_DIMENSIONS] Header {header_id}: Possível Width={first_int}, Height={second_int}")
                    
                    # Tentar ler o terceiro valor
                    try:
                        third_int = packet.read_int()
                        print(f" [ROOM_DIMENSIONS] Header {header_id}: {first_int}, {second_int}, {third_int}")
                        
                        # Se o terceiro valor é exatamente first*second, então é width, height, tileCount
                        if third_int == (first_int * second_int):
                            print(f" [FOUND_CORRECT_HEIGHTMAP] Header {header_id}: Width={first_int}, Height={second_int}, TileCount={third_int}")
                            
                            # Atualizar dimensões globais diretamente
                            global room_width, room_height, room_detected
                            room_width = first_int
                            room_height = second_int
                            room_detected = True
                            print(f" [SUCCESS] Dimensões CORRETAS definidas: {room_width}x{room_height}")
                            return
                            
                    except:
                        pass
                
                # Estrutura original (width, tileCount)
                if first_int > 5 and first_int <= 200 and second_int > 0:
                    calculated_height = int(second_int / first_int) if first_int > 0 else 0
                    
                    print(f" [POSSIBLE_HEIGHTMAP] Header {header_id}: Width={first_int}, TileCount={second_int}, Height={calculated_height}, Length: {packet_length}")
                    
                    # Se parece ser um HeightMap válido, processar apenas se não temos dimensões melhores
                    if calculated_height > 5 and calculated_height <= 200 and second_int == (first_int * calculated_height) and not room_detected:
                        packet.reset()
                        detect_room_dimensions(message)
                    
            except Exception as e:
                pass
                
    except Exception as e:
        pass

def detect_room_dimensions(message):
    global room_width, room_height, room_detected
    try:
        hm = HHeightMap(message.packet)
        if hm.width > 0 and hm.height > 0:
            room_width = hm.width
            room_height = hm.height
            room_detected = True
            # print(f" [SUCCESS] Dimensões do quarto: {room_width}x{room_height}")
    except Exception:
        pass

def detect_floor_dimensions(message):
    global room_width, room_height, room_detected
    try:
        p = message.packet
        p.reset()
        w, h = p.read('ii')
        if 5 <= w <= 200 and 5 <= h <= 200:
            room_width = w
            room_height = h
            room_detected = True
            # print(f" [SUCCESS] FloorHeightMap: {room_width}x{room_height}")
    except Exception:
        pass


def on_click(x, y, button, pressed):
    """Função chamada quando o mouse é clicado - DESABILITADA para evitar conflitos"""
    # NOTA: Esta função foi desabilitada porque as coordenadas de tela não correspondem
    # diretamente às coordenadas do jogo. A posição será capturada automaticamente
    # através dos packets UserUpdate e MoveAvatar quando o usuário clicar no jogo.
    pass

def on_key_press(key):
    """Função chamada quando uma tecla é pressionada - APENAS SETAS e quando ATIVA"""
    global current_x, current_y, room_width, room_height, room_detected, avatar_position_updated, key_pressed, extension_active, alt_pressed

    # Verificar se a extensão está ativa (botão play pressionado)
    if not extension_active:
        return True  # Retorna True para não bloquear a tecla

    # Atualizar estado de modificadores
    try:
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
            alt_pressed = True
    except Exception:
        pass

    # Mapear APENAS as setas do teclado
    arrow_keys = {
        keyboard.Key.up: 'up',
        keyboard.Key.down: 'down', 
        keyboard.Key.left: 'left',
        keyboard.Key.right: 'right'
    }
    
    # Se não é uma seta, ignorar completamente e não bloquear
    if key not in arrow_keys:
        return True  # Retorna True para permitir que outras aplicações recebam a tecla

    # Exigir Alt para processar movimento, para evitar travar digitação
    if MOVEMENT_REQUIRE_ALT and not alt_pressed:
        return True
    
    # Verificações de estado do quarto e avatar (sem logs para fluidez)
    if not room_detected:
        return True
    if not avatar_position_updated:
        return True
    
    try:
        key_pressed = arrow_keys[key]
        process_key()
        return True  # Não bloquear a tecla mesmo após processar
    except Exception:
        return True

def on_key_release(key):
    """Função chamada quando uma tecla é liberada"""
    global key_pressed, alt_pressed
    
    # Verificar se a extensão está ativa
    if not extension_active:
        return True  # Não processar se extensão estiver parada
    
    # Atualizar estado de modificadores
    try:
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
            alt_pressed = False
    except Exception:
        pass

    # Mapear APENAS as setas do teclado
    arrow_keys = {
        keyboard.Key.up: 'up',
        keyboard.Key.down: 'down', 
        keyboard.Key.left: 'left',
        keyboard.Key.right: 'right'
    }
    
    # Se não é uma seta, ignorar completamente
    if key not in arrow_keys:
        return True  # Permite que outras aplicações processem a tecla
    
    # Limpar apenas se for uma seta
    key_pressed = None
    return True

# Watchdog para o listener de teclado
keyboard_listener = None

def _start_keyboard_listener():
    global keyboard_listener
    try:
        keyboard_listener = keyboard.Listener(
            on_press=on_key_press,
            on_release=on_key_release,
            suppress=False,
            daemon=True
        )
        keyboard_listener.start()
    except Exception:
        keyboard_listener = None

def _keyboard_watchdog():
    global keyboard_listener
    while True:
        try:
            if keyboard_listener is None or not keyboard_listener.is_alive():
                _start_keyboard_listener()
            time.sleep(1)
        except Exception:
            time.sleep(2)

def process_key():
    global current_x, current_y, key_pressed, room_width, room_height, last_move_time
    
    # Verificar se a extensão está ativa
    if not extension_active:
        # print(" [DEBUG] Extensão PARADA - Ignorando tecla pressionada")
        return
    # Logs reduzidos
    
    if key_pressed and current_x is not None and current_y is not None:
        # Limite de taxa: evitar enviar movimentos em sequência muito rápida
        now = time.time() * 1000
        if MOVE_THROTTLE_MS > 0 and (now - last_move_time) < MOVE_THROTTLE_MS:
            # print(f" [THROTTLE] Movimento ignorado: aguardando {MOVE_THROTTLE_MS}ms entre comandos")
            return
        
        # Debug mínimo
        
        # Mapear apenas as setas do teclado
        direction_map = {
            'up': (0, -1),      # Seta para cima
            'down': (0, 1),     # Seta para baixo
            'left': (-1, 0),    # Seta para esquerda
            'right': (1, 0)     # Seta para direita
        }
        
        if key_pressed in direction_map:
            dx, dy = direction_map[key_pressed]
            new_x = current_x + dx
            new_y = current_y + dy
            
            # print(f" [DEBUG] Nova posição calculada: ({new_x}, {new_y})")
            
            if validate_position(new_x, new_y):
                # print(f" [DEBUG] Movimento válido para ({new_x}, {new_y})")
                current_x = new_x
                current_y = new_y
                # Enviar apenas um pacote para evitar anti-flood
                last_move_time = now
                move_avatar(current_x, current_y, multiple_clicks=False)
            else:
                # print(f"✗ [DEBUG] Movimento bloqueado: posição ({new_x}, {new_y}) fora dos limites do quarto {room_width}x{room_height}")
                pass
        else:
            print(f" [DEBUG] Tecla {key_pressed} não é uma seta válida")
    elif key_pressed:
        # print(f"⚠ [DEBUG] Posição atual não definida, forçando atualização")
        # Se não temos posição atual, forçar atualização
        if not room_detected:
            pass
        else:
            # print("⚠ [DEBUG] Clique no quarto primeiro para definir a posição inicial.")
            force_position_update()
    else:
        # print(" [DEBUG] Nenhuma tecla pressionada ou process_key chamado sem key_pressed")
        pass

def move_avatar(x, y, multiple_clicks=True):
    """Envia comando de movimento para o servidor"""
    import time
    
    try:
        print(f" [MOVE] Enviando movimento para ({x}, {y})")
        
        # Criar packet MoveAvatar TO_SERVER: {i:x}{i:y}
        move_packet = HPacket("MoveAvatar")
        move_packet.append_int(x)
        move_packet.append_int(y)
        
        # Enviar o packet para o servidor
        ext.send_to_server(move_packet)
        
        # NOTA: A posição atual será atualizada automaticamente pela função capture_move_position
        # que intercepta TODOS os packets MoveAvatar TO_SERVER, incluindo os que enviamos aqui
        
        print(f" [SUCCESS] Movimento enviado para ({x}, {y}) - posição será atualizada automaticamente")
        
        # Se múltiplos cliques estão habilitados, enviar vários packets
        if multiple_clicks and MULTIPLE_CLICKS_COUNT > 1:
            def send_multiple():
                for i in range(1, MULTIPLE_CLICKS_COUNT):
                    time.sleep(CLICK_DELAY)
                    try:
                        duplicate_packet = HPacket("MoveAvatar")
                        duplicate_packet.append_int(x)
                        duplicate_packet.append_int(y)
                        ext.send_to_server(duplicate_packet)
                    except Exception as e:
                        pass
                        break
            
            # Executar múltiplos cliques em thread separada
            threading.Thread(target=send_multiple, daemon=True).start()
            
    except Exception as e:
        print(f"✗ [ERROR] Erro ao enviar movimento: {e}")
        import traceback
        traceback.print_exc()

def validate_position(x, y):
    """Valida se a posição está dentro dos limites do quarto"""
    global room_width, room_height
    if room_width > 0 and room_height > 0:
        return 0 <= x < room_width and 0 <= y < room_height
    return True  # Se não temos dimensões do quarto, aceita qualquer posição

def force_position_update():
    """Força uma atualização da posição do avatar"""
    global current_x, current_y, avatar_position_updated
    # Solicita informações do usuário atual sem logar no console
    try:
        ext.send_to_server(HPacket("InfoRetrieve", 0))
    except Exception:
        pass
    avatar_position_updated = False  # Marca que precisa de atualização

def reset_position_on_room_change(message):
    """Reseta a posição quando muda de quarto"""
    global current_x, current_y, avatar_position_updated, room_detected, room_width, room_height
    print(f" [ROOM_CHANGE] Resetando posição e dimensões do quarto")
    current_x = None
    current_y = None
    avatar_position_updated = False
    room_detected = False
    room_width = 0
    room_height = 0

def reset_position_on_extension_start():
    """Reseta a posição quando a extensão é reiniciada"""
    global current_x, current_y, avatar_position_updated, room_detected, room_width, room_height
    print(f" [EXTENSION_START] Resetando todas as variáveis de estado")
    current_x = None
    current_y = None
    avatar_position_updated = False
    room_detected = False
    room_width = 0
    room_height = 0

reset_position_on_extension_start()

# Funções de controle da extensão (play/stop)
def start_extension():
    """Ativar a extensão (botão play)"""
    global extension_active, my_id
    extension_active = True
    print(" [CONTROL] Extensão ATIVADA - Mapeamento de setas habilitado")
    # Exibir mensagem no jogo instruindo o usuário
    try:
        msg = "reentre no quarto e clique em uma posicao para comecar a utilizar"
        if my_id is not None:
            # Envia mensagem de console (mensageiro) para o próprio usuário
            ext.send_to_client(HPacket("NewConsole", my_id, msg, 0, ""))
        else:
            # Se ainda não temos o id, escreve no console do G-Earth como fallback
            ext.write_to_console(msg)
    except Exception:
        pass

def stop_extension():
    """Parar a extensão (botão stop/x)"""
    global extension_active
    extension_active = False
    print(" [CONTROL] Extensão PARADA - Mapeamento de setas desabilitado")

def toggle_extension():
    """Alternar estado da extensão"""
    global extension_active
    if extension_active:
        stop_extension()
    else:
        start_extension()

# Interceptar comandos de controle da extensão
ext.intercept(Direction.TO_CLIENT, lambda msg: None, "ExtensionConsoleMessage", mode='async')

# Configurar interceptações de packets em modo assíncrono para não bloquear fluxo
ext.intercept(Direction.TO_CLIENT, initial_position, "Users", mode='async')
ext.intercept(Direction.TO_CLIENT, reset_position_on_room_change, "GetGuestRoom", mode='async')  # Reset ao mudar de quarto
ext.intercept(Direction.TO_CLIENT, detect_room_dimensions, "HeightMap", mode='async')
ext.intercept(Direction.TO_CLIENT, detect_floor_dimensions, "FloorHeightMap", mode='async')
ext.intercept(Direction.TO_SERVER, capture_move_position, "MoveAvatar", mode='async')

# Inicializar listeners de teclado se pynput estiver disponível
if PYNPUT_AVAILABLE:
    _start_keyboard_listener()
    threading.Thread(target=_keyboard_watchdog, daemon=True).start()
else:
    print(" [ERROR] PYNPUT não disponível - listeners não iniciados")
    print(" [ERROR] Instale o pynput: pip install pynput")

# Manter a extensão rodando
print(" [INIT] Mantendo extensão ativa...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print(" [SHUTDOWN] Extensão finalizada pelo usuário")
except Exception as e:
    print(f" [ERROR] Erro durante execução: {e}")
finally:
    print(" [SHUTDOWN] Extensão encerrada")




