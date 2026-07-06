#!/usr/bin/env bash
# Detects the host's LAN IP, prints the URLs an attacker machine should use,
# then brings up the stack. Run from the repo root: ./scripts/start.sh
set -e

IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
if [ -z "$IP" ]; then
  IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
fi
if [ -z "$IP" ]; then
  IP="<could not auto-detect - run 'ip addr' or 'ifconfig' and use the LAN interface's IPv4 address>"
fi

echo "=========================================================================="
echo " CloudGoat-Lite ('Initech Cloud' lab)"
echo ""
echo "   Web console (this host) : http://localhost:8080"
echo "   Web console (LAN)       : http://${IP}:8080"
echo "   API (LAN)               : http://${IP}:8000"
echo ""
echo " Point a second machine's browser/attack tooling at the LAN URLs above."
echo " WARNING: lab-network use only. Never expose these ports to the public"
echo " internet or deploy this outside an isolated lab network. See README.md."
echo "=========================================================================="

docker compose up --build
