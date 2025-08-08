# wpm.py

# Caclulates WPM from typing input (used by client side)
# Author: Arun

# 1. Track keypress times
# 2. Calculate elapsed time
# 3. Calculate words per minute based on typed string

import time

class WPMCalculator:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.keystrokes = 0
        self.is_typing = False
    
    def start_typing(self):
        """Start timing the typing session"""
        self.start_time = time.time()
        self.keystrokes = 0
        self.is_typing = True
    
    def record_keystroke(self, char):
        """Record a keystroke for WPM calculation"""
        if self.is_typing:
            self.keystrokes += 1
    
    def finish_typing(self):
        """Finish timing and calculate WPM"""
        if not self.is_typing or self.start_time is None:
            return 0
        
        self.end_time = time.time()
        self.is_typing = False
        
        # Calculate time in minutes
        time_minutes = (self.end_time - self.start_time) / 60.0
        
        if time_minutes <= 0:
            return 0
        
        # Calculate WPM (assuming average word length of 5 characters)
        wpm = (self.keystrokes / 5.0) / time_minutes
        return round(wpm, 1)
    
    def reset(self):
        """Reset the calculator for a new typing session"""
        self.start_time = None
        self.end_time = None
        self.keystrokes = 0
        self.is_typing = False

# Legacy function for backward compatibility
def calculate_wpm(start_time, end_time, num_words):
    """Calculate WPM given start time, end time, and number of words"""
    time_minutes = (end_time - start_time) / 60.0
    if time_minutes <= 0:
        return 0
    return round(num_words / time_minutes, 1)
