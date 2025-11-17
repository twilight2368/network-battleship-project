import pygame
import sys
import config
from components.draw_button import Button
from components.fields import Fields

def prepare_screen(screen, font):
    clock = pygame.time.Clock()
    running = True
    color_bg = config.BG_COLOR
    padding = 16

    # Hàm tạo nút Return
    def create_buttons(width, height):
        return Button(width // 2 - 100, height - 100, 200, 60, "Return", font)

    return_button = create_buttons(config.WIDTH, config.HEIGHT)

    while running:
        width, height = screen.get_size()
        screen.fill(color_bg)

        # Vùng layout (box)
        content_x = padding
        content_y = padding
        content_width = width - padding * 2
        content_height = height - padding * 2

        # ========== CẬP NHẬT FIELD ==========
        # Field chiếm tối đa 70% chiều cao của box
        max_field_size = min(content_width, int(content_height * 0.7))
        field_cell_size = max_field_size // 10

        # Tính kích thước thực của bảng
        field_width = field_cell_size * 10
        field_height = field_cell_size * 10

        # Canh giữa bảng theo cả 2 chiều trong box
        field_x = content_x + (content_width - field_width) // 6
        field_y = content_y + (content_height - field_height) // 2 - 40  # Dịch nhẹ lên trên 1 chút để nút Return có chỗ

        field = Fields(field_x , field_y, field_cell_size)

        # ========== NÚT RETURN ==========
        return_button = create_buttons(width, height)

        field.draw(screen)
        return_button.draw(screen)

        # ========== XỬ LÝ SỰ KIỆN ==========
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if return_button.is_clicked(event):
                return

        pygame.display.flip()
        clock.tick(60)
