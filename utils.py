# utils.py

# Any helper functions (e.g., rnadom string generation, timers, etc)
# Author: All

# 1. Random string generator for typing
# 2. Timer/stopwatch helper
# 3. Validation helpers

# def generate_typing_string(num_words): ...
# def timer(): return time.time()
import random
import string
import nltk
import pygame
from nltk.corpus import gutenberg
from config import LOCK_STRING_RANGES as size_range

# download corpus of sentences
nltk.download('punkt_tab', quiet=True)
nltk.download('gutenberg', quiet=True)

# generate strings for all locks in the grid
def generate_strings(grid, size):
    strings = []
    sentences = list(gutenberg.sents())
    output = ""

    # iterate over grid size
    for i in range(size):
        random.shuffle(sentences)                                       # shuffle sentences for each lock
        difficulty = grid[i]
        min_len, max_len = [x * 5 for x in size_range[difficulty]]      # assume word length is 5 chars
        strings.append(0)
        
        for s in sentences:                                             # iterate over all strings
            output = _clean_join(s)                                     # handle punctuation
            
            if min_len <= len(output) <= max_len:                       # if string length within difficulty range
                if output not in strings:                               # if string has not been repeated
                    strings[i] = output                                 # add string to list
                    break                                               # break once found
        
        if strings[i] == 0:
            strings[i] = "Couldn't find string, now have fun TyPinG tHis iNSteAd!"      # need this to prevent run time errors for now

    return strings

# helper method for generating clean sentences
def _clean_join(words):
    allowed = {',', '.', '!', ':', '?', "'"}
    result = ''
    special_case = False                                                # Example "don" + "'" + "t"
    
    for _, word in enumerate(words):
        if word == '"':
            continue                                                    # remove all double quotes
        elif word in allowed:
            result += word                                              # add valid punctuation
            if word == "'":                                 
                special_case = True     
        else:
            word = word.strip(string.punctuation.replace("'", ""))      # remove stray "'" not part of special case
            if result == '' or special_case:                            # if first word or special case, concat without white space
                result += word
                special_case = False
            else:
                result += ' ' + word                                    # add white space during concat

    return result.strip()

# map level to difficulty string to access config vars
def get_difficulty(level):
    match level:
        case 0:
            return 'easy'
        case 1:
            return 'medium'
        case 2:
            return 'hard'
        case _:
            return None
        
# calculate points based on sentence length and target wpm
def calculate_points(length, wpm):
    return round((length / wpm) * 25)                                   # scale by 25 as default output gets rounded to 1 (wpm is in minutes, strings of this size get typed in seconds)


# subtracts current time from the timestamp at which the game/timer began, returns remaining countdown in seconds
def countdown_timer(start_ticks, total_seconds):
    elapsed = (pygame.time.get_ticks() - start_ticks) // 1000
    return max(0, total_seconds - elapsed)



