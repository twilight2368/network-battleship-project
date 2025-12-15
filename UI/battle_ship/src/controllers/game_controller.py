# src/controllers/game_controller.py

import sys
import socket
import threading
import pygame
from pygame.locals import *
import os
import random

from src.network.networking import DEFAULT_HOST, DEFAULT_PORT, send_json, recv_json
from src.components.gui_elements import BOARD_SIZE, CELL_SIZE, WHITE, BLACK, RED, GREEN, BLUE, SHIP_SIZES, show_confirm_dialog

class GameController:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        # State Initialization
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
            
            # Lobby state
            "in_custom_lobby": False,
            "is_host": False,
            "lobby_code": "",
            "opponent_joined": False,
            "in_leaderboard": False,
            
            #Other
            "leaderboard": [],
        }
        self.show_password = False
        
        # Ship placement logic
        self.placing_ships = False
        self.ships_to_place = ["carrier", "battleship", "cruiser", "submarine", "destroyer"]
        self.current_ship_index = 0
        self.ship_orientation = 0  # 0=vertical, 1=horizontal
        self.placed_ships = {}
        self.temp_ship_cells = []
        self.ship_sizes = SHIP_SIZES
        self.ships_confirmed = False #updated
        
        # NEW: Drag & Drop support
        self.ship_orientations = {}  # Track orientation for each ship
        self.dragging_ship = None
        self.drag_start_pos = None
        self.ship_rects = {}  # Store rectangles for each ship item

        # UI State
        self.input_text = ""
        self.input_active = False
        self.input_mode = None
        self.username_temp = ""
        self.message = ""
        self.message_timer = 0
        
        # Pygame & Network Setup
        self.screen = None
        self.clock = None
        self.font_large, self.font_medium, self.font_small = None, None, None
        self.sock = None
        self.host = host
        self.port = port
        self.running = True
        
        # Image handles
        self.water_img = None
        self.ship_images = {}
        
        # Player time
        self.turn_time_limit = 30000  # 30 seconds per turn
        self.turn_start_time = 0
        self.remaining_time = self.turn_time_limit
        
    ### Server Connection Methods ###
    
    def connect_server(self):
        """Connect to server"""
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
        """Xử lý các tin nhắn đến từ server."""
        print(f"Received: {msg}")
        t = msg.get("type", "")
        
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
                self.show_message(msg.get("message", "Failed to host lobby"))

        elif t == "JOIN_ROOM_RES":
            if msg.get("result", 0) == 0:
                self.input_mode = "join_lobby_code"
                self.input_active = True
                self.show_message("Failed to join lobby. Check code or room is full.")
          
        elif t == "MATCH_FOUND": 
            self.state["in_queue"] = False
            
            if self.state["in_custom_lobby"]:
                self.input_mode = None
                self.input_active = False
                self.state["opponent_joined"] = True
            
            self.state["match_id"] = msg["match_id"]
            
            is_player1 = self.state["username"] == msg["player1"]
            self.state["enemy_name"] = msg["player2"] if is_player1 else msg["player1"]
            
            self.show_message(f"Match found! Opponent: {self.state['enemy_name']}")
            self.start_ship_placement()
        
        elif t == "PLACE_SHIP_RES":
            if msg.get("result", 0) == 1:
                self.show_message("Ships placed! Ready for match...")
                self.ships_confirmed = True #updated
            else:
                self.show_message("Ships placed failed!")
           
        elif t == "MATCH_START":
            self.placing_ships = False
            self.state["in_game"] = True
            
            first_user_id = msg.get("first_turn", 0)
            self.state["my_turn"] = (first_user_id == self.state["user_id"])
            
            if self.state["my_turn"]:
                self.reset_turn_timer()
            
            self.show_message("Match started!")
        
        elif t == "MOVE_RESULT":
            attacker = msg["attacker"]
            r, c = msg["row"], msg["col"]
            result = msg["result"]
            
            if attacker == self.state["username"]:
                self.state["enemy_board"][r][c] = "X" if result in ["HIT", "SUNK"] else "O"
            else:
                self.state["my_board"][r][c] = "X" if result in ["HIT", "SUNK"] else "O"
            
            self.state["my_turn"] = (msg["next_turn"] == self.state["user_id"])
            
            if self.state["my_turn"]:
                self.reset_turn_timer()
            self.show_message(f"{attacker} attacked ({r},{c}) -> {result}")
            
            if msg["next_turn"] == 0:
                self.show_message("GAME OVER!")
        
        elif t == "MATCH_RESULT":
            self.show_message(f"You {msg['result']}! New ELO: {msg['new_elo']}")
            self.state["in_game"] = False
            self.state["my_turn"] = False
            self.state["match_id"] = 0
            self.state["enemy_name"] = ""
            self.state["in_custom_lobby"] = False
        
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
        elif t == "LEADERBOARD_RES":
            if len(msg.get("players", [])) > 0:
                self.state["leaderboard"] = msg["players"]
                self.show_message("Success to get leaderboard")
            else:
                self.show_message("Failed to get leaderboard")
    def show_message(self, text):
        """Hiển thị tin nhắn tạm thời."""
        self.message = text
        self.message_timer = pygame.time.get_ticks() + 3000
        print(f"Message: {text}")

    ### Ship Placement Methods ###
    
    def start_ship_placement(self):
        """Khởi động giai đoạn đặt tàu."""
        self.placing_ships = True
        self.ships_to_place = ["carrier", "battleship", "cruiser", "submarine", "destroyer"]
        self.current_ship_index = 0
        self.ship_orientation = 0
        self.placed_ships = {ship: None for ship in self.ships_to_place}  # Initialize all as None
        self.ship_orientations = {ship: 0 for ship in self.ships_to_place}  # Default all vertical
        self.state["my_board"] = [["~" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.state["enemy_board"] = [["~" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.temp_ship_cells = []
        self.dragging_ship = None
        self.drag_start_pos = None
    
    def can_place_ship(self, row, col, ship_name, orientation=None):
        """Kiểm tra vị trí đặt tàu."""
        if orientation is None:
            orientation = self.ship_orientations.get(ship_name, 0)
        
        size = self.ship_sizes[ship_name]
        
        # Check bounds
        if orientation == 0:  # Vertical
            if row + size > BOARD_SIZE:
                return False
        else:  # Horizontal
            if col + size > BOARD_SIZE:
                return False
        
        # Check if cells are empty
        for i in range(size):
            r = row + i if orientation == 0 else row
            c = col + i if orientation == 1 else col
            cell = self.state["my_board"][r][c]
            if cell != "~":
                return False
        
        return True
    
    def place_ship(self, row, col, ship_name, orientation=None):
        """Đặt tàu lên board."""
        if orientation is None:
            orientation = self.ship_orientations.get(ship_name, 0)
        
        size = self.ship_sizes[ship_name]
        
        # Place ship on board
        for i in range(size):
            r = row + i if orientation == 0 else row
            c = col + i if orientation == 1 else col
            self.state["my_board"][r][c] = "s"
        
        self.placed_ships[ship_name] = [row, col, orientation]
        self.show_message(f"{ship_name.upper()} placed!")
    
    def remove_ship(self, ship_name):
        """Remove a ship from the board"""
        if ship_name in self.placed_ships and self.placed_ships[ship_name] is not None:
            row, col, orientation = self.placed_ships[ship_name]
            size = self.ship_sizes[ship_name]
            
            # Clear cells
            for i in range(size):
                r = row + i if orientation == 0 else row
                c = col + i if orientation == 1 else col
                self.state["my_board"][r][c] = "~"
            
            self.placed_ships[ship_name] = None
    
    def rotate_ship(self, ship_name):
        """Rotate a ship's orientation"""
        current = self.ship_orientations.get(ship_name, 0)
        new_orientation = 1 - current
        self.ship_orientations[ship_name] = new_orientation
        
        # If ship is already placed on board (not being dragged), try to re-place with new orientation
        if self.placed_ships.get(ship_name) is not None and self.dragging_ship != ship_name:
            row, col, old_orient = self.placed_ships[ship_name]
            self.remove_ship(ship_name)
            
            if self.can_place_ship(row, col, ship_name, new_orientation):
                self.place_ship(row, col, ship_name, new_orientation)
            else:
                # If can't place with new orientation, revert
                self.ship_orientations[ship_name] = old_orient
                self.place_ship(row, col, ship_name, old_orient)
                self.show_message(f"Can't rotate {ship_name} here!")
        else:
            # Ship is being dragged or not placed yet - just rotate the orientation
            print(f"Rotated {ship_name} to {'horizontal' if new_orientation == 1 else 'vertical'}")
    
    def clear_all_ships(self):
        """Clear all placed ships from board"""
        for ship_name in self.ships_to_place:
            self.remove_ship(ship_name)
        self.show_message("All ships cleared!")
    
    def confirm_ship_placement(self):
        """Send ship placement to server"""
        # Check all ships are placed
        if not all(self.placed_ships.get(ship) is not None for ship in self.ships_to_place):
            self.show_message("Please place all ships first!")
            return
        
        user_id = self.state["user_id"]
        match_id = self.state["match_id"]
        
        send_json(self.sock, {
            "type": "SHIPS_PLACED_REQ",
            "match_id": match_id, 
            "user_id": user_id, 
            "ships": self.placed_ships
        })
        
        self.show_message("Waiting for opponent...")

    def random_place_ships(self):
        """Randomly place all ships on the board."""
        import random
        
        # Reset board and placement data
        self.state["my_board"] = [["~" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.placed_ships = {ship: None for ship in self.ships_to_place}
        
        for ship_name in self.ships_to_place:
            size = self.ship_sizes[ship_name]
            placed = False
            max_attempts = 100
            attempts = 0
            
            while not placed and attempts < max_attempts:
                attempts += 1
                orientation = random.randint(0, 1)
                
                if orientation == 0:  # Vertical
                    row = random.randint(0, BOARD_SIZE - size)
                    col = random.randint(0, BOARD_SIZE - 1)
                else:  # Horizontal
                    row = random.randint(0, BOARD_SIZE - 1)
                    col = random.randint(0, BOARD_SIZE - size)
                
                # Check if placement is valid
                valid = True
                for i in range(size):
                    r = row + i if orientation == 0 else row
                    c = col + i if orientation == 1 else col
                    if self.state["my_board"][r][c] != "~":
                        valid = False
                        break
                
                if valid:
                    # Place the ship
                    for i in range(size):
                        r = row + i if orientation == 0 else row
                        c = col + i if orientation == 1 else col
                        self.state["my_board"][r][c] = "s"
                    
                    self.placed_ships[ship_name] = [row, col, orientation]
                    self.ship_orientations[ship_name] = orientation
                    placed = True
            
            if not placed:
                self.show_message("Random placement failed, retrying...")
                self.random_place_ships()
                return
        
        self.show_message("Ships randomly placed!")
    
    ### For Custom Lobby ###
    
    def host_lobby_mode(self):
        send_json(self.sock, {"type": "CREATE_ROOM_REQ", "user_id": self.state["user_id"]})
        self.show_message("Requesting to host a game...")

    def join_lobby_mode(self):
        self.state["in_custom_lobby"] = True
        self.state["is_host"] = False
        self.state["lobby_code"] = ""
        self.state["opponent_joined"] = False
        
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
        self.state["in_leaderboard"] = False
        self.input_mode = None
        self.input_active = False
        self.input_text = ""
        self.show_message("Returned to lobby.")
    
    
    def show_leaderboard(self):
        self.state["in_leaderboard"] = True
        send_json(self.sock, {"type": "LEADERBOARD_REQ"})
    ### Image Loading ###
    
    def load_images(self):
        """Load và scale hình ảnh."""
        self.water_img = None
        self.ship_images = {}
        
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        PROJECT_ROOT = os.path.join(BASE_DIR, '..', '..')

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
                img = pygame.image.load(ship_path).convert_alpha()
                
                self.ship_images[ship_name] = {
                    "vertical": pygame.transform.scale(img, (30, size * 30)),
                    "horizontal": pygame.transform.scale(
                        pygame.transform.rotate(img, 90), (size * 30, 30)
                    )
                }
            except Exception as e:
                print(f"ERROR: Cannot load ship image from {ship_path}. Error: {e}")
        
        # 3. Load background images
        login_bg_path = os.path.join(PROJECT_ROOT, "images", "lobby-bg-1.jpg")
        try:
            self.login_bg_img = self.scale_image_with_aspect_ratio(login_bg_path, 900, 700)
        except Exception as e:
            print(f"ERROR: Cannot load login background from {login_bg_path}. Error: {e}")
        
        lobby_bg_path = os.path.join(PROJECT_ROOT, "images", "lobby-bg-2.jpg")
        try:
            self.lobby_bg_img = self.scale_image_with_aspect_ratio(lobby_bg_path, 900, 700)
        except Exception as e:
            print(f"ERROR: Cannot load lobby background from {lobby_bg_path}. Error: {e}")
        
        in_queue_bg_path = os.path.join(PROJECT_ROOT, "images", "lobby-bg-4.jpg")
        try:
            self.in_queue_bg_img = self.scale_image_with_aspect_ratio(in_queue_bg_path, 900, 700)
        except Exception as e:
            print(f"ERROR: Cannot load in queue background from {in_queue_bg_path}. Error: {e}")
        
        room_bg_path = os.path.join(PROJECT_ROOT, "images", "lobby-bg-5.jpg")
        try:
            self.room_bg_img = self.scale_image_with_aspect_ratio(room_bg_path, 900, 700)
        except Exception as e:
            print(f"ERROR: Cannot load room background from {room_bg_path}. Error: {e}")
            
        in_game_bg_path = os.path.join(PROJECT_ROOT, "images", "lobby-bg-3.jpg")
        try:
            self.in_game_bg_img = self.scale_image_with_aspect_ratio(in_game_bg_path, 900, 700)
        except Exception as e:
            print(f"ERROR: Cannot load in game background from {in_game_bg_path}. Error: {e}")
            
    ### Timer Methods ###
    
    def reset_turn_timer(self):
        self.turn_start_time = pygame.time.get_ticks()
        self.remaining_time = self.turn_time_limit
        
    def update_turn_timer(self):
        if self.state["in_game"] and self.state["my_turn"]:
            elapsed_time = pygame.time.get_ticks() - self.turn_start_time
            if elapsed_time >= self.turn_time_limit:
                self.perform_random_move()
        
    ### Random shooting handler ###
    
    def find_random_cell(self):
        unhit_cells = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.state["enemy_board"][r][c] == "~":
                    unhit_cells.append((r, c))
        if unhit_cells:
            return random.choice(unhit_cells)
        return None
    
    def perform_random_move(self):
        if not self.state["in_game"] or not self.state["my_turn"]:
            return
        
        target = self.find_random_cell()
        if target:
            row, col = target
            self.show_message(f"TIME OUT! Auto-firing at ({row}, {col})")
            
            send_json(self.sock, {
                "type": "MOVE_REQ",
                "match_id": self.state["match_id"],
                "user_id": self.state["user_id"],
                "row": row,
                "col": col
            })
            self.state["my_turn"] = False
        
    def scale_image_with_aspect_ratio(self, image_path, target_width, target_height, fill_mode='cover'):
        """Scale image maintaining aspect ratio."""
        img = pygame.image.load(image_path)
        img_width, img_height = img.get_size()
        
        img_aspect = img_width / img_height
        target_aspect = target_width / target_height
        
        if fill_mode == 'cover':
            if img_aspect > target_aspect:
                scale_height = target_height
                scale_width = int(scale_height * img_aspect)
            else:
                scale_width = target_width
                scale_height = int(scale_width / img_aspect)
            
            scaled_img = pygame.transform.scale(img, (scale_width, scale_height))
            
            final_surface = pygame.Surface((target_width, target_height))
            
            x_offset = (target_width - scale_width) // 2
            y_offset = (target_height - scale_height) // 2
            
            final_surface.blit(scaled_img, (x_offset, y_offset))
            return final_surface
        
        else:  # 'contain' mode
            if img_aspect > target_aspect:
                scale_width = target_width
                scale_height = int(scale_width / img_aspect)
            else:
                scale_height = target_height
                scale_width = int(scale_height * img_aspect)
            
            scaled_img = pygame.transform.scale(img, (scale_width, scale_height))
            
            final_surface = pygame.Surface((target_width, target_height))
            final_surface.fill((0, 0, 0))
            
            x_offset = (target_width - scale_width) // 2
            y_offset = (target_height - scale_height) // 2
            
            final_surface.blit(scaled_img, (x_offset, y_offset))
            return final_surface