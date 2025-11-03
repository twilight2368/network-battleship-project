import pygame

class Fields:
    def __init__(self, x, y, cell_size=40):
        self.x = x  # Góc trái trên của bảng
        self.y = y
        self.cell_size = cell_size
        self.rows = 10
        self.cols = 10
        self.font = pygame.font.Font(None, int(cell_size * 0.5))
        self.header_font = pygame.font.Font(None, int(cell_size * 0.6))

    def draw(self, screen):
        # ===== MÀU =====
        line_color = (0, 0, 0)
        text_color = (20, 20, 80)
        bg_color = (230, 230, 250)

        # ===== VẼ NỀN BẢNG =====
        pygame.draw.rect(
            screen, bg_color,
            (self.x, self.y, self.cols * self.cell_size, self.rows * self.cell_size)
        )

        # ===== VẼ LƯỚI Ô =====
        for row in range(self.rows):
            for col in range(self.cols):
                rect = pygame.Rect(
                    self.x + col * self.cell_size,
                    self.y + row * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )
                pygame.draw.rect(screen, line_color, rect, 1)

        # ===== VẼ NHÃN HÀNG (1–10) =====
        for i in range(self.rows):
            label = str(i + 1)
            text = self.header_font.render(label, True, text_color)
            text_rect = text.get_rect(
                center=(self.x - self.cell_size * 0.4,
                        self.y + i * self.cell_size + self.cell_size / 2)
            )
            screen.blit(text, text_rect)

        # ===== VẼ NHÃN CỘT (A–J) =====
        for j in range(self.cols):
            label = chr(65 + j)
            text = self.header_font.render(label, True, text_color)
            text_rect = text.get_rect(
                center=(self.x + j * self.cell_size + self.cell_size / 2,
                        self.y - self.cell_size * 0.4)
            )
            screen.blit(text, text_rect)
