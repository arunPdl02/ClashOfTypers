# server.py

# Game server that handles connections, lock states, scores
# Author: Arun

import socket
import select
import json
from game import Grid
from config import GRID_ROWS, GRID_COLS, GAME_TIME
from messages import *

# Server address
# Bind to all interfaces so remote clients can connect
HOST = '0.0.0.0'
PORT = 5555

# Create TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()

print(f"[SERVER] Running on {HOST}:{PORT}")

# Sockets and game state
sockets_list = [server_socket]
clients = {}  # socket -> player_id
players = {}  # player_id -> { icon, score, locks_broken }
buffers = {} # socket -> partial data buffer
host_id = None
game_started = False

# Game grid
grid = Grid(GRID_ROWS, GRID_COLS)
grid.generate_locks()


# helper to send JSON messages
def send(socket, data):
    try:
        message = json.dumps(data) + '\n'
        socket.sendall(message.encode())
    except:
        pass

# Broadcast message to all clients (except one if needed)
def broadcast(data, exclude_socket=None):
    message = json.dumps(data) + '\n'
    for sock in clients:
        if sock != exclude_socket:
            try:
                sock.sendall(message.encode())
            except:
                pass

# Main loop
while True:
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    for notified_socket in read_sockets:
        if notified_socket == server_socket: #new player connecting
            client_socket, client_address = server_socket.accept()
            sockets_list.append(client_socket)
            # Defer assigning a final id until we receive a join message
            temp_id = f"Player{len(clients) + 1}"
            clients[client_socket] = temp_id
            buffers[client_socket] = ""

            print(f"[CONNECT] {temp_id} from {client_address}")

            # Assign host placeholder if first connection; will update once join arrives
            if host_id is None:
                host_id = temp_id

            # Do not broadcast or send grid yet; wait for join so names/icons are correct

        else: # message from exisiting connection (a update)
            try:
                data = notified_socket.recv(2048).decode()
                if not data:
                    raise ConnectionResetError

                #accumulate in buffer
                buffers[notified_socket] += data

                #process full messages
                while '\n' in buffers[notified_socket]:
                    line, buffers[notified_socket] = buffers[notified_socket].split('\n', 1)
                    if not line.strip():
                        continue

                    msg = json.loads(line.strip())
                    msg_type = msg.get("type")
                    user_id = msg.get("user_id")

                    print(msg)
                    # Ignore gameplay messages until game start
                    if not game_started and msg_type in (MSG_CLAIM_REQ, MSG_BREAK_REQ, MSG_UNCLAIM_REQ):
                        continue

                    # --- JOIN/HELLO ---
                    if msg_type == MSG_JOIN:
                        # Use requested id if available; otherwise, generate unique
                        requested_id = user_id or f"Player{len(players) + 1}"
                        final_id = requested_id
                        suffix = 2
                        while final_id in players:
                            final_id = f"{requested_id}_{suffix}"
                            suffix += 1

                        # Initialize player entry
                        icon = msg.get("icon", "★")
                        players[final_id] = {"icon": icon, "score": 0, "locks_broken": 0}

                        # Map this socket to final id
                        clients[notified_socket] = final_id

                        # Assign host if none yet
                        if host_id is None or host_id not in players:
                            host_id = final_id

                        # Send initial grid and players including their final id
                        send(notified_socket, {
                            "type": MSG_GRID_UPDATE,
                            "grid": grid.to_dict(),
                            "players": players,
                            "your_id": final_id,
                        })

                        # Acknowledge join explicitly so client can rename locally
                        send(notified_socket, {
                            "type": MSG_JOIN_ACK,
                            "user_id": final_id
                        })

                        # Broadcast lobby update with correct names
                        broadcast({
                            "type": MSG_LOBBY_UPDATE,
                            "players": players,
                            "host_id": host_id,
                            "game_started": game_started
                        })
                        continue

                    # --- CLAIM LOCK ---
                    if msg_type == MSG_CLAIM_REQ:
                        lock_id = msg.get("lock_id")
                        success = grid.claim_lock(lock_id, user_id)
                        lock = grid.get_lock(lock_id)
                        
                        #private response back to the player
                        send(notified_socket, {
                            "type": MSG_CLAIM_RES,
                            "success": success,
                            "lock": lock.to_dict()
                        })

                        #broadcast the updated grid and player info
                        broadcast({
                            "type": MSG_GRID_UPDATE,
                            "grid": grid.to_dict(),
                            "players": players
                        })

                    # --- BREAK LOCK ---
                    elif msg_type == MSG_BREAK_REQ:
                        try:
                            lock_id = msg.get("lock_id")
                            user_string = msg.get("user_string")
                            user_wpm = msg.get("user_wpm")

                            success, points = grid.break_lock(lock_id, user_string, user_wpm, user_id)
                            lock = grid.get_lock(lock_id)

                            if success:
                                players[user_id]["score"] += points
                                players[user_id]["locks_broken"] += 1

                            # send response to client
                            send(notified_socket, {
                                "type": MSG_BREAK_RES,
                                "success": success,
                                "points": points,
                                "lock": lock.to_dict()
                            })

                            # broadcast updated grid + scores
                            broadcast({
                                "type": MSG_GRID_UPDATE,
                                "grid": grid.to_dict(),
                                "players": players
                            })

                        except Exception as e:
                            print(f"[SERVER ERROR in BREAK_REQ] {e}")

                    # --- UNCLAIM LOCK ---
                    elif msg_type == MSG_UNCLAIM_REQ:
                        try:
                            lock_id = msg.get("lock_id")
                            success = grid.unclaim_lock(lock_id, user_id)
                            lock = grid.get_lock(lock_id)

                            # send response to client
                            send(notified_socket, {
                                "type": MSG_UNCLAIM_RES,
                                "success": success,
                                "lock": lock.to_dict()
                            })

                            # broadcast updated grid
                            broadcast({
                                "type": MSG_GRID_UPDATE,
                                "grid": grid.to_dict(),
                                "players": players
                            })

                        except Exception as e:
                            print(f"[SERVER ERROR in UNCLAIM_REQ] {e}")

                    # --- START GAME REQUEST (host only) ---
                    elif msg_type == MSG_START_REQ:
                        # Allow only host to trigger once
                        if not game_started and user_id == host_id:
                            game_started = True
                            # Announce synchronized start with a short countdown
                            broadcast({
                                "type": MSG_START_GAME,
                                "countdown_seconds": 3,
                                "game_time": GAME_TIME
                            })
                        else:
                            # If non-host tries, ignore silently
                            pass


            except Exception as e:
                pid = clients.get(notified_socket, "Unknown")
                print(f"[DISCONNECT] {pid}")
                sockets_list.remove(notified_socket)
                del buffers[notified_socket]
                if notified_socket in clients:
                    leaving_id = clients[notified_socket]
                    if leaving_id in players:
                        del players[leaving_id]
                    del clients[notified_socket]
                notified_socket.close()

                # Reassign host if needed and broadcast lobby update
                if pid == host_id:
                    host_id = next(iter(players.keys()), None)
                broadcast({
                    "type": MSG_LOBBY_UPDATE,
                    "players": players,
                    "host_id": host_id,
                    "game_started": game_started
                })

    for sock in exception_sockets:
        sockets_list.remove(sock)
        if sock in clients:
            leaving_id = clients[sock]
            if leaving_id in players:
                del players[leaving_id]
            del clients[sock]
        sock.close()
        # Broadcast lobby update on socket exception removal
        if host_id not in players:
            host_id = next(iter(players.keys()), None)
        broadcast({
            "type": MSG_LOBBY_UPDATE,
            "players": players,
            "host_id": host_id,
            "game_started": game_started
        })
