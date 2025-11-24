# src/main.py

import sys
import os
import pygame
from pygame.locals import *

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import modules
from src.controllers.game_controller import GameController
from src.screens.login_screen import draw_login_screen, handle_login_events
from src.screens.lobby_screen import draw_lobby_screen
from src.screens.game_screen import draw_ship_placement_screen, draw_game_screen, handle_game_events
from src.components.gui_elements import WHITE, BLACK, RED
from src.network.networking import DEFAULT_HOST, DEFAULT_PORT


def run_game(controller):
    """Vòng lặp game chính."""
    pygame.init()
    controller.screen = pygame.display.set_mode((900, 700))
    pygame.display.set_caption("Battleship Game")
    controller.clock = pygame.time.Clock()
    
    # Load fonts
    controller.font_large = pygame.font.Font(None, 48)
    controller.font_medium = pygame.font.Font(None, 32)
    controller.font_small = pygame.font.Font(None, 24)
    
    # Load assets
    controller.load_images()
    
    # Connect and start network thread
    if not controller.connect_server():
        pygame.quit()
        return

    controller.start_receiver_thread()
    
    while controller.running:
        clicked_events_occur = False
        # 1. Handle Events
        for event in pygame.event.get():
            if event.type == QUIT:
                controller.running = False
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                clicked_events_occur = True
            
            if not controller.state["is_login"]:
                handle_login_events(event, controller)
            elif controller.state["in_game"] or controller.placing_ships:
                handle_game_events(event, controller)

        # 2. Draw Screen
        if not controller.state["is_login"]:
            draw_login_screen(controller, clicked_events_occur)
        elif controller.placing_ships:
            draw_ship_placement_screen(controller, clicked_events_occur)
        elif controller.state["in_game"]:
            draw_game_screen(controller, clicked_events_occur)
        else:
            draw_lobby_screen(controller, clicked_events_occur)
        
        # 3. Draw Global Message
        if controller.message and pygame.time.get_ticks() < controller.message_timer:
            msg_surf = controller.font_small.render(controller.message, True, RED)
            msg_rect = msg_surf.get_rect(center=(450, 650))
            # Draw background box for message
            pygame.draw.rect(controller.screen, WHITE, (msg_rect.x - 5, msg_rect.y - 5, 
                                                  msg_rect.width + 10, msg_rect.height + 10))
            pygame.draw.rect(controller.screen, BLACK, (msg_rect.x - 5, msg_rect.y - 5,
                                                  msg_rect.width + 10, msg_rect.height + 10), 1)
            controller.screen.blit(msg_surf, msg_rect)
        
        # 4. Update Display
        pygame.display.flip()
        controller.clock.tick(60)
    
    # Cleanup
    if controller.sock:
        try:
            controller.sock.close()
        except:
            pass
    pygame.quit()


def main():
    host = sys.argv[1] if len(sys.argv) >= 2 else DEFAULT_HOST
    port = int(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_PORT
    
    game_controller = GameController(host, port)
    run_game(game_controller)


if __name__ == "__main__":
    main()