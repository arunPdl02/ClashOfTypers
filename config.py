# config.py

# Stores game constants: grid size, score ranges, WPM targets, etc.
# Author: Rushik + All (fine-tune)

# 1. Grid size
# 2. Score and WPM ranges
# 3. Lock color mapping

GRID_ROWS = 5 
GRID_COLS = 5
CELL_SIZE = 100
BORDER_WIDTH = 2
PADDING = CELL_SIZE / 1.5
HUD_PADDING = 25
HUD_HEIGHT = 50 
HUD_VERT_OFFSET = 15
GRID_ROW_OFFSET = HUD_VERT_OFFSET * 2
SCREEN_WIDTH = (GRID_COLS * CELL_SIZE) + (PADDING * 2)
SCREEN_HEIGHT = (GRID_ROWS * CELL_SIZE) + (PADDING * 2)
GAME_TIME = 300
LOCK_WPM = {
    "easy": 40,
    "medium": 60,
    "hard": 80
}

LOCK_STRING_RANGES = {
    "easy": (1, 3),
    "medium": (2, 4),
    "hard": (3, 5)
}
GRID_COLORS = {
    "easy": (0, 255, 128),          # Neon Green - Easy
    "medium": (255, 200, 0),        # Golden Yellow - Medium  
    "hard": (255, 80, 80),          # Warm Red - Hard
    "finished": (128, 128, 128),    # Gray - Finished/Broken
    "border": (255, 120, 0),        # Orange border
    "backdrop": (10, 10, 12),       # Near-black
    "lock_text": (0, 0, 0),
    "hud_backdrop": (45, 22, 0),    # Dark orange-brown
    "hud_text": (255, 210, 140)     # Warm light orange
}

