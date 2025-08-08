# CMPT 371 Project Report — Clash of Typers

## 1) Game Description & Design

Clash of Typers is a client–server multiplayer typing game. A 5×5 grid of locks is shared among all players. Each lock has:
- difficulty: easy/medium/hard
- target WPM threshold
- a unique sentence to type

Players can claim one lock at a time. While claimed, that lock is unavailable to others (the shared-object “lock”). The claimant must type the sentence and press Enter. If the typed string matches exactly and the WPM meets the target, the lock becomes broken, points are awarded, and the lock becomes permanently unavailable. Otherwise, the lock is released and returns to available state.

The server is authoritative: it grants claims, validates break attempts, updates scores, and broadcasts state to all clients. A lobby allows players to join; the first player is the host who can start the game with a synchronized countdown.

## 2) Application-layer Messaging Scheme

- Transport: TCP sockets
- Encoding: JSON per message, with a single newline character ("\n") as the delimiter
- Message fields: each message contains `type` and usually a `user_id`, plus message-specific fields

Key message types (see `messages.py`):
- `claim_request`, `break_request`, `unclaim_request`
- `claim_result`, `break_result`, `unclaim_result`
- `grid_update` (authoritative grid + players)
- `lobby_update` (players, host_id, game_started)
- `start_game_request`, `start_game` (countdown + game_time)

Example (client → server):
```json
{"type": "claim_request", "user_id": "Alice", "lock_id": 7}
```
Example (server → client broadcast):
```json
{"type": "grid_update", "grid": [...], "players": {"Alice": {"score": 10, ...}}}
```

## 3) Opening Sockets (code snippets)

Server socket open/bind/listen (`server.py`):
```python
HOST = '0.0.0.0'
PORT = 5555

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()
print(f"[SERVER] Running on {HOST}:{PORT}")
```
Accepting clients with `select` (`server.py`):
```python
read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

for notified_socket in read_sockets:
    if notified_socket == server_socket:  # new player connecting
        client_socket, client_address = server_socket.accept()
        sockets_list.append(client_socket)
```
Client connect and background listener (`networking.py`):
```python
class ClientNetwork:
    def __init__(self, user_id, server_ip='127.0.0.1', server_port=5555):
        self.user_id = user_id
        self.sock = socket.socket()
        self.addr = (server_ip, server_port)
        # ...
        print(f"[networking] Connecting to {self.addr}")
        self.sock.connect(self.addr)
        threading.Thread(target=self._listen, daemon=True).start()
```

## 4) Handling the Shared Object (locks)

Exclusive claim logic (`game.py`):
```python
def claim_lock(self, lock_id, player_id):
    lock = self.get_lock(lock_id)
    if lock.is_claimable_by(player_id):
        lock.claimed_by_user = player_id
        return True
    return False
```

Break logic (validation + scoring; release on failure) (`game.py`):
```python
def break_lock(self, lock_id, user_string, user_wpm, player_id):
    lock = self.get_lock(lock_id)
    if not lock:
        return False, 0
    if not lock.broken and lock.claimed_by_user == player_id:
        if user_string == lock.lock_string and user_wpm >= lock.wpm_target:
            lock.broken = True
            lock.broken_by_user = player_id
            points = lock.points
            lock.points = 0
            self.remaining_locks -= 1
            lock.claimed_by_user = None
            return True, points
        else:
            lock.claimed_by_user = None
            return False, 0
    return False, 0
```

Server request handling + broadcast (`server.py`):
```python
if msg_type == MSG_CLAIM_REQ:
    lock_id = msg.get("lock_id")
    success = grid.claim_lock(lock_id, user_id)
    lock = grid.get_lock(lock_id)
    send(notified_socket, {"type": MSG_CLAIM_RES, "success": success, "lock": lock.to_dict()})
    broadcast({"type": MSG_GRID_UPDATE, "grid": grid.to_dict(), "players": players})

elif msg_type == MSG_BREAK_REQ:
    lock_id = msg.get("lock_id")
    user_string = msg.get("user_string")
    user_wpm = msg.get("user_wpm")
    success, points = grid.break_lock(lock_id, user_string, user_wpm, user_id)
    lock = grid.get_lock(lock_id)
    if success:
        players[user_id]["score"] += points
        players[user_id]["locks_broken"] += 1
    send(notified_socket, {"type": MSG_BREAK_RES, "success": success, "points": points, "lock": lock.to_dict()})
    broadcast({"type": MSG_GRID_UPDATE, "grid": grid.to_dict(), "players": players})
```

## 5) Architecture Overview

- Server: single-threaded `select` loop, authoritative state, broadcasts JSON updates
- Client: background thread for socket reads, message queue, Pygame render loop
- State sync: clients keep a local grid, the server is the source of truth and pushes updates after each mutation
- Concurrency control: per-lock claim gating on the server ensures only one claimant at a time

## 6) How to Build & Run

- Install: `pip install pygame nltk`
- Download NLTK corpora (once): `python -m nltk.downloader punkt gutenberg`
- Start server (host): `python server.py`
- Start clients: `python client.py <UserName> <ServerIP> <Port>`
  - Example: `python client.py Alice 192.168.1.50 5555`

## 7) Group Members & Contributions

- Manan — 25% (Client UI and game logic)
- Surya — 25% (Messaging protocol and networking)
- Rushik — 25% (Configuration and utilities)
- Arun — 25% (WPM calculation and server)

## 8) Demo Video (to include)

Record a 1–2 minute video showing at least 3 clients: host starts; players claim different locks; at least one successful break and one failed attempt; final scoreboard.