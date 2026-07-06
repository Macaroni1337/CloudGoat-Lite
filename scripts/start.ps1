# Detects the host's LAN IP, prints the URLs an attacker machine should use,
# then brings up the stack. Run from the repo root: .\scripts\start.ps1

$ip = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object {
        $_.InterfaceAlias -notmatch 'Loopback' -and
        $_.IPAddress -notmatch '^169\.254\.' -and
        $_.IPAddress -notmatch '^127\.'
    } |
    Select-Object -First 1 -ExpandProperty IPAddress)

if (-not $ip) {
    $ip = "<could not auto-detect - run 'ipconfig' and use your LAN adapter's IPv4 address>"
}

Write-Host "=========================================================================="
Write-Host " CloudGoat-Lite ('Initech Cloud' lab)"
Write-Host ""
Write-Host "   Web console (this host) : http://localhost:8080"
Write-Host "   Web console (LAN)       : http://$ip`:8080"
Write-Host "   API (LAN)               : http://$ip`:8000"
Write-Host ""
Write-Host " Point a second machine's browser/attack tooling at the LAN URLs above."
Write-Host " WARNING: lab-network use only. Never expose these ports to the public"
Write-Host " internet or deploy this outside an isolated lab network. See README.md."
Write-Host "=========================================================================="

docker compose up --build
