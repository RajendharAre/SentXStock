"""
Admin Authentication — simple HMAC-signed token system.
Credentials are stored in .env:  ADMIN_USERNAME  ADMIN_PASSWORD
Token is a base64-encoded HMAC-SHA256 signature valid for 8 hours.
"""

import os
import hmac
import hashlib
import base64
import time
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (one level up from this admin/ folder)
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
_SECRET        = os.getenv("ADMIN_SECRET",   "").encode()

TOKEN_TTL = 8 * 3600  # 8 hours in seconds


def _sign(payload: str) -> str:
    """Return base64-encoded HMAC-SHA256 of payload."""
    sig = hmac.new(_SECRET, payload.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode()


def generate_token() -> str:
    """Generate a time-stamped admin token."""
    expires_at = int(time.time()) + TOKEN_TTL
    payload    = f"admin:{expires_at}"
    signature  = _sign(payload)
    raw        = f"{payload}:{signature}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def verify_token(token: str) -> bool:
    """Return True if token is valid and not expired."""
    try:
        raw       = base64.urlsafe_b64decode(token.encode()).decode()
        parts     = raw.rsplit(":", 1)          # split off the signature
        if len(parts) != 2:
            return False
        payload, signature = parts
        if not hmac.compare_digest(_sign(payload), signature):
            return False
        _, expires_at = payload.split(":", 1)
        if int(time.time()) > int(expires_at):
            return False
        return True
    except Exception:
        return False


def check_credentials(username: str, password: str) -> bool:
    """Validate admin username + password."""
    return (
        hmac.compare_digest(username, ADMIN_USERNAME) and
        hmac.compare_digest(password, ADMIN_PASSWORD)
    )
