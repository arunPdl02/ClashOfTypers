# game.py

# Contains game logic used by the client: grid layout, lock objects,etc.
# Author: Manan + Rushik

# 1. Define Lock class (id, color, score, status)
# 2. Define Grid class (list of Lock objects)
# 3. Helpers to update lock state and get lock by ID

# class Lock:
#     def __init__(self, lock_id, color, score): ...

# class Grid:
#     def __init__(self, num_locks): ...
#     def get_lock(self, lock_id): ...

import random
from utils import generate_strings
from utils import calculate_points
from utils import get_difficulty
from config import LOCK_WPM_RANGES as target_range

class Lock:
    def __init__(self, lock_id, difficulty, lock_string, wpm_target, points):
        self.lock_id = lock_id
        self.difficulty = difficulty
        self.lock_string = lock_string
        self.wpm_target = wpm_target
        self.points = points
        self.available = True
        self.broken = False
        self.user_id = None
    
    # checks whether a claim can be made
    # upon success updates internal variables to mark lock as claimed by given user
    def attempt_claim(self, user):
        success = False
        
        if self.available:
            self.available = False  # Mark as claimed
            success = True
            self.user_id = user

        return success
    
    # checks whether a lock has been successfully broken
    # upon success returns points and updates internal variables to mark lock as broken
    # upon failure lock is made available to all users
    def attempt_break(self, user_string, user_wpm):
        success = False
        points = 0
        if user_string == self.lock_string and user_wpm >= self.wpm_target:      
            self.broken = True
            self.available = False
            points = self.points
            self.points = 0
            success = True
        else:
            self.available = True
        return success, points

    # serialize lock for network transmission
    def to_dict(self):
        return {
            "lock_id": self.lock_id,
            "difficulty": self.difficulty,
            "lock_string": self.lock_string,
            "wpm_target": self.wpm_target,
            "points": self.points,
            "available": self.available,
            "broken": self.broken,
            "user_id": self.user_id,
        }

    @staticmethod
    def from_dict(data: dict):
        lock = Lock(
            lock_id=data["lock_id"],
            difficulty=data["difficulty"],
            lock_string=data["lock_string"],
            wpm_target=data["wpm_target"],
            points=data["points"],
        )
        lock.available = data.get("available", True)
        lock.broken = data.get("broken", False)
        lock.user_id = data.get("user_id")
        return lock

class Game:
    def __init__(self, height, width):
        self._grid = []
        self._grid_height = height
        self._grid_width = width
        self._size = height * width  
        
        # initialize the difficulty spread of the grid, all other initialization relies on this
        # TO DO: add gauss distribution for difficulty
        for _ in range(self._size):
            self._grid.append(get_difficulty(random.randint(0, 2)))

        self._init_locks()

    # string logic is currently commented out to make debugging easier, it runs slow as of now
    def _init_locks(self):
        #strings = generate_strings(self._grid, self._size)
        
        for i in range(self._size):
            difficulty = self._grid[i]
            lock_id = i
            wpm = random.randint(*target_range[difficulty])
            #lock_string = strings[i]
            lock_string = '1234567890'
            points = calculate_points(length=len(lock_string), wpm=wpm)

            self._grid[i] = Lock(lock_id=lock_id, difficulty=difficulty, lock_string=lock_string, wpm_target=wpm, points=points)
    
    # attempt to claim lock
    def claim_lock(self, lock, user):
        return lock.attempt_claim(user)
    
    # attempt to break lock
    def break_lock(self, lock, user_string, user_wpm):
        return lock.attempt_break(user_string=user_string, user_wpm=user_wpm)
    
    # access game state
    def get_grid(self):
        return self._grid
    
    def get_lock(self, id):
        return self._grid[id]

    def get_dimensions(self):
        return self._grid_height, self._grid_width
    
    def get_size(self):
        return self._size
    
    # update grid
    def set_grid(self, grid):
        self._grid = grid

    # network helpers
    def to_dict(self):
        return [lock.to_dict() for lock in self._grid]

    # debugging
    def _print_grid_state(self):
        for lock in self._grid:
            print(f"id: {lock.lock_id}, difficulty: {lock.difficulty}, color: {lock.color}, wpm: {lock.wpm_target}, points: {lock.points}, available: {lock.available}, broken: {lock.broken}")
            print(f"string: {lock.lock_string}\n")
    
    