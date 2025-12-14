# src/screens/game_screen.py

import pygame
from pygame.locals import *

# Import từ components và network
from src.components.gui_elements import BOARD_SIZE, CELL_SIZE, WHITE, BLACK, RED, GREEN, YELLOW, GRAY, LIGHT_GRAY, draw_button
from src.network.networking import send_json

# --- DRAWING LOGIC ---

def draw_board(controller, x_offset, y_offset, board, show_ships=True, color_number = BLACK):
    """Vẽ board game."""
    screen = controller.screen
    
    # Draw water background
    if controller.water_img:
        screen.blit(controller.water_img, (x_offset, y_offset))
    else:
        pygame.draw.rect(screen, (0, 100, 200), (x_offset, y_offset, 300, 300))
    
    # Draw ship images FIRST if available and showing ships
    if show_ships and controller.ship_images and controller.placed_ships:
        for ship_name, pos in controller.placed_ships.items():
            if pos:
                row, col, orientation = pos
                ship_x = x_offset + col * CELL_SIZE
                ship_y = y_offset + row * CELL_SIZE
                orient_key = "vertical" if orientation == 0 else "horizontal"
                if ship_name in controller.ship_images:
                    screen.blit(controller.ship_images[ship_name][orient_key], (ship_x, ship_y))
    
    # Draw cells (hits/misses) and grid
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            cell = board[r][c]
            cell_x = x_offset + c * CELL_SIZE
            cell_y = y_offset + r * CELL_SIZE
            
            if cell == "X":
                pygame.draw.line(screen, RED, (cell_x + 5, cell_y + 5), (cell_x + CELL_SIZE - 5, cell_y + CELL_SIZE - 5), 4)
                pygame.draw.line(screen, RED, (cell_x + CELL_SIZE - 5, cell_y + 5), (cell_x + 5, cell_y + CELL_SIZE - 5), 4)
            elif cell == "O":
                pygame.draw.circle(screen, WHITE, (cell_x + CELL_SIZE // 2, cell_y + CELL_SIZE // 2), CELL_SIZE // 3, 3)

    for i in range(BOARD_SIZE + 1):
        pygame.draw.line(screen, BLACK, (x_offset + i * CELL_SIZE, y_offset), (x_offset + i * CELL_SIZE, y_offset + 300), 1)
        pygame.draw.line(screen, BLACK, (x_offset, y_offset + i * CELL_SIZE), (x_offset + 300, y_offset + i * CELL_SIZE), 1)
    for i in range(BOARD_SIZE):
        text = controller.font_small.render(str(i), True, color_number)
        screen.blit(text, (x_offset + i * CELL_SIZE + 10, y_offset - 26))
        text = controller.font_small.render(str(i), True, color_number)
        screen.blit(text, (x_offset - 25, y_offset + i * CELL_SIZE + 1))
    
    return x_offset, y_offset, 300, 300

def draw_ship_item(screen, font_small, x, y, ship_name, size, orientation, is_placed, is_dragging=False, ship_images=None):
    """Vẽ một item tàu trong danh sách bên trái - LUÔN VERTICAL"""
    # LUÔN VẼ VERTICAL CHO DANH SÁCH (bỏ qua orientation)
    width = 50
    height = size * 18 + 10
    
    # Nền tàu
    if is_placed:
        color = (100, 200, 100, 180)  # Xanh lá - đã đặt (semi-transparent)
    elif is_dragging:
        color = (255, 255, 150, 200)  # Vàng nhạt - đang kéo
    else:
        color = LIGHT_GRAY  # Xám - chưa đặt
    
    # Vẽ nền
    ship_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    ship_surface.fill(color)
    pygame.draw.rect(ship_surface, BLACK, (0, 0, width, height), 2)
    screen.blit(ship_surface, (x, y))
    
    # Vẽ hình tàu nếu có - LUÔN VERTICAL
    if ship_images and ship_name in ship_images:
        ship_img = ship_images[ship_name]["vertical"]  # LUÔN DÙNG VERTICAL
        
        # Scale để vừa với box
        img_width = 35
        img_height = size * 18
        
        scaled_img = pygame.transform.scale(ship_img, (img_width, img_height))
        img_x = x + (width - img_width) // 2
        img_y = y + (height - img_height) // 2
        screen.blit(scaled_img, (img_x, img_y))
    
    # Tên tàu (rút gọn)
    short_names = {
        "carrier": "CAR",
        "battleship": "BAT", 
        "cruiser": "CRU",
        "submarine": "SUB",
        "destroyer": "DES"
    }
    name_text = font_small.render(short_names.get(ship_name, ship_name[:3].upper()), True, BLACK)
    text_x = x + width // 2 - name_text.get_width() // 2
    text_y = y + height + 3
    screen.blit(name_text, (text_x, text_y))
    
    return pygame.Rect(x, y, width, height)

def draw_ship_placement_screen(controller, clicked_events_occur):
    """Vẽ màn hình đặt tàu với drag & drop"""
    screen = controller.screen
    screen.fill(WHITE)
    
    # Draw background image if available
    if hasattr(controller, 'in_queue_bg_img') and controller.in_queue_bg_img:
        screen.blit(controller.in_queue_bg_img, (0, 0))
    else:
        screen.fill(WHITE)
    
    # Semi-transparent overlay for better text visibility
    overlay = pygame.Surface((900, 700))
    overlay.set_alpha(100)
    overlay.fill(WHITE)
    screen.blit(overlay, (0, 0))
    
    # Title
    title = controller.font_medium.render("PLACE YOUR SHIPS", True, BLACK)
    screen.blit(title, (50, 20))
    
    # Instructions
    inst1 = controller.font_small.render("Drag ships to board", True, BLACK)
    inst2 = controller.font_small.render("Press R while dragging to rotate", True, BLACK)
    screen.blit(inst1, (50, 60))
    screen.blit(inst2, (50, 85))
    
    # Draw board
    board_x, board_y = 400, 150
    draw_board(controller, board_x, board_y, controller.state["my_board"], show_ships=True)
    
    # Draw ship list on the left - 2 COLUMNS LAYOUT (LUÔN VERTICAL)
    ship_list_x1 = 30   # Column 1
    ship_list_x2 = 120  # Column 2
    ship_list_y = 180
    controller.ship_rects = {}
    
    col1_y_offset = 0
    col2_y_offset = 0
    
    for i, ship_name in enumerate(controller.ships_to_place):
        size = controller.ship_sizes[ship_name]
        is_placed = ship_name in controller.placed_ships and controller.placed_ships[ship_name] is not None
        
        # Get orientation for this ship (CHỈ DÙNG KHI KÉO)
        orientation = controller.ship_orientations.get(ship_name, 0)
        
        is_dragging = (controller.dragging_ship == ship_name)
        
        # Chia 2 cột: 3 tàu đầu cột 1, 2 tàu sau cột 2
        if i < 3:  # Column 1
            x_pos = ship_list_x1
            y_pos = ship_list_y + col1_y_offset
        else:  # Column 2
            x_pos = ship_list_x2
            y_pos = ship_list_y + col2_y_offset
        
        # draw_ship_item luôn vẽ vertical, bỏ qua orientation parameter
        rect = draw_ship_item(
            screen, controller.font_small,
            x_pos, y_pos,
            ship_name, size, orientation,  # orientation vẫn truyền nhưng không dùng
            is_placed, is_dragging,
            controller.ship_images
        )
        controller.ship_rects[ship_name] = rect
        
        # Cộng thêm khoảng cách cho tàu tiếp theo (LUÔN DÙNG CHIỀU CAO VERTICAL)
        if i < 3:
            col1_y_offset += rect.height + 25
        else:
            col2_y_offset += rect.height + 25
    
    # Draw dragging ship following mouse
    if controller.dragging_ship:
        mouse_pos = pygame.mouse.get_pos()
        ship_name = controller.dragging_ship
        size = controller.ship_sizes[ship_name]
        orientation = controller.ship_orientations.get(ship_name, 0)
        
        if controller.ship_images and ship_name in controller.ship_images:
            orient_key = "vertical" if orientation == 0 else "horizontal"
            ship_img = controller.ship_images[ship_name][orient_key]
            
            # Make it semi-transparent
            drag_img = ship_img.copy()
            drag_img.set_alpha(180)
            
            # Center on mouse
            img_rect = drag_img.get_rect(center=mouse_pos)
            screen.blit(drag_img, img_rect)
    
    # Draw preview on board when hovering (CHỈ KHI ĐANG KÉO)
    if controller.dragging_ship:
        mouse_pos = pygame.mouse.get_pos()
        if board_x <= mouse_pos[0] < board_x + 300 and board_y <= mouse_pos[1] < board_y + 300:
            col = (mouse_pos[0] - board_x) // CELL_SIZE
            row = (mouse_pos[1] - board_y) // CELL_SIZE
            
            ship_name = controller.dragging_ship
            orientation = controller.ship_orientations.get(ship_name, 0)
            
            if controller.can_place_ship(row, col, ship_name, orientation):
                size = controller.ship_sizes[ship_name]
                for i in range(size):
                    r = row + i if orientation == 0 else row
                    c = col + i if orientation == 1 else col
                    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                        cell_x = board_x + c * CELL_SIZE
                        cell_y = board_y + r * CELL_SIZE
                        
                        s = pygame.Surface((CELL_SIZE - 4, CELL_SIZE - 4))
                        s.set_alpha(128)
                        s.fill(GREEN)
                        screen.blit(s, (cell_x + 2, cell_y + 2))
    
    # Buttons
    all_placed = all(controller.placed_ships.get(ship) is not None for ship in controller.ships_to_place)
    
    # Random Place Button
    if draw_button(screen, controller.font_small, 50, 120, 150, 35, 
                  "Random Place", YELLOW, clicked_events_occur):
        controller.random_place_ships()
    
    # Clear All Button
    if draw_button(screen, controller.font_small, 220, 120, 120, 35,
                  "Clear All", RED, clicked_events_occur):
        controller.clear_all_ships()
    
    # Status text - ĐÚNG VỊ TRÍ
    if all_placed:
        remaining_text = "All ships placed!"
        text_color = GREEN
    else:
        remaining = sum(1 for ship in controller.ships_to_place if controller.placed_ships.get(ship) is None)
        remaining_text = f"Ships remaining: {remaining}"
        text_color = RED
    
    status = controller.font_small.render(remaining_text, True, text_color)
    screen.blit(status, (400, 480))
    
    # Play Button (only enabled when all ships placed)
    play_color = GREEN if all_placed else GRAY
    play_text = "READY!" if all_placed else "PLAY (Place all ships)"
    
    if draw_button(screen, controller.font_small, 400, 510, 300, 50,
                  play_text, play_color, clicked_events_occur and all_placed):
        if all_placed:
            controller.confirm_ship_placement()

def draw_game_screen(controller, clicked_events_occur):
    """Vẽ màn hình game chính."""
    screen = controller.screen
    state = controller.state
    
    screen.fill(WHITE)
    
    if hasattr(controller, 'in_game_bg_img') and controller.in_game_bg_img:
        screen.blit(controller.in_game_bg_img, (0, 0))
    else:
        screen.fill(WHITE)
    
    # Update timer
    if state["my_turn"]:
        elapsed_time = pygame.time.get_ticks() - controller.turn_start_time
        remaining_ms = controller.turn_time_limit - elapsed_time
        
        if remaining_ms <= 0:
            remaining_s = 0
        else:
            remaining_s = remaining_ms // 1000
        time_text = f"YOUR TURN: {remaining_s:02d}s"
        text_color = RED if remaining_s <= 5 else GREEN
    else:
        time_text = "OPPONENT'S TURN"
        text_color = BLACK
    time_surf = controller.font_small.render(time_text, True, text_color)
    time_rect = time_surf.get_rect(topright=(880, 20))
    screen.blit(time_surf, time_rect)    
    
    # Title/Turn Indicator
    title = controller.font_medium.render(f"VS {state['enemy_name']}", True, WHITE)
    screen.blit(title, (50, 20))
    turn_text = "YOUR TURN - Click enemy board to attack" if state["my_turn"] else "OPPONENT'S TURN"
    turn_color = GREEN if state["my_turn"] else RED
    turn_surf = controller.font_small.render(turn_text, True, turn_color)
    screen.blit(turn_surf, (50, 55))
    
    # Draw boards
    my_label = controller.font_small.render("Your Board", True,  WHITE)
    screen.blit(my_label, (130, 80))
    draw_board(controller, 80, 130, state["my_board"], show_ships=True, color_number=WHITE)
    
    enemy_label = controller.font_small.render("Enemy Board", True,  WHITE)
    screen.blit(enemy_label, (530, 80))
    enemy_board_rect = draw_board(controller, 480, 130, state["enemy_board"], show_ships=False, color_number=WHITE)
    
    # Buttons
    if draw_button(screen, controller.font_small, 350, 500, 200, 50, "RESIGN", event_click=clicked_events_occur):
        send_json(controller.sock, {
            "type": "RESIGN_REQ",
            "match_id": state["match_id"],
            "user_id": state["user_id"]
        })
    
    return enemy_board_rect

# --- EVENT HANDLERS ---

def handle_game_events(event, controller):
    """Xử lý sự kiện cho màn hình đặt tàu và game chính."""
    
    # update timer
    controller.update_turn_timer()
    
    if event.type == KEYDOWN:
        # Rotate ship WHILE DRAGGING - QUAN TRỌNG
        if controller.placing_ships and event.key == K_r:
            if controller.dragging_ship:
                # Xoay tàu đang kéo
                controller.rotate_ship(controller.dragging_ship)
                print(f"Rotated {controller.dragging_ship} while dragging")
            else:
                # Xoay tàu dưới con trỏ chuột (nếu không đang kéo)
                mouse_pos = pygame.mouse.get_pos()
                for ship_name, rect in controller.ship_rects.items():
                    if rect.collidepoint(mouse_pos):
                        controller.rotate_ship(ship_name)
                        break
    
    elif event.type == MOUSEBUTTONDOWN:
        if event.button == 1:  # Left click
            mouse_pos = pygame.mouse.get_pos()
            
            # Ship placement with drag & drop
            if controller.placing_ships:
                # Check if clicking on a ship in the list
                clicked_ship = False
                for ship_name, rect in controller.ship_rects.items():
                    if rect.collidepoint(mouse_pos):
                        # Start dragging
                        if controller.placed_ships.get(ship_name) is not None:
                            # Remove from board to re-place
                            controller.remove_ship(ship_name)
                        controller.dragging_ship = ship_name
                        controller.drag_start_pos = mouse_pos
                        clicked_ship = True
                        print(f"Started dragging: {ship_name}")
                        break
                
                # If not clicking on ship, check if clicking on board to remove ship
                if not clicked_ship:
                    board_x, board_y = 400, 150
                    if board_x <= mouse_pos[0] < board_x + 300 and board_y <= mouse_pos[1] < board_y + 300:
                        col = (mouse_pos[0] - board_x) // CELL_SIZE
                        row = (mouse_pos[1] - board_y) // CELL_SIZE
                        
                        # Check if there's a ship at this position
                        for ship_name, pos in controller.placed_ships.items():
                            if pos:
                                ship_row, ship_col, ship_orient = pos
                                size = controller.ship_sizes[ship_name]
                                
                                # Check if click is on this ship
                                on_ship = False
                                if ship_orient == 0:  # Vertical
                                    if col == ship_col and ship_row <= row < ship_row + size:
                                        on_ship = True
                                else:  # Horizontal
                                    if row == ship_row and ship_col <= col < ship_col + size:
                                        on_ship = True
                                
                                if on_ship:
                                    controller.remove_ship(ship_name)
                                    controller.dragging_ship = ship_name
                                    controller.drag_start_pos = mouse_pos
                                    print(f"Picked up ship from board: {ship_name}")
                                    break
            
            # Attack during game
            elif controller.state["in_game"] and controller.state["my_turn"]:
                enemy_board_x, enemy_board_y = 480, 130
                if enemy_board_x <= mouse_pos[0] < enemy_board_x + 300 and \
                   enemy_board_y <= mouse_pos[1] < enemy_board_y + 300:
                    col = (mouse_pos[0] - enemy_board_x) // CELL_SIZE
                    row = (mouse_pos[1] - enemy_board_y) // CELL_SIZE
                    
                    if controller.state["enemy_board"][row][col] == "~":
                        send_json(controller.sock, {
                            "type": "MOVE_REQ",
                            "match_id": controller.state["match_id"],
                            "row": row,
                            "col": col
                        })
    
    elif event.type == MOUSEBUTTONUP:
        if event.button == 1:  # Left click release
            mouse_pos = pygame.mouse.get_pos()
            
            # Drop ship on board
            if controller.placing_ships and controller.dragging_ship:
                board_x, board_y = 400, 150
                if board_x <= mouse_pos[0] < board_x + 300 and board_y <= mouse_pos[1] < board_y + 300:
                    col = (mouse_pos[0] - board_x) // CELL_SIZE
                    row = (mouse_pos[1] - board_y) // CELL_SIZE
                    
                    ship_name = controller.dragging_ship
                    orientation = controller.ship_orientations.get(ship_name, 0)
                    
                    if controller.can_place_ship(row, col, ship_name, orientation):
                        controller.place_ship(row, col, ship_name, orientation)
                        print(f"Placed {ship_name} at ({row}, {col})")
                    else:
                        print(f"Cannot place {ship_name} at ({row}, {col})")
                else:
                    print(f"Dropped {controller.dragging_ship} outside board")
                
                controller.dragging_ship = None
                controller.drag_start_pos = None