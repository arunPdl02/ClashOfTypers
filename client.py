# client.py

# Connects to server, displays grid, handles input & game updates.
# Author : Manan + Surya

# 1. Connect to the server via socket
# 2. Display grid of locks using Tkinter
# 3. Handle user clicks on locks (send attempt message)
# 4. Show typing challenge on lock granted
# 5. Update grid + scoreboard based on server messages

import sys
import pygame
from networking import ClientNetwork
from game import Grid
from game_ui import GameUI
from messages import MSG_GRID_UPDATE, MSG_JOIN_ACK
from config import *

# Allow overriding server IP/port via CLI
# Usage: python client.py <user_id> <server_ip> <port>
user_id = sys.argv[1] if len(sys.argv) > 1 else "Player1"
server_ip = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
try:
    server_port = int(sys.argv[3]) if len(sys.argv) > 3 else 5555
except ValueError:
    server_port = 5555

# Guard against invalid destination address for clients
if server_ip == "0.0.0.0":
    print("[CLIENT] Warning: '0.0.0.0' is not a valid destination. Using 127.0.0.1 instead.")
    server_ip = "127.0.0.1"

"""
Show a small non-blocking connecting window while waiting for the server's
initial grid update. This guarantees a window appears even if the network
message is delayed.
"""

# Connect to the server
network = ClientNetwork(user_id, server_ip, server_port)
print("[CLIENT] Waiting for initial grid update...")

# Lightweight connecting window
pygame.init()
screen = pygame.display.set_mode((420, 180))
pygame.display.set_caption("Clash Of Typers — Connecting…")
font = pygame.font.Font(None, 28)
clock = pygame.time.Clock()

init_packet = None
ack = None
frame_counter = 0
running_conn = True
while (init_packet is None or ack is None) and running_conn:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running_conn = False
            break

    # Draw simple status
    screen.fill((20, 20, 20))
    dots = (frame_counter // 20) % 4
    status = f"Connecting to {server_ip}:{server_port}" + ("." * dots)
    text = font.render(status, True, (220, 220, 220))
    screen.blit(text, (20, 70))
    pygame.display.flip()

    # Poll for join ack and initial grid packet
    if ack is None:
        ack = network.get_packet(MSG_JOIN_ACK)
        if ack and ack.get("user_id"):
            user_id = ack.get("user_id")
            # Update networking layer so future messages use correct id
            try:
                network.user_id = user_id
            except Exception:
                pass
    init_packet = network.get_packet(MSG_GRID_UPDATE)
    frame_counter += 1

if not running_conn:
    pygame.quit()
    network.close()
    sys.exit(0)

# Tear down the temporary window before launching full UI
pygame.quit()

# Extract grid and players
grid = Grid.from_dict(init_packet["grid"], GRID_ROWS, GRID_COLS)
players = init_packet["players"]

# Launch the UI
game_ui = GameUI(grid, players, network, user_id)
game_ui.run()
