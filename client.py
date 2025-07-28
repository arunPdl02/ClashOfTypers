# client.py

# Connects to server, displays grid, handles input & game updates.
# Author : Manan

# 1. Connect to the server via socket
# 2. Display grid of locks using Tkinter
# 3. Handle user clicks on locks (send attempt message)
# 4. Show typing challenge on lock granted
# 5. Update grid + scoreboard based on server messages

# Imports
import tkinter as tk
from messages import *
from game import *
from wpm import *

# Main loop:
#     receive messages
#     render grid
#     send unlock results after typing
