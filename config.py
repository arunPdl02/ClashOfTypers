# config.py

# Stores game constatns: grid size, score ranges, WPM targets, etc.
# Author: Rushik + All (fine-tune)

# 1. Grid size
# 2. Score and WPM ranges
# 3. Lock color mapping

GRID_SIZE = 5  # 5x5 = 25 locks
LOCK_WPM_RANGES = {
    "green": (15, 25),
    "yellow": (30, 40),
    "red": (50, 70)
}
LOCK_SCORE_RANGES = {
    "green": (1, 5),
    "yellow": (6, 10),
    "red": (11, 15)
}
