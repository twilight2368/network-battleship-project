# src/screens/game_screen.py

import pygame
from pygame.locals import *

# Import từ components và network
from src.components.gui_elements import BOARD_SIZE, CELL_SIZE, WHITE, BLACK, RED, GREEN, YELLOW, draw_button
from src.network.networking import send_json

# --- DRAWING LOGIC ---

def draw_board(controller, x_offset, y_offset, board, show_ships=True, color_number = BLACK):
    """Vẽ board game. (Rút gọn)"""
    screen = controller.screen
    # ... (Logic draw_board giữ nguyên như trong file gốc, sử dụng controller.water_img, controller.ship_images)
    
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

def draw_ship_placement_screen(controller, clicked_events_occur):
    """Vẽ màn hình đặt tàu."""
    screen = controller.screen
    screen.fill(WHITE)
    
    # Draw background image if available
    if hasattr(controller, 'in_queue_bg_img') and controller.in_queue_bg_img:
        screen.blit(controller.in_queue_bg_img, (0, 0))
    else:
        screen.fill(WHITE)
     # Semi-transparent overlay for better text visibility
    overlay = pygame.Surface((900, 700))
    overlay.set_alpha(100)  # Adjust transparency (0-255)
    overlay.fill(WHITE)
    screen.blit(overlay, (0, 0))
    
    # Title và Instructions 
    if controller.current_ship_index < len(controller.ships_to_place):
        ship_name = controller.ships_to_place[controller.current_ship_index]
        title = controller.font_medium.render(
            f"Place {ship_name.upper()} (size: {controller.ship_sizes[ship_name]})", True, BLACK)
        screen.blit(title, (50, 30))
        orient_text = "VERTICAL" if controller.ship_orientation == 0 else "HORIZONTAL"
        inst1 = controller.font_small.render(f"Orientation: {orient_text} (Press R to rotate)", True, BLACK)
        inst2 = controller.font_small.render("Click on board to place ship", True, BLACK)
        screen.blit(inst1, (50, 70))
        screen.blit(inst2, (50, 95))

         # Random Place Button - only show when placing ships
        if draw_button(screen, controller.font_small, 50, 130, 180, 40, 
                      "Random Place All", YELLOW, clicked_events_occur):
            controller.random_place_ships()
    # Draw board
    board_x, board_y = 300, 150
    draw_board(controller, board_x, board_y, controller.state["my_board"], show_ships=True)
    
    # Draw preview - UPDATE match start
    if controller.current_ship_index >= len(controller.ships_to_place):
        title = controller.font_large.render("Ships placed!", True, GREEN)
        title_rect = title.get_rect(center=(450, 40))
        screen.blit(title, title_rect)
        
        wait_text = controller.font_medium.render("Waiting for opponent to place ships...", True, BLACK)
        wait_rect = wait_text.get_rect(center=(450, 90))
        screen.blit(wait_text, wait_rect)
    else:
        mouse_pos = pygame.mouse.get_pos()
        if board_x <= mouse_pos[0] < board_x + 300 and board_y <= mouse_pos[1] < board_y + 300:
            col = (mouse_pos[0] - board_x) // CELL_SIZE
            row = (mouse_pos[1] - board_y) // CELL_SIZE
            
            ship_name = controller.ships_to_place[controller.current_ship_index]
            if controller.can_place_ship(row, col, ship_name):
                size = controller.ship_sizes[ship_name]
                for i in range(size):
                    r = row + i if controller.ship_orientation == 0 else row
                    c = col + i if controller.ship_orientation == 1 else col
                    cell_x = board_x + c * CELL_SIZE
                    cell_y = board_y + r * CELL_SIZE
                    
                    s = pygame.Surface((CELL_SIZE - 4, CELL_SIZE - 4))
                    s.set_alpha(128)
                    s.fill(GREEN)
                    screen.blit(s, (cell_x + 2, cell_y + 2))

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
    
    # Title/Turn Indicator (Giữ nguyên)
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
        # Rotate ship during placement
        if controller.placing_ships and event.key == K_r:
            controller.ship_orientation = 1 - controller.ship_orientation
    
    elif event.type == MOUSEBUTTONDOWN:
        if event.button == 1:  # Left click
            mouse_pos = pygame.mouse.get_pos()
            
            # Ship placement
            if controller.placing_ships and controller.current_ship_index < len(controller.ships_to_place):
                board_x, board_y = 300, 150
                if board_x <= mouse_pos[0] < board_x + 300 and board_y <= mouse_pos[1] < board_y + 300:
                    col = (mouse_pos[0] - board_x) // CELL_SIZE
                    row = (mouse_pos[1] - board_y) // CELL_SIZE
                    
                    ship_name = controller.ships_to_place[controller.current_ship_index]
                    if controller.can_place_ship(row, col, ship_name):
                        controller.place_ship(row, col, ship_name)
            
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