# src/screens/login_screen.py

import pygame
from pygame.locals import *
import os

# Import từ components và network
from src.components.gui_elements import WHITE, BLACK, draw_button, draw_input_box, draw_password_input_box
from src.network.networking import send_json

def draw_login_screen(controller, clicked_events_occur):
    """Vẽ màn hình đăng nhập/đăng ký."""
    screen = controller.screen
    
    # Draw background image if available
    if hasattr(controller, 'login_bg_img') and controller.login_bg_img:
        screen.blit(controller.login_bg_img, (0, 0))
    else:
        screen.fill(WHITE)
    
    # Semi-transparent overlay for better text visibility
    overlay = pygame.Surface((900, 700))
    overlay.set_alpha(100)  # Adjust transparency (0-255)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    
    # Title with shadow effect
    title_shadow = controller.font_large.render("BATTLESHIP", True, BLACK)
    title_shadow_rect = title_shadow.get_rect(center=(452, 102))
    screen.blit(title_shadow, title_shadow_rect)
    
    title = controller.font_large.render("BATTLESHIP", True, (255, 215, 0))  # Gold color
    title_rect = title.get_rect(center=(450, 100))
    screen.blit(title, title_rect)
    
    # Buttons
    if draw_button(screen, controller.font_small, 300, 250, 300, 50, "REGISTER", event_click=clicked_events_occur):
        controller.input_mode = "register_username"
        controller.input_active = True
        controller.input_text = ""
    
    if draw_button(screen, controller.font_small, 300, 320, 300, 50, "LOGIN", event_click=clicked_events_occur):
        controller.input_mode = "login_username"
        controller.input_active = True
        controller.input_text = ""
    
    if draw_button(screen, controller.font_small, 300, 390, 300, 50, "EXIT", event_click=clicked_events_occur):
        controller.running = False
    
    # Handle input boxes
    if controller.input_mode in ["register_username", "login_username"]:
        prompt = "Enter username:"
        screen.blit(controller.font_small.render(prompt, True, WHITE), (300, 480))
        draw_input_box(screen, controller.font_small, 300, 510, 300, 40, controller.input_active, controller.input_text)
    elif controller.input_mode in ["register_password", "login_password"]:
        prompt = "Enter password:"
        screen.blit(controller.font_small.render(prompt, True, WHITE), (300, 480))
        
        eye_clicked = draw_password_input_box(
            screen,
            controller.font_small,
            300, 510, 300, 40,
            controller.input_active,
            controller.input_text,
            controller.show_password,     # NEW — controls visibility
            clicked_events_occur          # NEW — click detection
        )

        # Toggle visibility if clicked
        if eye_clicked:
            controller.show_password = not controller.show_password

def handle_login_events(event, controller):
    """Xử lý sự kiện bàn phím cho màn hình đăng nhập/đăng ký."""
    if event.type == KEYDOWN and controller.input_active:
        if event.key == K_RETURN:
            # Logic submit input (Giữ nguyên)
            if controller.input_mode == "register_username":
                controller.username_temp = controller.input_text
                controller.input_text = ""
                controller.input_mode = "register_password"
            elif controller.input_mode == "register_password":
                send_json(controller.sock, {
                    "type": "REGISTER_REQ",
                    "username": controller.username_temp,
                    "password": controller.input_text
                })
                controller.input_text = ""
                controller.input_mode = None
                controller.input_active = False
            elif controller.input_mode == "login_username":
                controller.username_temp = controller.input_text
                controller.input_text = ""
                controller.input_mode = "login_password"
            elif controller.input_mode == "login_password":
                send_json(controller.sock, {
                    "type": "LOGIN_REQ",
                    "username": controller.username_temp,
                    "password": controller.input_text
                })
                controller.input_text = ""
                controller.input_mode = None
                controller.input_active = False
        elif event.key == K_BACKSPACE:
            controller.input_text = controller.input_text[:-1]
        elif event.key == K_ESCAPE:
            controller.input_text = ""
            controller.input_mode = None
            controller.input_active = False
        else:
            if len(controller.input_text) < 20:
                controller.input_text += event.unicode