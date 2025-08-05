# wpm.py

# Calculates WPM from typing input (used by client side)
# Author: Arun

# 1. Track keypress times
# 2. Calculate elapsed time
# 3. Calculate words per minute based on typed string

import time
import pygame

class WPMCalculator:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.keystrokes = 0
        self.typing_started = False
    
    def start_typing(self):
        """Start tracking typing session"""
        self.start_time = pygame.time.get_ticks()
        self.typing_started = True
        self.keystrokes = 0
    
    def record_keystroke(self, key):
        """Record a keystroke (excluding backspace, enter, etc.)"""
        if self.typing_started and key.isprintable():
            self.keystrokes += 1
    
    def finish_typing(self):
        """Finish typing session and calculate WPM"""
        if not self.typing_started:
            return 0
        
        self.end_time = pygame.time.get_ticks()
        self.typing_started = False
        
        # Calculate time in minutes
        time_elapsed = (self.end_time - self.start_time) / 1000.0  # Convert to seconds
        time_minutes = time_elapsed / 60.0
        
        # Calculate WPM (assuming average word length of 5 characters)
        if time_minutes > 0:
            wpm = (self.keystrokes / 5.0) / time_minutes
            return round(wpm, 1)
        else:
            return 0
    
    def reset(self):
        """Reset calculator state"""
        self.start_time = None
        self.end_time = None
        self.keystrokes = 0
        self.typing_started = False

def calculate_wpm(start_time, end_time, num_characters):
    """
    Calculate WPM from timing and character count
    
    Args:
        start_time: Start time in milliseconds
        end_time: End time in milliseconds  
        num_characters: Number of characters typed
    
    Returns:
        WPM (words per minute)
    """
    time_elapsed = (end_time - start_time) / 1000.0  # Convert to seconds
    time_minutes = time_elapsed / 60.0
    
    if time_minutes > 0:
        # Assume average word length of 5 characters
        wpm = (num_characters / 5.0) / time_minutes
        return round(wpm, 1)
    else:
        return 0
