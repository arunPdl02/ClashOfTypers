# networking.py


import socket
import threading
import json
from collections import deque
from messages import *
from utils import normalize_text_for_match


# using TCP
class ClientNetwork:
    def __init__(self, user_id, server_ip='127.0.0.1', server_port=5555):
        
        # multithreading
        self.user_id = user_id
        self.sock = socket.socket()
        self.addr = (server_ip, server_port)
        self.packet_stack = deque()
        self.lock = threading.Lock()
        self.running = True
        
        # connection attempt
        try:
            print(f"[networking] Connecting to {self.addr}")
            self.sock.connect(self.addr)
            threading.Thread(target=self._listen, daemon=True).start()
            # Introduce ourselves with desired id/icon so server can align names
            try:
                self._send(MSG_JOIN)
            except Exception:
                pass
        except Exception as e:
            print(f"[networking] Connection failed: {e}")
            raise SystemExit("Could not connect to server.")

    # socket active listener
    def _listen(self):
        buf = ""
        while self.running:
            try:
                # convert bytes to string
                data = self.sock.recv(1500).decode()
                if not data:                                                            # empty string
                    continue
                buf += data

                # split string by new line
                while '\n' in buf:
                    line, buf = buf.split('\n', 1)
                    try:
                        # parse as JSON
                        msg = json.loads(line.strip())
                        # DEBUG: log inbound messages once we've parsed them
                        try:
                            print("[CLIENT] RECV", msg)
                        except Exception:
                            pass
                        
                        with self.lock:                                                 # lock thread before writing
                            self.packet_stack.append(msg)           
                    except:
                        continue
            except:
                self.running = False
    
    # helper to send messages as JSON encoded to byte format, '\n' as delimiter
    def _send(self, msg_type, **kwargs):
        msg = {"type": msg_type, "user_id": self.user_id, **kwargs}
        
        # temporary until server is made
        try:
            self.sock.sendall((json.dumps(msg) + '\n').encode())
        except:
            pass
    
    # push to stack only after locking thread
    def _push(self, msg):
        with self.lock:
            self.packet_stack.append(msg)

    def send_claim(self, lock_id):
        self._send(MSG_CLAIM_REQ, lock_id=lock_id)
    
    # should be modified to send start time, stop time and number of char inputs for server side wpm verification
    def send_break(self, lock_id, user_string, user_wpm):
        # Normalize before sending to reduce mismatches end-to-end
        safe_string = normalize_text_for_match(user_string)
        self._send(MSG_BREAK_REQ, lock_id=lock_id, user_string=safe_string, user_wpm=user_wpm)

    def send_unclaim(self, lock_id):
        self._send(MSG_UNCLAIM_REQ, lock_id=lock_id)

    def send_start_game(self):
        self._send(MSG_START_REQ)
    
    def send_join(self, icon="★"):
        self._send(MSG_JOIN, icon=icon)

    def get_packet(self, msg_type):
        # Scan the queue without losing order; return the first matching packet
        with self.lock:
            found = None
            size = len(self.packet_stack)
            for _ in range(size):
                pkt = self.packet_stack.popleft()
                if found is None and pkt.get("type") == msg_type:
                    found = pkt
                    # do not append back; effectively remove it
                else:
                    self.packet_stack.append(pkt)
            return found

    def close(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass
