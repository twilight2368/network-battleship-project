# src/controllers/game_controller.py

import sys
import socket
import threading
import pygame
from pygame.locals import *
import os
# Import modules
from src.network.networking import DEFAULT_HOST, DEFAULT_PORT, send_json, recv_json
from src.components.gui_elements import BOARD_SIZE, CELL_SIZE, WHITE, BLACK, RED, GREEN, BLUE, SHIP_SIZES, show_confirm_dialog

class GameController:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        # State Initialization (Giữ nguyên như trong file gốc)
        self.state = {
            "is_login": False,
            "user_id": 0,
            "username": "",
            "in_queue": False,
            "in_game": False,
            "my_turn": False,
            "match_id": 0,
            "enemy_name": "",
            "my_board": [["~" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)],
            "enemy_board": [["~" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)],
            
            #Lobby state
            "in_custom_lobby": False,
            "is_host": False,
            "lobby_code": "",
            "opponent_joined": False,
        }
        
        # Ship placement logic (Giữ nguyên)
        self.placing_ships = False
        self.ships_to_place = ["carrier", "battleship", "cruiser", "submarine", "destroyer"]
        self.current_ship_index = 0
        self.ship_orientation = 0  # 0=vertical, 1=horizontal
        self.placed_ships = {}
        self.temp_ship_cells = []
        self.ship_sizes = SHIP_SIZES # Lấy từ gui_elements

        # UI State (Giữ nguyên)
        self.input_text = ""
        self.input_active = False
        self.input_mode = None
        self.username_temp = ""
        self.message = ""
        self.message_timer = 0
        
        # Pygame & Network Setup
        self.screen = None # Sẽ được khởi tạo trong main.py hoặc run()
        self.clock = None
        self.font_large, self.font_medium, self.font_small = None, None, None
        self.sock = None
        self.host = host
        self.port = port
        self.running = True
        
        # Image handles
        self.water_img = None
        self.ship_images = {}
        
    ### Server Connection Methods ###
    
    def connect_server(self):
        """Connect to server"""
        # ... (Giữ nguyên logic connect)
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.show_message(f"Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            self.show_message(f"Connection failed: {e}")
            self.running = False
            return False

    def start_receiver_thread(self):
        """Bắt đầu thread nhận tin nhắn."""
        if self.sock:
            self.receiver_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receiver_thread.start()

    def receive_messages(self):
        """Thread để nhận tin nhắn từ server."""
        # ... (Giữ nguyên logic receive_messages)
        while self.running:
            try:
                msg = recv_json(self.sock)
                if not msg:
                    break
                self.handle_server_message(msg)
            except:
                break
        
        if self.running:
            self.show_message("Disconnected from server")
            self.running = False
    
    def handle_server_message(self, msg):
        """Xử lý các tin nhắn đến từ server. (Giữ nguyên logic)"""
        print(f"Received: {msg}")
        t = msg.get("type", "")
        
        # ... (Logic xử lý tin nhắn như trong file gốc)
        if t == "QUEUE_ENTER_RES":
            if msg.get("result", 0) == 1:
                self.state["in_queue"] = True
                self.show_message("Entered queue successfully!")
            else:
                self.show_message(msg.get("message", "Enter queue failed"))
        
        elif t == "CREATE_ROOM_RES":
            if msg.get("result", 0) == 1:
                self.state["in_custom_lobby"] = True
                self.state["is_host"] = True
                self.state["lobby_code"] = msg["code"]
                self.show_message(f"Lobby hosted! Code: {msg['code']}")
            else:
                self.show_message(msg.get("message", "Failed to host lobby")) # Server nên gửi message chi tiết hơn

        elif t == "JOIN_ROOM_RES":
            if msg.get("result", 0) == 0:
                self.input_mode = "join_lobby_code" # Quay lại màn nhập mã
                self.input_active = True
                self.show_message("Failed to join lobby. Check code or room is full.")
            # Chú ý: Trường hợp thành công sẽ được server gửi MATCH_FOUND thay thế.
          
        elif t == "MATCH_FOUND": 
            # Đảm bảo logic custom lobby được xử lý đúng (MATCH_FOUND tự động bắt đầu game)
            
            # Cả 2 client (Host & Guest) đều nhận MATCH_FOUND
            self.state["in_game"] = True
            self.state["in_queue"] = False
            
            # Nếu đang ở chế độ Custom Lobby, xóa input mode
            if self.state["in_custom_lobby"]:
                self.input_mode = None
                self.input_active = False
                self.state["opponent_joined"] = True # Cập nhật trạng thái đối thủ cho Host
            
            self.state["match_id"] = msg["match_id"]
            
            # Tên đối thủ phụ thuộc vào việc mình là player1 hay player2 trong JSON
            is_player1 = self.state["username"] == msg["player1"]
            self.state["enemy_name"] = msg["player2"] if is_player1 else msg["player1"]
            
            # Kiểm tra xem mình có phải là người đi trước không
            self.state["my_turn"] = (msg.get("first_turn", 0) == 1 and is_player1) or \
                                    (msg.get("first_turn", 0) == 0 and not is_player1)
            
            self.show_message(f"Match found! Opponent: {self.state['enemy_name']}")
            #self.start_ship_placement()
            
            
        elif t == "MOVE_RESULT":
            attacker = msg["attacker"]
            r, c = msg["row"], msg["col"]
            result = msg["result"]
            
            if attacker == self.state["username"]:
                self.state["enemy_board"][r][c] = "X" if result in ["HIT", "SUNK"] else "O"
            else:
                self.state["my_board"][r][c] = "X" if result in ["HIT", "SUNK"] else "O"
            
            self.state["my_turn"] = (msg["next_turn"] == self.state["user_id"])
            self.show_message(f"{attacker} attacked ({r},{c}) -> {result}")
            
            if msg["next_turn"] == 0:
                self.show_message("GAME OVER!")
        
        elif t == "MATCH_RESULT":
            self.show_message(f"You {msg['result']}! New ELO: {msg['new_elo']}")
            self.state["in_game"] = False
            self.state["my_turn"] = False
            self.state["match_id"] = 0
            self.state["enemy_name"] = ""
        
        elif t == "LOGIN_RES":
            if msg.get("result", 0) == 0:
                self.show_message("Login failed!")
            else:
                self.state["is_login"] = True
                self.state["user_id"] = msg["user_id"]
                self.state["username"] = msg["username"]
                self.show_message(f"Logged in as {self.state['username']}")
        
        elif t == "REGISTER_RES":
            if msg.get("result", 0) == 1:
                self.show_message("Registration successful! Please login.")
            else:
                self.show_message(msg.get("message", "Registration failed"))

        elif t == "QUEUE_EXIT_RES":
            if msg.get("result", 1) == 1:
                self.state["in_queue"] = False
                self.show_message("Exited queue")
            else:
                self.show_message("Exit queue failed")

    def show_message(self, text):
        """Hiển thị tin nhắn tạm thời."""
        self.message = text
        self.message_timer = pygame.time.get_ticks() + 3000
        print(f"Message: {text}")

    ### Ship Placement Methods ###
    def start_ship_placement(self):
        """Khởi động giai đoạn đặt tàu."""
        # ... (Giữ nguyên logic start_ship_placement)
        self.placing_ships = True
        self.ships_to_place = ["carrier", "battleship", "cruiser", "submarine", "destroyer"]
        self.current_ship_index = 0
        self.ship_orientation = 0
        self.placed_ships = {}
        self.state["my_board"] = [["~" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.state["enemy_board"] = [["~" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.temp_ship_cells = []
    
    def can_place_ship(self, row, col, ship_name):
        """Kiểm tra vị trí đặt tàu."""
        # ... (Giữ nguyên logic can_place_ship)
        size = self.ship_sizes[ship_name]
        
        if self.ship_orientation == 0:  # Vertical
            if row + size > BOARD_SIZE:
                return False
        else:  # Horizontal
            if col + size > BOARD_SIZE:
                return False
        
        for i in range(size):
            r = row + i if self.ship_orientation == 0 else row
            c = col + i if self.ship_orientation == 1 else col
            if self.state["my_board"][r][c] != "~":
                return False
        
        return True
    
    def place_ship(self, row, col, ship_name):
        """Đặt tàu lên board và gửi lên server nếu hoàn tất."""
        size = self.ship_sizes[ship_name]
        
        for i in range(size):
            r = row + i if self.ship_orientation == 0 else row
            c = col + i if self.ship_orientation == 1 else col
            self.state["my_board"][r][c] = "s"
        
        self.placed_ships[ship_name] = [row, col, self.ship_orientation]
        self.current_ship_index += 1
        
        if self.current_ship_index >= len(self.ships_to_place):
            self.placing_ships = False
            
            #FIX LOGOUT_BUG
            self.state["in_queue"] = True
            
            send_json(self.sock, {"type": "QUEUE_ENTER_REQ", "ships": self.placed_ships})
            self.show_message("Ships placed! Entering queue...")
    
    ### For Custom Lobby ###
    
    def host_lobby_mode(self):
        # Dùng user_id của client để tạo phòng
        send_json(self.sock, {"type": "CREATE_ROOM_REQ", "user_id": self.state["user_id"]})
        self.show_message("Requesting to host a game...")

    def join_lobby_mode(self):
        self.state["in_custom_lobby"] = True
        self.state["is_host"] = False
        self.state["lobby_code"] = ""
        self.state["opponent_joined"] = False
        
        # BẬT CHẾ ĐỘ NHẬP LIỆU:
        self.input_mode = "join_lobby_code" 
        self.input_text = ""               
        self.input_active = True           
        self.show_message("Ready to join lobby.")

    def return_to_lobby(self):
        if self.state["in_custom_lobby"]:
            if self.state["is_host"]:
                send_json(self.sock, {"type": "ROOM_CLOSE_REQ", "code": self.state["lobby_code"]})
            
        self.state["in_custom_lobby"] = False
        self.state["is_host"] = False
        self.state["lobby_code"] = ""
        self.state["opponent_joined"] = False
        self.input_mode = None
        self.input_active = False
        self.input_text = ""
        self.show_message("Returned to lobby.")
        
    ### Image Loading ###
    def load_images(self):
        """Load và scale hình ảnh, in ra chi tiết lỗi tải ảnh."""
        self.water_img = None
        self.ship_images = {}
        
        # Đường dẫn cơ sở: Giả định thư mục chạy chính (main.py) nằm cùng cấp với thư mục 'images'
        BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Lấy đường dẫn của game_controller.py
        PROJECT_ROOT = os.path.join(BASE_DIR, '..', '..') # Lùi lại 2 cấp để về thư mục battle_ship/

        # 1. Load ảnh nước
        water_path = os.path.join(PROJECT_ROOT, "images", "water.jpg")
        try:
            self.water_img = pygame.image.load(water_path)
            self.water_img = pygame.transform.scale(self.water_img, (300, 300))
        except Exception as e:
            print(f"ERROR: Cannot load water image from {water_path}. Error: {e}")
            
        # 2. Load ảnh tàu
        for ship_name, size in self.ship_sizes.items():
            file_name = f"{ship_name.upper()}.png"
            ship_path = os.path.join(PROJECT_ROOT, "images", file_name)
            
            try:
                img = pygame.image.load(ship_path).convert_alpha() # Dùng convert_alpha() cho ảnh PNG
                
                self.ship_images[ship_name] = {
                    "vertical": pygame.transform.scale(img, (30, size * 30)),
                    "horizontal": pygame.transform.scale(
                        pygame.transform.rotate(img, 90), (size * 30, 30)
                    )
                }
            except Exception as e:
                print(f"ERROR: Cannot load ship image from {ship_path}. Error: {e}")
    