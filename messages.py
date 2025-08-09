# messages.py

# Defines message format constants and helpers (used by client & server)
# Author: Surya


# Message types:
MSG_CLAIM_REQ = "claim_request"             # client claim request (lock_id, user_name)
MSG_BREAK_REQ = "break_request"             # client break lock request (lock_id, user_string, wpm)
MSG_GRID_UPDATE = "grid_update"             # broadcast all clients lock object (lock object, player dict)
MSG_MOUSE_COORDS = "mouse_coords"           # client sends mouse coordinates to server
MSG_LOBBY_UPDATE = "lobby_update"           # server broadcasts player list and host
MSG_START_REQ = "start_game_request"        # client requests game start (host only)
MSG_START_GAME = "start_game"               # server announces synchronized game start
MSG_JOIN = "join"                           # client announces desired user_id/icon on connect
MSG_JOIN_ACK = "join_ack"                   # server acknowledges and returns the accepted user_id

# Server result/ack types:
MSG_CLAIM_RES = "claim_result"              # server response to claim request
MSG_BREAK_RES = "break_result"              # server response to break request

# Unclaim flow (client cancels a claim)
MSG_UNCLAIM_REQ = "unclaim_request"         # client requests to release a claimed lock
MSG_UNCLAIM_RES = "unclaim_result"          # server response to unclaim request
