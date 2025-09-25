import sys
import threading

from g_python.gextension import Extension
from g_python.hmessage import Direction, HMessage
from g_python.hpacket import HPacket
from g_python.hparsers import HHeightMap, HUserUpdate

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

room_width = 20  
room_height = 20  
room_detected = False

def capture_move_position(message):
    global current_x, current_y, avatar_position_updated
    
    try:
        packet = message.packet
        
        x = packet.read_int()
        y = packet.read_int()
        
        current_x = x
        current_y = y
        avatar_position_updated = True
        
    except Exception as e:
        print(f"Erro ao capturar posição: {e}")

def initial_position(message):
    global current_x, current_y, avatar_position_updated
    
    packet = message.packet
    
    packet_bytes = packet.bytearray
    packet_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in packet_bytes)
    
    if "/mv" in packet_str:
        try:
            mv_index = packet_str.find("/mv")
            if mv_index > 0:
                coords_str = packet_str[mv_index+4:].split("//")[0]
                coords = coords_str.split(",")
                if len(coords) >= 2:
                    x, y = int(float(coords[0])), int(float(coords[1]))
                    
                    current_x, current_y = x, y
                    avatar_position_updated = True
                    
        except Exception as e:
            print(f"Erro ao capturar posição: {e}")

def detect_room_dimensions(message):
    """Detecta as dimensões do quarto através do HeightMap"""
    global room_width, room_height, room_detected
    
    try:
        height_map = HHeightMap(message.packet)
        
        if hasattr(height_map, 'width') and hasattr(height_map, 'height'):
            hm_width = height_map.width
            hm_height = height_map.height
        
        if hasattr(height_map, 'tiles'):
            tiles = height_map.tiles
            
            if tiles:
                max_x = 0
                max_y = 0
                valid_tiles = 0
                
                for i, tile in enumerate(tiles):
                     x, y = height_map.index_to_coords(i)
                     if height_map.is_room_tile(x, y):
                         max_x = max(max_x, x)
                         max_y = max(max_y, y)
                         valid_tiles += 1
                
                real_width = max_x + 1
                real_height = max_y + 1
                
                if real_width != hm_width or real_height != hm_height:
                    room_width = real_width
                    room_height = real_height
                else:
                    room_width = hm_width
                    room_height = hm_height
            else:
                room_width = hm_width
                room_height = hm_height
        
        if room_width > 0 and room_height > 0:
            room_detected = True
        else:
            print("✗ Não foi possível detectar dimensões válidas do quarto")
            
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
            
            if not room_detected and calculated_width > 0 and calculated_height > 0:
                room_width = calculated_width
                room_height = calculated_height
                room_detected = True
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
        
       
        game_area_left = 100    
        game_area_top = 100    
        game_area_width = 800   
        game_area_height = 600  
        
        if (x < game_area_left or x > game_area_left + game_area_width or
            y < game_area_top or y > game_area_top + game_area_height):
            return
        
        relative_x = x - game_area_left
        relative_y = y - game_area_top
        
        cell_width = game_area_width / room_width
        cell_height = game_area_height / room_height
        
        room_x = int(relative_x / cell_width)
        room_y = int(relative_y / cell_height)
        
        room_x = max(0, min(room_width - 1, room_x))
        room_y = max(0, min(room_height - 1, room_y))
        
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
            
            if 0 <= new_x < room_width and 0 <= new_y < room_height:
                current_x = new_x
                current_y = new_y
                move_avatar(current_x, current_y)
            else:
                print(f"✗ Movimento bloqueado: posição ({new_x}, {new_y}) fora dos limites do quarto {room_width}x{room_height}")
    elif key_pressed:
        # Se não temos posição atual, define uma posição padrão
        if current_x is None or current_y is None:
            current_x = 10
            current_y = 10
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

ext.intercept(Direction.TO_CLIENT, detect_room_dimensions, "HeightMap")
ext.intercept(Direction.TO_CLIENT, detect_floor_dimensions, "FloorHeightMap")
ext.intercept(Direction.TO_CLIENT, reset_position_on_room_change, "RoomReady")

ext.intercept(Direction.TO_SERVER, capture_move_position, "MoveAvatar")

if PYNPUT_AVAILABLE:
    keyboard_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
    keyboard_listener.start()
    
    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.start()
    
else:
    print("Não foi possível iniciar o listener de teclado. Instale o pynput.")




