import pygame
import sys
import config
from components.draw_button import Button
from .prepare import prepare_screen

def choose_mode_screen(screen, font):
    clock = pygame.time.Clock()
    running = True

    color_bg = config.BG_COLOR

    # Hàm tạo lại toàn bộ nút dựa theo kích thước hiện tại
    def create_buttons(width, height):
        mode1_btn = Button(width // 2 - 100, height // 2 - 70, 200, 60, "Vs Human", font)
        mode2_btn = Button(width // 2 - 100, height // 2 + 10, 200, 60, "Vs Ai", font)
        return_btn = Button(width // 2 - 100, height // 2 + 90, 200, 60, "Return", font)
        return mode1_btn, mode2_btn, return_btn

    mode1_button, mode2_button, return_button = create_buttons(config.WIDTH, config.HEIGHT)

    while running:
        # Cập nhật vị trí nút theo kích thước hiện tại của cửa sổ
        width, height = screen.get_size()
        mode1_button, mode2_button, return_button = create_buttons(width, height)

        screen.fill(color_bg)

        # Tiêu đề
        title_text = font.render("CHOOSE MODE", True, (0, 0, 100))
        screen.blit(title_text, (width // 2 - title_text.get_width() // 2, 100))

        # Vẽ nút
        mode1_button.draw(screen)
        mode2_button.draw(screen)
        return_button.draw(screen)

        # Xử lý sự kiện
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if mode1_button.is_clicked(event):
                prepare_screen(screen, font)
            if mode2_button.is_clicked(event):
                prepare_screen(screen, font)
            if return_button.is_clicked(event):
                return
            
        pygame.display.flip()
        clock.tick(60)