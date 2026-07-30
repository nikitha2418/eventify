-- Reference schema (SQLite).
-- You do NOT need to run this manually — the app calls init_db() on startup
-- and creates this table automatically. Kept here for documentation.

CREATE TABLE IF NOT EXISTS event_plans (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type  TEXT    NOT NULL,
    event_date  TEXT,
    guest_count INTEGER NOT NULL DEFAULT 0,
    budget      REAL    NOT NULL DEFAULT 0,
    location    TEXT,
    notes       TEXT,
    plan_json   TEXT    NOT NULL,          -- the full AI-generated plan, as JSON
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
