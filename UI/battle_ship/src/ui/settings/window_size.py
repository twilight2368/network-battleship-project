import pygame
import sys
import os
import config
from components.draw_button import Button

def window_size_screen(screen, font, width, height, color_bg=(240, 240, 255)):
    clock = pygame.time.Clock()
    running = True
    selected_size = None # Giá trị trả kích thước mới (nếu có)

    window_sizes = [(800, 600), (1024, 768), (1280, 720), (1366, 768)]

    def create_buttons(w, h):
        btns = []
        for i, (bw, bh) in enumerate(window_sizes):
            btn = Button(w // 2 - 100, 200 + i * 70, 200, 60, f"{bw} x {bh}", font)
            btns.append((btn, (bw, bh)))
        return btns

    buttons = create_buttons(width, height)
    back_button = Button(20, 20, 120, 50, "Return", font)

    while running:
        screen.fill(color_bg)

        title_text = font.render("WINDOW SIZE", True, (0, 0, 100))
        screen.blit(title_text, (screen.get_width() // 2 - title_text.get_width() // 2, 80))

        for btn, _ in buttons:
            btn.draw(screen)
        back_button.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Nếu nhấn chọn kích thước mới
            for btn, (w, h) in buttons:
                if btn.is_clicked(event):
                    os.environ["SDL_VIDEO_CENTERED"] = "1"
                    screen = pygame.display.set_mode((w, h))
                    config.update_config(width=w, height=h)
                    buttons = create_buttons(w, h)
                    back_button.rect.topleft = (20, 20)
                    width, height = w, h
                    selected_size = (w, h)  # Lưu lại kích thước mới

            # Nút quay lại
            if back_button.is_clicked(event):
                return selected_size  # Trả về kích thước mới (nếu có)

        pygame.display.flip()
        clock.tick(60)
