"""SQLite helpers. The database is a single file (see Config.DB_PATH).

SQLite is built into Python, so there is nothing to install and no server
to run. init_db() creates the tables automatically on first launch, which
means your friend can run the project with zero setup.
"""
import sqlite3
from config import Config


def get_connection():
    """Open a connection to the SQLite file. Rows behave like dicts."""
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row  # access columns by name: row["event_type"]
    return conn


def init_db():
    """Create tables if they don't exist yet. Safe to call on every startup."""
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS event_plans (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                event_type  TEXT    NOT NULL,
                event_date  TEXT,
                guest_count INTEGER NOT NULL DEFAULT 0,
                budget      REAL    NOT NULL DEFAULT 0,
                location    TEXT,
                notes       TEXT,
                plan_json   TEXT    NOT NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def ping():
    """Return True if the database file is reachable. Used by the health check."""
    conn = get_connection()
    try:
        conn.execute("SELECT 1").fetchone()
        return True
    finally:
        conn.close()


# ---------- Users ----------

def create_user(username, password_hash):
    """Insert a new user. Raises sqlite3.IntegrityError if username is taken."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_user_by_username(username):
    """Return the user row (or None) for a given username."""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    finally:
        conn.close()


# ---------- Event plans ----------

def save_plan(user_id, details, plan_json):
    """Store a generated plan for a user. Returns the new plan id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO event_plans
               (user_id, event_type, event_date, guest_count, budget,
                location, notes, plan_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                details.get("event_type", ""),
                details.get("event_date") or None,
                int(details.get("guest_count") or 0),
                float(details.get("budget") or 0),
                details.get("location") or None,
                details.get("notes") or None,
                plan_json,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_plans_for_user(user_id):
    """Return all plans for a user, newest first."""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM event_plans WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()


def get_plan(plan_id, user_id):
    """Return one plan by id, but only if it belongs to this user."""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM event_plans WHERE id = ? AND user_id = ?",
            (plan_id, user_id),
        ).fetchone()
    finally:
        conn.close()


def delete_plan(plan_id, user_id):
    """Delete a plan, but only if it belongs to this user. Returns rows deleted."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "DELETE FROM event_plans WHERE id = ? AND user_id = ?",
            (plan_id, user_id),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()
