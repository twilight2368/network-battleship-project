# src/screens/lobby_screen.py

import pygame
from pygame.locals import *

# Import từ components và network
from src.components.gui_elements import ORANGE, WHITE, BLACK, BLUE, GREEN, draw_button, show_confirm_dialog, draw_input_box
from src.network.networking import send_json


def draw_host_screen(controller, click_event_occurred):
    screen = controller.screen
    state = controller.state
    
    if hasattr(controller, 'room_bg_img') and controller.room_bg_img:
        screen.blit(controller.room_bg_img, (0, 0))
    else:
        screen.fill(WHITE)
    
    title = controller.font_medium.render("Hosting Custom Game", True, BLACK)
    screen.blit(title, (50, 50))

    # Hiển thị mã phòng
    code_label = controller.font_medium.render("Room Code:", True, BLACK)
    screen.blit(code_label, (300, 150))
    code_text = controller.font_large.render(state['lobby_code'], True, BLUE)
    screen.blit(code_text, (300, 190))
    
    # Thông báo chờ
    if not state.get("opponent_joined"): 
        wait_text = controller.font_medium.render("Waiting for opponent to join...", True, ORANGE)
        
    else:
        wait_text = controller.font_medium.render("Opponent found! Starting game...", True, GREEN)
       
        
    wait_rect = wait_text.get_rect(center=(450, 300))
    screen.blit(wait_text, wait_rect)

    # Nút quay lại
    if draw_button(screen, controller.font_small, 300, 450, 300, 50, "RETURN TO LOBBY", event_click=click_event_occurred):
        if show_confirm_dialog(screen, controller.clock, controller.font_small, controller.font_small, "Close lobby and return?"):
            controller.return_to_lobby()
            
def draw_join_screen(controller, click_event_occurred):
    screen = controller.screen
    state = controller.state
    
    if hasattr(controller, 'room_bg_img') and controller.room_bg_img:
        screen.blit(controller.room_bg_img, (0, 0))
    else:
        screen.fill(WHITE)
    
    title = controller.font_medium.render("Join Custom Game", True, BLACK)
    screen.blit(title, (50, 50))

    # Vùng nhập mã phòng
    input_text = controller.input_text
    input_active = controller.input_mode == "join_lobby_code"

    # Input box
    draw_input_box(screen, controller.font_small, 300, 250, 300, 50, input_active, input_text, placeholder="Enter room code...")
    
    # Nút JOIN LOBBY (Enter)
    if draw_button(screen, controller.font_small, 300, 320, 300, 50, "JOIN LOBBY", event_click=click_event_occurred):
        if len(controller.input_text) > 0:
            # Gửi yêu cầu join với mã nhập vào
            send_json(controller.sock, {"type": "JOIN_ROOM_REQ", "code": controller.input_text})
            # Sau khi gửi, chúng ta khóa nhập liệu và hiển thị thông báo chờ
            controller.input_active = False 
            controller.show_message(f"Attempting to join room: {controller.input_text}")
        else:
            controller.show_message("Please enter a lobby code.")
            
    # Nút quay lại
    if draw_button(screen, controller.font_small, 300, 450, 300, 50, "RETURN TO LOBBY", event_click=click_event_occurred):
        controller.return_to_lobby()

def handle_join_lobby_events(event, controller):
    if controller.input_mode == "join_lobby_code" and controller.input_active:
        if event.type == KEYDOWN:
            if event.key == K_RETURN:
                if len(controller.input_text) > 0:
                    send_json(controller.sock, {"type": "JOIN_ROOM_REQ", "code": controller.input_text})
                    controller.show_message("Attempting to join...")
                else:
                    controller.show_message("Please enter a lobby code.")
            elif event.key == K_BACKSPACE:
                controller.input_text = controller.input_text[:-1]
            elif event.key == K_ESCAPE:
                controller.input_text = ""
                controller.input_mode = None
                controller.input_active = False
                controller.show_message("Cancelled input.")
            else:
                if len(controller.input_text) < 5 and event.unicode.isalnum(): # Giới hạn mã phòng 5 ký tự và chỉ cho phép chữ/số
                    controller.input_text += event.unicode
                    
def draw_lobby_screen(controller, click_event_occurred):
    """Vẽ màn hình sảnh (lobby) và các trạng thái phụ."""
    state = controller.state
    
    
    # 1. Xử lý màn hình Custom Lobby
    if state.get("in_custom_lobby"): 
        if state["is_host"]:
            draw_host_screen(controller, click_event_occurred)
        else:
            draw_join_screen(controller, click_event_occurred)
        return
    
    if state["in_leaderboard"]:
        draw_leaderboard_screen(controller, click_event_occurred)
        return
    # 2. Xử lý màn hình Queue (Giữ nguyên)
    screen = controller.screen
    
    # Draw background image if available
    if hasattr(controller, 'lobby_bg_img') and controller.lobby_bg_img:
        screen.blit(controller.lobby_bg_img, (0, 0))
    else:
        screen.fill(WHITE)
        
    # Title
    title = controller.font_large.render(f"Welcome, {state['username']}", True, BLACK)
    screen.blit(title, (50, 50))
    
    if state["in_queue"]:
        if hasattr(controller, 'in_queue_bg_img') and controller.in_queue_bg_img:
            screen.blit(controller.in_queue_bg_img, (0, 0))
        else:
            screen.fill(WHITE)
        
        queue_text = controller.font_large.render("Waiting for opponent...", True, ORANGE)
        text_rect = queue_text.get_rect(center=(450, 300))
        screen.blit(queue_text, text_rect)
            
        if draw_button(screen, controller.font_small, 300, 400, 300, 50, "EXIT QUEUE", event_click=click_event_occurred):
            if show_confirm_dialog(screen, controller.clock, controller.font_small, controller.font_small, "Exit matchmaking queue?"):
                send_json(controller.sock, {"type": "QUEUE_EXIT_REQ"})
                controller.show_message("Exited queue.")

    # 3. Xử lý màn hình Lobby chính (Không Queue, không Custom Lobby)
    else:
        # ENTER QUEUE (Auto Matchmaking)
        if draw_button(screen, controller.font_small, 300, 180, 300, 50, "ENTER QUEUE", event_click=click_event_occurred):
            send_json(controller.sock, {"type": "QUEUE_ENTER_REQ"})
            controller.show_message("Requesting to enter queue...")
            #controller.start_ship_placement()
        
        # JOIN LOBBY (CUSTOM)
        if draw_button(screen, controller.font_small, 300, 250, 300, 50, "JOIN LOBBY", event_click=click_event_occurred):
            controller.join_lobby_mode()
            
        # HOST LOBBY (CUSTOM)
        if draw_button(screen, controller.font_small, 300, 320, 300, 50, "HOST LOBBY", event_click=click_event_occurred):
            controller.host_lobby_mode()
            
        # LEADERBOARD (CUSTOM)
        if draw_button(screen, controller.font_small, 300, 390, 300, 50, "LEADERBOARD", event_click=click_event_occurred):
            controller.show_leaderboard()
        
        # LOGOUT (Vị trí mới: 460)
        if draw_button(screen, controller.font_small, 300,460, 300, 50, "LOGOUT", event_click=click_event_occurred):
            if show_confirm_dialog(screen, controller.clock, controller.font_small, controller.font_small, "Are you sure you want to logout?"):
                send_json(controller.sock, {"type": "LOGOUT"})
                state["is_login"] = False
                state["username"] = ""
                state["user_id"] = 0
                controller.show_message("Logged out!")


def draw_leaderboard_screen(controller, click_event_occurred):
    screen = controller.screen
    state = controller.state
    
    # Background
    if hasattr(controller, 'lobby_bg_img') and controller.lobby_bg_img:
        screen.blit(controller.lobby_bg_img, (0, 0))
    else:
        screen.fill(WHITE)
    
    # Title
    title = controller.font_large.render("LEADERBOARD", True, BLACK)
    title_rect = title.get_rect(center=(450, 50))
    screen.blit(title, title_rect)
    
    # Table headers
    headers = ["Rank", "Username", "ELO", "Wins", "Losses", "W/L Ratio"]
    header_x_positions = [150, 280, 430, 550, 660, 770]
    
    y_start = 120
    header_y = y_start
    
    # Draw header background
    pygame.draw.rect(screen, BLUE, (130, header_y - 5, 640, 40))
    
    # Draw headers
    for i, header in enumerate(headers):
        header_text = controller.font_small.render(header, True, WHITE)
        screen.blit(header_text, (header_x_positions[i], header_y))
    
    # Draw leaderboard data
    leaderboard = state.get("leaderboard", [])
    row_height = 45
    row_y = header_y + 50
    
    for entry in leaderboard[:10]:  # Show top 10
        # Alternate row colors
        if entry["rank"] % 2 == 0:
            pygame.draw.rect(screen, (240, 240, 240), (130, row_y - 5, 640, 40))
        else:
            pygame.draw.rect(screen, (255, 255, 255), (130, row_y - 5, 640, 40))
        
        # Calculate W/L ratio
        total_games = entry["wins"] + entry["losses"]
        if total_games > 0:
            wl_ratio = f"{(entry['wins'] / total_games * 100):.1f}%"
        else:
            wl_ratio = "N/A"
        
        # Highlight current user
        color = GREEN if entry["username"] == state.get("username") else BLACK
        
        # Draw data
        rank_text = controller.font_small.render(f"#{entry['rank']}", True, color)
        username_text = controller.font_small.render(entry["username"], True, color)
        elo_text = controller.font_small.render(str(entry["elo"]), True, color)
        wins_text = controller.font_small.render(str(entry["wins"]), True, color)
        losses_text = controller.font_small.render(str(entry["losses"]), True, color)
        ratio_text = controller.font_small.render(wl_ratio, True, color)
        
        screen.blit(rank_text, (header_x_positions[0], row_y))
        screen.blit(username_text, (header_x_positions[1], row_y))
        screen.blit(elo_text, (header_x_positions[2], row_y))
        screen.blit(wins_text, (header_x_positions[3], row_y))
        screen.blit(losses_text, (header_x_positions[4], row_y))
        screen.blit(ratio_text, (header_x_positions[5], row_y))
        
        row_y += row_height
    
    # Back button
    if draw_button(screen, controller.font_small, 300, 550, 300, 50, "BACK TO LOBBY", event_click=click_event_occurred):
        controller.return_to_lobby()