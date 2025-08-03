# networking.py

import socket
import json
import threading
from messages import *
from collections import deque

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

class ClientNetworkHandler:
    def __init__(self, server_ip='localhost', server_port=5555, user_id=None):
        # connection set up
        self.server_ip = server_ip
        self.server_port = server_port
        self.user_id = user_id
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.server_ip, self.server_port))

        # multithreading for concurrent updates                             
        self.running = True
        self.lock = threading.Lock()
        self.msg_event = threading.Event()
        
        # behaves like circular linked list to allow insertion/retrieval from both ends in O(1), but used as LIFO
        self.buffers = {                                                            # separate buffers based on frequency
            "grid_update": deque(),                                                 # grid_updates are "real-time" broadcasts, mainly for UI updates and so they will be hihg freq 
            "responses": deque(),                                                   # responses holds message replies from server for the specific client
        }                                                                           
                                                      
        threading.Thread(target=self._listener, daemon=True).start()

    # helper to receieve messages from server
    def _listener(self):
        while self.running:
            try:
                data = self.sock.recv(4096)                                         # assume receiving complete message
                if not data:
                    break
                decoded = data.decode()

                for raw in decoded.strip().split('\n'):                             # assume message delimiter is '\n' for parsing
                    msg = json.loads(raw)
                    
                    with self.lock:
                        msg_type = msg.get("type")
                        if msg_type == MSG_GRID_UPDATE:
                            self.buffers["grid_update"].append(msg)
                        else:
                            self.buffers["responses"].append(msg)
                        self.msg_event.set()
            except:
                break
        
    # helper for sending messages to server
    def _send(self, message):
        try:
            self.sock.sendall((json.dumps(message) + '\n').encode())
        except Exception as e:
            print("Send failed:", e)

    # client message types
    def send_claim_request(self, lock_id):
        self._send({
            "type": MSG_CLAIM_REQ,
            "user_id": self.user_id,
            "lock_id": lock_id
        })

    def send_unlock_success(self, lock_id, user_string, user_wpm):
        self._send({
            "type": MSG_VERIFY_SUCCESS,
            "user_id": self.user_id,
            "lock_id": lock_id,
            "user_wpm": user_wpm,
            "user_string": user_string
        })

    def send_unlock_fail(self, lock_id):
        self._send({
            "type": MSG_INFORM_BREAKFAIL,
            "user_id": self.user_id,
            "lock_id": lock_id
        })

    # waits for response message and fetches latest grid update
    def wait_for_message_type(self, expected_types, timeout=5.0):
        self.msg_event.wait(timeout)

        with self.lock:
            response = None

            # check if the stored response is of interest
            if self.response_packet and self.response_packet.get("type") in expected_types:
                response = self.response_packet
            self.response_packet = None  # clear it

            # get most recent grid update, clear older
            grid_update = self.grid_updates[-1] if self.grid_updates else None
            self.grid_updates.clear()

        return response, grid_update

    '''
    Old implementation, keeping here since might modify and use the concept later

    # update buffer and retrieve multiple expected packets
    # utilizes only O(1) operations, automatically clears old packets by only keeping newer ones, retrieves partial if not all types are present  
    def wait_for_message_type(self, expected_types, timeout=5.0):               
        self.msg_event.wait(timeout)                                                    # update buffer, wait 5 ticks
        temp = deque()
        output_arr = []

        with self.locks:                                                                # lock thread to prevent desynced updated of self.buffer
        # iterate until message buffer is empty
            while self.buffer:
                if len(output_arr) == len(expected_types):                              # exit loop early
                    break
                
                msg = self.buffer.pop()                                                 # get latest message                                    
                if msg.get("type") in expected_types:                                   
                    output_arr.append(msg)                                              # if expected type append to output
                else:
                    temp.appendleft(msg)                                                # else push to front of queue to maintain order
            
            self.buffer.clear()                                                         # clear buffer in place
            self.buffer.extend(temp)                                                    # append new deque 
            
            return output_arr
    '''
    # close connection
    def close(self):
        self.running = False
        self.sock.close()
