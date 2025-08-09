# game_ui.py
import math
import random
import pygame
from wpm import calculate_wpm
from messages import (
    MSG_CLAIM_REQ,
    MSG_BREAK_REQ,
    MSG_GRID_UPDATE,
    MSG_CLAIM_RES,
    MSG_BREAK_RES,
    MSG_UNCLAIM_RES,
    MSG_LOBBY_UPDATE,
    MSG_START_GAME,
)
from game import Grid, Lock
from config import *
from utils import countdown_timer, normalize_text_for_match


class GameUI:
    def __init__(self, grid, players, network, user_id):
        self.grid = grid
        self.players = players
        self.network = network
        self.user_id = user_id
        # Be defensive in case server-assigned IDs differ from local
        if user_id in players and isinstance(players[user_id], dict):
            self.icon = players[user_id].get("icon", "★")
        else:
            # Fallback to any player's icon if mismatch
            try:
                self.icon = next(iter(players.values())).get("icon", "★")
            except Exception:
                self.icon = "★"
        self.wpm_score = 0

        # Multiplayer lobby state
        self.in_lobby = True
        self.host_id = None
        self.is_host = False
        self.countdown_active = False
        self.countdown_end_ticks = None
        self.game_duration_seconds = GAME_TIME

        pygame.init()
        # Larger, resizable window by default
        self.windowed_size = (1024, 720)
        self.fullscreen = False
        self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        pygame.display.set_caption("Clash Of Typers")

        # Fonts
        self.font = pygame.font.Font(None, 24)
        self.hud_font = pygame.font.Font(None, 22)
        self.title_font = pygame.font.Font(None, 72)
        self.mono_font = pygame.font.Font(None, 24)
        # Typing screen fonts (bigger and more visible)
        self.lock_text_font = pygame.font.Font(None, 32)
        self.lock_mono_font = pygame.font.Font(None, 36)
        self.lock_info_font = pygame.font.Font(None, 28)
        self.clock = pygame.time.Clock()

        # Retro/CRT overlay surfaces (cover whole window)
        self.scanline_surface = self._create_scanline_surface(self.screen.get_size())
        self.vignette_surface = self._create_vignette_surface(self.screen.get_size())
        self.flicker_phase = 0

        # Input state for lock screen
        self.selected_lock = None
        self.input_text = ""
        self.start_time = None
        self.wpm = 0

        # Game session state
        self.game_start_ticks = None
        # Overlays are off by default to avoid blocking view
        self.show_help_overlay = False
        self.show_legend_overlay = False
        self.toasts = []  # list of (text, expiry_ms, color)

        # Buttons cached per-frame
        self.help_button_rect = None
        self.legend_button_rect = None

        # Responsive layout metrics (computed each frame)
        self.content_rect = pygame.Rect(0, 0, *self.windowed_size)
        self.grid_origin_x = 10
        self.grid_origin_y = 52
        self.tile_w = 140
        self.tile_h = 80
        self.tile_gap = 12
        self.tile_aspect_ratio = 140 / 80

    def _normalize_char_for_input(self, ch: str) -> str:
        # Normalize single characters for consistent input and visual comparison
        if not ch:
            return ""
        # Map common unicode variants to ASCII
        translation_map = {
            ord('‘'): "'", ord('’'): "'", ord('‚'): "'", ord('‛'): "'", ord('`'): "'",
            ord('“'): '"', ord('”'): '"', ord('„'): '"', ord('″'): '"',
            ord('–'): "-", ord('—'): "-", ord('−'): "-",
            0x00A0: " ", 0x2007: " ", 0x202F: " ", 0x2009: " ",
            0x200B: "", 0x200C: "", 0x200D: "", 0x2060: "", 0xFEFF: "",
        }
        return ch.translate(translation_map)

    def _chars_equivalent(self, a: str, b: str) -> bool:
        return self._normalize_char_for_input(a) == self._normalize_char_for_input(b)

    def _rebuild_overlays(self):
        size = self.screen.get_size()
        self.scanline_surface = self._create_scanline_surface(size)
        self.vignette_surface = self._create_vignette_surface(size)

    # ---------- Retro helpers ----------
    def _create_scanline_surface(self, size):
        width, height = size
        scan = pygame.Surface((width, height), pygame.SRCALPHA)
        scan.set_alpha(90)
        for y in range(0, height, 3):
            pygame.draw.line(scan, (0, 0, 0, 140), (0, y), (width, y))
        return scan

    def _apply_crt_overlay(self):
        # Subtle flicker
        self.flicker_phase = (self.flicker_phase + 1) % 120
        flicker_alpha = 10 + int(10 * abs(math.sin(self.flicker_phase / 12)))
        width, height = self.screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, flicker_alpha))
        self.screen.blit(overlay, (0, 0))
        # Scanlines
        if self.scanline_surface.get_size() != (width, height):
            self.scanline_surface = self._create_scanline_surface((width, height))
        self.screen.blit(self.scanline_surface, (0, 0))
        # Vignette
        if self.vignette_surface.get_size() != (width, height):
            self.vignette_surface = self._create_vignette_surface((width, height))
        self.screen.blit(self.vignette_surface, (0, 0))

    def _create_vignette_surface(self, size):
        width, height = size
        vignette = pygame.Surface((width, height), pygame.SRCALPHA)
        # Simple radial dark corners
        for i in range(10):
            alpha = int(18 - i * 1.8)
            pygame.draw.rect(
                vignette,
                (0, 0, 0, alpha),
                pygame.Rect(0 + i, 0 + i, width - i * 2, height - i * 2),
                border_radius=6,
            )
        return vignette

    def _draw_text_with_shadow(self, text, pos, color=(255, 255, 255), shadow=(20, 20, 20)):
        x, y = pos
        shadow_surf = self.font.render(text, True, shadow)
        text_surf = self.font.render(text, True, color)
        self.screen.blit(shadow_surf, (x + 2, y + 2))
        self.screen.blit(text_surf, (x, y))

    def _draw_frame(self):
        # Pixel-style frame/border around the screen (responsive)
        width, height = self.screen.get_size()
        border_color = GRID_COLORS.get("border", (255, 120, 0))
        inner_color = GRID_COLORS.get("hud_text", (226, 203, 156))
        outer_margin = 6
        inner_margin = 10
        outer_rect = pygame.Rect(outer_margin, outer_margin, width - 2 * outer_margin, height - 2 * outer_margin)
        inner_rect = pygame.Rect(inner_margin, inner_margin, width - 2 * inner_margin, height - 2 * inner_margin)
        pygame.draw.rect(self.screen, border_color, outer_rect, border_radius=0)
        pygame.draw.rect(self.screen, inner_color, inner_rect, width=3)
        # Content rect slightly inset from inner_rect for UI content
        self.content_rect = pygame.Rect(inner_rect.x + 4, inner_rect.y + 4, inner_rect.w - 8, inner_rect.h - 8)

    def _compute_layout(self):
        # Compute grid layout centered in available content area above the HUD
        width, height = self.screen.get_size()
        hud_reserved_h = 46  # hud height + spacing
        gap = 12

        grid_area = pygame.Rect(
            self.content_rect.x + 10,
            self.content_rect.y + 10,
            self.content_rect.w - 20,
            max(0, (height - hud_reserved_h) - (self.content_rect.y + 10))
        )

        max_tile_w = (grid_area.w - (GRID_COLS - 1) * gap) / GRID_COLS if GRID_COLS > 0 else grid_area.w
        max_tile_h = (grid_area.h - (GRID_ROWS - 1) * gap) / GRID_ROWS if GRID_ROWS > 0 else grid_area.h

        tile_w_from_h = max_tile_h * self.tile_aspect_ratio
        tile_h_from_w = max_tile_w / self.tile_aspect_ratio

        if tile_w_from_h <= max_tile_w:
            tile_w = tile_w_from_h
            tile_h = max_tile_h
        else:
            tile_w = max_tile_w
            tile_h = tile_h_from_w

        tile_w = max(60, int(tile_w))
        tile_h = max(40, int(tile_h))

        actual_grid_w = GRID_COLS * tile_w + (GRID_COLS - 1) * gap
        actual_grid_h = GRID_ROWS * tile_h + (GRID_ROWS - 1) * gap
        origin_x = grid_area.x + (grid_area.w - actual_grid_w) // 2
        origin_y = grid_area.y + (grid_area.h - actual_grid_h) // 2

        self.tile_w = tile_w
        self.tile_h = tile_h
        self.tile_gap = gap
        self.grid_origin_x = origin_x
        self.grid_origin_y = origin_y

    # ---------- UI building blocks ----------
    def _add_toast(self, text, duration_ms=1600, color=(226, 203, 156)):
        expiry = pygame.time.get_ticks() + duration_ms
        self.toasts.append({"text": text, "expiry": expiry, "color": color})

    def _draw_toasts(self):
        now = pygame.time.get_ticks()
        # Remove expired
        self.toasts = [t for t in self.toasts if t["expiry"] > now]
        if not self.toasts:
            return
        # Draw up to 3, newest last at top
        to_draw = self.toasts[-3:]
        base_y = 18
        width, _ = self.screen.get_size()
        for i, toast in enumerate(reversed(to_draw)):
            text_surf = self.hud_font.render(toast["text"], True, toast["color"]) 
            padding = 8
            w = text_surf.get_width() + padding * 2
            h = text_surf.get_height() + padding
            x = (width - w) // 2
            y = base_y + i * (h + 6)
            pygame.draw.rect(self.screen, (20, 20, 20), pygame.Rect(x, y, w, h))
            pygame.draw.rect(self.screen, (143, 19, 19), pygame.Rect(x, y, w, h), 2)
            self.screen.blit(text_surf, (x + padding, y + padding // 2))
    def _draw_progress_bar(self, x, y, w, h, pct, label=None):
        pct = max(0.0, min(1.0, pct))
        back = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, (20, 20, 20), back)
        pygame.draw.rect(self.screen, (226, 203, 156), pygame.Rect(x, y, int(w * pct), h))
        pygame.draw.rect(self.screen, (143, 19, 19), back, 2)
        if label:
            text = self.hud_font.render(label, True, (226, 203, 156))
            self.screen.blit(text, (x + 6, y - 18))

    def _draw_legend_overlay(self):
        width, height = self.screen.get_size()
        # Dim background
        dim = pygame.Surface((width, height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 140))
        self.screen.blit(dim, (0, 0))
        # Panel
        panel_w, panel_h = min(480, width - 80), 200
        panel = pygame.Rect((width - panel_w) // 2, (height - panel_h) // 2, panel_w, panel_h)
        pygame.draw.rect(self.screen, (20, 20, 20), panel)
        pygame.draw.rect(self.screen, GRID_COLORS.get("border", (255, 120, 0)), panel, 2)
        title = self.hud_font.render("Legend", True, GRID_COLORS.get("hud_text", (226, 203, 156)))
        self.screen.blit(title, (panel.x + 12, panel.y + 10))
        rows = [
            ("Easy", GRID_COLORS.get("easy", (0, 255, 0))),
            ("Medium", GRID_COLORS.get("medium", (255, 255, 0))),
            ("Hard", GRID_COLORS.get("hard", (255, 0, 0))),
            ("Broken", GRID_COLORS.get("finished", (128, 128, 128))),
        ]
        for i, (name, color) in enumerate(rows):
            y = panel.y + 40 + i * 28
            pygame.draw.rect(self.screen, color, pygame.Rect(panel.x + 16, y, 18, 18))
            label = self.hud_font.render(name, True, (220, 220, 220))
            self.screen.blit(label, (panel.x + 44, y - 2))

    def _draw_help_overlay(self):
        width, height = self.screen.get_size()
        # Dim background
        dim = pygame.Surface((width, height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 140))
        self.screen.blit(dim, (0, 0))
        # Panel
        panel_w, panel_h = min(640, width - 80), 220
        panel = pygame.Rect((width - panel_w) // 2, (height - panel_h) // 2, panel_w, panel_h)
        pygame.draw.rect(self.screen, (20, 20, 20), panel)
        pygame.draw.rect(self.screen, GRID_COLORS.get("border", (255, 120, 0)), panel, 2)
        header = self.hud_font.render("How to Play", True, GRID_COLORS.get("hud_text", (226, 203, 156)))
        self.screen.blit(header, (panel.x + 12, panel.y + 10))
        lines = [
            "1) Click a lock to claim it.",
            "2) Type the sentence exactly.",
            "3) Press Enter when done.",
            "Goal: Meet the WPM target to break the lock!",
            "Tips: ESC to cancel, H/L to toggle panels",
        ]
        for i, text in enumerate(lines):
            line = self.hud_font.render(text, True, (200, 200, 200))
            self.screen.blit(line, (panel.x + 12, panel.y + 42 + i * 22))

    def _draw_hud(self, remaining_seconds):
        # HUD background along bottom
        width, height = self.screen.get_size()
        hud_bg = pygame.Rect(10, height - 40, width - 20, 30)
        pygame.draw.rect(self.screen, GRID_COLORS.get("hud_backdrop", (60, 30, 30)), hud_bg)
        pygame.draw.rect(self.screen, (0, 0, 0), hud_bg, 2)

        # Timer + remaining locks
        mins = remaining_seconds // 60
        secs = remaining_seconds % 60
        timer_text = self.hud_font.render(f"{mins:02d}:{secs:02d}", True, GRID_COLORS.get("hud_text", (226, 203, 156)))
        self.screen.blit(timer_text, (20, hud_bg.y + 5))

        # Render each player's score compactly
        offset_x = 100
        for pid, pdata in self.players.items():
            color = (226, 203, 156) if pid == self.user_id else (200, 200, 200)
            text = f"{pid}: {pdata['score']} ({pdata['locks_broken']})"
            surf = self.hud_font.render(text, True, color)
            self.screen.blit(surf, (offset_x, hud_bg.y + 5))
            offset_x += surf.get_width() + 20

        # Progress bar (locks broken)
        total = getattr(self.grid, "size", GRID_ROWS * GRID_COLS)
        remaining = getattr(self.grid, "remaining_locks", total)
        broken = max(0, total - remaining)
        pct = broken / float(total or 1)
        # Progress aligned to right side of HUD
        bar_w = 280
        self._draw_progress_bar(width - bar_w - 20, hud_bg.y + 2, bar_w, 20, pct, label=f"Progress {broken}/{total}")

    def _draw_hud_controls(self):
        # Small clickable labels in the HUD bar (bottom-right)
        width, height = self.screen.get_size()
        base_y = height - 38
        labels = []
        if True:
            labels.append(("H: Help", 'help'))
            labels.append(("L: Legend", 'legend'))
            labels.append(("F: Fullscreen", None))
        # Measure and place from right to left
        x = width - 24
        spacing = 10
        self.help_button_rect = None
        self.legend_button_rect = None
        for text, key in reversed(labels):
            surf = self.hud_font.render(text, True, GRID_COLORS.get("hud_text", (226, 203, 156)))
            rect = pygame.Rect(x - surf.get_width() - 12, base_y, surf.get_width() + 12, surf.get_height() + 6)
            pygame.draw.rect(self.screen, (20, 20, 20), rect)
            pygame.draw.rect(self.screen, GRID_COLORS.get("border", (255, 120, 0)), rect, 2)
            self.screen.blit(surf, (rect.x + 6, rect.y + 3))
            if key == 'help':
                self.help_button_rect = rect
            elif key == 'legend':
                self.legend_button_rect = rect
            x = rect.x - spacing

    def _draw_tile(self, lock, hovered=False):
        if lock.broken_by_user:
            fill_color = GRID_COLORS["finished"]
        elif lock.claimed_by_user == self.user_id:
            fill_color = (120, 255, 120)
        elif lock.claimed_by_user:
            fill_color = (120, 120, 255)
        else:
            fill_color = GRID_COLORS.get(lock.difficulty, (255, 255, 255))

        w, h = self.tile_w, self.tile_h
        x = self.grid_origin_x + lock.col * (w + self.tile_gap)
        y = self.grid_origin_y + lock.row * (h + self.tile_gap)

        # Pixel box: border + fill
        pygame.draw.rect(self.screen, (20, 20, 20), pygame.Rect(x - 2, y - 2, w + 4, h + 4))
        pygame.draw.rect(self.screen, fill_color, pygame.Rect(x, y, w, h))
        border_width = 4 if hovered else 3
        pygame.draw.rect(self.screen, (0, 0, 0), pygame.Rect(x, y, w, h), border_width)

        # Difficulty tag and label
        diff = lock.difficulty[:1].upper()
        badge_color = (0, 0, 0)
        pygame.draw.rect(self.screen, (226, 203, 156), pygame.Rect(x - 2, y - 18, 28, 16))
        pygame.draw.rect(self.screen, (143, 19, 19), pygame.Rect(x - 2, y - 18, 28, 16), 2)
        diff_surf = self.hud_font.render(diff, True, badge_color)
        self.screen.blit(diff_surf, (x + 7 - diff_surf.get_width() // 2, y - 18))

        # Show a short preview of the sentence
        text = f"{lock.lock_string[:10]}..."
        self._draw_text_with_shadow(text, (x + 8, y + h // 2 - 8), (0, 0, 0))

        # Claimed/owner indicator
        if lock.claimed_by_user:
            owner = "You" if lock.claimed_by_user == self.user_id else lock.claimed_by_user
            claim_text = self.hud_font.render(f"Claimed: {owner}", True, (0, 0, 0))
            self.screen.blit(claim_text, (x + 8, y + h - 18))

    def _draw_grid(self, mouse_pos):
        hovered_lock = None
        for lock in self.grid.grid:
            rect = pygame.Rect(
                self.grid_origin_x + lock.col * (self.tile_w + self.tile_gap),
                self.grid_origin_y + lock.row * (self.tile_h + self.tile_gap),
                self.tile_w,
                self.tile_h,
            )
            is_hovered = rect.collidepoint(mouse_pos)
            if is_hovered:
                hovered_lock = lock
            self._draw_tile(lock, hovered=is_hovered)
        return hovered_lock

    def _draw_tooltip(self, lock, mouse_pos):
        if not lock:
            return
        lines = [
            f"Difficulty: {lock.difficulty.title()}",
            f"WPM target: {lock.wpm_target}",
            f"Points: {lock.points}",
        ]
        if lock.broken:
            lines.append(f"Broken by: {lock.broken_by_user}")
        elif lock.claimed_by_user and lock.claimed_by_user != self.user_id:
            lines.append(f"Claimed by: {lock.claimed_by_user}")
        else:
            lines.append("Status: Available")

        max_w = max(self.hud_font.size(s)[0] for s in lines) + 16
        h = 8 + len(lines) * 18
        x, y = mouse_pos
        width, height = self.screen.get_size()
        x = min(max(14, x + 12), width - max_w - 14)
        y = min(max(52, y + 12), height - h - 14)
        panel = pygame.Rect(x, y, max_w, h)
        pygame.draw.rect(self.screen, (20, 20, 20), panel)
        pygame.draw.rect(self.screen, (143, 19, 19), panel, 2)
        for i, s in enumerate(lines):
            line = self.hud_font.render(s, True, (220, 220, 220))
            self.screen.blit(line, (panel.x + 8, panel.y + 4 + i * 18))

    # ---------- Screens ----------
    def show_loading_screen(self):
        start = pygame.time.get_ticks()
        done = False
        pulse = 0
        while not done:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    self._rebuild_overlays()
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER):
                    done = True

            # Backdrop
            self.screen.fill(GRID_COLORS.get("backdrop", (10, 10, 12)))
            self._draw_frame()

            # Title
            width, height = self.screen.get_size()
            title_shadow = self.title_font.render("CLASH OF TYPERS", True, (20, 20, 20))
            title = self.title_font.render("CLASH OF TYPERS", True, GRID_COLORS.get("hud_text", (226, 203, 156)))
            tx = (width - title.get_width()) // 2
            self.screen.blit(title_shadow, (tx + 4, 136))
            self.screen.blit(title, (tx, 132))

            # Loading bar
            elapsed = (pygame.time.get_ticks() - start) / 1000.0
            duration = 1.75
            progress = max(0.0, min(1.0, elapsed / duration))
            bar_w = min(600, width - 200)
            bar_rect = pygame.Rect((width - bar_w) // 2, 360, bar_w, 18)
            pygame.draw.rect(self.screen, (20, 20, 20), bar_rect)
            pygame.draw.rect(self.screen, GRID_COLORS.get("hud_text", (226, 203, 156)), pygame.Rect(bar_rect.x, bar_rect.y, int(bar_w * progress), 18))
            pygame.draw.rect(self.screen, GRID_COLORS.get("border", (255, 120, 0)), bar_rect, 3)

            # Press start prompt (blinks)
            pulse = (pulse + 1) % 60
            if pulse < 40:
                prompt = self.hud_font.render("PRESS ENTER TO CONTINUE", True, GRID_COLORS.get("hud_text", (226, 203, 156)))
                px = (width - prompt.get_width()) // 2
                self.screen.blit(prompt, (px, 400))

            self._apply_crt_overlay()
            pygame.display.flip()
            # Do not auto-skip when full; require Enter to proceed

    def render(self, remaining_seconds):
        # Retro backdrop
        self.screen.fill(GRID_COLORS.get("backdrop", (10, 10, 12)))
        self._draw_frame()
        self._compute_layout()

        mouse_pos = pygame.mouse.get_pos()
        hovered_lock = self._draw_grid(mouse_pos)

        # Panels: help/legend toggled as overlays only
        self._draw_hud(remaining_seconds)
        self._draw_hud_controls()

        if self.show_help_overlay:
            self._draw_help_overlay()
        if self.show_legend_overlay:
            self._draw_legend_overlay()

        # Tooltip on hover
        self._draw_tooltip(hovered_lock, mouse_pos)

        # Toasts
        self._draw_toasts()

        self._apply_crt_overlay()
        pygame.display.flip()

    def render_lock_screen(self, lock, remaining_seconds):
        self.screen.fill((0, 0, 0))
        self._draw_frame()

        # Header
        width, height = self.screen.get_size()
        header = self.title_font.render("LOCK CHALLENGE", True, GRID_COLORS.get("hud_text", (226, 203, 156)))
        hx = (width - header.get_width()) // 2
        self.screen.blit(header, (hx, 40))

        # Target info panel
        info = [
            f"Difficulty: {lock.difficulty.title()}",
            f"WPM target: {lock.wpm_target}",
            f"Points: {lock.points}",
            "Press ESC to cancel",
        ]
        panel = pygame.Rect(20, 120, 760, 80)
        pygame.draw.rect(self.screen, (20, 20, 20), panel)
        pygame.draw.rect(self.screen, GRID_COLORS.get("border", (255, 120, 0)), panel, 2)
        for i, s in enumerate(info):
            t = self.hud_font.render(s, True, (220, 220, 220))
            self.screen.blit(t, (panel.x + 12 + i * 190, panel.y + 10))

        # Target text block (larger and more visible with wrap)
        def wrap_text(text, font, max_w):
            words = text.split(' ')
            lines = []
            current = ''
            for w in words:
                test = (current + ' ' + w).strip()
                if font.size(test)[0] <= max_w:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    current = w
            if current:
                lines.append(current)
            return lines

        max_text_w = width - 48
        wrapped_lines = wrap_text(lock.lock_string, self.lock_text_font, max_text_w)
        for i, line in enumerate(wrapped_lines[:8]):
            text_surf = self.lock_text_font.render(line, True, GRID_COLORS.get("hud_text", (226, 203, 156)))
            self.screen.blit(text_surf, (24, 220 + i * (self.lock_text_font.get_height() + 6)))

        # Input with blinking cursor + correctness coloring
        target = lock.lock_string
        input_text = self.input_text
        # Compare with normalization to avoid false negatives on quotes/dashes/spaces
        correct_len = 0
        for a, b in zip(input_text, target):
            if self._chars_equivalent(a, b):
                correct_len += 1
            else:
                break
        correct_part = input_text[:correct_len]
        wrong_part = input_text[correct_len:]

        cursor_visible = (pygame.time.get_ticks() // 400) % 2 == 0
        caret = "▌" if cursor_visible else " "

        x0, y0 = 24, min(420, 220 + len(wrapped_lines[:8]) * (self.lock_text_font.get_height() + 6) + 20)
        # Draw correct part in green
        correct_surf = self.lock_mono_font.render(correct_part, True, (0, 255, 128))
        self.screen.blit(correct_surf, (x0, y0))
        # Draw wrong part in red
        x_off = x0 + correct_surf.get_width()
        wrong_surf = self.lock_mono_font.render(wrong_part, True, (255, 80, 80))
        self.screen.blit(wrong_surf, (x_off, y0))
        # Draw caret
        caret_surf = self.lock_mono_font.render(caret, True, (0, 255, 128))
        self.screen.blit(caret_surf, (x_off + wrong_surf.get_width(), y0))

        # Live WPM + timer
        wpm_text = self.lock_info_font.render(f"WPM: {self.wpm:.1f}", True, (255, 255, 0))
        self.screen.blit(wpm_text, (24, y0 + self.lock_mono_font.get_height() + 12))
        mins = remaining_seconds // 60
        secs = remaining_seconds % 60
        timer_text = self.lock_info_font.render(f"Time Left: {mins:02d}:{secs:02d}", True, GRID_COLORS.get("hud_text", (226, 203, 156)))
        self.screen.blit(timer_text, (24 + wpm_text.get_width() + 20, y0 + self.lock_mono_font.get_height() + 12))

        # Toasts
        self._draw_toasts()

        self._apply_crt_overlay()
        pygame.display.flip()

    # ---------- Interaction helpers ----------
    def detect_click(self, pos):
        for lock in self.grid.grid:
            rect = pygame.Rect(
                self.grid_origin_x + lock.col * (self.tile_w + self.tile_gap),
                self.grid_origin_y + lock.row * (self.tile_h + self.tile_gap),
                self.tile_w,
                self.tile_h,
            )
            if rect.collidepoint(pos):
                return lock
        return None

    # ---------- Lobby & countdown ----------
    def _render_lobby_screen(self):
        width, height = self.screen.get_size()
        self.screen.fill(GRID_COLORS.get("backdrop", (10, 10, 12)))
        self._draw_frame()

        title_shadow = self.title_font.render("LOBBY", True, (20, 20, 20))
        title = self.title_font.render("LOBBY", True, GRID_COLORS.get("hud_text", (226, 203, 156)))
        tx = (width - title.get_width()) // 2
        self.screen.blit(title_shadow, (tx + 4, 90))
        self.screen.blit(title, (tx, 86))

        # Players panel
        panel_w = min(640, width - 160)
        panel = pygame.Rect((width - panel_w) // 2, 180, panel_w, 260)
        pygame.draw.rect(self.screen, (20, 20, 20), panel)
        pygame.draw.rect(self.screen, GRID_COLORS.get("border", (255, 120, 0)), panel, 2)
        header = self.hud_font.render("Players joined:", True, GRID_COLORS.get("hud_text", (226, 203, 156)))
        self.screen.blit(header, (panel.x + 12, panel.y + 10))

        for i, (pid, pdata) in enumerate(self.players.items()):
            host_mark = " (Host)" if pid == self.host_id else ""
            color = GRID_COLORS.get("hud_text", (226, 203, 156)) if pid == self.user_id else (200, 200, 200)
            row_text = f"{pdata.get('icon', '★')}  {pid}{host_mark}"
            surf = self.hud_font.render(row_text, True, color)
            self.screen.blit(surf, (panel.x + 14, panel.y + 40 + i * 26))

        # Start button for host
        btn_rect = pygame.Rect((width - 280) // 2, 460, 280, 44)
        if self.is_host:
            pygame.draw.rect(self.screen, (20, 20, 20), btn_rect)
            pygame.draw.rect(self.screen, GRID_COLORS.get("border", (255, 120, 0)), btn_rect, 3)
            label = self.hud_font.render("Start Game (Enter)", True, GRID_COLORS.get("hud_text", (226, 203, 156)))
            self.screen.blit(label, (btn_rect.x + (btn_rect.w - label.get_width()) // 2, btn_rect.y + 10))
        else:
            # Waiting label
            label = self.hud_font.render("Waiting for host to start...", True, GRID_COLORS.get("hud_text", (226, 203, 156)))
            lx = (width - label.get_width()) // 2
            self.screen.blit(label, (lx, 470))

        self._apply_crt_overlay()
        pygame.display.flip()

        return btn_rect if self.is_host else None

    def _render_countdown_screen(self):
        width, height = self.screen.get_size()
        self.screen.fill(GRID_COLORS.get("backdrop", (10, 10, 12)))
        self._draw_frame()

        remaining_ms = max(0, (self.countdown_end_ticks or 0) - pygame.time.get_ticks())
        remaining = int(math.ceil(remaining_ms / 1000.0))
        text = "GO!" if remaining <= 0 else str(remaining)
        color = (120, 255, 120) if text == "GO!" else GRID_COLORS.get("hud_text", (226, 203, 156))
        title = self.title_font.render(text, True, color)
        tx = (width - title.get_width()) // 2
        self.screen.blit(title, (tx, 240))

        subtitle = self.hud_font.render("Get ready...", True, GRID_COLORS.get("hud_text", (226, 203, 156)))
        sx = (width - subtitle.get_width()) // 2
        self.screen.blit(subtitle, (sx, 320))

        self._apply_crt_overlay()
        pygame.display.flip()

    def run(self):
        # Show retro loading screen first
        self.show_loading_screen()

        running = True
        # Lobby first; start after server start signal
        self.game_start_ticks = None
        while running:
            self.clock.tick(60)

            # Lobby updates
            lobby = self.network.get_packet(MSG_LOBBY_UPDATE)
            if lobby:
                try:
                    self.players = lobby.get("players", self.players)
                    self.host_id = lobby.get("host_id", self.host_id)
                    self.is_host = (self.user_id == self.host_id)
                    if lobby.get("game_started") and self.in_lobby and not self.countdown_active:
                        # Fall-through in case we joined late
                        self.in_lobby = False
                        if self.game_start_ticks is None:
                            self.game_start_ticks = pygame.time.get_ticks()
                except Exception:
                    pass

            start_msg = self.network.get_packet(MSG_START_GAME)
            if start_msg and self.in_lobby and not self.countdown_active:
                try:
                    cd = int(start_msg.get("countdown_seconds", 3))
                    self.game_duration_seconds = int(start_msg.get("game_time", GAME_TIME))
                except Exception:
                    cd = 3
                    self.game_duration_seconds = GAME_TIME
                self.countdown_active = True
                self.countdown_end_ticks = pygame.time.get_ticks() + cd * 1000

            # If still in lobby, render lobby / countdown and handle events
            if self.in_lobby:
                if self.countdown_active:
                    self._render_countdown_screen()
                    if pygame.time.get_ticks() >= (self.countdown_end_ticks or 0):
                        self.in_lobby = False
                        self.countdown_active = False
                        self.game_start_ticks = pygame.time.get_ticks()
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                    continue
                else:
                    start_btn_rect = self._render_lobby_screen()
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                        elif event.type == pygame.VIDEORESIZE:
                            self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                            self._rebuild_overlays()
                        elif event.type == pygame.KEYDOWN and self.is_host and (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER):
                            self.network.send_start_game()
                        elif event.type == pygame.KEYDOWN and (event.key == pygame.K_f or event.key == pygame.K_F11):
                            # Toggle fullscreen
                            self.fullscreen = not self.fullscreen
                            if self.fullscreen:
                                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                            else:
                                self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
                            self._rebuild_overlays()
                        elif event.type == pygame.MOUSEBUTTONDOWN and self.is_host and start_btn_rect and start_btn_rect.collidepoint(event.pos):
                            self.network.send_start_game()
                    continue

            # Receive server updates
            packet = self.network.get_packet(MSG_GRID_UPDATE)
            if packet:
                self.grid = Grid.from_dict(packet["grid"], GRID_ROWS, GRID_COLS)
                self.players = packet["players"]
                # Keep selected lock reference in sync with latest grid
                if self.selected_lock is not None:
                    try:
                        latest = self.grid.get_lock(self.selected_lock.lock_id)
                        # If lock is no longer ours or is broken, exit lock screen
                        if latest.broken or latest.claimed_by_user != self.user_id:
                            self._add_toast("Lock no longer available", color=(255, 120, 120))
                            self.selected_lock = None
                            self.input_text = ""
                            self.start_time = None
                            self.wpm = 0
                        else:
                            self.selected_lock = latest
                    except Exception:
                        pass

            # Claim result handling (resolve races gracefully)
            claim_result = self.network.get_packet(MSG_CLAIM_RES)
            if claim_result:
                success = claim_result.get("success")
                lock_data = claim_result.get("lock")
                if lock_data:
                    try:
                        updated_lock = Lock.from_dict(lock_data)
                        self.grid.update_lock(updated_lock)
                        # If we were working on this lock, refresh reference
                        if self.selected_lock and self.selected_lock.lock_id == updated_lock.lock_id:
                            # If claim failed, exit the lock screen
                            if not success:
                                self._add_toast("Lock already claimed!", color=(255, 120, 120))
                                self.selected_lock = None
                                self.input_text = ""
                                self.start_time = None
                                self.wpm = 0
                            else:
                                # Refresh local reference to avoid stale data
                                self.selected_lock = self.grid.get_lock(updated_lock.lock_id)
                    except Exception:
                        pass

            # Optional: unclaim result handling (update local grid if provided)
            unclaim_result = self.network.get_packet(MSG_UNCLAIM_RES)
            if unclaim_result:
                lock_data = unclaim_result.get("lock")
                if lock_data:
                    try:
                        self.grid.update_lock(Lock.from_dict(lock_data))
                    except Exception:
                        pass

            # Break result feedback
            break_result = self.network.get_packet(MSG_BREAK_RES)
            if break_result:
                success = break_result.get("success")
                points = break_result.get("points", 0)
                lock_data = break_result.get("lock")
                if lock_data:
                    try:
                        self.grid.update_lock(Lock.from_dict(lock_data))
                    except Exception:
                        pass
                if success:
                    self._add_toast(f"Unlocked! +{points} pts", color=(120, 255, 120))
                else:
                    self._add_toast("Failed to unlock", color=(255, 120, 120))

            # Remaining time
            remaining_seconds = countdown_timer(self.game_start_ticks, self.game_duration_seconds)

            # End condition: time or all locks broken
            total = getattr(self.grid, "size", GRID_ROWS * GRID_COLS)
            remaining = getattr(self.grid, "remaining_locks", total)
            if remaining_seconds <= 0 or remaining <= 0:
                self._render_end_screen()
                break

            if self.selected_lock:
                self.render_lock_screen(self.selected_lock, remaining_seconds)
            else:
                self.render(remaining_seconds)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    self._rebuild_overlays()
                elif event.type == pygame.MOUSEBUTTONDOWN and not self.selected_lock:
                    # HUD controls clicks
                    if self.help_button_rect and self.help_button_rect.collidepoint(event.pos):
                        self.show_help_overlay = not self.show_help_overlay
                        continue
                    if self.legend_button_rect and self.legend_button_rect.collidepoint(event.pos):
                        self.show_legend_overlay = not self.show_legend_overlay
                        continue
                    clicked = self.detect_click(event.pos)
                    if clicked and not clicked.broken:
                        # Block entry if claimed by another user
                        if clicked.claimed_by_user not in (None, self.user_id):
                            self._add_toast("Already claimed", color=(255, 120, 120))
                            continue
                        # Optimistically mark as claimed for local UI feel
                        clicked.claimed_by_user = self.user_id
                        self.network.send_claim(clicked.lock_id)
                        # Begin lock screen
                        self.selected_lock = clicked
                        self.input_text = ""
                        self.start_time = pygame.time.get_ticks()
                elif event.type == pygame.KEYDOWN and self.selected_lock:
                    if event.key == pygame.K_ESCAPE:
                        # Properly request unclaim on cancel
                        try:
                            self.network.send_unclaim(self.selected_lock.lock_id)
                        except Exception:
                            pass
                        self.selected_lock = None
                        self.input_text = ""
                        self.wpm = 0
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                        # Update live WPM when editing
                        if self.start_time is not None:
                            self.wpm = calculate_wpm(self.start_time, pygame.time.get_ticks(), len(self.input_text))
                    elif event.key == pygame.K_RETURN:
                        end_time = pygame.time.get_ticks()
                        self.wpm = calculate_wpm(self.start_time, end_time, len(self.input_text))
                        self.network.send_break(self.selected_lock.lock_id, self.input_text, self.wpm)
                        self.selected_lock = None
                        self.input_text = ""
                        self.start_time = None
                    else:
                        # Filter non-printable control chars to keep retro look
                        if event.unicode and event.unicode.isprintable():
                            self.input_text += event.unicode
                            # Live WPM while typing
                            if self.start_time is not None:
                                self.wpm = calculate_wpm(self.start_time, pygame.time.get_ticks(), len(self.input_text))
                elif event.type == pygame.KEYDOWN and not self.selected_lock:
                    if event.key == pygame.K_h:
                        self.show_help_overlay = not self.show_help_overlay
                    elif event.key == pygame.K_l:
                        self.show_legend_overlay = not self.show_legend_overlay
                    elif event.key == pygame.K_f or event.key == pygame.K_F11:
                        # Toggle fullscreen
                        self.fullscreen = not self.fullscreen
                        if self.fullscreen:
                            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        else:
                            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
                        self._rebuild_overlays()

    def _render_end_screen(self):
        # Winner/loser end screen with final scores and tie handling
        done = False
        pulse = 0
        # Determine winners based on top score
        sorted_players = sorted(self.players.items(), key=lambda kv: kv[1]["score"], reverse=True)
        winners = []
        if sorted_players:
            top_score = sorted_players[0][1]["score"]
            winners = [pid for pid, pdata in self.players.items() if pdata["score"] == top_score]
        user_won = self.user_id in winners
        while not done:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE):
                    done = True

            width, height = self.screen.get_size()
            self.screen.fill(GRID_COLORS.get("backdrop", (30, 30, 30)))
            self._draw_frame()

            # Winner/loser banner
            banner_text = "YOU WIN!" if user_won else "YOU LOSE"
            banner_color = (120, 255, 120) if user_won else (255, 120, 120)
            title_shadow = self.title_font.render(banner_text, True, (20, 20, 20))
            title = self.title_font.render(banner_text, True, banner_color)
            tx = (width - title.get_width()) // 2
            self.screen.blit(title_shadow, (tx + 4, 136))
            self.screen.blit(title, (tx, 132))

            # Winners line (ties supported)
            if winners:
                winners_label = "Winners: " + ", ".join(winners)
                winners_surf = self.hud_font.render(winners_label, True, GRID_COLORS.get("hud_text", (226, 203, 156)))
                wx = (width - winners_surf.get_width()) // 2
                self.screen.blit(winners_surf, (wx, 200))

            # Scores panel
            panel_w = min(600, width - 200)
            panel = pygame.Rect((width - panel_w) // 2, 240, panel_w, 220)
            pygame.draw.rect(self.screen, (20, 20, 20), panel)
            pygame.draw.rect(self.screen, (143, 19, 19), panel, 2)
            sorted_players = sorted(self.players.items(), key=lambda kv: kv[1]["score"], reverse=True)
            for i, (pid, pdata) in enumerate(sorted_players[:6]):
                color = (226, 203, 156) if pid == self.user_id else (200, 200, 200)
                row_text = f"{i+1}. {pid} - {pdata['score']} pts, {pdata['locks_broken']} locks"
                surf = self.hud_font.render(row_text, True, color)
                self.screen.blit(surf, (panel.x + 14, panel.y + 16 + i * 24))

            pulse = (pulse + 1) % 60
            if pulse < 40:
                prompt = self.hud_font.render("Press ENTER to exit", True, (226, 203, 156))
                px = (width - prompt.get_width()) // 2
                self.screen.blit(prompt, (px, 450))

            self._apply_crt_overlay()
            pygame.display.flip()
