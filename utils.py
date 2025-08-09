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
import unicodedata
import nltk
import pygame
from nltk.corpus import gutenberg
from config import LOCK_STRING_RANGES as size_range

# download corpus of sentences
nltk.download('punkt', quiet=True)
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
    if level == 0:
        return 'easy'
    elif level == 1:
        return 'medium'
    elif level == 2:
        return 'hard'
    else:
        return None
        
# calculate points based on sentence length and target wpm
def calculate_points(length, wpm):
    return round((length / wpm) * 25)                                   # scale by 25 as default output gets rounded to 1 (wpm is in minutes, strings of this size get typed in seconds)


# subtracts current time from the timestamp at which the game/timer began, returns remaining countdown in seconds
def countdown_timer(start_ticks, total_seconds):
    elapsed = (pygame.time.get_ticks() - start_ticks) // 1000
    return max(0, total_seconds - elapsed)



def normalize_text_for_match(text: str) -> str:
    """
    Normalize text for robust equality checks between user input and target strings.

    This function harmonizes common user-visible variations so that visually identical
    inputs are treated as equal:
    - Unify curly quotes and backticks to straight quotes
    - Unify en/em/minus dashes to hyphen-minus
    - Remove zero-width characters
    - Convert non-breaking/thin spaces to regular spaces
    - Unicode normalize (NFKC)
    - Standardize spacing characters to regular spaces and strip ends
    """
    if text is None:
        return ""

    # Replace various spacing characters with normal space
    text = (
        text
        .replace("\u00A0", " ")  # NO-BREAK SPACE
        .replace("\u2007", " ")  # FIGURE SPACE
        .replace("\u202F", " ")  # NARROW NO-BREAK SPACE
        .replace("\u2009", " ")  # THIN SPACE
    )

    # Remove zero-width and BOM characters
    text = (
        text
        .replace("\u200B", "")   # ZERO WIDTH SPACE
        .replace("\u200C", "")   # ZERO WIDTH NON-JOINER
        .replace("\u200D", "")   # ZERO WIDTH JOINER
        .replace("\u2060", "")   # WORD JOINER
        .replace("\uFEFF", "")   # BOM
    )

    # Map curly quotes/backticks and typographic dashes to ASCII equivalents
    translation_map = {
        ord('‘'): "'",
        ord('’'): "'",
        ord('‚'): "'",
        ord('‛'): "'",
        ord('`'): "'",
        ord('“'): '"',
        ord('”'): '"',
        ord('„'): '"',
        ord('″'): '"',
        ord('–'): "-",
        ord('—'): "-",
        ord('−'): "-",
    }
    text = text.translate(translation_map)

    # Unicode normalization to compatibility decomposition/composition
    text = unicodedata.normalize('NFKC', text)

    # Trim edges
    return text.strip()

