"""
KilnLink / Parali Mitra Configuration and Secrets Manager
Loads dotenv ONCE at module import (root .env first, then backend/.env).
Exposes typed accessor functions so raw secrets are never logged or leaked.
"""
import os
import hmac
import pathlib
from typing import List, Optional

_DOTENV_LOADED = False

def _init_dotenv():
    global _DOTENV_LOADED
    if not _DOTENV_LOADED:
        try:
            from dotenv import load_dotenv
            base_dir = pathlib.Path(__file__).resolve().parent.parent.parent
            root_env = base_dir / ".env"
            backend_env = base_dir / "backend" / ".env"
            if root_env.exists():
                try:
                    load_dotenv(dotenv_path=root_env, override=False, encoding="utf-8")
                except Exception:
                    try:
                        load_dotenv(dotenv_path=root_env, override=False, encoding="utf-16")
                    except Exception:
                        pass
            if backend_env.exists():
                try:
                    load_dotenv(dotenv_path=backend_env, override=False, encoding="utf-8")
                except Exception:
                    pass
        except Exception:
            pass
        _DOTENV_LOADED = True

_init_dotenv()


def get_admin_key() -> Optional[str]:
    """
    Returns the configured ADMIN_KEY from environment, or None if unset.
    No hard-coded fallback is ever used.
    """
    v = os.environ.get("ADMIN_KEY", "").strip()
    return v if v else None


def get_firms_key() -> Optional[str]:
    """
    Returns the NASA FIRMS map key from environment, or None if unset.
    """
    v = (os.environ.get("FIRMS_MAP_KEY") or os.environ.get("NASA_FIRMS_MAP_KEY") or "").strip()
    return v if v else None


def get_cors_origins() -> List[str]:
    """
    Returns CORS allowed origins from CORS_ORIGINS environment variable
    (comma-separated), or safe local defaults.
    """
    raw = os.environ.get("CORS_ORIGINS", "").strip()
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return ["http://127.0.0.1:8000", "http://localhost:8000"]


def verify_admin_key(provided_key: Optional[str]) -> bool:
    """
    Constant-time comparison using hmac.compare_digest to prevent timing attacks.
    Returns False if server ADMIN_KEY is not configured or provided key is empty/mismatched.
    """
    expected = get_admin_key()
    if not expected or not provided_key:
        return False
    return hmac.compare_digest(provided_key.strip(), expected)

