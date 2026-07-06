import jwt
from fastapi import Header, HTTPException

from app import auth, db


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    """
    Validates the bearer token's signature and expiry and resolves it to a
    live principal record (user or service principal / app registration).

    NOTE: this only proves "who are you", never "are you allowed to do this".
    Every router is responsible for its own authorization checks - and V5/V7
    are exactly the routers that forgot to add one. There is no role/scope
    gate here on purpose; adding one here would blanket-fix bugs this lab is
    designed to teach.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = auth.decode_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    principal_type = payload.get("principal_type")
    principal_id = payload.get("principal_id")

    if principal_type == "user":
        record = db.users.get(principal_id)
    elif principal_type == "service_principal":
        record = db.app_registrations.get(principal_id)
    else:
        record = None

    if record is None:
        raise HTTPException(status_code=401, detail="Principal no longer exists")

    # Live record wins over the token's stale claims (e.g. role may have
    # changed since the token was issued, such as after a role assignment).
    return record


def get_optional_current_user(authorization: str | None = Header(default=None)) -> dict | None:
    """Same as get_current_user, but returns None instead of 401 when no
    Authorization header is present at all. Used by endpoints (like public
    storage objects) that are intentionally reachable anonymously."""
    if not authorization:
        return None
    return get_current_user(authorization)
