from contextvars import ContextVar

# Context variable to securely hold the current user's ID during a request lifecycle
current_user_id: ContextVar[str] = ContextVar("current_user_id", default="")
