# src/screens/lobby_screen.py

import pygame
from pygame.locals import *

# Import từ components và network
from src.components.gui_elements import GRAY, ORANGE, RED, WHITE, BLACK, BLUE, GREEN, draw_button, show_confirm_dialog, draw_input_box
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
    screen.blit(code_label, (450, 150))
    code_text = controller.font_large.render(state['lobby_code'], True, BLUE)
    screen.blit(code_text, (450, 190))
    
    # Thông báo chờ
    if not state.get("opponent_joined"): 
        wait_text = controller.font_medium.render("Waiting for opponent to join...", True, ORANGE)
        
    else:
        wait_text = controller.font_medium.render("Opponent found! Starting game...", True, GREEN)
       
        
    wait_rect = wait_text.get_rect(center=(600, 300))
    screen.blit(wait_text, wait_rect)

    # Nút quay lại
    if draw_button(screen, controller.font_small, 450, 450, 300, 50, "RETURN TO LOBBY", event_click=click_event_occurred):
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
    draw_input_box(screen, controller.font_small, 450, 250, 300, 50, input_active, input_text, placeholder="Enter room code...")
    
    # Nút JOIN LOBBY (Enter)
    if draw_button(screen, controller.font_small, 450, 320, 300, 50, "JOIN LOBBY", event_click=click_event_occurred):
        if len(controller.input_text) > 0:
            # Gửi yêu cầu join với mã nhập vào
            send_json(controller.sock, {"type": "JOIN_ROOM_REQ", "code": controller.input_text})
            # Sau khi gửi, chúng ta khóa nhập liệu và hiển thị thông báo chờ
            controller.input_active = False 
            controller.show_message(f"Attempting to join room: {controller.input_text}")
        else:
            controller.show_message("Please enter a lobby code.")
            
    # Nút quay lại
    if draw_button(screen, controller.font_small, 450, 450, 300, 50, "RETURN TO LOBBY", event_click=click_event_occurred):
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
        text_rect = queue_text.get_rect(center=(600, 300))
        screen.blit(queue_text, text_rect)
            
        if draw_button(screen, controller.font_small, 450, 400, 300, 50, "EXIT QUEUE", event_click=click_event_occurred):
            if show_confirm_dialog(screen, controller.clock, controller.font_small, controller.font_small, "Exit matchmaking queue?"):
                send_json(controller.sock, {"type": "QUEUE_EXIT_REQ"})
                controller.show_message("Exited queue.")

    # 3. Xử lý màn hình Lobby chính (Không Queue, không Custom Lobby)
    else:
        if controller.init_online_players:
            send_json(controller.sock, {"type": "ONLINE_PLAYERS_REQ"})
            controller.init_online_players = False
        # Draw online players list on the right side
        draw_online_players_list(controller, 0, 150, 300, 430, click_event_occurred)
        # ENTER QUEUE (Auto Matchmaking)
        if draw_button(screen, controller.font_small, 450, 180, 300, 50, "ENTER QUEUE", event_click=click_event_occurred):
            send_json(controller.sock, {"type": "QUEUE_ENTER_REQ"})
            controller.show_message("Requesting to enter queue...")
            #controller.start_ship_placement()
        
        # JOIN LOBBY (CUSTOM)
        if draw_button(screen, controller.font_small, 450, 250, 300, 50, "JOIN LOBBY", event_click=click_event_occurred):
            controller.join_lobby_mode()
            
        # HOST LOBBY (CUSTOM)
        if draw_button(screen, controller.font_small, 450, 320, 300, 50, "HOST LOBBY", event_click=click_event_occurred):
            controller.host_lobby_mode()
            
        # LEADERBOARD (CUSTOM)
        if draw_button(screen, controller.font_small, 450, 390, 300, 50, "LEADERBOARD", event_click=click_event_occurred):
            controller.show_leaderboard()
        
        # LOGOUT (Vị trí mới: 460)
        if draw_button(screen, controller.font_small, 450, 460, 300, 50, "LOGOUT", event_click=click_event_occurred):
            if show_confirm_dialog(screen, controller.clock, controller.font_small, controller.font_small, "Are you sure you want to logout?"):
                send_json(controller.sock, {"type": "LOGOUT"})
                state["is_login"] = False
                state["username"] = ""
                state["user_id"] = 0
                controller.show_message("Logged out!")


def draw_leaderboard_screen(controller, click_event_occurred):
    screen = controller.screen
    state = controller.state
    # Initialize scroll offset if not exists
    if not hasattr(controller, 'leaderboard_scroll_offset'):
        controller.leaderboard_scroll_offset = 0
    
    # Background
    if hasattr(controller, 'lobby_bg_img') and controller.lobby_bg_img:
        screen.blit(controller.lobby_bg_img, (0, 0))
    else:
        screen.fill(WHITE)
    
    # Title
    title = controller.font_large.render("LEADERBOARD", True, BLACK)
    title_rect = title.get_rect(center=(600, 50))
    screen.blit(title, title_rect)
    
    # Table layout constants
    table_x = 180
    table_width = 840
    
    # Table headers with better spacing
    headers = ["Rank", "Username", "ELO", "Wins", "Losses", "W/L Ratio"]
    header_x_positions = [200, 300, 480, 610, 730, 840]
    
    y_start = 120
    header_y = y_start
    
    # Draw header background
    pygame.draw.rect(screen, BLUE, (table_x, header_y - 5, table_width, 40))
    
    # Draw headers
    for i, header in enumerate(headers):
        header_text = controller.font_small.render(header, True, WHITE)
        screen.blit(header_text, (header_x_positions[i], header_y))
    
    # Create scrollable area
    scroll_area_y = header_y + 50
    scroll_area_height = 380  # Height of visible scroll area
    scroll_area_rect = pygame.Rect(table_x, scroll_area_y, table_width, scroll_area_height)
    
    # Create a surface for the scrollable content
    leaderboard = state.get("leaderboard", [])
    row_height = 45
    total_content_height = len(leaderboard) * row_height
    
    # Calculate max scroll offset
    max_scroll = max(0, total_content_height - scroll_area_height)
    controller.leaderboard_scroll_offset = max(0, min(controller.leaderboard_scroll_offset, max_scroll))
    
    # Create clipping rectangle for scrollable area
    clip_rect = screen.get_clip()
    screen.set_clip(scroll_area_rect)
    
    # Draw leaderboard data with scroll offset
    row_y = scroll_area_y - controller.leaderboard_scroll_offset
    
    for entry in leaderboard:
        # Only draw if row is visible in scroll area
        if row_y + row_height >= scroll_area_y and row_y < scroll_area_y + scroll_area_height:
            # Alternate row colors
            if entry["rank"] % 2 == 0:
                pygame.draw.rect(screen, (240, 240, 240), (table_x, row_y - 5, table_width, 40))
            else:
                pygame.draw.rect(screen, (255, 255, 255), (table_x, row_y - 5, table_width, 40))
            
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
    
    # Restore clip
    screen.set_clip(clip_rect)
    
    # Draw scrollbar if needed
    if total_content_height > scroll_area_height:
        scrollbar_x = table_x + table_width + 5
        scrollbar_y = scroll_area_y
        scrollbar_width = 15
        scrollbar_height = scroll_area_height
        
        # Scrollbar background
        pygame.draw.rect(screen, (200, 200, 200), (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height))
        
        # Scrollbar thumb
        thumb_height = max(30, int((scroll_area_height / total_content_height) * scrollbar_height))
        thumb_y = scrollbar_y + int((controller.leaderboard_scroll_offset / max_scroll) * (scrollbar_height - thumb_height))
        pygame.draw.rect(screen, BLUE, (scrollbar_x, thumb_y, scrollbar_width, thumb_height))
    
    # Back button (centered)
    if draw_button(screen, controller.font_small, 450, 560, 300, 50, "BACK TO LOBBY", event_click=click_event_occurred):
        controller.leaderboard_scroll_offset = 0  # Reset scroll
        controller.return_to_lobby()
        
def handle_leaderboard_scroll(event, controller):
    """Handle scroll events for leaderboard"""
    if event.type == MOUSEBUTTONDOWN:
        if event.button == 4:  # Scroll up
            controller.leaderboard_scroll_offset = max(0, controller.leaderboard_scroll_offset - 45)
        elif event.button == 5:  # Scroll down
            leaderboard = controller.state.get("leaderboard", [])
            row_height = 45
            total_content_height = len(leaderboard) * row_height
            scroll_area_height = 380
            max_scroll = max(0, total_content_height - scroll_area_height)
            controller.leaderboard_scroll_offset = min(max_scroll, controller.leaderboard_scroll_offset + 45)
            


# Add to src/screens/lobby_screen.py
def draw_online_players_list(controller, x, y, width, height, click_event_occurred):
    """
    Draw a scrollable list of online players with status indicators and refresh button.
    
    Args:
        controller: GameController instance
        x, y: Position of the list
        width, height: Dimensions of the list
        click_event_occurred: Whether a click event occurred this frame
    """
    screen = controller.screen
    state = controller.state
    
    # Initialize scroll offset if not exists
    if not hasattr(controller, 'online_players_scroll_offset'):
        controller.online_players_scroll_offset = 0
    
    # Title and Refresh Button
    title = controller.font_small.render("Online Players", True, BLACK)
    screen.blit(title, (x + 5, y - 35))
    
    # Refresh button (small button next to title)
    refresh_btn_x = x + width - 160
    refresh_btn_y = y - 30
    refresh_btn_width = 80
    refresh_btn_height = 25
    
    if draw_button(screen, controller.font_supersmall, refresh_btn_x, refresh_btn_y, 
                   refresh_btn_width, refresh_btn_height, "refresh", color=BLUE ,event_click=click_event_occurred):
        send_json(controller.sock, {"type": "ONLINE_PLAYERS_REQ"})
        controller.show_message("Refreshing online players...")
    
    # Get online players data
    online_players = state.get("online_players", [])
    
    if not online_players:
        no_players_text = controller.font_supersmall.render("No players online", True, BLACK)
        text_rect = no_players_text.get_rect(center=(x + width//2, y + height//2))
        screen.blit(no_players_text, text_rect)
        return
    
    # Scrollable area setup - REDUCED VALUES
    row_height = 25  # Reduced from 35
    padding = 5      # Reduced from 10
    total_content_height = len(online_players) * row_height
    scroll_area_height = height - (2 * padding)
    
    # Calculate max scroll offset
    max_scroll = max(0, total_content_height - scroll_area_height)
    controller.online_players_scroll_offset = max(0, min(controller.online_players_scroll_offset, max_scroll))
    
    # Create clipping rectangle for scrollable area
    scroll_area_rect = pygame.Rect(x + padding, y + padding, width - 2*padding - 15, scroll_area_height)
    clip_rect = screen.get_clip()
    screen.set_clip(scroll_area_rect)
    
    # Draw players with scroll offset
    row_y = y + padding - controller.online_players_scroll_offset
    
    for player in online_players:
        # Only draw if row is visible in scroll area
        if row_y + row_height >= y + padding and row_y < y + height - padding:
            # Determine status color
            if player.get("in_game", False):
                status_color = RED
            elif player.get("in_queue", False):
                status_color = ORANGE
            elif player.get("is_login", False):
                status_color = GREEN
            else:
                status_color = GRAY
            
            # Draw status indicator (circle) - slightly smaller
            circle_x = x + padding + 8  # Adjusted for smaller padding
            circle_y = row_y + row_height // 2
            pygame.draw.circle(screen, status_color, (circle_x, circle_y), 5)  # Reduced from 6
            pygame.draw.circle(screen, BLACK, (circle_x, circle_y), 5, 1)
            
            # Draw username with supersmall font
            username_text = controller.font_supersmall.render(player["username"], True, BLACK)
            screen.blit(username_text, (circle_x + 15, row_y + 6))  # Adjusted positioning
        
        row_y += row_height
    
    # Restore clip
    screen.set_clip(clip_rect)
    
    # Draw scrollbar if needed
    if total_content_height > scroll_area_height:
        scrollbar_x = x + width - padding - 8
        scrollbar_y = y + padding
        scrollbar_width = 6  # Slightly narrower
        scrollbar_height = scroll_area_height
        
        # Scrollbar background
        pygame.draw.rect(screen, LIGHT_GRAY, (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height))
        
        # Scrollbar thumb
        thumb_height = max(20, int((scroll_area_height / total_content_height) * scrollbar_height))
        thumb_y = scrollbar_y + int((controller.online_players_scroll_offset / max_scroll) * (scrollbar_height - thumb_height))
        pygame.draw.rect(screen, BLUE, (scrollbar_x, thumb_y, scrollbar_width, thumb_height))


def handle_online_players_scroll(event, controller):
    """Handle scroll events for online players list"""
    if event.type == MOUSEBUTTONDOWN:
        if event.button == 4:  # Scroll up
            controller.online_players_scroll_offset = max(0, controller.online_players_scroll_offset - 25)
        elif event.button == 5:  # Scroll down
            online_players = controller.state.get("online_players", [])
            row_height = 25  # Updated to match new row height
            total_content_height = len(online_players) * row_height
            scroll_area_height = 380  # Adjust based on your height parameter
            max_scroll = max(0, total_content_height - scroll_area_height)
            controller.online_players_scroll_offset = min(max_scroll, controller.online_players_scroll_offset + 25)