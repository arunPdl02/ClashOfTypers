import socket
import threading
import json
from game import Game
from messages import *
from config import GRID_ROWS, GRID_COLS

class Server:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
        self.game = Game(GRID_ROWS, GRID_COLS)
        self.player_data = {}
        self.lock = threading.Lock()

    def _send(self, client_socket, message):
        try:
            client_socket.send((json.dumps(message) + '\n').encode())
        except:
            try:
                self.clients.remove(client_socket)
            except ValueError:
                pass

    def broadcast(self, message):
        for client_socket in list(self.clients):
            self._send(client_socket, message)

    def handle_client(self, client_socket, addr):
        print(f"Accepted connection from {addr}")
        buffer = ""
        # On connect, send initial state
        init_payload = {"type": MSG_GRID_UPDATE, "grid": self.game.to_dict(), "players": self.player_data}
        self._send(client_socket, init_payload)
        
        while True:
            try:
                data = client_socket.recv(1500).decode()
                if not data:
                    break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if not line.strip():
                        continue
                    try:
                        msg = json.loads(line.strip())
                    except json.JSONDecodeError:
                        continue
                    self._process_message(client_socket, msg)
            except ConnectionError:
                break
            except Exception:
                break
        try:
            self.clients.remove(client_socket)
        except ValueError:
            pass
        client_socket.close()

    def _process_message(self, client_socket, msg):
        msg_type = msg.get("type")
        user_id = msg.get("user_id", "unknown")
        # Ensure player in registry
        with self.lock:
            if user_id not in self.player_data:
                self.player_data[user_id] = {"icon": "★", "score": 0, "locks_broken": 0}

        if msg_type == MSG_CLAIM_REQ:
            lock_id = msg.get("lock_id")
            if lock_id is None:
                return
            with self.lock:
                lock = self.game.get_lock(lock_id)
                success = self.game.claim_lock(lock, user_id)
                # Broadcast updated lock state (or full grid for simplicity)
                payload = {"type": MSG_GRID_UPDATE, "grid": self.game.to_dict(), "players": self.player_data}
            self.broadcast(payload)

        elif msg_type == MSG_BREAK_REQ:
            lock_id = msg.get("lock_id")
            user_string = msg.get("user_string", "")
            user_wpm = msg.get("user_wpm", 0)
            if lock_id is None:
                return
            with self.lock:
                lock = self.game.get_lock(lock_id)
                success, points = self.game.break_lock(lock, user_string, user_wpm)
                if success:
                    self.player_data[user_id]["score"] += points
                    self.player_data[user_id]["locks_broken"] += 1
                payload = {"type": MSG_GRID_UPDATE, "grid": self.game.to_dict(), "players": self.player_data}
            self.broadcast(payload)
        else:
            # ignore unknown for now
            pass

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Server listening on {self.host}:{self.port}")

        while True:
            client_socket, addr = self.server_socket.accept()
            self.clients.append(client_socket)
            t = threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True)
            t.start()
            
if __name__ == "__main__":
    server = Server()
    server.start()
