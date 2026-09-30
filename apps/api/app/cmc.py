"""Backward-compatible CMC client shim.

Delegates to the new services/cmc/client.py module.
Kept for any code that imports from app.cmc directly.
"""

from .services.cmc.client import CMCClient, CMCError, CMCAuthError, CMCRateLimitError

__all__ = ["CMCClient", "CMCError", "CMCAuthError", "CMCRateLimitError"]
