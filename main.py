from rich.table import Table
from rich.console import Console
from rich.prompt import IntPrompt
import db

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
    table.add_column("Notes", justify="center")

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
            goal[9] if goal[9] else "-",      # Created At
            goal[10],   # Notes
        )

    console.print(table)
def get_user_input():
    """Prompt user for goal details and return as a dictionary."""
    goal_name = console.input("[bold]Enter goal name:[/bold] ")
    target_amount = IntPrompt.ask("[bold]Enter target amount (INR):[/bold] ")
    time_horizon = IntPrompt.ask("[bold]Enter time horizon (years):[/bold] ")
    cagr = IntPrompt.ask("[bold]Enter expected CAGR (%):[/bold] ")

    # Investment Mode Selection
    console.print("\n[bold cyan]Select Investment Mode:[/bold cyan]")
    console.print("[bold yellow]1[/bold yellow]: SIP")
    console.print("[bold yellow]2[/bold yellow]: Lumpsum")
    console.print("[bold yellow]3[/bold yellow]: SIP + Lumpsum")

    while True:
        mode_choice = IntPrompt.ask("[bold]Choose an option (1-3):[/bold] ")
        if mode_choice in [1, 2, 3]:
            investment_modes = {1: "SIP", 2: "Lumpsum", 3: "SIP + Lumpsum"}
            investment_mode = investment_modes[mode_choice]
            break
        console.print("[red]Invalid choice. Please select 1, 2, or 3.[/red]")

    # Ask for investment amounts based on mode
    initial_investment = 0
    sip_amount = 0

    if investment_mode in ["Lumpsum", "SIP + Lumpsum"]:
        initial_investment = IntPrompt.ask("[bold]Enter lumpsum amount (INR) (if applicable):[/bold] ", default=0)

    if investment_mode in ["SIP", "SIP + Lumpsum"]:
        sip_amount = IntPrompt.ask("[bold]Enter SIP amount (INR) (if applicable):[/bold] ", default=0)

    # Start Date Input
    start_date = console.input("[bold]Enter start date (YYYY-MM-DD):[/bold] ") or None

    notes = console.input("[bold]Enter notes (optional, press Enter to skip):[/bold] ") or None

    return {
        "goal_name": goal_name,
        "target_amount": target_amount,
        "time_horizon": time_horizon,
        "cagr": cagr,
        "investment_mode": investment_mode,
        "initial_investment": initial_investment,
        "sip_amount": sip_amount,
        "start_date": start_date,
        "notes": notes  # Now included in the return dictionary
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