# game_ui.py
import pygame
from wpm import calculate_wpm
from messages import MSG_CLAIM_REQ, MSG_BREAK_REQ, MSG_GRID_UPDATE
from game import Grid
from config import *

class GameUI:
    def __init__(self, grid, players, network, user_id):
        self.grid = grid
        self.players = players
        self.network = network
        self.user_id = user_id
        self.icon = players[user_id]['icon']
        self.wpm_score = 0

        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Typing Locks")
        self.font = pygame.font.Font(None, 28)
        self.clock = pygame.time.Clock()

        self.selected_lock = None
        self.input_text = ""
        self.start_time = None
        self.wpm = 0

    def render(self):
        self.screen.fill((30, 30, 30))
        for lock in self.grid.grid:
            color = (255, 255, 255)
            if lock.claimed_by_user == self.user_id:
                color = (100, 255, 100)
            elif lock.claimed_by_user:
                color = (100, 100, 255)
            elif lock.broken_by_user:
                color = (255, 100, 100)

            pygame.draw.rect(self.screen, color, pygame.Rect(lock.col * 160 + 10, lock.row * 100 + 10, 140, 80))
            text_surf = self.font.render(f"{lock.lock_string[:10]}...", True, (0, 0, 0))
            self.screen.blit(text_surf, (lock.col * 160 + 15, lock.row * 100 + 40))

        score_text = self.font.render(f"Score: {self.players[self.user_id]['score']}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 570))

        pygame.display.flip()

    def render_lock_screen(self, lock):
        self.screen.fill((0, 0, 0))
        lines = [lock.lock_string[i:i+60] for i in range(0, len(lock.lock_string), 60)]
        for i, line in enumerate(lines):
            text_surf = self.font.render(line, True, (255, 255, 255))
            self.screen.blit(text_surf, (20, 40 + i * 30))

        input_surf = self.font.render(self.input_text, True, (0, 255, 0))
        self.screen.blit(input_surf, (20, 400))
        wpm_text = self.font.render(f"WPM: {self.wpm:.1f}", True, (255, 255, 0))
        self.screen.blit(wpm_text, (20, 440))
        pygame.display.flip()

    def detect_click(self, pos):
        for lock in self.grid.grid:
            rect = pygame.Rect(lock.col * 160 + 10, lock.row * 100 + 10, 140, 80)
            if rect.collidepoint(pos):
                return lock
        return None

    def run(self):
        running = True
        while running:
            self.clock.tick(30)

            # Receive server updates
            packet = self.network.get_packet(MSG_GRID_UPDATE)
            if packet:
                self.grid = Grid.from_dict(packet["grid"], GRID_ROWS, GRID_COLS)
                self.players = packet["players"]

            if self.selected_lock:
                self.render_lock_screen(self.selected_lock)
            else:
                self.render()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and not self.selected_lock:
                    clicked = self.detect_click(event.pos)
                    if clicked and not clicked.broken:
                        self.selected_lock = clicked
                        self.input_text = ""
                        self.start_time = pygame.time.get_ticks()
                elif event.type == pygame.KEYDOWN and self.selected_lock:
                    if event.key == pygame.K_ESCAPE:
                        self.selected_lock = None
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        
                        if self.input_text.strip() == self.selected_lock.lock_string.strip():
                            end_time = pygame.time.get_ticks()
                            self.wpm = calculate_wpm(self.start_time, end_time, len(self.input_text))

                            if self.wpm >= self.selected_lock.wpm_target:
                                self.network.send_break(self.selected_lock.lock_id, self.input_text, self.wpm)
                                print(f"[CLIENT_BREAK_SENT] lock_id={self.selected_lock.lock_id}, wpm={self.wpm}")
                            else:
                                self.network.send_claim(self.selected_lock.lock_id)
                                print(f"[CLIENT_CLAIM_SENT] lock_id={self.selected_lock.lock_id}, wpm={self.wpm}")

                        self.selected_lock = None
                    else:
                        self.input_text += event.unicode
