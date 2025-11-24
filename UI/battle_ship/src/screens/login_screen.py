# src/screens/login_screen.py

import pygame
from pygame.locals import *

# Import từ components và network
from src.components.gui_elements import WHITE, BLACK, draw_button, draw_input_box
from src.network.networking import send_json

def draw_login_screen(controller):
    """Vẽ màn hình đăng nhập/đăng ký."""
    screen = controller.screen
    
    screen.fill(WHITE)
    
    # Title
    title = controller.font_large.render("BATTLESHIP", True, BLACK)
    title_rect = title.get_rect(center=(450, 100))
    screen.blit(title, title_rect)
    
    # Buttons
    if draw_button(screen, controller.font_small, 300, 250, 300, 50, "REGISTER"):
        controller.input_mode = "register_username"
        controller.input_active = True
        controller.input_text = ""
    
    if draw_button(screen, controller.font_small, 300, 320, 300, 50, "LOGIN"):
        controller.input_mode = "login_username"
        controller.input_active = True
        controller.input_text = ""
    
    if draw_button(screen, controller.font_small, 300, 390, 300, 50, "EXIT"):
        controller.running = False
    
    # Handle input boxes
    if controller.input_mode in ["register_username", "login_username"]:
        prompt = "Enter username:"
        screen.blit(controller.font_small.render(prompt, True, BLACK), (300, 480))
        draw_input_box(screen, controller.font_small, 300, 510, 300, 40, controller.input_active, controller.input_text)
    elif controller.input_mode in ["register_password", "login_password"]:
        prompt = "Enter password:"
        screen.blit(controller.font_small.render(prompt, True, BLACK), (300, 480))
        draw_input_box(screen, controller.font_small, 300, 510, 300, 40, controller.input_active, controller.input_text)

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