# 🛡️ Datum Gateway Watchdog & Web Dashboard

A lightweight monitoring script and optional web dashboard for `datum_gateway`. Designed to detect stalled or disconnected states, notify on low client count, and optionally trigger recovery actions.

---

## 📦 Features

- ✅ Monitors `datum_gateway` logs using `journalctl`
- ⏱ Checks if last "heartbeat" log is within a healthy time window
- 👥 Validates if at least **N** clients are connected
- 🛠 Optionally restart service if 0 clients and stale heartbeat
- 🖥 Includes a simple Flask-based **status dashboard**
- 📁 Outputs health data to `/tmp/datum_gateway_status.json` for integrations

---

## 📁 Files

| File | Description |
|------|-------------|
| `test_datum_dash.py` | Main watchdog script (run via cron) |
| `datum_dashboard.py`   | Optional web dashboard (Flask) |
| `README.md`            | This file |

---

## ⚙️ Configuration

Edit values inside `test_datum_dash.py`:

```python
min_clients = 1           # Minimum clients expected
max_age_minutes = 30      # How old is "too old" for heartbeat
datum_service_name = "datum_gateway"
````

The log line being monitored looks like this:

```
datum_gateway[781961]: 2025-08-16 15:03:54.487 [main] INFO: Server stats: 2 clients / 14.36 Th/s
```

---

## 🚀 Usage

### 1. Install dependencies

```bash
pip install flask
```

### 2. Run heartbeat check (manually)

```bash
python3 test_datum_dash.py
```

It will output something like:

```
[OK] Last heartbeat 2.9 min ago with 2 clients — all good.
```

or

```
[WARN] Heartbeat is recent (5.1 min ago) but only 1 clients.
```

or

```
[FAIL] No recent heartbeat found in journal logs.
```

### 3. Set up a cron job (every hour)

```cron
0 * * * * /usr/bin/python3 /path/to/test_datum_dash.py
```

### 4. Run optional web dashboard

```bash
python3 datum_dashboard.py
```

Then open [http://localhost:8080](http://localhost:8080)

---

## 🧠 Logic

* If **no heartbeat** in last `max_age_minutes` → FAIL
* If **recent heartbeat**, but `< min_clients` → WARN
* If **recent heartbeat** and `>= min_clients` → OK
* If **0 clients + stale heartbeat** → Optional restart

> 🛑 Automatic restart is **disabled by default**, but you can uncomment the line in the script.

---

## 📝 Status Output

Health status is written to:

```
/tmp/datum_gateway_status.json
```

Sample:

```json
{
  "last_heartbeat": "2025-08-16T14:31:12",
  "minutes_ago": 2.9,
  "clients": 2,
  "ok": true
}
```

---

## 🧩 Integration Ideas

* 📊 Monitor via Prometheus or Telegraf using the status file
* 🔔 Send alert via Telegram or email if `ok = false`
* 🖥 Run dashboard on a Pi with a touchscreen display
* 🌐 Publish live status via Nostr or a public web dashboard


## 🛠 License

MIT — do whatever you want, no warranty.
