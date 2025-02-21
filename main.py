from rich.table import Table
from rich.console import Console
from rich.prompt import IntPrompt

console = Console()
import db

def display_goals():
    """Fetch and display saved financial goals in a table format."""
    goals = db.fetch_goals()

    if not goals:
        console.print("[yellow]No goals found. Add a goal first![/yellow]")
        return

    table = Table(title="Saved Financial Goals")
    table.add_column("ID", justify="right", style="bold yellow")
    table.add_column("Goal Name", style="bold cyan")
    table.add_column("Target (INR)", justify="right")
    table.add_column("Time (Years)", justify="center")
    table.add_column("CAGR (%)", justify="right")
    table.add_column("Mode", justify="center", style="bold magenta")
    table.add_column("Lumpsum (INR)", justify="right")
    table.add_column("SIP (INR)", justify="right")
    table.add_column("Start Date", justify="center")
    table.add_column("Created At", justify="center")

    for goal in goals:
        table.add_row(
            str(goal[0]),  # ID
            goal[1],       # Goal Name
            f"{goal[2]:,.2f}",  # Target Amount
            str(goal[3]),  # Time Horizon
            f"{goal[4]:.1f}",  # CAGR
            goal[5],       # Investment Mode
            f"{goal[6]:,.2f}" if goal[6] else "-",  # Lumpsum Investment
            f"{goal[7]:,.2f}" if goal[7] else "-",  # SIP Amount
            goal[8] if goal[8] else "-",  # Start Date
            goal[9],       # Created At
        )

    console.print(table)

def get_user_input():
    """Prompt user for goal details and return as a dictionary."""
    goal_name = console.input("[bold]Enter goal name:[/bold] ")
    target_amount = IntPrompt.ask("[bold]Enter target amount (INR):[/bold] ")
    time_horizon = IntPrompt.ask("[bold]Enter time horizon (years):[/bold] ")
    cagr = IntPrompt.ask("[bold]Enter expected CAGR (%):[/bold] ")
    investment_mode = console.input("[bold]Enter investment mode (Lumpsum/SIP):[/bold] ")
    lumpsum = IntPrompt.ask("[bold]Enter lumpsum amount (INR) (if applicable):[/bold] ", default=0)
    sip = IntPrompt.ask("[bold]Enter SIP amount (INR) (if applicable):[/bold] ", default=0)
    start_date = console.input("[bold]Enter start date (YYYY-MM-DD):[/bold] ")

    return {
        "goal_name": goal_name,
        "target_amount": target_amount,
        "time_horizon": time_horizon,
        "cagr": cagr,
        "investment_mode": investment_mode,
        "lumpsum": lumpsum,
        "sip": sip,
        "start_date": start_date
    }

def main_menu():
    """Display CLI menu with Rich UI."""
    while True:
        console.print("\n[bold cyan]=== Financial Goals Tracker ===[/bold cyan]\n")

        table = Table(show_header=False)
        table.add_column("Option", justify="center", style="bold yellow", no_wrap=True)
        table.add_column("Description", style="bold")

        table.add_row("1", "Add Goal")
        table.add_row("2", "View Goals")
        table.add_row("3", "Exit")

        console.print(table)

        while True:
            choice = IntPrompt.ask("[bold]Choose an option (1-3)[/bold]")
            if choice in [1, 2, 3]:
                break
            console.print("[red]Invalid choice. Please select a valid option (1, 2, or 3).[/red]")

        if choice == 1:
            goal_data = get_user_input()
            db.insert_goal(goal_data)
            console.print("\n[green]Goal added successfully![/green]\n")

        elif choice == 2:
            display_goals()

        elif choice == 3:
            console.print("[bold red]Exiting program.[/bold red]")
            break

if __name__ == "__main__":
    db.initialize_db()  # Ensure DB is set up
    main_menu()