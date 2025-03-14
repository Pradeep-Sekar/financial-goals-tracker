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
            fund_name TEXT,
            nav REAL,
            FOREIGN KEY(goal_id) REFERENCES goals(id) ON DELETE CASCADE
        )
    """)

    # Create basics table with recommendations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_basics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT CHECK(category IN ('emergency_fund', 'health_insurance', 'term_insurance')) NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            is_funded BOOLEAN DEFAULT 0,
            recommendation_formula TEXT NOT NULL,
            recommendation_description TEXT NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert default recommendations if they don't exist
    cursor.execute("SELECT COUNT(*) FROM financial_basics")
    if cursor.fetchone()[0] == 0:
        default_basics = [
            ('emergency_fund', 0, 0, 0, '6 * monthly_expenses', 'Recommended: 6 months of monthly expenses'),
            ('health_insurance', 0, 0, 0, 'max(500000, family_members * 200000)', 'Recommended: ₹5L or ₹2L per family member'),
            ('term_insurance', 0, 0, 0, 'max(10000000, annual_income * 10)', 'Recommended: ₹1Cr or 10x annual income')
        ]
        cursor.executemany("""
            INSERT INTO financial_basics (category, target_amount, current_amount, is_funded, recommendation_formula, recommendation_description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, default_basics)

    # Create table for tracking historical changes to basics
    create_basics_history_table()

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
        ORDER BY created_at DESC
    """)

    goals = cursor.fetchall()
    conn.close()
    return goals

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

def log_contribution(goal_id, amount, date, fund_name=None, nav=None):
    """Log a new contribution and update the total contributions in the goals table."""
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Insert the contribution into the contributions table
        if fund_name and nav:
            cursor.execute("""
                INSERT INTO contributions (goal_id, amount, date, fund_name, nav)
                VALUES (?, ?, ?, ?, ?)
            """, (goal_id, amount, date, fund_name, nav))
        else:
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
        console.print("[green]Contribution logged successfully![/green]")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

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
        SELECT contributions_total FROM goals WHERE id = ?
    """, (goal_id,))
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0

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

def fetch_all_goals():
    """Retrieve all financial goals."""
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

def fetch_all_contributions():
    """Retrieve all contributions."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT contributions.id, goal_id, goal_name, amount, date
        FROM contributions
        JOIN goals ON contributions.goal_id = goals.id
        ORDER BY date DESC
    """)
    contributions = cursor.fetchall()
    conn.close()
    return contributions

def fetch_contributions_for_graph(goal_id):
    """Retrieve contribution amounts and dates for graphing."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date, SUM(amount) 
        FROM contributions 
        WHERE goal_id = ? 
        GROUP BY date 
        ORDER BY date ASC
    """, (goal_id,))
    data = cursor.fetchall()
    conn.close()
    return data  # List of (date, total amount contributed)

def fetch_goal_by_id(goal_id):
    """Retrieve a specific goal by its ID."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, goal_name, target_amount, time_horizon, cagr, investment_mode, 
               initial_investment, sip_amount, start_date
        FROM goals 
        WHERE id = ?
    """, (goal_id,))

    goal = cursor.fetchone()  # Fetch one goal
    conn.close()
    return goal  # Returns (id, goal_name, target_amount) or None if not found

def get_goal_total_contributions(goal_id):
    """Fetch total contributions for a specific goal."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(amount) FROM contributions WHERE goal_id = ?
    """, (goal_id,))
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0  # Ensure it returns 0 if no contributions exist

def update_basic_amount(category, amount, monthly_expenses=None, family_members=None, annual_income=None):
    """Update amount and calculate if basic is funded."""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Calculate recommended amount based on category
    if category == 'emergency_fund' and monthly_expenses:
        recommended = monthly_expenses * 6
    elif category == 'health_insurance' and family_members:
        recommended = max(500000, family_members * 200000)
    elif category == 'term_insurance' and annual_income:
        recommended = max(10000000, annual_income * 10)
    else:
        recommended = 0

    # Fetch the current amount before updating
    cursor.execute("""
        SELECT current_amount FROM financial_basics WHERE category = ?
    """, (category,))
    current_amount = cursor.fetchone()[0] if cursor.fetchone() else 0

    # Update the basic
    cursor.execute("""
        UPDATE financial_basics 
        SET current_amount = ?, 
            target_amount = ?,
            is_funded = ?,
            last_updated = CURRENT_TIMESTAMP
        WHERE category = ?
    """, (amount, recommended, amount >= recommended, category))

    # Log the change
    log_basics_change(category, current_amount, amount, f"Updated {category} amount")

    conn.commit()
    conn.close()

def get_basics_status():
    """Fetch status of all financial basics."""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT category, target_amount, current_amount, is_funded, 
               recommendation_description, last_updated
        FROM financial_basics
    """)
    
    result = cursor.fetchall()
    conn.close()
    return result

def fetch_basics():
    """Retrieve all financial basics from the database."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            category,
            target_amount,
            current_amount,
            is_funded,
            recommendation_description,
            last_updated
        FROM financial_basics
        ORDER BY id
    """)

    basics = cursor.fetchall()
    conn.close()
    return basics

def export_all_data(export_dir="backups"):
    """Export all data from database to CSV files with timestamp."""
    # Create timestamp for unique backup folders
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(export_dir, timestamp)
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Export goals
        cursor.execute("SELECT * FROM goals")
        goals = cursor.fetchall()
        with open(f"{backup_dir}/goals.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([description[0] for description in cursor.description])
            writer.writerows(goals)
        
        # Export contributions
        cursor.execute("SELECT * FROM contributions")
        contributions = cursor.fetchall()
        with open(f"{backup_dir}/contributions.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([description[0] for description in cursor.description])
            writer.writerows(contributions)
            
        # Export financial basics
        cursor.execute("SELECT * FROM financial_basics")
        basics = cursor.fetchall()
        with open(f"{backup_dir}/financial_basics.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([description[0] for description in cursor.description])
            writer.writerows(basics)
        
        return backup_dir
    
    finally:
        conn.close()

def import_all_data(backup_dir):
    """Import all data from CSV files into database."""
    if not os.path.exists(backup_dir):
        raise FileNotFoundError(f"Backup directory not found: {backup_dir}")
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Clear existing data
        cursor.execute("DELETE FROM contributions")
        cursor.execute("DELETE FROM goals")
        cursor.execute("DELETE FROM financial_basics")
        
        # Import goals
        goals_file = os.path.join(backup_dir, "goals.csv")
        if os.path.exists(goals_file):
            with open(goals_file, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)  # Skip headers
                for row in reader:
                    cursor.execute("""
                        INSERT INTO goals 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, row)
        
        # Import contributions
        contributions_file = os.path.join(backup_dir, "contributions.csv")
        if os.path.exists(contributions_file):
            with open(contributions_file, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)  # Skip headers
                for row in reader:
                    cursor.execute("""
                        INSERT INTO contributions 
                        VALUES (?, ?, ?, ?)
                    """, row)
        
        # Import financial basics
        basics_file = os.path.join(backup_dir, "financial_basics.csv")
        if os.path.exists(basics_file):
            with open(basics_file, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)  # Skip headers
                for row in reader:
                    cursor.execute("""
                        INSERT INTO financial_basics 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, row)
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def list_backups(backup_dir="backups"):
    """List all available backups."""
    if not os.path.exists(backup_dir):
        return []
    
    backups = []
    for d in os.listdir(backup_dir):
        backup_path = os.path.join(backup_dir, d)
        if os.path.isdir(backup_path):
            backups.append(d)
    
    return sorted(backups, reverse=True)  # Most recent first

def update_basic(category, target_amount, current_amount, notes, additional_info=None):
    """Update a financial basic with new values."""
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Convert category name to database format
        category_db = category.lower().replace(" ", "_")

        # Fetch the current amount before updating
        cursor.execute("SELECT current_amount FROM financial_basics WHERE category = ?", (category_db,))
        result = cursor.fetchone()
        old_amount = result[0] if result else 0

        # Calculate recommended amount for reference
        if additional_info:
            if category_db == "emergency_fund" and "monthly_expenses" in additional_info:
                recommended = additional_info["monthly_expenses"] * 6
            elif category_db == "health_insurance" and "family_members" in additional_info:
                recommended = max(500000, additional_info["family_members"] * 200000)
            elif category_db == "term_insurance" and "annual_income" in additional_info:
                recommended = max(10000000, additional_info["annual_income"] * 10)
        
        # Use the user's target amount instead of the recommended amount
        is_funded = current_amount >= target_amount

        # Update the basic
        cursor.execute("""
            UPDATE financial_basics 
            SET target_amount = ?,
                current_amount = ?,
                is_funded = ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE category = ?
        """, (target_amount, current_amount, is_funded, category_db))

        # Log the change using the same connection
        log_basics_change(category_db, old_amount, current_amount, notes, conn)

        conn.commit()
        return True

    except Exception as e:
        if conn:
            conn.rollback()
        console.print(f"[red]Error updating financial basic: {str(e)}[/red]")
        return False
    finally:
        if conn:
            conn.close()

def create_basics_history_table():
    """Create table for tracking historical changes to basics."""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_basics_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL NOT NULL,
            change_amount REAL NOT NULL,
            change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def log_basics_change(category, old_amount, new_amount, notes="", conn=None):
    """Log changes to financial basics for historical tracking."""
    should_close = False
    if conn is None:
        conn = connect_db()
        should_close = True
    
    cursor = conn.cursor()
    try:
        # Get current target amount
        cursor.execute("SELECT target_amount FROM financial_basics WHERE category = ?", (category,))
        result = cursor.fetchone()
        target_amount = result[0] if result else 0
        
        change_amount = new_amount - old_amount
        
        cursor.execute("""
            INSERT INTO financial_basics_history 
            (category, target_amount, current_amount, change_amount, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (category, target_amount, new_amount, change_amount, notes))
        
        conn.commit()
    finally:
        if should_close:
            conn.close()
