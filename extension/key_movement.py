import sys
import threading

from g_python.gextension import Extension
from g_python.hmessage import Direction, HMessage
from g_python.hpacket import HPacket

# Import classes individually to avoid circular import issues
try:
    from g_python.hparsers import HHeightMap, HUserUpdate
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

try:
    from pynput import keyboard, mouse
    PYNPUT_AVAILABLE = True
    print(" [INIT] pynput importado com sucesso")
except ImportError:
    PYNPUT_AVAILABLE = False
    print(" [ERROR] pynput não encontrado - instale com: pip install pynput")
    # print("AVISO: pynput não está instalado. Execute 'pip install pynput' para usar esta extensão.")

extension_info = {
    "title": "KeyMovement",
    "description": "Movimento livre com setas",
    "version": "1.0.0",
    "author": "Valdir"
}

ext = Extension(extension_info, sys.argv)
ext.start()

current_x = None
current_y = None
avatar_position_updated = False
key_pressed = None
last_move_time = 0

# Controle de estado da extensão (play/stop)
extension_active = True  # Extensão inicia ativa por padrão

# Configuração de múltiplos cliques
MULTIPLE_CLICKS_COUNT = 5  # Número de cliques a serem enviados (configurável)
CLICK_DELAY = 0.03  # Delay entre cliques em segundos (30ms)

room_width = 0  # Será detectado automaticamente
room_height = 0  # Será detectado automaticamente
room_detected = False

def initial_position(message):
    """Captura a posição inicial do avatar quando entra no quarto"""
    global current_x, current_y, avatar_position_updated, room_width, room_height
    
    print(f" [INTERCEPTED] RoomReady packet interceptado!")
    
    try:
        # RoomReady não contém posição diretamente, mas indica que o quarto foi carregado
        # A posição será capturada pelo próximo UserUpdate
        print(f" [INFO] Quarto carregado, aguardando UserUpdate para posição inicial...")
        
        # Reset das variáveis de posição para forçar nova captura
        current_x = None
        current_y = None
        avatar_position_updated = False
        
    except Exception as e:
        print(f"✗ [ERROR] Erro ao processar RoomReady: {e}")
        import traceback
        traceback.print_exc()

def capture_move_position(message):
    """Captura TODOS os movimentos enviados ao servidor e atualiza posição atual"""
    global current_x, current_y, avatar_position_updated, room_width, room_height
    
    print(f" [INTERCEPTED] MoveAvatar TO_SERVER interceptado!")
    
    try:
        # Debug completo do packet
        packet = message.packet
        print(f" [DEBUG] Packet completo: {packet}")
        print(f" [DEBUG] Packet length: {len(packet.bytearray)}")
        print(f" [DEBUG] Packet bytes: {[hex(b) for b in packet.bytearray[:20]]}")
        
        # IMPORTANTE: Fazer uma cópia do packet para não interferir no fluxo original
        packet_bytes = message.packet.bytearray
        
        # Ler diretamente do bytearray
        # Bytes 6-9: x coordinate (big endian)
        x = int.from_bytes(packet_bytes[6:10], byteorder='big', signed=True)
        # Bytes 10-13: y coordinate (big endian)  
        y = int.from_bytes(packet_bytes[10:14], byteorder='big', signed=True)
        
        print(f" [DEBUG] MoveAvatar enviado - x: {x}, y: {y}")
        
        # SEMPRE atualizar a posição atual quando um movimento é enviado ao servidor
        # Isso garante que tanto clicks do mouse quanto movimentos por setas atualizem a posição
        current_x = x
        current_y = y
        avatar_position_updated = True
        
        # Validar se está dentro dos limites do quarto (apenas para log)
        if room_width > 0 and room_height > 0:
            if 0 <= x < room_width and 0 <= y < room_height:
                print(f" [SUCCESS] Posição atualizada para: ({x}, {y}) - dentro dos limites")
            else:
                print(f" [WARNING] Posição atualizada para: ({x}, {y}) - fora dos limites do quarto {room_width}x{room_height}")
        else:
            print(f" [SUCCESS] Posição atualizada para: ({x}, {y}) - aguardando dimensões do quarto")
            
        # NÃO BLOQUEAR: Deixar o packet original continuar seu fluxo normal
        
    except Exception as e:
        print(f"✗ [ERROR] Erro ao capturar movimento: {e}")
        import traceback
        traceback.print_exc()

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
                if first_int > 10 and first_int < 200 and second_int > 10 and second_int < 200:
                    # Pode ser width, height diretamente
                    print(f" [POSSIBLE_ROOM_DIMENSIONS] Header {header_id}: Possível Width={first_int}, Height={second_int}")
                    
                    # Tentar ler o terceiro valor
                    try:
                        third_int = packet.read_int()
                        print(f" [ROOM_DIMENSIONS] Header {header_id}: {first_int}, {second_int}, {third_int}")
                        
                        # Se o terceiro valor é aproximadamente first*second, então é width, height, tileCount
                        if abs(third_int - (first_int * second_int)) < 10:
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
                if first_int > 0 and first_int < 200 and second_int > 0:
                    calculated_height = int(second_int / first_int) if first_int > 0 else 0
                    
                    print(f" [POSSIBLE_HEIGHTMAP] Header {header_id}: Width={first_int}, TileCount={second_int}, Height={calculated_height}, Length: {packet_length}")
                    
                    # Se parece ser um HeightMap válido, processar apenas se não temos dimensões melhores
                    if calculated_height > 0 and calculated_height < 200 and not room_detected:
                        packet.reset()
                        detect_room_dimensions(message)
                    
            except Exception as e:
                pass
                
    except Exception as e:
        pass

def detect_room_dimensions(message):
    global room_width, room_height, room_detected
    
    print(f" [INTERCEPTED] HeightMap packet interceptado!")
    
    try:
        # IMPORTANTE: Usar o packet original diretamente
        packet = message.packet
        
        print(f" [DEBUG] HeightMap recebido - analisando packet...")
        print(f" [DEBUG] Packet header ID: {packet.header_id()}")
        print(f" [DEBUG] Packet length: {len(packet.bytearray)}")
        
        # Debug: Mostrar os primeiros bytes do packet
        raw_bytes = packet.bytearray[:20]  # Primeiros 20 bytes
        print(f" [DEBUG] Primeiros bytes: {[hex(b) for b in raw_bytes]}")
        
        # Analisando os bytes manualmente
        # Bytes 6-9: width (big-endian)
        # Bytes 10-13: tile count (big-endian)
        
        # Extrair width dos bytes 6-9
        width_bytes = packet.bytearray[6:10]
        hm_width = int.from_bytes(width_bytes, byteorder='big')
        
        # Extrair tile count dos bytes 10-14
        tile_count_bytes = packet.bytearray[10:14]
        tile_count = int.from_bytes(tile_count_bytes, byteorder='big')
        
        print(f" [DEBUG] Width bytes: {[hex(b) for b in width_bytes]} = {hm_width}")
        print(f" [DEBUG] Tile count bytes: {[hex(b) for b in tile_count_bytes]} = {tile_count}")
        
        # Calcular height
        if hm_width > 0 and tile_count > 0:
            hm_height = int(tile_count / hm_width)
        else:
            hm_height = 0
        
        print(f" [DEBUG] Dimensões calculadas - Width: {hm_width}, Height: {hm_height}")
        
        # Verificar se as dimensões são válidas (quartos do Habbo geralmente são entre 5x5 e 50x50)
        if 5 <= hm_width <= 50 and 5 <= hm_height <= 50:
            room_width = hm_width
            room_height = hm_height
            room_detected = True
            print(f" [SUCCESS] Dimensões do quarto DEFINIDAS: {room_width}x{room_height}")
            print(f" [SUCCESS] Room detected: {room_detected}")
        else:
            print(f" [ERROR] Dimensões fora do esperado: {hm_width}x{hm_height}")
            # Usar dimensões padrão como fallback
            room_width = 20
            room_height = 20
            room_detected = True
            print(f" [FALLBACK] Usando dimensões padrão: {room_width}x{room_height}")
        
        # NÃO BLOQUEAR: Deixar o packet original continuar seu fluxo normal
        
    except Exception as e:
        print(f"✗ [ERROR] Erro ao detectar dimensões: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback final - usar dimensões padrão
        room_width = 20
        room_height = 20
        room_detected = True
        print(f" [EMERGENCY FALLBACK] Usando dimensões de emergência: {room_width}x{room_height}")

def detect_floor_dimensions(message):
    """Detecta dimensões através do FloorHeightMap como fallback"""
    global room_width, room_height, room_detected
    
    try:
        packet = message.packet
        packet.reset()
        
        # Tentar ler FloorHeightMap
        floor_width = packet.read_int()
        floor_height = packet.read_int()
        
        if 1 <= floor_width <= 200 and 1 <= floor_height <= 200:
            room_width = floor_width
            room_height = floor_height
            room_detected = True
            # print(f"✓ Dimensões detectadas via FloorMap: {room_width}x{room_height}")
        else:
            # print("✗ FloorMap vazio ou inválido")
            pass
            
    except Exception as e:
        # print(f"✗ Erro ao detectar dimensões via FloorHeightMap: {e}")
        pass


def on_click(x, y, button, pressed):
    """Função chamada quando o mouse é clicado"""
    global current_x, current_y, avatar_position_updated, room_width, room_height, room_detected
    
    if pressed and button == mouse.Button.left:
        if not room_detected:
            # print("Aguarde a detecção das dimensões do quarto antes de clicar.")
            return
        
        # Converter coordenadas da tela para coordenadas do quarto
        # Assumindo uma proporção simples (pode precisar de ajuste)
        room_x = int(x / 20)  # Ajustar conforme necessário
        room_y = int(y / 20)  # Ajustar conforme necessário
        
        # Validar se as coordenadas estão dentro dos limites
        if 0 <= room_x < room_width and 0 <= room_y < room_height:
            # print(f"✓ Clique mapeado para coordenada ({room_x}, {room_y}) no quarto {room_width}x{room_height}")
            
            # NOTA: Não atualizamos current_x e current_y aqui manualmente
            # A posição será atualizada automaticamente pela função capture_move_position
            # quando o packet MoveAvatar for enviado ao servidor
            
            # Usar múltiplos cliques para reforçar o movimento
            move_avatar(room_x, room_y, multiple_clicks=True)

def on_key_press(key):
    """Função chamada quando uma tecla é pressionada - APENAS SETAS e quando ATIVA"""
    global current_x, current_y, room_width, room_height, room_detected, avatar_position_updated, key_pressed, extension_active
    
    # Verificar se a extensão está ativa (botão play pressionado)
    if not extension_active:
        return  # Não processar teclas se extensão estiver parada
    
    # Mapear APENAS as setas do teclado
    arrow_keys = {
        keyboard.Key.up: 'up',
        keyboard.Key.down: 'down', 
        keyboard.Key.left: 'left',
        keyboard.Key.right: 'right'
    }
    
    # Se não é uma seta, ignorar completamente
    if key not in arrow_keys:
        return
    
    # Verificações de estado do quarto e avatar
    if not room_detected:
        print(" [WARNING] Quarto ainda não detectado - aguardando HeightMap...")
        return
    
    if not avatar_position_updated:
        print(" [WARNING] Posição do avatar ainda não capturada - aguardando movimento...")
        return
    
    try:
        key_pressed = arrow_keys[key]
        print(f" [DEBUG] Seta detectada: {key_pressed}")
        process_key()
    except Exception as e:
        print(f"✗ [ERROR] Erro ao processar tecla: {e}")

def on_key_release(key):
    global key_pressed
    key_pressed = None
    return True

def process_key():
    global current_x, current_y, key_pressed, room_width, room_height
    
    # Verificar se a extensão está ativa
    if not extension_active:
        print(" [DEBUG] Extensão PARADA - Ignorando tecla pressionada")
        return
    
    print(f" [DEBUG] process_key chamado - key_pressed: {key_pressed}")
    print(f" [DEBUG] Posição atual: current_x={current_x}, current_y={current_y}")
    print(f" [DEBUG] Dimensões do quarto: {room_width}x{room_height}")
    
    if key_pressed and current_x is not None and current_y is not None:
        
        print(f" [DEBUG] Processando tecla: {key_pressed}")
        print(f" [DEBUG] Posição atual: ({current_x}, {current_y})")
        print(f" [DEBUG] Dimensões do quarto: {room_width}x{room_height}")
        
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
            
            print(f" [DEBUG] Nova posição calculada: ({new_x}, {new_y})")
            
            if 0 <= new_x < room_width and 0 <= new_y < room_height:
                print(f" [DEBUG] Movimento válido para ({new_x}, {new_y})")
                current_x = new_x
                current_y = new_y
                # Usar múltiplos cliques para reforçar o movimento com setas
                move_avatar(current_x, current_y, multiple_clicks=True)
            else:
                print(f"✗ [DEBUG] Movimento bloqueado: posição ({new_x}, {new_y}) fora dos limites do quarto {room_width}x{room_height}")
        else:
            print(f" [DEBUG] Tecla {key_pressed} não é uma seta válida")
    elif key_pressed:
        print(f"⚠ [DEBUG] Posição atual não definida. current_x={current_x}, current_y={current_y}")
        # Se não temos posição atual, aguardar detecção
        if not room_detected:
            print("⚠ [DEBUG] Aguarde a detecção das dimensões do quarto antes de usar as setas.")
        else:
            print("⚠ [DEBUG] Clique no quarto primeiro para definir a posição inicial.")
            avatar_position_updated = True
    else:
        print(" [DEBUG] Nenhuma tecla pressionada ou process_key chamado sem key_pressed")

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
                        print(f" [MULTI] Movimento adicional {i+1}/{MULTIPLE_CLICKS_COUNT} enviado")
                    except Exception as e:
                        print(f"✗ [ERROR] Erro no movimento múltiplo {i+1}: {e}")
                        break
            
            # Executar múltiplos cliques em thread separada
            threading.Thread(target=send_multiple, daemon=True).start()
            
    except Exception as e:
        print(f"✗ [ERROR] Erro ao enviar movimento: {e}")
        import traceback
        traceback.print_exc()

def reset_position_on_room_change(message):
    """Reseta a posição quando muda de quarto"""
    global current_x, current_y, avatar_position_updated, room_detected
    current_x = None
    current_y = None
    avatar_position_updated = False
    room_detected = False  # Reseta detecção do quarto

def reset_position_on_extension_start():
    """Reseta a posição quando a extensão é reiniciada"""
    global current_x, current_y, avatar_position_updated
    current_x = None
    current_y = None
    avatar_position_updated = False

reset_position_on_extension_start()

# Funções de controle da extensão (play/stop)
def start_extension():
    """Ativar a extensão (botão play)"""
    global extension_active
    extension_active = True
    print(" [CONTROL] Extensão ATIVADA - Mapeamento de setas habilitado")

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
ext.intercept(Direction.TO_CLIENT, lambda msg: None, "ExtensionConsoleMessage")

# Configurar interceptações de packets
ext.intercept(Direction.TO_CLIENT, initial_position, "Users")
ext.intercept(Direction.TO_CLIENT, detect_room_dimensions, "HeightMap")
ext.intercept(Direction.TO_CLIENT, detect_floor_dimensions, "FloorHeightMap")
ext.intercept(Direction.TO_SERVER, capture_move_position, "MoveAvatar")

# Inicializar listeners apenas se pynput estiver disponível
if PYNPUT_AVAILABLE:
    print(" [INIT] Iniciando listeners de teclado e mouse...")
    keyboard_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
    keyboard_listener.start()
    print(" [INIT] Keyboard listener iniciado")
    
    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.start()
    print(" [INIT] Mouse listener iniciado")
    
    print(" [STATUS] Extensão iniciada em modo ATIVO")
    print(" [INFO] Use as SETAS do teclado para mover o avatar")
    print(" [INFO] A extensão só responde quando está no modo PLAY")
    
else:
    print(" [ERROR] PYNPUT não disponível - listeners não iniciados")
    print(" [ERROR] Instale o pynput: pip install pynput")




