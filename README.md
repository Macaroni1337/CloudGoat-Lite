# CloudGoat-Lite - "Initech Cloud" Training Lab

A deliberately vulnerable, locally-hostable mock cloud console for pentest training.
It looks and feels like a simplified Azure Portal / AWS Console hybrid - Resource
Groups, Storage Accounts, Key Vault, IAM/Access Control - and is riddled with
realistic, intentional misconfigurations so you can practice the same categories of
bugs found in real Azure/AWS engagements: over-privileged app registrations, public
storage, weak/leaked credentials, IDOR, SSRF against a fake metadata service, and
privilege escalation.

It is **not** a clone of the real Azure/AWS APIs. It's a teaching simulacrum: same
visual/conceptual shape, simplified mechanics underneath, so the *concepts* transfer
even though exact real-world tool syntax (ROADrecon, AzureHound, aws-cli, etc.) won't
work against it out of the box.

See also: [SCENARIO.md](SCENARIO.md) (the fictional engagement brief) and
[VULNERABILITIES.md](VULNERABILITIES.md) (the instructor's answer key - don't read
this before attempting the lab if you want the full experience).

## Warning - read before running this anywhere

- **This stack is intentionally broken.** Every listed misconfiguration is real and
  exploitable, on purpose.
- **CORS is wide open** (`allow_origins=["*"]`) and both containers bind to
  `0.0.0.0`. This is required so a second machine on your LAN can act as the
  attacker box - it is **not safe for any network you don't control**.
- **Run this only on an isolated lab network** (a home lab VLAN, an offline VM host,
  a NAT-only virtual network shared only by your target VM and your Kali VM).
- **Never expose these ports to the public internet.** Do not port-forward them on a
  router, do not deploy this to a cloud VM with a public IP, do not run it on a
  network you share with untrusted devices.
- All data is fictional. No real cloud SDKs or credentials are used anywhere in this
  project.

## Architecture

- **Backend**: Python + FastAPI, serving a small REST API that mimics a slice of
  Azure Resource Manager / Microsoft Graph concepts (Resource Groups, App
  Registrations, Key Vault) blended with AWS-style IAM naming. In-memory Python data
  store, reseeded every time the backend process starts.
- **Frontend**: static HTML/CSS/JS (no build step), served by nginx, styled to
  loosely resemble a cloud console (dark sidebar, resource cards, IAM tables).
- **Auth**: a simplified JWT scheme. Deliberately weak in specific, documented ways
  (see [VULNERABILITIES.md](VULNERABILITIES.md) V1) - this is not meant to be secure
  auth, it's meant to be breakable.

```
docker compose
├── backend   -> FastAPI + Uvicorn, binds 0.0.0.0:8000
└── frontend  -> nginx serving static files, binds 0.0.0.0:8080
```

## Requirements

- Docker and Docker Compose (Docker Desktop on Windows/Mac, or Docker Engine + the
  `docker compose` plugin on Linux).
- Two machines/VMs on the same LAN or lab network: one to host this stack (the
  "target"), one to attack from (e.g. a Kali VM).

## Running it

From the repo root, on the **target** machine:

```bash
# macOS/Linux
./scripts/start.sh

# Windows (PowerShell)
.\scripts\start.ps1
```

Either script detects your host's LAN IP, prints the URLs to use, and then runs
`docker compose up --build`. If you'd rather run it directly:

```bash
docker compose up --build
```

Then find your host's LAN IP yourself:

- **Windows**: `ipconfig` (look for the IPv4 address of your active adapter)
- **macOS/Linux**: `ifconfig` or `ip addr` (look for your LAN interface, e.g. `en0`
  or `eth0`)

## Accessing it from a second (attacker) machine

Once the containers are up, from your **attacker machine** (e.g. Kali), point a
browser or your tools at:

- Web console: `http://<TARGET-LAN-IP>:8080`
- API directly: `http://<TARGET-LAN-IP>:8000` (interactive OpenAPI docs are at
  `http://<TARGET-LAN-IP>:8000/docs` - a good place to start enumerating the API
  surface, just like you'd enumerate a real API in an engagement)

Both machines must be on the same network/subnet and able to route to each other
(same LAN, same lab VLAN, or the same isolated virtual network in your
hypervisor). If you're using VMs, make sure their network adapters are attached to
the same virtual network (e.g. VirtualBox/VMware "internal network" or a shared
host-only network) rather than each being NAT-isolated from each other.

## Starting credential (your entry point)

You are simulating an assessment that starts from a single leaked/weak low-privilege
credential - a realistic starting foothold, not full pre-authorization to every
account.

```
Username: j.intern
Password: Welcome2024!
```

This account has the `Reader` role scoped to `RG-Intern-Sandbox` only. Everything
else in the tenant is meant to be reached by chaining the vulnerabilities documented
in [VULNERABILITIES.md](VULNERABILITIES.md) - start there once you've explored the
console a bit on your own.

## Resetting the lab

State is in-memory only. Restart the backend container to reseed everything from
scratch:

```bash
docker compose restart backend
```

## Project layout

```
CloudGoat-Lite/
├── docker-compose.yml
├── backend/            FastAPI app (see backend/app/routers for each API area)
├── frontend/            static console UI served by nginx
├── scripts/             start.sh / start.ps1 (LAN IP detection + docker compose up)
├── SCENARIO.md          fictional engagement brief
└── VULNERABILITIES.md   instructor answer key: what's broken, where, and why
```
