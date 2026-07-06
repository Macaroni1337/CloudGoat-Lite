from fastapi import APIRouter, Depends, HTTPException

from app import db
from app.deps import get_current_user

router = APIRouter(prefix="/api/keyvault", tags=["keyvault"])


@router.get("/vaults")
def list_vaults(current_user: dict = Depends(get_current_user)):
    return list(db.key_vaults.values())


@router.get("/{vault_id}/secrets")
def list_secrets(vault_id: int, current_user: dict = Depends(get_current_user)):
    """
    VULNERABILITY (V5 - broken Key Vault access policy): this is meant to be
    an admin-only view (only Owner should be able to list/read secret
    values), but the access policy was never actually enforced in code - it
    only checks that the caller has SOME valid token via get_current_user,
    not that current_user["role"] == "Owner". Any authenticated user,
    including a bare Reader, can pull plaintext secret values.
    """
    if vault_id not in db.key_vaults:
        raise HTTPException(status_code=404, detail="Key vault not found")
    return [s for s in db.key_vault_secrets.values() if s["vault_id"] == vault_id]
