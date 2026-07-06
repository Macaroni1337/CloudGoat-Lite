from fastapi import APIRouter, Depends, HTTPException

from app import db
from app.deps import get_current_user, get_optional_current_user

router = APIRouter(prefix="/api/storage", tags=["storage"])


@router.get("/accounts")
def list_accounts(current_user: dict = Depends(get_current_user)):
    return list(db.storage_accounts.values())


@router.get("/accounts/{account_id}/containers")
def list_containers(account_id: int, current_user: dict = Depends(get_current_user)):
    if account_id not in db.storage_accounts:
        raise HTTPException(status_code=404, detail="Storage account not found")
    return [c for c in db.storage_containers.values() if c["account_id"] == account_id]


@router.get("/containers/{container_id}/objects")
def list_objects(container_id: int, current_user: dict = Depends(get_current_user)):
    container = db.storage_containers.get(container_id)
    if container is None:
        raise HTTPException(status_code=404, detail="Container not found")
    objs = [o for o in db.storage_objects.values() if o["container_id"] == container_id]
    # Metadata listing only - content is fetched via /objects/{id}.
    return [{"id": o["id"], "name": o["name"], "content_type": o["content_type"]} for o in objs]


@router.get("/objects/{object_id}")
def get_object(object_id: int, current_user: dict | None = Depends(get_optional_current_user)):
    """
    VULNERABILITY (V3 - public storage misconfiguration): when the parent
    container's `public` flag is True, this endpoint returns the object's
    content with NO authentication check at all - anyone who can reach the
    API on the network can read it, exactly like a real "public read access"
    blob container / S3 bucket. Private containers still require a valid
    token and a Contributor/Owner role.
    """
    obj = db.storage_objects.get(object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")

    container = db.storage_containers[obj["container_id"]]

    if container["public"]:
        return obj

    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required for private container")
    if current_user["role"] not in ("Owner", "Contributor"):
        raise HTTPException(status_code=403, detail="Reader role cannot read private container objects")

    return obj
