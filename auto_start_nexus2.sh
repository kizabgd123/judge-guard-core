#!/usr/bin/env bash
# auto_start_nexus2.sh — Ensures Agent Nexus 2 is always running.
# Called at system startup or manually. Safe to run multiple times.
set -euo pipefail

WORKSPACE="/home/kizabgd/.gemini/antigravity/worktrees/brave-meitner/install_jugard_system_integration"
DAEMON_SCRIPT="$WORKSPACE/agent_nexus2_daemon.py"
LOG_FILE="$WORKSPACE/agent_nexus2.log"
HEALTH_URL="http://localhost:7861/health"
PID_FILE="/tmp/agent_nexus2.pid"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG_FILE"; }

# Check if already running
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    log "Agent Nexus 2 already running (PID=$OLD_PID). Checking health..."
    if curl -sf "$HEALTH_URL" > /dev/null; then
      log "✅ Health OK — nothing to do."
      exit 0
    else
      log "⚠️ Health check failed — restarting daemon."
      kill "$OLD_PID" 2>/dev/null || true
      sleep 1
    fi
  fi
fi

log "🚀 Starting Agent Nexus 2 daemon..."
cd "$WORKSPACE"
source "$WORKSPACE/.env" 2>/dev/null || true

python3 "$DAEMON_SCRIPT" >> "$LOG_FILE" 2>&1 &
DAEMON_PID=$!
echo "$DAEMON_PID" > "$PID_FILE"
log "Daemon started (PID=$DAEMON_PID)"

# Wait for health
for i in $(seq 1 10); do
  sleep 2
  if curl -sf "$HEALTH_URL" > /dev/null; then
    log "✅ Agent Nexus 2 LIVE at $HEALTH_URL (PID=$DAEMON_PID)"
    exit 0
  fi
done

log "❌ Agent Nexus 2 failed to start. Check $LOG_FILE"
exit 1
