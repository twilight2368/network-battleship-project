# src/screens/lobby_screen.py

import pygame
from pygame.locals import *

# Import từ components và network
from src.components.gui_elements import WHITE, BLACK, BLUE, draw_button, show_confirm_dialog
from src.network.networking import send_json

def draw_lobby_screen(controller):
    """Vẽ màn hình sảnh (lobby)."""
    screen = controller.screen
    state = controller.state
    
    screen.fill(WHITE)
    
    # Title
    title = controller.font_medium.render(f"Welcome, {state['username']}", True, BLACK)
    screen.blit(title, (50, 50))
    
    if state["in_queue"]:
        queue_text = controller.font_large.render("Waiting for opponent...", True, BLUE)
        text_rect = queue_text.get_rect(center=(450, 300))
        screen.blit(queue_text, text_rect)
        
        if draw_button(screen, controller.font_small, 300, 400, 300, 50, "EXIT QUEUE"):
            if show_confirm_dialog(screen, controller.clock, controller.font_small, controller.font_medium, "Exit matchmaking queue?"):
                send_json(controller.sock, {"type": "QUEUE_EXIT_REQ"})
                controller.show_message("Exited queue.")

    else:
        if draw_button(screen, controller.font_small, 300, 250, 300, 50, "ENTER QUEUE"):
            controller.start_ship_placement()
        
        if draw_button(screen, controller.font_small, 300, 320, 300, 50, "LOGOUT"):
            if show_confirm_dialog(screen, controller.clock, controller.font_small, controller.font_medium, "Are you sure you want to logout?"):
                send_json(controller.sock, {"type": "LOGOUT"})
                state["is_login"] = False
                state["username"] = ""
                state["user_id"] = 0
                controller.show_message("Logged out!")