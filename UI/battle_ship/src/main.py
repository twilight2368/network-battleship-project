import pygame
import sys
import os
import importlib  # Dùng để reload config
import config  
from components.draw_button import Button
from ui.settings.setting import setting_screens
from ui.plays.choose_mode import choose_mode_screen

# ========== KHỞI TẠO PYGAME ==========
pygame.init()

# ========== CẤU HÌNH CỬA SỔ ==========
os.environ['SDL_VIDEO_CENTERED'] = '1'
screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
pygame.display.set_caption("BattleShip")

# ========== FONT & CLOCK ==========
font = pygame.font.Font(None, 40)
title_font = pygame.font.Font(None, 60)
clock = pygame.time.Clock()

# ========== HÀM CẬP NHẬT NÚT ==========
def update_buttons(neww=None, newh=None):
    if newh is None:
        newh = config.HEIGHT
    if neww is None:
        neww = config.WIDTH

    start_btn = Button(neww // 2 - 100, newh // 2 - 30, 200, 60, "Start Game", font)
    setting_btn = Button(neww // 2 - 100, newh // 2 + 50, 200, 60, "Settings", font)
    quit_btn = Button(neww // 2 - 100, newh // 2 + 130, 200, 60, "Quit", font)
    return start_btn, setting_btn, quit_btn

# ========== BIẾN TRẠNG THÁI ==========
start_button, setting_button, quit_button = update_buttons()
current_width, current_height = config.WIDTH, config.HEIGHT

# ========== VÒNG LẶP CHÍNH ==========
running = True

while running:
    screen.fill(config.BG_COLOR)

    # ===== TIÊU ĐỀ (động theo kích thước) =====
    title_text = title_font.render("MAIN MENU", True, (0, 0, 120))
    screen.blit(title_text, (current_width // 2 - title_text.get_width() // 2, 100))

    # ===== VẼ NÚT =====
    start_button.draw(screen)
    setting_button.draw(screen)
    quit_button.draw(screen)

    # ===== XỬ LÝ SỰ KIỆN =====
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if start_button.is_clicked(event):
            choose_mode_screen(screen, font)

        if setting_button.is_clicked(event):
            new_size = setting_screens(screen, font)
            importlib.reload(config)

            # Nếu có kích thước mới => cập nhật lại
            if new_size:
                w, h = new_size
                os.environ['SDL_VIDEO_CENTERED'] = '1'
                screen = pygame.display.set_mode((w, h))
                start_button, setting_button, quit_button = update_buttons(w, h)
                current_width, current_height = w, h  # Cập nhật kích thước hiện tại

        if quit_button.is_clicked(event):
            pygame.quit()
            sys.exit()

    pygame.display.flip()
    clock.tick(config.FPS)

pygame.quit()
sys.exit()
