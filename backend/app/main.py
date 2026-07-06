import socket

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import seed_data
from app.routers import auth, iam, keyvault, metadata, resources, storage

app = FastAPI(title="CloudGoat-Lite API", version="0.1.0")

# Permissively configured for LAN reachability from a separate attacker
# machine on the training network. This is intentional for a lab tool - see
# README.md "Network Accessibility" for why this must never be exposed to
# the public internet.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(resources.router)
app.include_router(storage.router)
app.include_router(keyvault.router)
app.include_router(iam.router)
app.include_router(metadata.router)


def _guess_lan_ip() -> str:
    """Best-effort LAN IP guess from inside the container's network namespace.
    Under Docker Compose this is usually the container's bridge-network IP,
    not the host's LAN IP - scripts/start.sh and start.ps1 print the actual
    host LAN IP before bringing the stack up, which is what students should
    point attack tooling at. This is printed here only as a secondary hint."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


@app.on_event("startup")
def on_startup():
    seed_data.seed()
    ip = _guess_lan_ip()
    print("=" * 70)
    print(" CloudGoat-Lite API is up.")
    print(f" Container-internal address guess: http://{ip}:8000")
    print(" Use scripts/start.sh or scripts/start.ps1 on the HOST to see the")
    print(" real LAN IP other machines should use, or run `ipconfig` /")
    print(" `ip addr` on the host yourself. See README.md for details.")
    print(" Seeded tenant: Initech Cloud. Entry-point credential: j.intern /")
    print(" Welcome2024! (documented in README.md).")
    print("=" * 70)


@app.get("/api/health")
def health():
    return {"status": "ok"}
