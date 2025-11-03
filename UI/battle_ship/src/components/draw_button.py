import pygame

class Button:
    def __init__(self, x, y, w, h, text, font, bg_color=(200, 200, 200), hover_color=(230, 230, 230), text_color=(0, 0, 0)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color

    def draw(self, screen):
        mouse = pygame.mouse.get_pos()
        is_hovered = self.rect.collidepoint(mouse)
        color = self.hover_color if is_hovered else self.bg_color

        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2, border_radius=10)

        text_surface = self.font.render(self.text, True, self.text_color)
        screen.blit(
            text_surface,
            (
                self.rect.x + (self.rect.width - text_surface.get_width()) // 2,
                self.rect.y + (self.rect.height - text_surface.get_height()) // 2
            )
        )

    def is_clicked(self, event):
        """Trả về True nếu nút được nhấn"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False
