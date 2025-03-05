# Financial Goals Tracker

A command-line tool for tracking financial goals, calculating required investments, and monitoring progress.

## Features
### Implemented
- Create financial goals (SIP, Lumpsum, or both)
- View saved goals (including target amount, CAGR, and time horizon)
- Calculate required investment to meet financial targets
- Track contributions and update progress
- Edit and delete goals
- Investment recommendations based on time horizon & CAGR

### Upcoming
- View detailed contribution history
- Export goals & progress as CSV
- Graphical progress tracking

## Installation & Setup
### Prerequisites
- Python 3.12+
- `uv` (dependency manager)
- SQLite (built-in with Python)

### Steps
1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/financial-goals-tracker.git
   cd financial-goals-tracker
   ```
2. Set up the virtual environment:
   ```sh
   uv venv
   uv pip install -e .  # Install package in editable mode
   ```
3. Run the application:
   ```sh
   uv run -m financial_goals_tracker.main
   ```

## Usage
### Running the application
```sh
uv run -m financial_goals_tracker.main
```
### Example CLI Workflow
```
=== Financial Goals Tracker ===
┌───┬─────────────────┐
│ 1 │ Add Goal        │
│ 2 │ View Goals      │
│ 3 │ Goal Calculator │
│ 4 │ Edit Goal       │
│ 5 │ Delete Goal     │
│ 6 │ Log Contribution│
│ 7 │ Exit            │
└───┴─────────────────┘
Choose an option (1-7): 1
Enter goal name: Buy a car
Enter target amount (INR): 1500000
Enter time horizon (years): 3
Enter expected CAGR (%): 12
Select Investment Mode:
1: SIP
2: Lumpsum
3: SIP + Lumpsum
Choose an option (1-3): 1
Goal added successfully!
```

## License
[MIT License](LICENSE)

---

This README will be updated as new features are added.

