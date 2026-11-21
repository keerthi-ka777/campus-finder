import os
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'campus_finder.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    claimed_by INTEGER,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    item_type TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Open',
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (claimed_by) REFERENCES users(id)
);
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    if db.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0:
        # Demo account: its password is random, so nobody can sign in as it.
        cur = db.execute(
            "INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo Student", "demo@campus.local", generate_password_hash(os.urandom(16).hex())))
        uid = db.execute("SELECT id FROM users WHERE email=?", ("demo@campus.local",)).fetchone()[0]
        now = datetime.now()
        demo = [
            ("Blue water bottle", "Other", "Lost", "Library, 2nd floor",
             "Blue steel bottle with a white cap and a sticker on the side.", "Open", 3),
            ("Student ID card", "ID card", "Found", "Canteen entrance",
             "ID card found near the canteen. Handed over to the security office.", "Claimed", 2),
            ("Scientific calculator", "Electronics", "Lost", "Block B, Room 204",
             "Casio fx-991 with initials written on the back.", "Open", 1),
        ]
        for title, cat, typ, loc, desc, status, days in demo:
            ts = (now - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            db.execute("INSERT INTO items (user_id, title, category, item_type, location, description, status, created_at) "
                       "VALUES (?,?,?,?,?,?,?,?)", (uid, title, cat, typ, loc, desc, status, ts))
        db.commit()
    db.close()
