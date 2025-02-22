import goals_calculator
from rich.table import Table
from rich.console import Console
from rich.prompt import Prompt
import db
import investment_recommendation 

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

def get_numeric_input(prompt_text, default=0, input_type=int):
    """Reusable function to get a numeric input with validation."""
    while True:
        user_input = Prompt.ask(f"[bold]{prompt_text}[/bold]", default=str(default))
        try:
            return input_type(user_input)  # Convert input to int or float
        except ValueError:
            console.print(f"[red]Invalid input. Please enter a valid {input_type.__name__}.[/red]")

def get_user_input():
    """Prompt user for goal details and return as a dictionary."""
    goal_name = console.input("[bold]Enter goal name:[/bold] ")
    target_amount = Prompt.ask("[bold]Enter target amount (INR):[/bold] ", default=0, convert=int)
    time_horizon = Prompt.ask("[bold]Enter time horizon (years):[/bold] ", default=0, convert=int)
    cagr = Prompt.ask("[bold]Enter expected CAGR (%):[/bold] ", default=0.0, convert=float)

    # Investment Mode Selection
    console.print("\n[bold cyan]Select Investment Mode:[/bold cyan]")
    console.print("[bold yellow]1[/bold yellow]: SIP")
    console.print("[bold yellow]2[/bold yellow]: Lumpsum")
    console.print("[bold yellow]3[/bold yellow]: SIP + Lumpsum")

    while True:
        mode_choice = Prompt.ask("[bold]Choose an option (1-3):[/bold] ")
        if mode_choice in [1, 2, 3]:
            investment_modes = {1: "SIP", 2: "Lumpsum", 3: "SIP + Lumpsum"}
            investment_mode = investment_modes[mode_choice]
            break
        console.print("[red]Invalid choice. Please select 1, 2, or 3.[/red]")

    # Ask for investment amounts based on mode
    initial_investment = 0
    sip_amount = 0

    if investment_mode in ["Lumpsum", "SIP + Lumpsum"]:
        initial_investment = Prompt.ask("[bold]Enter lumpsum amount (INR) (if applicable):[/bold] ", default=0, convert=int)

    if investment_mode in ["SIP", "SIP + Lumpsum"]:
        sip_amount = Prompt.ask("[bold]Enter SIP amount (INR) (if applicable):[/bold] ", default=0, convert=int)

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

def goal_calculator_menu():
    """Prompt user for goal details and calculate required investments."""
    console.print("\n[bold cyan]Goal Target Calculator[/bold cyan]\n")



    target_amount = get_numeric_input("Enter target amount (INR):")
    time_horizon = get_numeric_input("Enter time horizon (years):")
    cagr = get_numeric_input("Enter expected CAGR (%):", default=12.0, input_type=float)

    console.print("\n[bold cyan]Select Investment Mode:[/bold cyan]")
    console.print("[bold yellow]1[/bold yellow]: SIP")
    console.print("[bold yellow]2[/bold yellow]: Lumpsum")
    console.print("[bold yellow]3[/bold yellow]: SIP + Lumpsum")
    recommendation = investment_recommendation.recommend_investment(time_horizon, cagr)
    console.print(f"\n[bold green]Recommended Investment:[/bold green] {recommendation}")

    while True:
        mode_choice = Prompt.ask("[bold]Choose an option (1-3):[/bold] ")
        try:
            mode_choice = int(mode_choice)  # Convert input manually
            break
        except ValueError:
            console.print("[red]Invalid choice. Please select 1, 2, or 3.[/red]")

    table = Table(title="Investment Calculation")
    table.add_column("Investment Mode", style="bold cyan")
    table.add_column("Required Investment (INR)", justify="right")

    if mode_choice == 1:
        sip_amount = goals_calculator.calculate_sip(target_amount, time_horizon, cagr)
        table = Table(title="Investment Calculation")
        table.add_column("Investment Mode", style="bold cyan")
        table.add_column("Required Investment (INR)", justify="right")

        table.add_row("SIP (Monthly)", f"{sip_amount:,.2f}")
        console.print(table)  # Ensure results are displayed before returning
        console.input("\nPress Enter to return to the main menu...")  # Pause before returning

    elif mode_choice == 2:  # Lumpsum Calculation
        lumpsum = goals_calculator.calculate_lumpsum(target_amount, time_horizon, cagr)
        table = Table(title="Investment Calculation")
        table.add_column("Investment Mode", style="bold cyan")
        table.add_column("Required Investment (INR)", justify="right")

        table.add_row("Lumpsum (Today)", f"{lumpsum:,.2f}")
        console.print(table)
        console.input("\nPress Enter to return to the main menu...")  # Pause before exiting

    elif mode_choice == 3:
        console.print("\n[bold cyan]Choose how to allocate your Lumpsum investment:[/bold cyan]")
        console.print("[bold yellow]1[/bold yellow]: Enter a percentage of the target amount")
        console.print("[bold yellow]2[/bold yellow]: Enter a fixed lumpsum amount")

        while True:
            lumpsum_option = get_numeric_input("Choose an option (1-2):", default=1)
            if lumpsum_option in [1, 2]:
                break
            console.print("[red]Invalid choice. Please select 1 or 2.[/red]")

        if lumpsum_option == 1:
            lumpsum_percentage = get_numeric_input("Enter percentage of target to invest as Lumpsum:", default=50, input_type=float)
            lumpsum, sip = goals_calculator.calculate_mixed(target_amount, time_horizon, cagr, lumpsum_percentage=lumpsum_percentage)
        
        elif lumpsum_option == 2:
            lumpsum_amount = get_numeric_input("Enter the fixed Lumpsum amount (INR):", default=0, input_type=float)
            lumpsum, sip = goals_calculator.calculate_mixed(target_amount, time_horizon, cagr, lumpsum_amount=lumpsum_amount)

        if lumpsum > 0:
            table.add_row("Lumpsum (Today)", f"{lumpsum:,.2f}")
        if sip > 0:
            table.add_row("SIP (Monthly)", f"{sip:,.2f}")

        console.print(table)
        recommendation = investment_recommendation.recommend_investment(time_horizon, cagr)
        console.print(f"\n[bold green]Recommended Investment:[/bold green] {recommendation}")

def delete_goal_menu():
    """Allow the user to delete a goal by selecting its ID."""
    display_goals()  # Show existing goals

    goal_id = get_numeric_input("Enter the ID of the goal to delete (or 0 to cancel):", default=0)
    
    if goal_id == 0:
        console.print("[yellow]Deletion canceled.[/yellow]")
        return

    # Verify that the goal exists before confirming deletion
    if not db.goal_exists(goal_id):
        console.print("[red]Error: No goal found with this ID.[/red]")
        return

    confirm = console.input("[bold red]Are you sure you want to delete this goal? (yes/no):[/bold red] ").strip().lower()
    if confirm == "yes":
        db.delete_goal(goal_id)
        console.print("[green]Goal deleted successfully![/green]")
    else:
        console.print("[yellow]Deletion canceled.[/yellow]")

def edit_goal_menu():
    """Allow the user to edit multiple fields of a goal in one session."""
    display_goals()  # Show existing goals

    goal_id = get_numeric_input("Enter the ID of the goal to edit (or 0 to cancel):", default=0)

    if goal_id == 0:
        console.print("[yellow]Edit canceled.[/yellow]")
        return

    if not db.goal_exists(goal_id):
        console.print("[red]Error: No goal found with this ID.[/red]")
        return

    console.print("\n[bold cyan]Select fields to edit (enter multiple numbers separated by commas):[/bold cyan]")
    fields = {
        "1": "goal_name",
        "2": "target_amount",
        "3": "time_horizon",
        "4": "cagr",
        "5": "investment_mode",
        "6": "initial_investment",
        "7": "sip_amount",
        "8": "start_date",
        "9": "notes"
    }

    for key, field in fields.items():
        console.print(f"[bold yellow]{key}[/bold yellow]: {field.replace('_', ' ').title()}")

    selected_fields = console.input("[bold]Enter field numbers to edit (comma-separated, e.g., 2,3,5):[/bold] ").strip()

    selected_fields = selected_fields.split(",")  # Convert input into a list
    selected_fields = [field.strip() for field in selected_fields if field.strip() in fields]  # Validate input

    if not selected_fields:
        console.print("[red]No valid fields selected. Returning to main menu.[/red]")
        return

    updated_data = {}
    
    for field_choice in selected_fields:
        field_name = fields[field_choice]
        new_value = console.input(f"[bold]Enter new value for {field_name.replace('_', ' ').title()}:[/bold] ").strip()
        updated_data[field_name] = new_value

    console.print("\n[bold cyan]Confirm changes:[/bold cyan]")
    for field, value in updated_data.items():
        console.print(f"  [bold yellow]{field.replace('_', ' ').title()}[/bold yellow]: {value}")

    confirm = console.input("[bold red]Are you sure you want to update these fields? (y)es/(n)o):[/bold red] ").strip().lower()
    if confirm == "y":
        for field, value in updated_data.items():
            db.update_goal(goal_id, field, value)
        console.print("[green]Goal updated successfully![/green]")
    else:
        console.print("[yellow]Edit canceled.[/yellow]")

def main_menu():
    """Display CLI menu with Rich UI."""
    while True:
        console.print("\n[bold cyan]=== Financial Goals Tracker ===[/bold cyan]\n")

        table = Table(show_header=False)
        table.add_column("Option", justify="center", style="bold yellow", no_wrap=True)
        table.add_column("Description", style="bold")

        table.add_row("1", "Add Goal")
        table.add_row("2", "View Goals")
        table.add_row("3", "Goal Calculator")
        table.add_row("4", "Edit Goal")  # New option
        table.add_row("5", "Delete Goal")
        table.add_row("6", "Exit")  # Shift exit to option 6

        console.print(table)

        while True:
            choice = Prompt.ask("[bold]Choose an option (1-6)[/bold]")
            try:
                choice = int(choice)  # Convert input manually
                if choice in [1, 2, 3, 4, 5, 6]:
                    break
                console.print("[red]Invalid choice. Please select a valid option (1-6).[/red]")
            except ValueError:
                console.print("[red]Invalid input. Please enter a number (1-6).[/red]")

        if choice == 1:
            goal_data = get_user_input()
            db.insert_goal(goal_data)
            console.print("\n[green]Goal added successfully![/green]\n")

        elif choice == 2:
            display_goals()

        elif choice == 3:
            goal_calculator_menu()

        elif choice == 4:
            edit_goal_menu()

        elif choice == 5:
             delete_goal_menu()
            
        elif choice == 6:
            console.print("[bold red]Exiting program.[/bold red]")
            break
if __name__ == "__main__":
    db.initialize_db()  # Ensure DB is set up
    main_menu()