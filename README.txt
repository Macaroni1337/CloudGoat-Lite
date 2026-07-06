==============================================================================
 CloudGoat-Lite ("Initech Cloud") - Setup Guide & Account Reference
==============================================================================

This is a plain-text quick-reference version of README.md. Read README.md
for the full explanation of the project; this file is meant to be the one
you keep open in a terminal while you set the lab up and log in.

------------------------------------------------------------------------------
 1. WHAT THIS IS
------------------------------------------------------------------------------

A deliberately vulnerable, self-hosted mock cloud console (Azure Portal / AWS
Console hybrid) for pentest training. Two Docker containers:

  - backend  : FastAPI REST API, port 8000
  - frontend : static HTML/CSS/JS console served by nginx, port 8080

Both bind to 0.0.0.0 so a second machine on your LAN (e.g. a Kali VM) can
attack it. It is NOT a real cloud provider and contains no real cloud SDKs
or credentials.

WARNING: lab-network use only. Never expose these ports to the public
internet, never port-forward them on a router, never run this on a network
you share with untrusted devices.

------------------------------------------------------------------------------
 2. REQUIREMENTS
------------------------------------------------------------------------------

  - Docker Desktop (or Docker Engine + docker compose plugin on Linux)
  - Two machines/VMs on the same LAN or lab network:
      * TARGET  - runs this stack
      * ATTACKER - e.g. a Kali VM, used to attack the target

------------------------------------------------------------------------------
 3. SETUP - ON THE TARGET MACHINE
------------------------------------------------------------------------------

From the repo root:

    # macOS/Linux
    ./scripts/start.sh

    # Windows (PowerShell)
    .\scripts\start.ps1

  Either script detects your LAN IP, prints the URLs to use, then runs
  `docker compose up --build`. Or just run it directly:

    docker compose up --build

  Find your LAN IP yourself if needed:
    Windows       : ipconfig            (look for your active adapter's IPv4)
    macOS/Linux   : ifconfig / ip addr  (look for en0/eth0 etc.)

------------------------------------------------------------------------------
 4. WINDOWS FIREWALL (if the target is a Windows host)
------------------------------------------------------------------------------

  Docker containers publishing to 0.0.0.0 are still subject to the Windows
  Firewall on the host. If your network adapter is on the "Public" profile,
  Windows blocks unsolicited inbound connections by default, and your
  attacker machine will NOT be able to reach ports 8000/8080 even though
  `docker compose ps` shows them bound to 0.0.0.0.

  Fix: open PowerShell AS ADMINISTRATOR on the target/host machine and run:

    New-NetFirewallRule -DisplayName "CloudGoat-Lite" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000,8080

  Verify it took:

    Get-NetFirewallRule -DisplayName "CloudGoat-Lite" | Select-Object DisplayName, Enabled, Direction, Action

------------------------------------------------------------------------------
 5. ATTACKER VM NETWORKING (e.g. Kali in VirtualBox/VMware/Hyper-V)
------------------------------------------------------------------------------

  Your attacker VM's network adapter must be on the SAME LAN/subnet as the
  target, not isolated behind the hypervisor's NAT:

    VirtualBox / VMware : set the adapter to "Bridged" (not NAT, not
                           Host-only)
    Hyper-V             : use an "External" virtual switch (not Internal
                           or Private)

  With NAT mode, the VM gets an IP behind an isolated hypervisor network and
  cannot be reached from / reach the LAN directly - that's the most common
  reason "I can't access it from my Kali VM" happens even after the target
  stack is running correctly.

  After switching to bridged/external, confirm from Kali:

    ip addr                          # should show an IP on the same subnet
    ping <TARGET-LAN-IP>
    curl http://<TARGET-LAN-IP>:8000/api/health

------------------------------------------------------------------------------
 6. ACCESSING THE CONSOLE
------------------------------------------------------------------------------

  From the attacker machine's browser:

    http://<TARGET-LAN-IP>:8080

  API directly (and interactive OpenAPI docs - good enumeration starting
  point):

    http://<TARGET-LAN-IP>:8000
    http://<TARGET-LAN-IP>:8000/docs

------------------------------------------------------------------------------
 7. ACCOUNT DETAILS (seeded "Initech Cloud" tenant)
------------------------------------------------------------------------------

  INTENDED STARTING CREDENTIAL (the only one you should use to log in with
  at the start of an assessment - see PENTEST.txt for the intended path):

      Username : j.intern
      Password : Welcome2024!
      Role     : Reader
      Scope    : RG-Intern-Sandbox

  Full account list (this is the answer key - everyone else's password is
  meant to be discovered/derived during the exercise, not typed in on day
  one):

      Username       Password               Role          Resource Group
      -------------- ---------------------- ------------- ------------------
      sarah.chen     P@ssw0rd_Sarah!2024     Owner         RG-Production
      mike.torres    Summer2024!             Contributor   RG-Production
      priya.patel    Priya#Dev2024           Contributor   RG-Dev
      alex.wu        AlexHelp!2024           Reader        RG-Helpdesk
      j.intern       Welcome2024!            Reader        RG-Intern-Sandbox

      Note: mike.torres's password is intentionally identical to the
      "legacy shared admin password" planted in the public secrets_backup.txt
      file (password reuse - see VULNERABILITIES.md V8). It's meant to be
      found, not looked up here, if you're doing this as an exercise rather
      than administering it.

  App registrations / service principals:

      Name                            Client ID                              Client Secret            Role          Scope
      ------------------------------- -------------------------------------- ------------------------ ------------- --------------
      Initech-Deploy-Bot              a1b2c3d4-5e6f-7890-a1b2-deploy0000bot  DB_S3cr3t_kj28dHqL!      Contributor   subscription  (over-permissioned, V4)
      Initech-Helpdesk-Portal         e5f6g7h8-9012-helpdesk-portal-app      HP_9fXcvQ2mNw!           Reader        RG-Helpdesk
      Initech-Logo-Importer-Service   i9j0k1l2-3456-logo-importer-svc        LI_7pZrTt4Vb!            Contributor   RG-Production (leaked via SSRF, V6)

  Key Vault "initech-kv-prod" secrets (should be Owner-only, isn't - V5):

      sql-admin-password    = KV_SqlAdm1n_9!xQ
      storage-account-key   = KV_StorageKey_7hT2v==

  JWT signing secret (hardcoded, V1):

      initech-cloud-2024-dev

------------------------------------------------------------------------------
 8. RESETTING THE LAB
------------------------------------------------------------------------------

  All state is in-memory. To reseed everything from scratch:

    docker compose restart backend

------------------------------------------------------------------------------
 9. WHERE TO GO NEXT
------------------------------------------------------------------------------

  SCENARIO.md       - the fictional engagement brief
  PENTEST.txt       - guided, tool-by-tool tutorial (assumed-breach/graybox,
                      starts from the j.intern credential above)
  PENTEST_BLACKBOX.txt - same tutorial style, but for a zero-knowledge
                      external assessment: no credential handed to you at
                      all, just the target IP
  VULNERABILITIES.md - full instructor answer key for every bug
==============================================================================
