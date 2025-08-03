# networking.py

import socket
import json
import threading
from messages import *
from collections import deque

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
