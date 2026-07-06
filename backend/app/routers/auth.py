from fastapi import APIRouter, HTTPException

from app import auth, db
from app.models import LoginRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "username": user["username"],
        "display_name": user["display_name"],
        "email": user["email"],
        "role": user["role"],
        "resource_group": user["resource_group"],
        "principal_type": "user",
    }


@router.post("/login")
def login(body: LoginRequest):
    # Passwords are stored/compared in plaintext - fine for a disposable lab
    # tenant, never do this in anything real.
    user = db.find_user_by_username(body.username)
    if user is None or user["password"] != body.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = auth.create_token(
        sub=user["username"],
        principal_id=user["id"],
        principal_type="user",
        role=user["role"],
    )
    return {"access_token": token, "token_type": "bearer", "user": _public_user(user)}
