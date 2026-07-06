from fastapi import APIRouter, HTTPException, Request

from app import db

router = APIRouter(tags=["metadata"])

# Real cloud instance metadata services (Azure IMDS, AWS IMDS) live at a
# link-local address that is only reachable from within the VM/instance
# itself, and by design require no authentication at all - that lack of
# auth is *correct* there, because network topology is the only access
# control. This route recreates that shape: it only answers requests whose
# source address is loopback (i.e. the request came from this same backend
# process, such as the SSRF-vulnerable logo importer), and refuses anything
# that looks like it came from an external client.
LOOPBACK_ADDRESSES = {"127.0.0.1", "::1"}


@router.get("/internal/metadata/instance")
def instance_metadata(request: Request):
    client_host = request.client.host if request.client else None
    if client_host not in LOOPBACK_ADDRESSES:
        raise HTTPException(status_code=403, detail="metadata service is only reachable from localhost")

    app = None
    for candidate in db.app_registrations.values():
        if candidate["name"] == "Initech-Logo-Importer-Service":
            app = candidate
            break

    return {
        "service": "Initech-Logo-Importer-Service",
        "client_id": app["client_id"] if app else None,
        "client_secret": app["client_secret"] if app else None,
        "role": app["role"] if app else None,
        "scope": app["scope"] if app else None,
        "note": "instance managed-identity credential - exchange via POST /api/iam/app-registrations/{id}/token",
    }
