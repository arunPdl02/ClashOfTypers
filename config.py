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
LOCK_WPM_RANGES = {
    "easy": (15, 30),
    "medium": (30, 50),
    "hard": (50, 70)
}

LOCK_STRING_RANGES = {
    "easy": (1, 5),
    "medium": (5, 10),
    "hard": (10, 15)
}
GRID_COLORS = {
    "easy": (0, 255, 0),            # Green - Easy
    "medium": (255, 255, 0),        # Yellow - Medium  
    "hard": (255, 0, 0),            # Red - Hard
    "finished": (128, 128, 128),    # Gray - Finished/Broken
    "border": (143, 19, 19),        # 8F1313
    "backdrop": (40, 40, 60),       # 28283C
    "lock_text": (0,0,0),
    "hud_backdrop": (143, 19, 19),  # 8F1313
    "hud_text": (226, 203, 156)     # E2CB92
}

