# messages.py

# Defines message format constatns and helpers (used by client & server)
# Author: Surya

# 1. Define standard message types
# 2. Helper functions to format JSON messages

# Message types:
MSG_ATTEMPT_LOCK = "attempt_lock"
MSG_LOCK_GRANTED = "lock_granted"
MSG_UNLOCK_SUCCESS = "unlock_success"
MSG_LOCK_CAPTURED = "lock_captured"
MSG_LOCK_DENIED = "lock_denied"

# def make_message(type, **kwargs): return json.dumps(...)
# def parse_message(data): return json.loads(...)
