"""
Seeds the "Initech Cloud" fictional tenant used by the training scenario.
See SCENARIO.md for the engagement framing and VULNERABILITIES.md for how each
seeded record ties into one of the 8 intentional bugs.
"""
from app import db


def seed() -> None:
    db.clear_all()
    _seed_users()
    _seed_app_registrations()
    _seed_resources()
    _seed_storage()
    _seed_key_vault()
    _seed_role_assignments()


def _seed_users() -> None:
    users = [
        dict(
            username="sarah.chen",
            email="sarah.chen@initech-cloud.local",
            display_name="Sarah Chen",
            password="P@ssw0rd_Sarah!2024",
            role="Owner",
            resource_group="RG-Production",
            title="VP of Engineering",
        ),
        dict(
            username="mike.torres",
            email="mike.torres@initech-cloud.local",
            display_name="Mike Torres",
            # Password reuse (V8): this is the same "legacy shared admin password"
            # planted in the public secrets_backup.txt file (see _seed_storage).
            password="Summer2024!",
            role="Contributor",
            resource_group="RG-Production",
            title="IT Administrator",
        ),
        dict(
            username="priya.patel",
            email="priya.patel@initech-cloud.local",
            display_name="Priya Patel",
            password="Priya#Dev2024",
            role="Contributor",
            resource_group="RG-Dev",
            title="Software Developer",
        ),
        dict(
            username="alex.wu",
            email="alex.wu@initech-cloud.local",
            display_name="Alex Wu",
            password="AlexHelp!2024",
            role="Reader",
            resource_group="RG-Helpdesk",
            title="Helpdesk Agent",
        ),
        dict(
            # V8 (documented entry point in README): weak, easily-guessed password
            # for a low-privilege account. This is where the student starts.
            username="j.intern",
            email="j.intern@initech-cloud.local",
            display_name="J. Intern",
            password="Welcome2024!",
            role="Reader",
            resource_group="RG-Intern-Sandbox",
            title="IT Intern",
        ),
    ]
    for u in users:
        uid = db.next_id("users")
        db.users[uid] = {"id": uid, "principal_type": "user", **u}


def _seed_app_registrations() -> None:
    apps = [
        dict(
            name="Initech-Deploy-Bot",
            client_id="a1b2c3d4-5e6f-7890-a1b2-deploy0000bot",
            client_secret="DB_S3cr3t_kj28dHqL!",
            # V4: over-permissioned - a deploy bot only needs Contributor on
            # RG-Production, but it was granted Contributor at the subscription
            # scope, i.e. over every resource group in the tenant.
            role="Contributor",
            scope="subscription",
            description="CI/CD pipeline identity used to push builds to production.",
        ),
        dict(
            name="Initech-Helpdesk-Portal",
            client_id="e5f6g7h8-9012-helpdesk-portal-app",
            client_secret="HP_9fXcvQ2mNw!",
            role="Reader",
            scope="RG-Helpdesk",
            description="Internal helpdesk ticketing integration. Correctly scoped.",
        ),
        dict(
            name="Initech-Logo-Importer-Service",
            client_id="i9j0k1l2-3456-logo-importer-svc",
            client_secret="LI_7pZrTt4Vb!",
            # This is the credential leaked via the SSRF -> fake metadata
            # service chain (V6).
            role="Contributor",
            scope="RG-Production",
            description="Backs the branding 'import logo from URL' feature.",
        ),
    ]
    for a in apps:
        aid = db.next_id("app_registrations")
        db.app_registrations[aid] = {"id": aid, "principal_type": "service_principal", **a}


def _seed_resources() -> None:
    def uid_of(username: str) -> int:
        return db.find_user_by_username(username)["id"]

    resources = [
        # RG-Intern-Sandbox - j.intern's own scope, safe to browse normally
        dict(name="intern-sandbox-vm", type="Virtual Machine", resource_group="RG-Intern-Sandbox",
             region="eastus", owner="j.intern",
             details={"os": "Ubuntu 22.04", "size": "Standard_B1s", "note": "Personal sandbox VM"}),
        dict(name="intern-test-db", type="Database", resource_group="RG-Intern-Sandbox",
             region="eastus", owner="j.intern",
             details={"engine": "PostgreSQL 15", "note": "Scratch DB for training exercises"}),
        dict(name="intern-web-static", type="Web App", resource_group="RG-Intern-Sandbox",
             region="eastus", owner="j.intern",
             details={"runtime": "static-html", "note": "Placeholder site"}),
        # RG-Production - should be off-limits to the intern (V2 IDOR target)
        dict(name="prod-web-app", type="Web App", resource_group="RG-Production",
             region="eastus2", owner="sarah.chen",
             details={"runtime": "node18", "note": "Customer-facing storefront - PCI scope"}),
        dict(name="prod-sql-db", type="Database", resource_group="RG-Production",
             region="eastus2", owner="sarah.chen",
             details={"engine": "SQL Server 2022", "note": "Primary production database. See Key Vault initech-kv-prod for credentials."}),
        dict(name="prod-payment-gateway", type="Virtual Machine", resource_group="RG-Production",
             region="eastus2", owner="mike.torres",
             details={"os": "Windows Server 2022", "size": "Standard_D4s_v5", "note": "PCI-scoped payment processor"}),
        dict(name="prod-api-gateway", type="API Gateway", resource_group="RG-Production",
             region="eastus2", owner="mike.torres",
             details={"note": "Public API front door"}),
        dict(name="prod-backup-vm", type="Virtual Machine", resource_group="RG-Production",
             region="eastus2", owner="sarah.chen",
             details={"os": "Ubuntu 22.04", "note": "Nightly backup target"}),
        # RG-Dev
        dict(name="dev-feature-branch-app", type="Web App", resource_group="RG-Dev",
             region="eastus", owner="priya.patel",
             details={"runtime": "node18", "note": "Feature branch preview deploys"}),
        dict(name="dev-ci-runner", type="Virtual Machine", resource_group="RG-Dev",
             region="eastus", owner="priya.patel",
             details={"os": "Ubuntu 22.04", "note": "Self-hosted CI runner"}),
    ]
    for r in resources:
        rid = db.next_id("resources")
        owner_username = r.pop("owner")
        db.resources[rid] = {
            "id": rid,
            "owner_user_id": uid_of(owner_username),
            **r,
        }


def _seed_storage() -> None:
    account_id = db.next_id("storage_accounts")
    db.storage_accounts[account_id] = {
        "id": account_id,
        "name": "initechprodstorage",
        "resource_group": "RG-Production",
    }

    public_container_id = db.next_id("storage_containers")
    db.storage_containers[public_container_id] = {
        "id": public_container_id,
        "account_id": account_id,
        "name": "public-assets",
        # V3: container-level public read access misconfiguration.
        "public": True,
    }

    private_container_id = db.next_id("storage_containers")
    db.storage_containers[private_container_id] = {
        "id": private_container_id,
        "account_id": account_id,
        "name": "private-backups",
        "public": False,
    }

    logo_obj_id = db.next_id("storage_objects")
    db.storage_objects[logo_obj_id] = {
        "id": logo_obj_id,
        "container_id": public_container_id,
        "name": "company-logo.png",
        "content_type": "image/png",
        "content": "<binary image data placeholder - not a real image>",
    }

    secrets_obj_id = db.next_id("storage_objects")
    db.storage_objects[secrets_obj_id] = {
        "id": secrets_obj_id,
        "container_id": public_container_id,
        "name": "secrets_backup.txt",
        "content_type": "text/plain",
        # V3 payload: a plaintext secrets dump sitting in a publicly-readable
        # container. Leaks the over-permissioned Deploy-Bot app registration's
        # client secret (chains into V4) and a reused legacy password (V8).
        "content": (
            "Initech Cloud - emergency access backup\n"
            "DO NOT COMMIT THIS FILE (yes, we know it's ironic that it's here)\n\n"
            "[Initech-Deploy-Bot service principal]\n"
            "client_id: a1b2c3d4-5e6f-7890-a1b2-deploy0000bot\n"
            "client_secret: DB_S3cr3t_kj28dHqL!\n\n"
            "[legacy shared admin password - rotate before next audit]\n"
            "password: Summer2024!\n"
        ),
    }

    backup_obj_id = db.next_id("storage_objects")
    db.storage_objects[backup_obj_id] = {
        "id": backup_obj_id,
        "container_id": private_container_id,
        "name": "db_dump_2024_06.sql.gz",
        "content_type": "application/gzip",
        "content": "<binary db dump placeholder - not a real dump>",
    }


def _seed_key_vault() -> None:
    vault_id = db.next_id("key_vaults")
    db.key_vaults[vault_id] = {
        "id": vault_id,
        "name": "initech-kv-prod",
        "resource_group": "RG-Production",
    }

    secrets = [
        ("sql-admin-password", "KV_SqlAdm1n_9!xQ"),
        ("storage-account-key", "KV_StorageKey_7hT2v=="),
    ]
    for name, value in secrets:
        sid = db.next_id("key_vault_secrets")
        db.key_vault_secrets[sid] = {
            "id": sid,
            "vault_id": vault_id,
            "name": name,
            "value": value,
        }


def _seed_role_assignments() -> None:
    def user_id(username: str) -> int:
        return db.find_user_by_username(username)["id"]

    def app_id(name: str) -> int:
        for app in db.app_registrations.values():
            if app["name"] == name:
                return app["id"]
        raise KeyError(name)

    assignments = [
        dict(principal_type="user", principal_id=user_id("sarah.chen"), role="Owner", scope="subscription"),
        dict(principal_type="user", principal_id=user_id("mike.torres"), role="Contributor", scope="RG-Production"),
        dict(principal_type="user", principal_id=user_id("priya.patel"), role="Contributor", scope="RG-Dev"),
        dict(principal_type="user", principal_id=user_id("alex.wu"), role="Reader", scope="RG-Helpdesk"),
        dict(principal_type="user", principal_id=user_id("j.intern"), role="Reader", scope="RG-Intern-Sandbox"),
        # V4 shows up here too: Deploy-Bot's assignment is scope=subscription,
        # not scope=RG-Production, visible in a plain IAM audit table.
        dict(principal_type="service_principal", principal_id=app_id("Initech-Deploy-Bot"),
             role="Contributor", scope="subscription"),
        dict(principal_type="service_principal", principal_id=app_id("Initech-Helpdesk-Portal"),
             role="Reader", scope="RG-Helpdesk"),
        dict(principal_type="service_principal", principal_id=app_id("Initech-Logo-Importer-Service"),
             role="Contributor", scope="RG-Production"),
    ]
    for a in assignments:
        rid = db.next_id("role_assignments")
        db.role_assignments[rid] = {"id": rid, **a}
