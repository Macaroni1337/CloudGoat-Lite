"""
In-memory data store for CloudGoat-Lite.

Everything lives in plain module-level dicts, keyed by small SEQUENTIAL integer
IDs rather than GUIDs. That sequential-ID choice is itself intentional (see
VULNERABILITIES.md V2 - IDOR): it means an attacker can simply increment an ID
to enumerate resources belonging to other users/resource groups.

State resets whenever the process restarts - that's expected for a lab. Call
reset_and_seed() once at startup (done in main.py).
"""

# Each store is a dict[int, dict]. "id" is duplicated inside the record for
# convenience when serializing.
users: dict[int, dict] = {}
app_registrations: dict[int, dict] = {}
resources: dict[int, dict] = {}
storage_accounts: dict[int, dict] = {}
storage_containers: dict[int, dict] = {}
storage_objects: dict[int, dict] = {}
key_vaults: dict[int, dict] = {}
key_vault_secrets: dict[int, dict] = {}
role_assignments: dict[int, dict] = {}

# Simple auto-increment counters so seed_data.py doesn't have to hand-track IDs.
_counters: dict[str, int] = {}


def next_id(store_name: str) -> int:
    _counters[store_name] = _counters.get(store_name, 0) + 1
    return _counters[store_name]


def clear_all() -> None:
    for store in (
        users,
        app_registrations,
        resources,
        storage_accounts,
        storage_containers,
        storage_objects,
        key_vaults,
        key_vault_secrets,
        role_assignments,
    ):
        store.clear()
    _counters.clear()


def find_user_by_username(username: str) -> dict | None:
    for user in users.values():
        if user["username"] == username:
            return user
    return None


def find_app_registration_by_client_id(client_id: str) -> dict | None:
    for app in app_registrations.values():
        if app["client_id"] == client_id:
            return app
    return None
