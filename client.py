# client.py

# Connects to server, displays grid, handles input & game updates.
# Author : Manan + Surya

# 1. Connect to the server via socket
# 2. Display grid of locks using Tkinter
# 3. Handle user clicks on locks (send attempt message)
# 4. Show typing challenge on lock granted
# 5. Update grid + scoreboard based on server messages

# Main loop:
#     receive messages
#     render grid
#     send unlock results after typing

# Cient-server:
# send message to server to claim lock
# process server message
# if success lock screen start
# or display claim fail screen
# server should send updated grid (lock not available) to all clients

# client_main.py
# Clean version of client.py integrated with networking
# client_main.py
import sys
from networking import ClientNetwork
from game import Grid
from game_ui import GameUI
from messages import MSG_GRID_UPDATE
from config import *

# Allow overriding server IP/port via CLI
# Usage: python client.py <user_id> <server_ip> <port>
user_id = sys.argv[1] if len(sys.argv) > 1 else "Player1"
server_ip = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
try:
    server_port = int(sys.argv[3]) if len(sys.argv) > 3 else 5555
except ValueError:
    server_port = 5555

# Connect to the server
network = ClientNetwork(user_id, server_ip, server_port)
print("[CLIENT] Waiting for initial grid update...")

# Wait for MSG_GRID_UPDATE
init_packet = None
while init_packet is None:
    init_packet = network.get_packet(MSG_GRID_UPDATE)

# Extract grid and players
grid = Grid.from_dict(init_packet["grid"], GRID_ROWS, GRID_COLS)
players = init_packet["players"]

# Launch the UI
game_ui = GameUI(grid, players, network, user_id)
game_ui.run()
