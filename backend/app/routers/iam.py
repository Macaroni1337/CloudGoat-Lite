import httpx
from fastapi import APIRouter, Depends, HTTPException

from app import auth, db
from app.deps import get_current_user
from app.models import LogoImportRequest, RoleAssignmentCreate, TokenExchangeRequest

router = APIRouter(prefix="/api/iam", tags=["iam"])


@router.get("/users")
def list_users(current_user: dict = Depends(get_current_user)):
    return [
        {
            "id": u["id"],
            "principal_type": "user",
            "display_name": u["display_name"],
            "email": u["email"],
            "role": u["role"],
            "resource_group": u["resource_group"],
            "title": u["title"],
        }
        for u in db.users.values()
    ]


@router.get("/app-registrations")
def list_app_registrations(current_user: dict = Depends(get_current_user)):
    """
    Visible in the IAM / Access Control page like a real console audit view.
    Initech-Deploy-Bot's scope="subscription" is the tell for V4 - a careful
    look shows it holds Contributor over the whole tenant instead of just
    RG-Production, which is all its description says it needs.
    Client secrets are intentionally NOT included here - they're only
    reachable via the other planted bugs (V3 public storage, V6 SSRF).
    """
    return [
        {
            "id": a["id"],
            "principal_type": "service_principal",
            "name": a["name"],
            "client_id": a["client_id"],
            "role": a["role"],
            "scope": a["scope"],
            "description": a["description"],
        }
        for a in db.app_registrations.values()
    ]


@router.post("/app-registrations/{app_id}/token")
def exchange_client_credentials(app_id: int, body: TokenExchangeRequest):
    """Lets a caller authenticate AS a service principal, given its
    client_id/client_secret - mirrors an OAuth2 client-credentials grant.
    This is the intended way to "become" Deploy-Bot once its secret has been
    obtained from the leaked storage file (V3/V4 chain)."""
    app = db.app_registrations.get(app_id)
    if app is None or app["client_id"] != body.client_id or app["client_secret"] != body.client_secret:
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    token = auth.create_token(
        sub=app["name"],
        principal_id=app["id"],
        principal_type="service_principal",
        role=app["role"],
    )
    return {"access_token": token, "token_type": "bearer"}


@router.get("/role-assignments")
def list_role_assignments(current_user: dict = Depends(get_current_user)):
    return list(db.role_assignments.values())


@router.post("/role-assignments")
def create_role_assignment(body: RoleAssignmentCreate, current_user: dict = Depends(get_current_user)):
    """
    VULNERABILITY (V7 - privilege escalation): this endpoint calls
    get_current_user (so SOME valid token is required) but never checks that
    current_user["role"] == "Owner" before granting a new role assignment.
    Any authenticated principal - including the low-privilege intern - can
    call this directly (e.g. via curl/Burp, bypassing the fact that the UI
    only shows this form to admins) and grant themselves Owner.
    """
    if body.principal_type == "user":
        principal = db.users.get(body.principal_id)
    elif body.principal_type == "service_principal":
        principal = db.app_registrations.get(body.principal_id)
    else:
        raise HTTPException(status_code=400, detail="principal_type must be 'user' or 'service_principal'")

    if principal is None:
        raise HTTPException(status_code=404, detail="Principal not found")

    rid = db.next_id("role_assignments")
    assignment = {
        "id": rid,
        "principal_type": body.principal_type,
        "principal_id": body.principal_id,
        "role": body.role,
        "scope": body.scope,
    }
    db.role_assignments[rid] = assignment

    # Reflect the new role directly on the principal record so the change is
    # immediately visible/effective (no re-login required to see impact).
    principal["role"] = body.role

    return assignment


@router.post("/app-registrations/{app_id}/logo")
def import_logo(app_id: int, body: LogoImportRequest, current_user: dict = Depends(get_current_user)):
    """
    VULNERABILITY (V6 - SSRF): fetches an arbitrary attacker-supplied URL
    server-side with no scheme/host allowlist, no blocking of loopback or
    link-local addresses, and returns the response body back to the caller.
    Pointing `url` at this server's own internal metadata route
    (http://127.0.0.1:8000/internal/metadata/instance or
    http://localhost:8000/internal/metadata/instance) works because the
    *fetch itself* originates from the backend process (source = loopback),
    exactly like real IMDS-based credential theft via SSRF.
    """
    if app_id not in db.app_registrations:
        raise HTTPException(status_code=404, detail="App registration not found")

    try:
        response = httpx.get(body.url, timeout=5.0, follow_redirects=True)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch logo URL: {exc}")

    return {
        "requested_url": body.url,
        "status_code": response.status_code,
        "body": response.text[:4000],
    }
