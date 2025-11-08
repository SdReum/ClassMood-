"""Password utilities using bcrypt.

Never store raw passwords. We store only hashes produced by bcrypt.
"""

import bcrypt


def hash_password(password: str) -> str:
    """Return a bcrypt hash for the given plain-text password.

    bcrypt automatically salts the password, so the same password will
    produce different hashes each time (which is good for security).
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check whether a plain-text password matches a stored bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))