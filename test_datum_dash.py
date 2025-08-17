#!/usr/bin/env python3

import subprocess
import re
from datetime import datetime, timedelta
import json
import os
import sys

# Configurable variables
SERVICE_NAME = "datum"
MIN_CLIENTS = 2
MAX_HEARTBEAT_AGE_MINUTES = 30
LOG_LOOKBACK_MINUTES = 10
STATUS_FILE = "/tmp/datum_gateway_status.json"
RESTART_BACKOFF_MINUTES = 100
RESTART_TIMESTAMP_FILE = "/tmp/datum_gateway_last_restart.timestamp"

def get_latest_heartbeat():
    # journalctl --since "10 minutes ago" -u datum_gateway
    since_time = (datetime.now() - timedelta(minutes=LOG_LOOKBACK_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    try:
        journal_cmd = [
            "journalctl",
            "-u", SERVICE_NAME,
            "--since", since_time,
            "-o", "short-precise",
            "--no-pager"
        ]
        output = subprocess.check_output(journal_cmd, text=True)
    except subprocess.CalledProcessError:
        return None, None

    # Parse lines with pattern like:
    # datum_gateway[781961]: 2025-08-16 15:03:54.487 [                                        main] INFO: Server stats: 2 clients / 14.36 Th/s
    heartbeat_re = re.compile(
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+).*INFO: Server stats: (\d+) clients"
    )

    latest_time = None
    latest_clients = None

    for line in output.splitlines():
        m = heartbeat_re.search(line)
        if m:
            ts_str = m.group(1)
            clients = int(m.group(2))
            try:
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                continue
            if (latest_time is None) or (ts > latest_time):
                latest_time = ts
                latest_clients = clients

    return latest_time, latest_clients

def can_restart():
    # Check if we restarted too recently
    if not os.path.exists(RESTART_TIMESTAMP_FILE):
        return True
    with open(RESTART_TIMESTAMP_FILE) as f:
        ts_str = f.read().strip()
    try:
        last_restart = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return True
    age = datetime.now() - last_restart
    return age > timedelta(minutes=RESTART_BACKOFF_MINUTES)

def record_restart():
    with open(RESTART_TIMESTAMP_FILE, "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def restart_service():
    if not can_restart():
        print("[INFO] Restart skipped due to backoff.")
        return "SKIPPED_BACKOFF"

    print(f"[ACTION] Restarting {SERVICE_NAME} service...")
    try:
        #subprocess.check_call(["systemctl", "restart", SERVICE_NAME])
        record_restart()
        print("[SUCCESS] Service restarted.")
        return "RESTARTED"
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to restart service: {e}")
        return "RESTART_FAILED"

def write_status_file(status, age_minutes=None, clients=None):
    data = {
        "status": status,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    if age_minutes is not None:
        data["heartbeat_age_minutes"] = age_minutes
    if clients is not None:
        data["clients"] = clients

    try:
        with open(STATUS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to write status file: {e}")

def main():
    timestamp, clients = get_latest_heartbeat()
    now = datetime.now()

    if timestamp is None or clients is None:
        print(f"[FAIL] No recent heartbeat log found.")
        status = restart_service()
        write_status_file(status)
        return

    age_minutes = (now - timestamp).total_seconds() / 60

    if age_minutes > MAX_HEARTBEAT_AGE_MINUTES:
        print(f"[FAIL] Last heartbeat was {age_minutes:.1f} minutes ago — too old.")
        status = restart_service()
        write_status_file(status, age_minutes, clients)
        return

    if clients == 0:
        print(f"[FAIL] No clients connected — restarting.")
        status = restart_service()
        write_status_file(status, age_minutes, clients)
        return

    if clients < MIN_CLIENTS:
        print(f"[WARN] Only {clients} clients connected — expected at least {MIN_CLIENTS}.")
        write_status_file("WARNING", age_minutes, clients)
        return

    print(f"[OK] Last heartbeat {age_minutes:.1f} min ago with {clients} clients — all good.")
    write_status_file("OK", age_minutes, clients)

if __name__ == "__main__":
    main()

