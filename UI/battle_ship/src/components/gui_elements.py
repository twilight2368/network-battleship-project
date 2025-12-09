# src/components/gui_elements.py

import pygame
from pygame.locals import MOUSEBUTTONDOWN, QUIT

# Game/Board Constants
BOARD_SIZE = 10
CELL_SIZE = 30

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
BLUE = (0, 100, 200)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
# Ship data
SHIP_SIZES = {
    "carrier": 5,
    "battleship": 4,
    "cruiser": 3,
    "submarine": 3,
    "destroyer": 2
}

# src/components/gui_elements.py (Hàm draw_button đã sửa đổi)

def draw_button(screen, font_small, x, y, width, height, text, color=GRAY, event_click=False):
    """Vẽ nút và trả về True nếu nút được click.
    Tham số event_click là True nếu có sự kiện MOUSEBUTTONDOWN trong frame hiện tại."""
    mouse_pos = pygame.mouse.get_pos()
    # Loại bỏ việc sử dụng pygame.mouse.get_pressed()
    
    hover = x < mouse_pos[0] < x + width and y < mouse_pos[1] < y + height
    
    button_color = LIGHT_GRAY if hover else color
    pygame.draw.rect(screen, button_color, (x, y, width, height))
    pygame.draw.rect(screen, BLACK, (x, y, width, height), 2)
    
    text_surf = font_small.render(text, True, BLACK)
    text_rect = text_surf.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(text_surf, text_rect)
    
    # LOGIC MỚI: Chỉ kiểm tra hover VÀ sự kiện click chuột (MOUSEBUTTONDOWN) 
    is_clicked = hover and event_click 
    
    if is_clicked:
        print(f"Đang bấm nút: {text}") # Giữ lại logic in ra tên nút
    
    return is_clicked

def draw_input_box(screen, font_small, x, y, width, height, input_active, input_text, placeholder=""):
    """Vẽ hộp nhập liệu."""
    color = BLUE if input_active else GRAY
    pygame.draw.rect(screen, WHITE, (x, y, width, height))
    pygame.draw.rect(screen, color, (x, y, width, height), 2)
    
    display_text = input_text if input_text else placeholder
    text_color = BLACK if input_text else GRAY
    text_surf = font_small.render(display_text, True, text_color)
    screen.blit(text_surf, (x + 5, y + 10))

def show_confirm_dialog(screen, clock, font_small, font_medium, text):
    """Hiển thị dialog xác nhận. Trả về True nếu chọn Yes."""
    dialog_width = 400
    dialog_height = 200
    x = (900 - dialog_width) // 2
    y = (700 - dialog_height) // 2

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            if event.type == MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if x+50 <= mx <= x+170 and y+120 <= my <= y+170: # Yes
                    return True
                if x+230 <= mx <= x+350 and y+120 <= my <= y+170: # No
                    return False
        
        
        # ... (Phần vẽ dialog giữ nguyên như trong file gốc)
        overlay = pygame.Surface((900, 700))
        overlay.set_alpha(10)
        overlay.fill((105,105,105))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, WHITE, (x, y, dialog_width, dialog_height), border_radius=10)
        pygame.draw.rect(screen, BLACK, (x, y, dialog_width, dialog_height), 3, border_radius=10)

        text_surf = font_medium.render(text, True, BLACK)
        screen.blit(text_surf, (x + 40, y + 40))

        pygame.draw.rect(screen, (100, 200, 100), (x+50, y+120, 120, 50), border_radius=8)
        yes_text = font_small.render("YES", True, BLACK)
        screen.blit(yes_text, (x+95, y+135))

        pygame.draw.rect(screen, (200, 100, 100), (x+230, y+120, 120, 50), border_radius=8)
        no_text = font_small.render("NO", True, BLACK)
        screen.blit(no_text, (x+275, y+135))

        pygame.display.update()
        clock.tick(60)

def draw_password_input_box(
        screen, font_small, x, y, width, height, 
        input_active, input_text, show_password, event_click
    ):
    """
    Draw a password input box with show/hide toggle button.
    - show_password: bool that determines if password is visible
    - event_click: True if a MOUSEBUTTONDOWN occurred in this frame
    Returns: (eye_clicked: bool)
    """

    # ==== MAIN INPUT BOX ====
    color = BLUE if input_active else GRAY

    pygame.draw.rect(screen, WHITE, (x, y, width, height))
    pygame.draw.rect(screen, color, (x, y, width, height), 2)

    # Display text
    if show_password:
        display_text = input_text
    else:
        display_text = "*" * len(input_text)

    text_surf = font_small.render(display_text, True, BLACK)
    screen.blit(text_surf, (x + 5, y + 10))

    # ==== EYE BUTTON (show/hide) ====
    eye_size = height - 10
    eye_x = x + width - (eye_size + 5)
    eye_y = y + 5

    # Eye button rectangle
    pygame.draw.rect(screen, LIGHT_GRAY, (eye_x, eye_y, eye_size, eye_size))
    pygame.draw.rect(screen, BLACK, (eye_x, eye_y, eye_size, eye_size), 1)

    # Eye icon text (simple)
    icon_text = "o" if show_password else "-"
    icon_surf = font_small.render(icon_text, True, BLACK)
    icon_rect = icon_surf.get_rect(center=(eye_x + eye_size//2, eye_y + eye_size//2))
    screen.blit(icon_surf, icon_rect)

    # Detect eye button click
    mouse_pos = pygame.mouse.get_pos()
    hover_eye = eye_x <= mouse_pos[0] <= eye_x + eye_size and eye_y <= mouse_pos[1] <= eye_y + eye_size

    eye_clicked = hover_eye and event_click

    return eye_clicked