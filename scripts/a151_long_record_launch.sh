#!/usr/bin/env bash
# Unattended launcher for the a150 long-record HYSPLIT campaign (all three phases chained).
# Idempotent: finished runs and weeks are skipped by receipt, so this is also the resume command.
# Refuses to start a second copy, or while outputs/hysplit/long_record/STOP exists.
set -euo pipefail
ROOT=/run/media/workstation-llm/HDD2/GHG_Analysis
LR=$ROOT/outputs/hysplit/long_record
PY=/run/media/workstation-llm/HDD2/.venv/bin/python
WORKERS=${WORKERS:-9}
mkdir -p "$LR/logs"
if [[ -f $LR/campaign.pid ]] && kill -0 "$(cat "$LR/campaign.pid")" 2>/dev/null; then
  echo "already running: PID $(cat "$LR/campaign.pid")"; exit 1
fi
if [[ -f $LR/STOP ]]; then echo "remove $LR/STOP first"; exit 1; fi
cd "$ROOT/scripts"
echo "=== launch $(date -u +%FT%TZ) workers=$WORKERS ===" >> "$LR/logs/campaign.log"
PYTHONUNBUFFERED=1 setsid nohup nice -n 19 "$PY" a150_hysplit_long_record.py campaign --workers "$WORKERS" \
  >> "$LR/logs/campaign.log" 2>&1 < /dev/null &
echo $! > "$LR/campaign.pid"
echo "started PID $(cat "$LR/campaign.pid"); log $LR/logs/campaign.log"
