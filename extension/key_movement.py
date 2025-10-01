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
except ImportError:
    PYNPUT_AVAILABLE = False
    print("AVISO: pynput não está instalado. Execute 'pip install pynput' para usar esta extensão.")

extension_info = {
    "title": "Seta",
    "description": "Use as setas para mover o avatar a partir da posição atual",
    "version": "1.0",
    "author": "Valdir"
}

ext = Extension(extension_info, sys.argv)
ext.start()

current_x = None
current_y = None
avatar_position_updated = False
key_pressed = None
last_move_time = 0

room_width = 0  # Será detectado automaticamente
room_height = 0  # Será detectado automaticamente
room_detected = False

def initial_position(message):
    """Captura a posição inicial do avatar"""
    global current_x, current_y, avatar_position_updated, room_width, room_height
    
    try:
        packet = message.packet
        
        # Ler a posição inicial do avatar
        x = packet.read_int()
        y = packet.read_int()
        
        # Validar se as coordenadas estão dentro dos limites do quarto
        if room_width > 0 and room_height > 0:
            if 0 <= x < room_width and 0 <= y < room_height:
                current_x = x
                current_y = y
                avatar_position_updated = True
                print(f"✓ Posição inicial do avatar: ({x}, {y}) no quarto {room_width}x{room_height}")
            else:
                print(f"⚠ Posição inicial ({x}, {y}) fora dos limites do quarto {room_width}x{room_height}, usando posição padrão")
                # Usar posição segura no centro do quarto
                current_x = min(10, room_width // 2)
                current_y = min(10, room_height // 2)
                avatar_position_updated = True
        else:
            # Se ainda não temos dimensões do quarto, armazenar temporariamente
            current_x = x
            current_y = y
            avatar_position_updated = True
            print(f"✓ Posição inicial temporária: ({x}, {y}) - aguardando detecção do quarto")
            
    except Exception as e:
        print(f"✗ Erro ao capturar posição inicial: {e}")
        import traceback
        traceback.print_exc()

def capture_move_position(message):
    """Captura a posição quando o avatar se move"""
    global current_x, current_y, avatar_position_updated, room_width, room_height
    
    try:
        packet = message.packet
        
        x = packet.read_int()
        y = packet.read_int()
        
        # Validar coordenadas antes de atualizar
        if room_width > 0 and room_height > 0:
            if 0 <= x < room_width and 0 <= y < room_height:
                current_x = x
                current_y = y
                avatar_position_updated = True
                print(f"✓ Avatar movido para: ({x}, {y})")
            else:
                print(f"⚠ Movimento para ({x}, {y}) fora dos limites do quarto {room_width}x{room_height}")
        else:
            # Se ainda não temos dimensões, armazenar temporariamente
            current_x = x
            current_y = y
            avatar_position_updated = True
            
    except Exception as e:
        print(f"✗ Erro ao capturar movimento: {e}")
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
            print(f"🔍 [ALL_PACKETS] Header ID: {header_id}, Length: {packet_length}")
            
            # Analisar TODOS os packets grandes para encontrar o correto
            packet.reset()
            try:
                # Tentar ler como diferentes estruturas
                first_int = packet.read_int()
                second_int = packet.read_int()
                
                # Verificar se pode ser width, height (ao invés de width, tileCount)
                if first_int > 10 and first_int < 200 and second_int > 10 and second_int < 200:
                    # Pode ser width, height diretamente
                    print(f"🎯 [POSSIBLE_ROOM_DIMENSIONS] Header {header_id}: Possível Width={first_int}, Height={second_int}")
                    
                    # Tentar ler o terceiro valor
                    try:
                        third_int = packet.read_int()
                        print(f"🔍 [ROOM_DIMENSIONS] Header {header_id}: {first_int}, {second_int}, {third_int}")
                        
                        # Se o terceiro valor é aproximadamente first*second, então é width, height, tileCount
                        if abs(third_int - (first_int * second_int)) < 10:
                            print(f"🎯 [FOUND_CORRECT_HEIGHTMAP] Header {header_id}: Width={first_int}, Height={second_int}, TileCount={third_int}")
                            
                            # Atualizar dimensões globais diretamente
                            global room_width, room_height, room_detected
                            room_width = first_int
                            room_height = second_int
                            room_detected = True
                            print(f"✅ [SUCCESS] Dimensões CORRETAS definidas: {room_width}x{room_height}")
                            return
                            
                    except:
                        pass
                
                # Estrutura original (width, tileCount)
                if first_int > 0 and first_int < 200 and second_int > 0:
                    calculated_height = int(second_int / first_int) if first_int > 0 else 0
                    
                    print(f"🎯 [POSSIBLE_HEIGHTMAP] Header {header_id}: Width={first_int}, TileCount={second_int}, Height={calculated_height}, Length: {packet_length}")
                    
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
    
    print(f"🎯 [INTERCEPTED] HeightMap packet interceptado!")
    
    try:
        packet = message.packet
        
        print(f"🔍 [DEBUG] HeightMap recebido - analisando packet...")
        print(f"🔍 [DEBUG] Packet header ID: {packet.header_id()}")
        print(f"🔍 [DEBUG] Packet length: {len(packet.bytearray)}")
        
        # Reset packet position to start
        packet.reset()
        
        # Usar a estrutura correta do HHeightMap
        hm_width, tiles_count = packet.read('ii')
        hm_height = int(tiles_count / hm_width) if hm_width > 0 else 0
        
        print(f"🔍 [DEBUG] Estrutura correta - Width: {hm_width}, TileCount: {tiles_count}")
        print(f"🔍 [DEBUG] Height calculado: {hm_height}")
        
        tiles = []
        for _ in range(tiles_count):
            tiles.append(packet.read_short())
        
        print(f"🔍 [DEBUG] Primeiros 10 tiles: {tiles[:10] if len(tiles) >= 10 else tiles}")
        
        # Verificar se as dimensões são válidas
        if hm_width > 0 and hm_height > 0:
            room_width = hm_width
            room_height = hm_height
            room_detected = True
            
            print(f"✅ [SUCCESS] Dimensões do quarto DEFINIDAS: {room_width}x{room_height}")
            print(f"✅ [SUCCESS] Room detected: {room_detected}")
        else:
            print(f"❌ [ERROR] Dimensões inválidas: {hm_width}x{hm_height}")
            
    except Exception as e:
        print(f"✗ Erro ao detectar dimensões: {e}")
        import traceback
        traceback.print_exc()

def detect_floor_dimensions(message):
    global room_width, room_height, room_detected
    
    try:
        packet = message.packet
        
        floor_map_str = packet.read_string()
        
        lines = floor_map_str.strip().split('\r')
        
        if lines and len(lines) > 0:
            first_line = lines[0]
            
            calculated_height = len(lines)
            calculated_width = len(first_line) if first_line else 0
            
            # Só usar FloorMap se HeightMap não foi detectado ainda
            if not room_detected and calculated_width > 0 and calculated_height > 0:
                room_width = calculated_width
                room_height = calculated_height
                room_detected = True
                print(f"✓ Dimensões detectadas via FloorMap: {room_width}x{room_height}")
        else:
            print("✗ FloorMap vazio ou inválido")
            
    except Exception as e:
        print(f"✗ Erro ao detectar dimensões via FloorHeightMap: {e}")
        import traceback
        traceback.print_exc()


def on_click(x, y, button, pressed):
    global current_x, current_y, avatar_position_updated, room_width, room_height, room_detected
    
    if pressed:  
        if not room_detected:
            print("Aguarde a detecção das dimensões do quarto antes de clicar.")
            return
        
        # Área do jogo ajustada - valores mais realistas
        game_area_left = 50    
        game_area_top = 50    
        game_area_width = 700   
        game_area_height = 500  
        
        # Verificar se o clique está dentro da área do jogo
        if (x < game_area_left or x > game_area_left + game_area_width or
            y < game_area_top or y > game_area_top + game_area_height):
            return
        
        # Calcular posição relativa dentro da área do jogo
        relative_x = x - game_area_left
        relative_y = y - game_area_top
        
        # Calcular tamanho de cada célula
        cell_width = game_area_width / room_width
        cell_height = game_area_height / room_height
        
        # Converter para coordenadas do quarto
        room_x = int(relative_x / cell_width)
        room_y = int(relative_y / cell_height)
        
        # Garantir que as coordenadas estão dentro dos limites
        room_x = max(0, min(room_width - 1, room_x))
        room_y = max(0, min(room_height - 1, room_y))
        
        print(f"✓ Clique mapeado para coordenada ({room_x}, {room_y}) no quarto {room_width}x{room_height}")
        
        current_x = room_x
        current_y = room_y
        avatar_position_updated = True
        
        move_avatar(room_x, room_y)

def on_key_press(key):
    """Função chamada quando uma tecla é pressionada"""
    global key_pressed, current_x, current_y, avatar_position_updated
    
    if key == keyboard.Key.esc:
        print("Saindo...")
        return False
    
    if current_x is None or current_y is None:
        current_x, current_y = 10, 10  
        avatar_position_updated = True
    
    key_map = {
        keyboard.Key.up: 'up',
        keyboard.Key.down: 'down', 
        keyboard.Key.left: 'left',
        keyboard.Key.right: 'right'
    }
    
    if key in key_map:
        key_pressed = key_map[key]
        process_key()
    
    return True

def on_key_release(key):
    global key_pressed
    key_pressed = None
    return True

def process_key():
    global current_x, current_y, key_pressed, room_width, room_height
    
    if key_pressed and current_x is not None and current_y is not None:
        
        print(f"🔍 [DEBUG] Processando tecla: {key_pressed}")
        print(f"🔍 [DEBUG] Posição atual: ({current_x}, {current_y})")
        print(f"🔍 [DEBUG] Dimensões do quarto: {room_width}x{room_height}")
        
        direction_map = {
            'up': (0, -1),
            'down': (0, 1),
            'left': (-1, 0),
            'right': (1, 0)
        }
        
        if key_pressed in direction_map:
            dx, dy = direction_map[key_pressed]
            new_x = current_x + dx
            new_y = current_y + dy
            
            print(f"🔍 [DEBUG] Nova posição calculada: ({new_x}, {new_y})")
            
            if 0 <= new_x < room_width and 0 <= new_y < room_height:
                print(f"✅ [DEBUG] Movimento válido para ({new_x}, {new_y})")
                current_x = new_x
                current_y = new_y
                move_avatar(current_x, current_y)
            else:
                print(f"✗ Movimento bloqueado: posição ({new_x}, {new_y}) fora dos limites do quarto {room_width}x{room_height}")
    elif key_pressed:
        print(f"⚠ [DEBUG] Posição atual não definida. current_x={current_x}, current_y={current_y}")
        # Se não temos posição atual, aguardar detecção
        if not room_detected:
            print("⚠ Aguarde a detecção das dimensões do quarto antes de usar as setas.")
        else:
            print("⚠ Clique no quarto primeiro para definir a posição inicial.")
            avatar_position_updated = True

def move_avatar(x, y):
    global current_x, current_y, avatar_position_updated
    
    current_x = x
    current_y = y
    avatar_position_updated = True
    
    packet = HPacket('MoveAvatar', x, y)
    ext.send_to_server(packet)

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

print("🚀 [INIT] Configurando interceptações...")

# Interceptar TODOS os packets para debug
ext.intercept(Direction.TO_CLIENT, intercept_all_packets)
print("✅ [INIT] Interceptação geral configurada")

ext.intercept(Direction.TO_CLIENT, detect_room_dimensions, "HeightMap")
print("✅ [INIT] HeightMap interceptação configurada")

ext.intercept(Direction.TO_CLIENT, detect_floor_dimensions, "FloorHeightMap")
print("✅ [INIT] FloorHeightMap interceptação configurada")

ext.intercept(Direction.TO_CLIENT, reset_position_on_room_change, "RoomReady")
print("✅ [INIT] RoomReady interceptação configurada")

ext.intercept(Direction.TO_SERVER, capture_move_position, "MoveAvatar")
print("✅ [INIT] MoveAvatar interceptação configurada")

# Interceptar MoveAvatar TO_CLIENT com header IDs específicos
ext.intercept(Direction.TO_CLIENT, capture_move_position, 83)
ext.intercept(Direction.TO_CLIENT, capture_move_position, 1982)
print("✅ [INIT] MoveAvatar TO_CLIENT interceptações configuradas")

if PYNPUT_AVAILABLE:
    keyboard_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
    keyboard_listener.start()
    
    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.start()
    
else:
    print("Não foi possível iniciar o listener de teclado. Instale o pynput.")




