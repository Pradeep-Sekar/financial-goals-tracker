import sqlite3
from datetime import datetime

DB_FILE = "financial_goals.db"

def connect_db():
    """Establish a database connection and return the connection object."""
    return sqlite3.connect(DB_FILE)

def initialize_db():
    """Create the goals table if it does not exist."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            time_horizon INTEGER NOT NULL,
            cagr REAL DEFAULT 12,
            investment_mode TEXT CHECK(investment_mode IN ('SIP', 'Lumpsum', 'Lumpsum + SIP')) NOT NULL,
            initial_investment REAL,
            sip_amount REAL,
            start_date TEXT DEFAULT CURRENT_DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def insert_goal(goal_data):
    """Insert a new financial goal into the database."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO goals 
        (goal_name, target_amount, time_horizon, cagr, investment_mode, initial_investment, sip_amount, start_date, notes) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        goal_data["goal_name"],
        goal_data["target_amount"],
        goal_data["time_horizon"],
        goal_data["cagr"],
        goal_data["investment_mode"],
        goal_data["initial_investment"],
        goal_data["sip_amount"],  # <-- Updated to match get_user_input()
        goal_data["start_date"],
        goal_data["notes"]
    ))

    conn.commit()  # <-- Ensure this line exists
    conn.close()

def fetch_goals():
    """Retrieve all saved financial goals from the database."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, goal_name, target_amount, time_horizon, cagr, investment_mode, initial_investment, sip_amount, start_date, created_at, notes
        FROM goals
        ORDER BY created_at DESC
    """)

    goals = cursor.fetchall()
    conn.close()
    return goals  # Returns a list of tuples

    conn.commit()
    conn.close()

def delete_goal(goal_id):
    """Delete a goal from the database by its ID."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()

def goal_exists(goal_id):
    """Check if a goal with the given ID exists in the database."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM goals WHERE id = ?", (goal_id,))
    exists = cursor.fetchone()[0] > 0

    conn.close()
    return exists
