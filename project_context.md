# Financial Goals Tracker - Project Context

## Project Structure
```
financial-goals-tracker/
├── README.md
├── pyproject.toml
├── .gitignore
├── main.py
├── db.py
├── goals_calculator.py
├── investment_recommendation.py
└── data/
    ├── financial_goals.db
    ├── goals_export.csv
    └── contributions_export.csv
```

## Dependencies (from pyproject.toml)
- Python 3.12+
- openai
- anthropic
- google-generativeai
- python-dotenv
- click
- sqlite-utils
- rich
- matplotlib

## Core Modules

### db.py
**Imports:**
```python
import sqlite3
from datetime import datetime
import os
from rich.console import Console
import csv
```

**Database Schema:**
- `goals` table:
  - id (PRIMARY KEY)
  - goal_name (TEXT)
  - target_amount (REAL)
  - contributions_total (REAL)
  - time_horizon (INTEGER)
  - cagr (REAL)
  - investment_mode (TEXT)
  - initial_investment (REAL)
  - sip_amount (REAL)
  - start_date (TEXT)
  - notes (TEXT)
  - created_at (TIMESTAMP)
  - investment_fund (TEXT)

- `contributions` table:
  - id (PRIMARY KEY)
  - goal_id (INTEGER, FOREIGN KEY)
  - amount (REAL)
  - date (TEXT)
  - fund_name (TEXT)
  - nav_at_time_of_investment (REAL)
  - units_purchased (REAL)

**Key Functions:**
- `connect_db()`: Creates database connection
- `initialize_db()`: Sets up database schema
- `fetch_goals()`: Retrieves all goals
- `log_contribution(goal_id, amount, date, fund_name, nav, units_purchased)`: Records new contribution
- `get_goal_total_contributions(goal_id)`: Calculates total contributions for a goal
- `fetch_contributions(goal_id)`: Gets all contributions for a goal
- `fetch_goal_by_id(goal_id)`: Retrieves specific goal
- `goal_exists(goal_id)`: Checks if goal exists
- `fetch_goal_funds(goal_id)`: Gets funds associated with a goal

### goals_calculator.py
**Imports:**
```python
import math
```

**Key Functions:**
- `calculate_lumpsum(target_amount, time_horizon, cagr)`: Calculates required one-time investment
- `calculate_sip(target_amount, time_horizon, cagr)`: Calculates required monthly SIP
- `calculate_mixed(target_amount, time_horizon, cagr, lumpsum_percentage, lumpsum_amount)`: Calculates hybrid investment plan

### investment_recommendation.py
**Key Functions:**
- `recommend_investment(time_horizon, cagr)`: Provides investment recommendations based on timeline and expected returns

### main.py
**Imports:**
```python
import goals_calculator
from rich.table import Table
from rich.console import Console
from rich.prompt import Prompt
import db
import investment_recommendation 
import csv
import matplotlib.pyplot as plt
from datetime import datetime
import os
```

**Key Functions:**
- `display_goals()`: Shows all goals in tabular format
- `get_numeric_input()`: Validates numeric input
- `get_user_input()`: Collects goal details from user
- `goal_calculator_menu()`: Calculator interface
- `log_contribution_menu()`: Interface for logging contributions
- `view_contributions_menu()`: Shows contribution history
- `export_to_csv()`: Exports data to CSV
- `plot_goal_progress()`: Generates progress visualization
- `calculate_milestones()`: Tracks goal milestones
- `calculate_future_value()`: Projects investment growth
- `main_menu()`: Main CLI interface

## Key Features
1. Goal Management:
   - Create financial goals (SIP/Lumpsum/Hybrid)
   - Edit/Delete goals
   - Track progress
   - Calculate required investments

2. Investment Tracking:
   - Log contributions
   - Track NAV and units
   - Monitor fund performance
   - Calculate future value

3. Reporting:
   - Progress visualization
   - Milestone tracking
   - CSV export
   - Investment recommendations

## Data Flow
1. User input → main.py
2. Calculations → goals_calculator.py
3. Storage → db.py
4. Recommendations → investment_recommendation.py
5. Visualization/Display → main.py (using rich)

## Notes
- Uses SQLite for persistent storage
- Rich library for CLI formatting
- Supports multiple investment modes
- Includes data validation and error handling
- Maintains contribution history
- Tracks fund-specific details (NAV, units)