#!/usr/bin/env bash
set -uo pipefail

python -m uvicorn oracle_api.main:app --host 127.0.0.1 --port 8001 &
api_pid=$!

node server.js &
web_pid=$!

shutdown() {
  kill "$web_pid" "$api_pid" 2>/dev/null || true
}
trap shutdown EXIT INT TERM

wait -n "$web_pid" "$api_pid"
