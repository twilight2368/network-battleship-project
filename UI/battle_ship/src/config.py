# config.py
import os

# Lấy thư mục gốc của project (nằm 1 cấp trên file config.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WIDTH = 800
HEIGHT = 600
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GRAY = (230, 230, 230)
BG_COLOR = (240, 240, 255)

IMAGE_PATH = os.path.join(BASE_DIR, "resources", "images")

def update_config(width=None, height=None, bg_color=None):
    import builtins
