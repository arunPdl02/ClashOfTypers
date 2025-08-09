# networking.py

# TCP or UDP?
#
# TCP should be able to handle everything and it should be used for everything that needs to be reliable, so all game state related data
# However, it won't be able to handle mouse cursor rendering. Two options:
#
# Either UDP is used as a separate socket purely for this
# or 
# The polling rate for the mouse cursor is limited, transmit information every 200-300ms (the countdown utility can help with this), draw from last stored coordinates

# INITIALISATION
#
# note that sending the whole grid may not be possible as grids get larger, in which case fragmentation would need handling I think
# though after initialization all packets should be well under 1500 bytes
# if raw strings for the user names are causing issues then enumerated player_id's could be used instead
#
# upon initialization clients send their icon and user_name. server creates dictionary of icon and user names to broadcast to clients (player: icon)
# server generates grid and sends the whole grid once upon initialization 
# client stores grid and the renderer draws it as normal
# client stores player dictionary and renderer uses this to draw the icons and plaer names on the HUD
# client also randomly assigns cursor colors to each player in the dictionary but this information stays unique to local rendering
# lock objects contain most of the information that is needed, and so during the live game mainly broadcast lock updates to everyone
# rely on lock user_name attribute to render icons that have been claimed
# rely on lock available attribute to render no player icon
# rely on lock broken attribute to render a lock as "broken" 

# MOUSE CURSOR RENDERING
#
# clients always transmit user coordinates to server
# if they are in the lock break screen then the coordinates are transmitted as None
# server combines these packets as a dictionary object that is broadcasted to all users
# client renderer will draw icons only if the user is not in the lock break screen
# using None clients that are currently breaking locks should not have their cursor rendered 
# if they are not on the lock break screen then they send None or something else

# WPM checks
#
# after the broadcast is sent the server waits for a message only from the client that has claimed this particular lock
# once the user starts typing the start_time is saved by the client
# once the user presses enter the client saves the end_time
# client also counts the total number of keyboard presses that occurred excluding backspace and enter
# the final packet contains both timestamps, the total and the string that the user input
# the server uses both timestamps and subtracts them to get the time taken for typing
# then this is used to divide the total key presses (adjust for fact that time will be in milliseconds, minutes need to be extrapolated)
# the result is the wpm, from here on the LOCK BREAK logic follows as described below
#
# start_time, end_time could be sent in different packets for more complex validation
# server could start it's own set of clocks to time the user and stop clocks when receiving the packets to account for RTT to get the true time
# this could potentially provide safety against hacked clients who may cheat if calculated properly

# LOCK CLAIM
#
# when a client clicks on a lock a message is sent to request access
# the server processes the first packet it receives and verifies whether the lock is available
# if it is then the lock is updated to reflect the same and the lock object is broadcasted to all clients (they will use this to update the local grid, rest the renderer can handle)
#
# clients should not wait for any message from the server, rather they can use the lock to check if lock.claimed_by_user == player_name
# if true then the lock is yours and you can proceed with the lock_break object
# if false, then the local client renders some sort of "fail" message (and the updated icon) which players use to try and click another lock

# LOCK BREAK
#    
# once the player is in the lock break screen they type as usual
# if 10 seconds are over or the user presses enter then the verify success message and the packet contains user string and wpm (calculated locally)
# server checks whether the string and wpm is acceptable and breaks the lock
# internal score board dictionary (player: total_points, locks_broken) and the locks_remaining variable is updated depending on outcome
#
# if True
# update lock set broken=True, available=False, broken_by_user=Player, 
# update dictionary: increment player total_points by points and locks_broken by 1
# decrement remaining_locks variable
# 
# if False
# update lock set broken=False, available=True, broken_by_user=None, claimed_by_user=None
# don't update dictionary
#
# server broadcasts the updated lock, dictionary, and locks_remaining to all clients 
#
# client processes packet, if lock.broken_by_user == player_name
# if true display something, if false display something
# either way, only the packet variables need to be used to update the local, similar logic used by server
#
# next call to renderer should automatically be able to use the updated info to make relevant changes to the GUI

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
