from fastapi import APIRouter, Depends, HTTPException

from app import db
from app.deps import get_current_user

router = APIRouter(prefix="/api/resources", tags=["resources"])


@router.get("")
def list_resources(current_user: dict = Depends(get_current_user)):
    """Properly scoped: only shows resources in the caller's own resource group,
    the same way a real console's default resource list is scoped to what
    you're allowed to see."""
    scope = current_user.get("resource_group") if current_user["principal_type"] == "user" else current_user.get("scope")
    return [r for r in db.resources.values() if r["resource_group"] == scope]


@router.get("/{resource_id}")
def get_resource(resource_id: int, current_user: dict = Depends(get_current_user)):
    """
    VULNERABILITY (V2 - IDOR): looks up a resource purely by its sequential
    integer ID and returns it to any authenticated principal, without checking
    whether resource["resource_group"] matches the caller's own scope. A
    logged-in Reader in RG-Intern-Sandbox can simply increment this ID to read
    resources that live in RG-Production.
    """
    resource = db.resources.get(resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource
