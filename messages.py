# messages.py

# Defines message format constants and helpers (used by client & server)
# Author: Surya

# 1. Define standard message types
# 2. Helper functions to format JSON messages

# Message types:
MSG_CLAIM_REQ = "claim_request"             # client claim request
MSG_CLAIM_ACCEPTED = "claim_accepted"       # server claim acceptance response
MSG_CLAIM_REJECTED = "claim_rejected"       # server claim rejection response
MSG_VERIFY_SUCCESS = "verify_success"       # client verify string + WPM request
MSG_INFORM_BREAKFAIL = "inform_breakfail"   # client inform server lock break fail 
MSG_LOCK_CAPTURED = "lock_captured"         # 
MSG_LOCK_REVOKED = "lock_revoked"
MSG_GRID_UPDATE = "grid_update"     # broadcast all clients return game.get_grid() after: claim_accepted, lock_captured, lock_revoked 

# def make_message(type, **kwargs): return json.dumps(...)
# def parse_message(data): return json.loads(...)
