"""SQLite layer. Single source of truth. All queries parameterized."""
import sqlite3
import os
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database")
DB_PATH = os.path.join(DB_DIR, "parking.db")

def _connect():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS parking_records (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            plate        TEXT    NOT NULL,
            entry_ts     TEXT    NOT NULL,
            exit_ts      TEXT,
            duration_sec INTEGER,
            status       TEXT    NOT NULL CHECK(status IN ('Parked','Completed')),
            is_sample    INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        """)

def get_settings():
    with _connect() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
    return {r["key"]: r["value"] for r in rows}

def set_setting(key, value):
    with _connect() as conn:
        conn.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))

def count_currently_parked():
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM parking_records WHERE status='Parked'").fetchone()[0]

def count_entries_today():
    today = datetime.now().strftime("%Y-%m-%d")
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM parking_records WHERE date(entry_ts)=?", (today,)).fetchone()[0]

def count_exits_today():
    today = datetime.now().strftime("%Y-%m-%d")
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM parking_records WHERE status='Completed' AND date(exit_ts)=?", (today,)).fetchone()[0]

def get_parking_capacity():
    s = get_settings()
    try: return int(s.get("parking_capacity", "50"))
    except: return 50

def count_available_spaces():
    return max(0, get_parking_capacity() - count_currently_parked())

def fetch_recent_records(limit=50, search="", date_from="", date_to=""):
    sql = "SELECT * FROM parking_records WHERE 1=1"
    params = []
    if search:
        sql += " AND plate LIKE ?"
        params.append(f"%{search.upper()}%")
    sql += " ORDER BY entry_ts DESC LIMIT ?"
    params.append(limit)
    with _connect() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]

def fetch_vehicle_summary(search=""):
    sql = "SELECT plate, COUNT(*) AS visits, MAX(entry_ts) AS last_entry, MAX(COALESCE(exit_ts, '')) AS last_exit, MAX(CASE WHEN status='Parked' THEN 1 ELSE 0 END) AS is_parked FROM parking_records"
    params = []
    if search:
        sql += " WHERE plate LIKE ?"
        params.append(f"%{search.upper()}%")
    sql += " GROUP BY plate ORDER BY last_entry DESC LIMIT 500"
    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    out = []
    for r in rows:
        entry = r["last_entry"] or ""
        exit_ = r["last_exit"] or ""
        out.append({
            "plate": r["plate"], "status": "Parked" if r["is_parked"] else "Completed",
            "last_entry": (entry[:10] + " " + entry[11:19]) if len(entry) >= 19 else "—",
            "last_exit": (exit_[:10] + " " + exit_[11:19]) if len(exit_) >= 19 else "—",
            "visits": r["visits"],
        })
    return out

def fetch_daily_counts(days=7):
    with _connect() as conn:
        rows = conn.execute("""
            WITH RECURSIVE dates(d) AS (
                SELECT date('now', ?) UNION ALL SELECT date(d, '+1 day') FROM dates WHERE d < date('now')
            )
            SELECT d AS date, (SELECT COUNT(*) FROM parking_records WHERE date(entry_ts)=d) AS entries, (SELECT COUNT(*) FROM parking_records WHERE status='Completed' AND date(exit_ts)=d) AS exits FROM dates
        """, (f"-{days - 1} day",)).fetchall()
    return [dict(r) for r in rows]

def fetch_occupancy():
    return {"parked": count_currently_parked(), "capacity": get_parking_capacity()}

def fetch_hourly_entries_today():
    today = datetime.now().strftime("%Y-%m-%d")
    with _connect() as conn:
        rows = conn.execute("SELECT CAST(strftime('%H', entry_ts) AS INTEGER) AS hour, COUNT(*) AS count FROM parking_records WHERE date(entry_ts)=? GROUP BY hour", (today,)).fetchall()
    by_hour = {r["hour"]: r["count"] for r in rows}
    return [{"hour": h, "count": by_hour.get(h, 0)} for h in range(24)]