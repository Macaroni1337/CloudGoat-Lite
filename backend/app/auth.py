"""
JWT helpers for CloudGoat-Lite.

VULNERABILITY (V1 - see VULNERABILITIES.md): JWT_SECRET is a hardcoded, guessable
string committed to source. Anyone who reads this file (or finds the secret leaked
elsewhere, as would happen in a real engagement via a public repo, a config dump,
or a decompiled client) can forge tokens for ANY user or role, including
"Owner" tenant admin, without ever knowing a real password.
"""
import time
import jwt

JWT_SECRET = "initech-cloud-2024-dev"
JWT_ALGORITHM = "HS256"
TOKEN_LIFETIME_SECONDS = 60 * 60 * 8  # 8 hours


def create_token(*, sub: str, principal_id: int, principal_type: str, role: str, tenant: str = "initech-cloud") -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "principal_id": principal_id,
        "principal_type": principal_type,  # "user" or "service_principal"
        "role": role,
        "tenant": tenant,
        "iat": now,
        "exp": now + TOKEN_LIFETIME_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    # Raises jwt.PyJWTError on invalid signature/expiry - caller turns this into a 401.
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
