import sys
import json
import socket
import threading
import pygame
from pygame.locals import *

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
BUFFER_SIZE = 1024
BOARD_SIZE = 10
CELL_SIZE = 30

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
BLUE = (0, 100, 200)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
YELLOW = (255, 255, 0)

# ==========================================
# JSON SEND/RECV
# ==========================================
def send_json(sock, obj):
    try:
        sock.sendall(json.dumps(obj).encode("utf-8"))
    except:
        pass

def recv_json(sock):
    data = ""
    brace_count = 0
    inside_json = False

    while True:
        try:
            chunk = sock.recv(BUFFER_SIZE).decode("utf-8")
            if not chunk:
                return None

            data += chunk
            for ch in chunk:
                if ch == "{":
                    brace_count += 1
                    inside_json = True
                elif ch == "}":
                    brace_count -= 1

            if inside_json and brace_count == 0:
                break
        except:
            return None

    try:
        return json.loads(data)
    except:
        return None


# ==========================================
# BATTLESHIP GUI
# ==========================================
class BattleshipGUI:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        pygame.init()
        self.screen = pygame.display.set_mode((900, 700))
        pygame.display.set_caption("Battleship Game")
        self.clock = pygame.time.Clock()
        
        self.sock = None
        self.host = host
        self.port = port
        self.running = True
        
        # Load images
        self.load_images()
        
        # State
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
            "enemy_board": [["~" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        }
        
        # Ship placement
        self.placing_ships = False
        self.ships_to_place = []
        self.current_ship_index = 0
        self.ship_orientation = 0  # 0=vertical, 1=horizontal
        self.placed_ships = {}
        self.temp_ship_cells = []
        
        # Ship data
        self.ship_sizes = {
            "carrier": 5,
            "battleship": 4,
            "cruiser": 3,
            "submarine": 3,
            "destroyer": 2
        }
        
        # UI
        self.input_text = ""
        self.input_active = False
        self.input_mode = None  # "username", "password", "attack"
        self.username_temp = ""
        self.message = ""
        self.message_timer = 0
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Connect to server
        self.connect_server()
        
        # Start receiver thread
        self.receiver_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receiver_thread.start()
    
    def load_images(self):
        """Load and scale images"""
        try:
            # Load water background (300x300)
            self.water_img = pygame.image.load("images/water.jpg")
            self.water_img = pygame.transform.scale(self.water_img, (300, 300))
            
            # Load ship images (vertical, 30x(size*30))
            self.ship_images = {}
            for ship_name, size in [("CARRIER", 5), ("BATTLESHIP", 4), ("CRUISER", 3), 
                                    ("SUBMARINE", 3), ("DESTROYER", 2)]:
                img = pygame.image.load(f"images/{ship_name}.png")
                # Vertical image
                self.ship_images[ship_name.lower()] = {
                    "vertical": pygame.transform.scale(img, (30, size * 30)),
                    "horizontal": pygame.transform.scale(
                        pygame.transform.rotate(img, 90), (size * 30, 30)
                    )
                }
        except Exception as e:
            print(f"Error loading images: {e}")
            self.water_img = None
            self.ship_images = {}
    
    def connect_server(self):
        """Connect to server"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.show_message(f"Connected to {self.host}:{self.port}")
        except Exception as e:
            self.show_message(f"Connection failed: {e}")
            self.running = False
    
    def receive_messages(self):
        """Thread to receive messages from server"""
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
        """Handle incoming server messages"""
        print(f"Received: {msg}")  # Debug
        t = msg.get("type", "")
        
        # Queue enter
        if t == "QUEUE_ENTER_RES":
            if msg.get("result", 0) == 1:
                self.state["in_queue"] = True
                self.show_message("Entered queue successfully!")
            else:
                self.show_message(msg.get("message", "Enter queue failed"))
        
        # Queue exit
        elif t == "QUEUE_EXIT_RES":
            if msg.get("result", 1) == 1:
                self.state["in_queue"] = False
                self.show_message("Exited queue")
            else:
                self.show_message("Exit queue failed")
        
        # Match found
        elif t == "MATCH_FOUND":
            self.state["in_queue"] = False
            self.state["in_game"] = True
            self.state["match_id"] = msg["match_id"]
            
            p1, p2 = msg["player1"], msg["player2"]
            self.state["enemy_name"] = p2 if self.state["username"] == p1 else p1
            self.state["my_turn"] = (msg["first_turn"] == self.state["user_id"])
            
            turn_msg = "Your turn!" if self.state["my_turn"] else "Opponent's turn"
            self.show_message(f"Match found vs {self.state['enemy_name']}! {turn_msg}")
        
        # Move result
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
        
        # Match end
        elif t == "MATCH_RESULT":
            self.show_message(f"You {msg['result']}! New ELO: {msg['new_elo']}")
            self.state["in_game"] = False
            self.state["my_turn"] = False
            self.state["match_id"] = 0
            self.state["enemy_name"] = ""
            # Don't reset boards immediately - let player see final state
            # Boards will reset when entering queue again
        
        # Login response
        elif t == "LOGIN_RES":
            if msg.get("result", 0) == 0:
                self.show_message("Login failed!")
            else:
                self.state["is_login"] = True
                self.state["user_id"] = msg["user_id"]
                self.state["username"] = msg["username"]
                self.show_message(f"Logged in as {self.state['username']}")
        
        # Register response
        elif t == "REGISTER_RES":
            if msg.get("result", 0) == 1:
                self.show_message("Registration successful! Please login.")
            else:
                self.show_message(msg.get("message", "Registration failed"))
    
    def show_message(self, text):
        """Show temporary message"""
        self.message = text
        self.message_timer = pygame.time.get_ticks() + 3000  # Show for 3 seconds
        print(f"Message: {text}")  # Debug
    
    def start_ship_placement(self):
        """Start ship placement phase"""
        self.placing_ships = True
        self.ships_to_place = ["carrier", "battleship", "cruiser", "submarine", "destroyer"]
        self.current_ship_index = 0
        self.ship_orientation = 0
        self.placed_ships = {}
        # Reset boards
        self.state["my_board"] = [["~" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.state["enemy_board"] = [["~" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.temp_ship_cells = []
    
    def can_place_ship(self, row, col, ship_name):
        """Check if ship can be placed at position"""
        size = self.ship_sizes[ship_name]
        
        # Check boundaries
        if self.ship_orientation == 0:  # Vertical
            if row + size > BOARD_SIZE:
                return False
        else:  # Horizontal
            if col + size > BOARD_SIZE:
                return False
        
        # Check overlap
        for i in range(size):
            r = row + i if self.ship_orientation == 0 else row
            c = col + i if self.ship_orientation == 1 else col
            if self.state["my_board"][r][c] != "~":
                return False
        
        return True
    
    def place_ship(self, row, col, ship_name):
        """Place ship on board"""
        size = self.ship_sizes[ship_name]
        
        for i in range(size):
            r = row + i if self.ship_orientation == 0 else row
            c = col + i if self.ship_orientation == 1 else col
            self.state["my_board"][r][c] = "s"
        
        self.placed_ships[ship_name] = [row, col, self.ship_orientation]
        self.current_ship_index += 1
        
        if self.current_ship_index >= len(self.ships_to_place):
            # All ships placed, send to server
            self.placing_ships = False
            send_json(self.sock, {"type": "QUEUE_ENTER_REQ", "ships": self.placed_ships})
            self.show_message("Ships placed! Entering queue...")
    
    def draw_board(self, x_offset, y_offset, board, show_ships=True, clickable=False):
        """Draw a game board"""
        # Draw water background
        if self.water_img:
            self.screen.blit(self.water_img, (x_offset, y_offset))
        else:
            pygame.draw.rect(self.screen, BLUE, (x_offset, y_offset, 300, 300))
        
        # Draw grid
        for i in range(BOARD_SIZE + 1):
            # Vertical lines
            pygame.draw.line(self.screen, BLACK, 
                        (x_offset + i * CELL_SIZE, y_offset),
                        (x_offset + i * CELL_SIZE, y_offset + 300), 1)
            # Horizontal lines
            pygame.draw.line(self.screen, BLACK,
                        (x_offset, y_offset + i * CELL_SIZE),
                        (x_offset + 300, y_offset + i * CELL_SIZE), 1)
        
        # Draw row/col labels
        for i in range(BOARD_SIZE):
            # Column numbers (top)
            text = self.font_small.render(str(i), True, BLACK)
            self.screen.blit(text, (x_offset + i * CELL_SIZE + 10, y_offset - 25))
            # Row numbers (left)
            text = self.font_small.render(str(i), True, BLACK)
            self.screen.blit(text, (x_offset - 25, y_offset + i * CELL_SIZE + 5))
        
        # Draw ship images FIRST if available and showing ships
        if show_ships and self.ship_images and self.placed_ships:
            for ship_name, pos in self.placed_ships.items():
                if pos:
                    row, col, orientation = pos
                    ship_x = x_offset + col * CELL_SIZE
                    ship_y = y_offset + row * CELL_SIZE
                    
                    orient_key = "vertical" if orientation == 0 else "horizontal"
                    if ship_name in self.ship_images:
                        self.screen.blit(self.ship_images[ship_name][orient_key], 
                                    (ship_x, ship_y))
        
        # Draw cells (green squares for ships if no images, and hits/misses)
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                cell = board[r][c]
                cell_x = x_offset + c * CELL_SIZE
                cell_y = y_offset + r * CELL_SIZE
                
                # Only draw green square if showing ships but no ship images
                if cell == "s" and show_ships and not self.ship_images:
                    pygame.draw.rect(self.screen, GREEN, 
                                (cell_x + 2, cell_y + 2, CELL_SIZE - 4, CELL_SIZE - 4))
                
                # Draw hits and misses ON TOP of everything
                if cell == "X":
                    # Hit (red X)
                    pygame.draw.line(self.screen, RED,
                                (cell_x + 5, cell_y + 5),
                                (cell_x + CELL_SIZE - 5, cell_y + CELL_SIZE - 5), 4)
                    pygame.draw.line(self.screen, RED,
                                (cell_x + CELL_SIZE - 5, cell_y + 5),
                                (cell_x + 5, cell_y + CELL_SIZE - 5), 4)
                elif cell == "O":
                    # Miss (white circle)
                    pygame.draw.circle(self.screen, WHITE,
                                    (cell_x + CELL_SIZE // 2, cell_y + CELL_SIZE // 2),
                                    CELL_SIZE // 3, 3)
        
        return x_offset, y_offset, 300, 300
    
    
    def draw_button(self, x, y, width, height, text, color=GRAY):
        """Draw a button and return if clicked"""
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()[0]
        
        # Check hover
        hover = x < mouse_pos[0] < x + width and y < mouse_pos[1] < y + height
        
        # Draw button
        button_color = LIGHT_GRAY if hover else color
        pygame.draw.rect(self.screen, button_color, (x, y, width, height))
        pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2)
        
        # Draw text
        text_surf = self.font_small.render(text, True, BLACK)
        text_rect = text_surf.get_rect(center=(x + width // 2, y + height // 2))
        self.screen.blit(text_surf, text_rect)
        
        return hover and mouse_click
    
    def draw_input_box(self, x, y, width, height, placeholder=""):
        """Draw an input box"""
        # Draw box
        color = BLUE if self.input_active else GRAY
        pygame.draw.rect(self.screen, WHITE, (x, y, width, height))
        pygame.draw.rect(self.screen, color, (x, y, width, height), 2)
        
        # Draw text
        display_text = self.input_text if self.input_text else placeholder
        text_color = BLACK if self.input_text else GRAY
        text_surf = self.font_small.render(display_text, True, text_color)
        self.screen.blit(text_surf, (x + 5, y + 10))
    
    def draw_login_screen(self):
        """Draw login/register screen"""
        self.screen.fill(WHITE)
        
        # Title
        title = self.font_large.render("BATTLESHIP", True, BLACK)
        title_rect = title.get_rect(center=(450, 100))
        self.screen.blit(title, title_rect)
        
        # Buttons
        if self.draw_button(300, 250, 300, 50, "REGISTER"):
            self.input_mode = "register_username"
            self.input_active = True
            self.input_text = ""
        
        if self.draw_button(300, 320, 300, 50, "LOGIN"):
            self.input_mode = "login_username"
            self.input_active = True
            self.input_text = ""
        
        if self.draw_button(300, 390, 300, 50, "EXIT"):
            self.running = False
        
        # Handle input
        if self.input_mode in ["register_username", "login_username"]:
            prompt = "Enter username:"
            self.screen.blit(self.font_small.render(prompt, True, BLACK), (300, 480))
            self.draw_input_box(300, 510, 300, 40)
        elif self.input_mode in ["register_password", "login_password"]:
            prompt = "Enter password:"
            self.screen.blit(self.font_small.render(prompt, True, BLACK), (300, 480))
            self.draw_input_box(300, 510, 300, 40)
    
    def draw_lobby_screen(self):
        """Draw lobby screen (logged in, not in game)"""
        self.screen.fill(WHITE)
        
        # Title
        title = self.font_medium.render(f"Welcome, {self.state['username']}", True, BLACK)
        self.screen.blit(title, (50, 50))
        
        if self.state["in_queue"]:
            # In queue
            queue_text = self.font_large.render("Waiting for opponent...", True, BLUE)
            text_rect = queue_text.get_rect(center=(450, 300))
            self.screen.blit(queue_text, text_rect)
            
            if self.draw_button(300, 400, 300, 50, "EXIT QUEUE"):
                send_json(self.sock, {"type": "QUEUE_EXIT_REQ"})
        else:
            # Not in queue
            if self.draw_button(300, 250, 300, 50, "ENTER QUEUE"):
                self.start_ship_placement()
            
            if self.draw_button(300, 320, 300, 50, "LOGOUT"):
                send_json(self.sock, {"type": "LOGOUT"})
                self.state["is_login"] = False
                self.state["username"] = ""
                self.state["user_id"] = 0
    
    def draw_ship_placement_screen(self):
        """Draw ship placement screen"""
        self.screen.fill(WHITE)
        
        # Title
        if self.current_ship_index < len(self.ships_to_place):
            ship_name = self.ships_to_place[self.current_ship_index]
            title = self.font_medium.render(
                f"Place {ship_name.upper()} (size: {self.ship_sizes[ship_name]})",
                True, BLACK
            )
            self.screen.blit(title, (50, 30))
            
            # Instructions
            orient_text = "VERTICAL" if self.ship_orientation == 0 else "HORIZONTAL"
            inst1 = self.font_small.render(
                f"Orientation: {orient_text} (Press R to rotate)",
                True, BLACK
            )
            inst2 = self.font_small.render(
                "Click on board to place ship",
                True, BLACK
            )
            self.screen.blit(inst1, (50, 70))
            self.screen.blit(inst2, (50, 95))
        
        # Draw board
        board_x, board_y = 300, 150
        self.draw_board(board_x, board_y, self.state["my_board"], show_ships=True)
        
        # Draw preview of current ship
        if self.current_ship_index < len(self.ships_to_place):
            mouse_pos = pygame.mouse.get_pos()
            # Convert mouse to grid
            if board_x <= mouse_pos[0] < board_x + 300 and board_y <= mouse_pos[1] < board_y + 300:
                col = (mouse_pos[0] - board_x) // CELL_SIZE
                row = (mouse_pos[1] - board_y) // CELL_SIZE
                
                ship_name = self.ships_to_place[self.current_ship_index]
                if self.can_place_ship(row, col, ship_name):
                    # Draw preview (transparent green)
                    size = self.ship_sizes[ship_name]
                    for i in range(size):
                        r = row + i if self.ship_orientation == 0 else row
                        c = col + i if self.ship_orientation == 1 else col
                        cell_x = board_x + c * CELL_SIZE
                        cell_y = board_y + r * CELL_SIZE
                        
                        s = pygame.Surface((CELL_SIZE - 4, CELL_SIZE - 4))
                        s.set_alpha(128)
                        s.fill(GREEN)
                        self.screen.blit(s, (cell_x + 2, cell_y + 2))
    
    def draw_game_screen(self):
        """Draw game screen"""
        self.screen.fill(WHITE)
        
        # Title
        title = self.font_medium.render(
            f"VS {self.state['enemy_name']}",
            True, BLACK
        )
        self.screen.blit(title, (50, 20))
        
        # Turn indicator
        turn_text = "YOUR TURN - Click enemy board to attack" if self.state["my_turn"] else "OPPONENT'S TURN"
        turn_color = GREEN if self.state["my_turn"] else RED
        turn_surf = self.font_small.render(turn_text, True, turn_color)
        self.screen.blit(turn_surf, (50, 55))
        
        # Draw boards side by side
        # My board (left)
        my_label = self.font_small.render("Your Board", True, BLACK)
        self.screen.blit(my_label, (130, 80))
        my_board_rect = self.draw_board(80, 130, self.state["my_board"], show_ships=True, clickable=False)
        
        # Enemy board (right)
        enemy_label = self.font_small.render("Enemy Board", True, BLACK)
        self.screen.blit(enemy_label, (530, 80))
        enemy_board_rect = self.draw_board(480, 130, self.state["enemy_board"], show_ships=False, clickable=True)
        
        # Buttons
        if self.draw_button(350, 500, 200, 50, "RESIGN"):
            send_json(self.sock, {
                "type": "RESIGN_REQ",
                "match_id": self.state["match_id"],
                "user_id": self.state["user_id"]
            })
        
        return enemy_board_rect
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            
            elif event.type == KEYDOWN:
                if self.input_active:
                    if event.key == K_RETURN:
                        # Submit input
                        if self.input_mode == "register_username":
                            self.username_temp = self.input_text
                            self.input_text = ""
                            self.input_mode = "register_password"
                        elif self.input_mode == "register_password":
                            send_json(self.sock, {
                                "type": "REGISTER_REQ",
                                "username": self.username_temp,
                                "password": self.input_text
                            })
                            self.input_text = ""
                            self.input_mode = None
                            self.input_active = False
                        elif self.input_mode == "login_username":
                            self.username_temp = self.input_text
                            self.input_text = ""
                            self.input_mode = "login_password"
                        elif self.input_mode == "login_password":
                            send_json(self.sock, {
                                "type": "LOGIN_REQ",
                                "username": self.username_temp,
                                "password": self.input_text
                            })
                            self.input_text = ""
                            self.input_mode = None
                            self.input_active = False
                    elif event.key == K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif event.key == K_ESCAPE:
                        self.input_text = ""
                        self.input_mode = None
                        self.input_active = False
                    else:
                        if len(self.input_text) < 20:
                            self.input_text += event.unicode
                
                # Rotate ship during placement
                elif self.placing_ships and event.key == K_r:
                    self.ship_orientation = 1 - self.ship_orientation
            
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Ship placement
                    if self.placing_ships and self.current_ship_index < len(self.ships_to_place):
                        board_x, board_y = 300, 150
                        if board_x <= mouse_pos[0] < board_x + 300 and board_y <= mouse_pos[1] < board_y + 300:
                            col = (mouse_pos[0] - board_x) // CELL_SIZE
                            row = (mouse_pos[1] - board_y) // CELL_SIZE
                            
                            ship_name = self.ships_to_place[self.current_ship_index]
                            if self.can_place_ship(row, col, ship_name):
                                self.place_ship(row, col, ship_name)
                    
                    # Attack during game
                    elif self.state["in_game"] and self.state["my_turn"]:
                        enemy_board_x, enemy_board_y = 480, 130
                        if enemy_board_x <= mouse_pos[0] < enemy_board_x + 300 and \
                           enemy_board_y <= mouse_pos[1] < enemy_board_y + 300:
                            col = (mouse_pos[0] - enemy_board_x) // CELL_SIZE
                            row = (mouse_pos[1] - enemy_board_y) // CELL_SIZE
                            
                            # Check if cell already attacked
                            if self.state["enemy_board"][row][col] == "~":
                                send_json(self.sock, {
                                    "type": "MOVE_REQ",
                                    "match_id": self.state["match_id"],
                                    "row": row,
                                    "col": col
                                })
                                # Optimistically mark as pending to prevent double-click
                                # Server will send actual result
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            
            # Draw appropriate screen
            if not self.state["is_login"]:
                self.draw_login_screen()
            elif self.placing_ships:
                self.draw_ship_placement_screen()
            elif self.state["in_game"]:
                self.draw_game_screen()
            else:
                self.draw_lobby_screen()
            
            # Draw message
            if self.message and pygame.time.get_ticks() < self.message_timer:
                msg_surf = self.font_small.render(self.message, True, RED)
                msg_rect = msg_surf.get_rect(center=(450, 650))
                pygame.draw.rect(self.screen, WHITE, (msg_rect.x - 5, msg_rect.y - 5, 
                                                      msg_rect.width + 10, msg_rect.height + 10))
                pygame.draw.rect(self.screen, BLACK, (msg_rect.x - 5, msg_rect.y - 5,
                                                      msg_rect.width + 10, msg_rect.height + 10), 1)
                self.screen.blit(msg_surf, msg_rect)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        pygame.quit()


# ==========================================
# MAIN
# ==========================================
def main():
    host = sys.argv[1] if len(sys.argv) >= 2 else DEFAULT_HOST
    port = int(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_PORT
    
    game = BattleshipGUI(host, port)
    game.run()


if __name__ == "__main__":
    main()