import pygame
from pygame.locals import *

# Import từ components và network
from src.components.gui_elements import (
    WHITE, BLACK,
    draw_button,
    draw_input_box,
    draw_password_input_box
)
from src.network.networking import send_json


SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700

CENTER_X = SCREEN_WIDTH // 2
BUTTON_WIDTH = 300
BUTTON_HEIGHT = 50
BUTTON_X = CENTER_X - BUTTON_WIDTH // 2

INPUT_WIDTH = 300
INPUT_HEIGHT = 40
INPUT_X = CENTER_X - INPUT_WIDTH // 2


def draw_login_screen(controller, clicked_events_occur):
    """Vẽ màn hình đăng nhập/đăng ký."""
    screen = controller.screen

    # Background
    if hasattr(controller, 'login_bg_img') and controller.login_bg_img:
        screen.blit(controller.login_bg_img, (0, 0))
    else:
        screen.fill(WHITE)

    # Semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(100)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # ===== TITLE =====
    title_shadow = controller.font_large.render("BATTLESHIP", True, BLACK)
    title_shadow_rect = title_shadow.get_rect(center=(CENTER_X + 2, 102))
    screen.blit(title_shadow, title_shadow_rect)

    title = controller.font_large.render("BATTLESHIP", True, (255, 215, 0))
    title_rect = title.get_rect(center=(CENTER_X, 100))
    screen.blit(title, title_rect)

    # ===== BUTTONS =====
    if draw_button(
        screen, controller.font_small,
        BUTTON_X, 260, BUTTON_WIDTH, BUTTON_HEIGHT,
        "REGISTER", event_click=clicked_events_occur
    ):
        controller.input_mode = "register_username"
        controller.input_active = True
        controller.input_text = ""

    if draw_button(
        screen, controller.font_small,
        BUTTON_X, 330, BUTTON_WIDTH, BUTTON_HEIGHT,
        "LOGIN", event_click=clicked_events_occur
    ):
        controller.input_mode = "login_username"
        controller.input_active = True
        controller.input_text = ""

    if draw_button(
        screen, controller.font_small,
        BUTTON_X, 400, BUTTON_WIDTH, BUTTON_HEIGHT,
        "EXIT", event_click=clicked_events_occur
    ):
        controller.running = False

    # ===== INPUT BOXES =====
    if controller.input_mode in ["register_username", "login_username"]:
        prompt = "Enter username:"
        screen.blit(
            controller.font_small.render(prompt, True, WHITE),
            (INPUT_X, 480)
        )

        draw_input_box(
            screen,
            controller.font_small,
            INPUT_X, 510,
            INPUT_WIDTH, INPUT_HEIGHT,
            controller.input_active,
            controller.input_text
        )

    elif controller.input_mode in ["register_password", "login_password"]:
        prompt = "Enter password:"
        screen.blit(
            controller.font_small.render(prompt, True, WHITE),
            (INPUT_X, 480)
        )

        eye_clicked = draw_password_input_box(
            screen,
            controller.font_small,
            INPUT_X, 510,
            INPUT_WIDTH, INPUT_HEIGHT,
            controller.input_active,
            controller.input_text,
            controller.show_password,
            clicked_events_occur
        )

        if eye_clicked:
            controller.show_password = not controller.show_password


def handle_login_events(event, controller):
    """Xử lý sự kiện bàn phím cho màn hình đăng nhập/đăng ký."""
    if event.type == KEYDOWN and controller.input_active:

        if event.key == K_RETURN:
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
