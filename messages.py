# messages.py

# Defines message format constants and helpers (used by client & server)
# Author: Surya

# 1. Define standard message types
# 2. Helper functions to format JSON messages

# Message types:
MSG_CLAIM_REQ = "claim_request"             # client claim request (lock_id, user_name)
MSG_BREAK_REQ = "break_request"             # client break lock request (lock_id, user_string, wpm)
MSG_GRID_UPDATE = "grid_update"             # broadcast all clients lock object (lock object, player dict)
MSG_MOUSE_COORDS = "mouse_coords"           # client sends mouse coordinates to server

# def make_message(type, **kwargs): return json.dumps(...)
# def parse_message(data): return json.loads(...)
