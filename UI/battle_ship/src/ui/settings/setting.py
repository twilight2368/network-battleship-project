import pygame
import sys
import config  # Lấy thông số màn hình & màu nền từ file config.py
from components.draw_button import Button
from ui.settings.window_size import window_size_screen


def setting_screens(screen, font):
    clock = pygame.time.Clock()
    running = True
    new_size = None # Kích thước mới (nếu có)
    
    color_bg = config.BG_COLOR

    # Hàm tạo lại toàn bộ nút dựa theo kích thước hiện tại
    def create_buttons(width, height):
        window_size_btn = Button(width // 2 - 100, height // 2 - 30, 200, 60, "Window Size", font)
        return_btn = Button(width // 2 - 100, height // 2 + 50, 200, 60, "Return", font)
        return window_size_btn, return_btn

    window_size_button, return_button = create_buttons(config.WIDTH, config.HEIGHT)

    while running:
        # Cập nhật vị trí nút theo kích thước hiện tại của cửa sổ
        width, height = screen.get_size()
        window_size_button, return_button = create_buttons(width, height)

        screen.fill(color_bg)

        # Tiêu đề
        title_text = font.render("SETTINGS MENU", True, (0, 0, 100))
        screen.blit(title_text, (width // 2 - title_text.get_width() // 2, 100))

        # Vẽ nút
        window_size_button.draw(screen)
        return_button.draw(screen)

        # Xử lý sự kiện
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if window_size_button.is_clicked(event):
                new_size = window_size_screen(screen, font, width, height)
            if return_button.is_clicked(event):
                return new_size # Quay lại Main Menu

        pygame.display.flip()
        clock.tick(60)
