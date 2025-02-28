import sqlite3
from datetime import datetime
import os
from rich.console import Console
import csv

console = Console()

DB_FILE = "financial_goals.db"

def connect_db():
    """Establish a database connection and return the connection object."""
    return sqlite3.connect(DB_FILE)

def initialize_db():
    """Create the goals and contributions tables if they do not exist, and apply necessary updates."""
    conn = connect_db()
    cursor = conn.cursor()

    # Create basics table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_basics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            is_completed BOOLEAN DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)

    # Insert default categories if they don't exist
    default_basics = [
        ('Emergency Fund', 0, 0, 0, None),
        ('Health Insurance', 0, 0, 0, None),
        ('Term Insurance', 0, 0, 0, None)
    ]

    for basic in default_basics:
        cursor.execute("""
            INSERT OR IGNORE INTO financial_basics 
            (category, target_amount, current_amount, is_completed, notes)
            SELECT ?, ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM financial_basics WHERE category = ?)
        """, (*basic, basic[0]))

    # Create goals table if not exists
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

    # Ensure missing columns are added dynamically
    cursor.execute("PRAGMA table_info(goals)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    if "investment_fund" not in existing_columns:
        cursor.execute("ALTER TABLE goals ADD COLUMN investment_fund TEXT")

    if "contributions_total" not in existing_columns:
        cursor.execute("ALTER TABLE goals ADD COLUMN contributions_total REAL DEFAULT 0")

    # Ensure contributions table has necessary columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            fund_name TEXT,
            nav_at_time_of_investment REAL,
            units_purchased REAL,
            FOREIGN KEY(goal_id) REFERENCES goals(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("PRAGMA table_info(contributions)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    if "fund_name" not in existing_columns:
        cursor.execute("ALTER TABLE contributions ADD COLUMN fund_name TEXT")

    if "nav_at_time_of_investment" not in existing_columns:
        cursor.execute("ALTER TABLE contributions ADD COLUMN nav_at_time_of_investment REAL")

    if "units_purchased" not in existing_columns:
        cursor.execute("ALTER TABLE contributions ADD COLUMN units_purchased REAL")

    # Commit changes before closing connection
    conn.commit()
    conn.close()

def fetch_goals():
    """Retrieve all saved financial goals from the database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, goal_name, target_amount, time_horizon, cagr, investment_mode,
               initial_investment, sip_amount, start_date, created_at, notes, contributions_total, investment_fund
        FROM goals
    """)
    goals = cursor.fetchall()
    conn.close()
    return goals

def log_contribution(goal_id, amount, date, fund_name=None, nav=None, units_purchased=None):
    """Log a new contribution, including fund selection and NAV tracking."""
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO contributions (
                goal_id, amount, date, fund_name, 
                nav_at_time_of_investment, units_purchased
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (goal_id, amount, date, fund_name, nav, units_purchased))

        # Update total contributions in the goals table
        cursor.execute("""
            UPDATE goals
            SET contributions_total = contributions_total + ?
            WHERE id = ?
        """, (amount, goal_id))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

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
        SELECT id, amount, date, fund_name, nav_at_time_of_investment, units_purchased 
        FROM contributions
        WHERE goal_id = ? 
        ORDER BY date DESC
    """, (goal_id,))

    contributions = cursor.fetchall()
    conn.close()
    return contributions  # Returns a list of tuples (id, amount, date, fund_name, nav, units)

def fetch_goal_by_id(goal_id):
    """Retrieve a specific goal by its ID."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, goal_name, target_amount, time_horizon, cagr, investment_mode, 
               initial_investment, sip_amount, start_date, created_at, notes, investment_fund
        FROM goals 
        WHERE id = ?
    """, (goal_id,))

    goal = cursor.fetchone()  # Fetch one goal
    conn.close()
    return goal  # Returns a tuple or None if not found

def goal_exists(goal_id):
    """Check if a goal with the given ID exists in the database."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM goals WHERE id = ?", (goal_id,))
    exists = cursor.fetchone()[0] > 0

    conn.close()
    return exists

def fetch_goal_funds(goal_id):
    """Fetch all funds associated with a specific goal."""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT fund_name 
        FROM contributions 
        WHERE goal_id = ? AND fund_name IS NOT NULL
        UNION
        SELECT investment_fund 
        FROM goals 
        WHERE id = ? AND investment_fund IS NOT NULL
    """, (goal_id, goal_id))
    
    funds = [row[0] for row in cursor.fetchall() if row[0]]  # Filter out None values
    conn.close()
    return funds

def fetch_basics():
    """Retrieve all financial basics and their status."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, category, target_amount, current_amount, is_completed, last_updated, notes
        FROM financial_basics
    """)
    basics = cursor.fetchall()
    conn.close()
    return basics

def update_basic(category, target_amount, current_amount, notes=None):
    """Update a financial basic category."""
    conn = connect_db()
    cursor = conn.cursor()
    
    is_completed = 1 if current_amount >= target_amount else 0
    
    try:
        cursor.execute("""
            UPDATE financial_basics
            SET target_amount = ?,
                current_amount = ?,
                is_completed = ?,
                notes = ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE category = ?
        """, (target_amount, current_amount, is_completed, notes, category))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

initialize_db()  # Ensure database is set up when the module is imported
