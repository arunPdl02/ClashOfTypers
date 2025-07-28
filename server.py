# Cewntral game server. Manages connections, lock states, scores
# Author: Arun

# server.py

# 1. Setup TCP socket server
# 2. Accept incoming client connections
# 3. Keep track of lock states and player scores
# 4. Handle messages: lock attempts, score updates, etc.
# 5. Broadcast game state to all connected clients

# Imports
import socket, select, json
from messages import *
from config import *

# Core: server_socket, sockets_list, player_scores, lock_states
# Loop:
#     handle new connections
#     handle game messages (attempt_lock, unlock_success, etc.)
#     broadcast updates to all clients
