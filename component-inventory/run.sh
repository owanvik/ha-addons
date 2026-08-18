#!/usr/bin/with-contenv bashio
set -euo pipefail

export INVENTORY_DB="/data/inventory.db"
export INVENTORY_SETTINGS="/data/settings.json"

bashio::log.info "Starting Component Inventory web UI on ingress port 8099"
/opt/venv/bin/python /app/web.py &
WEB_PID=$!

bashio::log.info "Starting MCP endpoint on port 8098"
/opt/venv/bin/python /app/mcp_server.py &
MCP_PID=$!

trap 'kill "$WEB_PID" "$MCP_PID" 2>/dev/null || true' TERM INT EXIT
wait -n "$WEB_PID" "$MCP_PID"
STATUS=$?
kill "$WEB_PID" "$MCP_PID" 2>/dev/null || true
wait || true
exit "$STATUS"
