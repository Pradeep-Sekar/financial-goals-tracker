import sqlite3
from datetime import datetime
import os
from rich.console import Console

console = Console()

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
            contributions_total REAL DEFAULT 0,       
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

    # Ensure contributions_total column exists (for older databases)
    cursor.execute("PRAGMA table_info(goals)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    if "contributions_total" not in existing_columns:
        cursor.execute("ALTER TABLE goals ADD COLUMN contributions_total REAL DEFAULT 0")
        conn.commit()

    # Create contributions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY(goal_id) REFERENCES goals(id) ON DELETE CASCADE
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
    """Retrieve all saved financial goals from the database, ensuring correct column order."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, goal_name, target_amount, time_horizon, cagr, investment_mode,
               initial_investment, sip_amount, start_date, created_at, notes, contributions_total
        FROM goals
    """)

    goals = cursor.fetchall()
    conn.close()
    return goals

    cursor.execute("""
        SELECT id, goal_name, target_amount, time_horizon, cagr, investment_mode, initial_investment, sip_amount, start_date, created_at, contributions_total, notes
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

def update_goal(goal_id, field, new_value):
    """Update a specific field of a goal in the database."""
    conn = connect_db()
    cursor = conn.cursor()

    # Ensure only allowed fields can be updated
    allowed_fields = ["goal_name", "target_amount", "time_horizon", "cagr",
                      "investment_mode", "initial_investment", "sip_amount", "start_date", "notes"]

    if field not in allowed_fields:
        conn.close()
        raise ValueError(f"Invalid field: {field}")

    query = f"UPDATE goals SET {field} = ? WHERE id = ?"
    cursor.execute(query, (new_value, goal_id))

    conn.commit()
    conn.close()

def log_contribution(goal_id, amount, date):
    """Log a new contribution and update the total contributions in the goals table."""
    conn = connect_db()
    cursor = conn.cursor()

    # Insert the contribution into the contributions table
    cursor.execute("""
        INSERT INTO contributions (goal_id, amount, date)
        VALUES (?, ?, ?)
    """, (goal_id, amount, date))

    # Update the total contributions in the goals table
    cursor.execute("""
        UPDATE goals
        SET contributions_total = contributions_total + ?
        WHERE id = ?
    """, (amount, goal_id))

    conn.commit()
    conn.close()
    console.print("[green]Contribution logged successfully![/green]")

def get_goal_progress(goal_id):
    """Retrieve total contributions and calculate progress percentage."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT contributions_total, target_amount FROM goals WHERE id = ?
    """, (goal_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        contributions_total, target_amount = result
        progress = (contributions_total / target_amount) * 100 if target_amount > 0 else 0
        return round(progress, 2)
    return None

def get_goal_total_contributions(goal_id):
    """Fetch total contributions for a specific goal."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM contributions WHERE goal_id = ?
    """, (goal_id,))
    
    total_contributions = cursor.fetchone()[0]  # Get the sum or 0 if no contributions

    conn.close()
    return total_contributions

def fetch_contributions(goal_id):
    """Retrieve all contributions for a given goal, sorted by date (latest first)."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, amount, date FROM contributions
        WHERE goal_id = ? ORDER BY date DESC
    """, (goal_id,))

    contributions = cursor.fetchall()
    conn.close()
    return contributions
