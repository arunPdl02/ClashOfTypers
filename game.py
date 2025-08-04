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
from utils import generate_strings, calculate_points, get_difficulty
from config import LOCK_WPM_RANGES as target_range

# defines lock objects on the grid and helpers to access information
class Lock:
    def __init__(self, lock_id, difficulty, lock_string, wpm_target, points):
        self.lock_id = lock_id
        self.difficulty = difficulty
        self.lock_string = lock_string
        self.wpm_target = wpm_target
        self.points = points
        self.broken = False
        self.claimed_by_user = None
        self.broken_by_user = None

    # checks whether a lock can be claimed
    # true if lock is not broken and has not been claimed by any other person
    def is_claimable_by(self, user_id):
        return not self.broken and (self.claimed_by_user is None or self.claimed_by_user == user_id)

    # produce a dict from lock metadata to send to clients
    def to_dict(self):
        return {
            "lock_id": self.lock_id,
            "difficulty": self.difficulty,
            "lock_string": self.lock_string,
            "wpm_target": self.wpm_target,
            "points": self.points,
            "broken": self.broken,
            "claimed_by_user": self.claimed_by_user,
            "broken_by_user": self.broken_by_user
        }

    # initialize a new lock object using the dictionary sent from server
    @staticmethod
    def from_dict(data):
        lock = Lock(
            lock_id=data["lock_id"],
            difficulty=data["difficulty"],
            lock_string=data["lock_string"],
            wpm_target=data["wpm_target"],
            points=data["points"]
        )
        lock.broken = data["broken"]
        lock.claimed_by_user = data["claimed_by_user"]
        lock.broken_by_user = data["broken_by_user"]
        
        return lock

# defines the grid and helpers to manage game state
class Grid:
    def __init__(self, height, width):
        # grid dimensions
        self.height = height
        self.width = width
        self.size = height * width
        self.remaining_locks = self.size
        self.grid = []

    # generate all locks for the grid
    def generate_locks(self):
        self._difficulty_list = [get_difficulty(random.randint(0, 2)) for _ in range(self.size)]
        self._strings = generate_strings(self._difficulty_list, self.size)
        
        grid = []
        for i in range(self.size):
            difficulty = self._difficulty_list[i]
            string = self._strings[i]
            wpm = random.randint(*target_range[difficulty])
            points = calculate_points(len(string), wpm)
            lock = Lock(i, difficulty, string, wpm, points)
            
            grid.append(lock)

        self.grid = grid

    # return a lock object given an id
    def get_lock(self, lock_id):
        return self.grid[lock_id]

    # access grid object for a game
    def get_grid(self):
        return self.grid

    # access grid rows, cols data
    def get_dimensions(self):
        return self.height, self.width

    # attempts to claim a lock, returns False if lock is unclaimable
    # modifies the lock in place to reflect the change if successful
    def claim_lock(self, lock_id, player_id):
        lock = self.get_lock(lock_id)
        
        if lock.is_claimable_by(player_id):
            lock.claimed_by_user = player_id
            return True
        
        return False
    
    # attempts to break a lock and returns a boolean to indicate success along with the appropriate points to be received
    # modifies the lock in place to reflect the change if successful
    def break_lock(self, lock_id, user_string, user_wpm, player_id):
        lock = self.get_lock(lock_id)                                                           # get lock from grid

        if not lock.broken and lock.claimed_by_user == player_id:                               # redundancy check
            
            # update lock to reflect broken state
            if user_string == lock.lock_string and user_wpm >= lock.wpm_target:                 # validate user attempt
                lock.broken = True
                lock.broken_by_user = player_id
                
                points = lock.points
                lock.points = 0
                
                self.remaining_locks -= 1
                lock.claimed_by_user = None
            
                return True, points
            
            # unclaim the lock upon failure to free up for other players 
            else:
                lock.claimed_by_user = None
                return False, 0

    # swap in lock with new data in place 
    def update_lock(self, lock):
        if 0 <= lock.lock_id < self.size:                                                       # redundancy check                      
            self.grid[lock.lock_id] = lock

    # IMPORTANT: for now the whole grid is being used, but for efficiency it's better if only locks are transmitted
    # turn grid data into dictionary
    def to_dict(self):
        return [lock.to_dict() for lock in self.grid]

    # construct grid from given dictionary
    @staticmethod
    def from_dict(data, height, width):
        temp = Grid(height, width)
        for d in data:
            temp.grid.append(Lock.from_dict(d))
            temp.remaining_locks = sum(1 for lock in temp.grid if not lock.broken)
        
        return temp

# main game running logic (needs to be modified for server to run this later)
class LocalGameClient:
    def __init__(self, grid_height, grid_width, user_id, icon):
        
        # initialize score board / player metadata (need to make dynamic)
        self.user_id = user_id
        self.icon = icon

        self.players = {
            user_id: {
                "icon": icon,
                "score": 0,
                "locks_broken": 0
            },
            "bot1": {
                "icon": "★",
                "score": 50,
                "locks_broken": 1
            },
            "bot2": {
                "icon": "♞",
                "score": 30,
                "locks_broken": 1
            }
        }

        # grid initialization
        self.grid = Grid(grid_height, grid_width)
        self.grid.generate_locks()
    
    # return lock from grid with given id
    def get_lock(self, lock_id):
        return self.grid.get_lock(lock_id)
    
    # get entire grid
    def get_all_locks(self):
        return self.grid.get_grid()

    # return grid dimensions
    def get_dimensions(self):
        return self.grid.get_dimensions()

    # attempt to claim lock using user input 
    def try_claim(self, lock_id):
        return self.grid.claim_lock(lock_id, self.user_id)

    # attempt to break lock using user input 
    # updates score board as apppropriate
    def try_break(self, lock_id, user_string, user_wpm):
        success, points = self.grid.break_lock(lock_id, user_string, user_wpm, self.user_id)
        
        if success:
            self.players[self.user_id]["score"] += points
            self.players[self.user_id]["locks_broken"] += 1
        
        return success, points
    
    # get number of remaining locks
    def get_remaining_locks(self):
        return self.grid.remaining_locks

    # get dictionary for scoreboard
    def get_player_dict(self):
        return self.players