from financial_goals_tracker import goals_calculator
from financial_goals_tracker import db
from financial_goals_tracker import investment_recommendation
from rich.table import Table
from rich.console import Console
from rich.prompt import Prompt
import csv
import matplotlib.pyplot as plt
from datetime import datetime
import os

console = Console()

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
    table.add_column("Total Contributions", justify="right", style="green")  # New Column
    table.add_column("Progress (%)", justify="right", style="magenta")  # New Column
    table.add_column("Notes", style="italic")
    table.add_column("Created At", justify="center")
    
    for goal in goals:
        goal_id = goal[0]  # ID
        total_contributions = db.get_goal_total_contributions(goal_id)  # Fetch from DB
        progress = (total_contributions / goal[2]) * 100 if goal[2] > 0 else 0  # Calculate %

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
            f"{total_contributions:,.2f}",  # Display Contributions
            f"{progress:.2f}%",  # Display Progress
            goal[10] if goal[9] else "-", # Notes
            goal[9] 

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
    """Prompt user for goal details, integrate goal calculator, and allow fund selection."""
    goal_name = Prompt.ask("[bold]Enter goal name[/bold]")

    # Handle numeric inputs with validation
    while True:
        try:
            target_amount = int(Prompt.ask("[bold]Enter target amount (INR):[/bold] ", default="0"))
            if target_amount < 0:
                console.print("[red]Amount cannot be negative.[/red]")
                continue
            break
        except ValueError:
            console.print("[red]Please enter a valid number.[/red]")

    while True:
        try:
            time_horizon = int(Prompt.ask("[bold]Enter time horizon (years):[/bold] ", default="0"))
            if time_horizon < 0:
                console.print("[red]Time horizon cannot be negative.[/red]")
                continue
            break
        except ValueError:
            console.print("[red]Please enter a valid number.[/red]")

    while True:
        try:
            cagr = float(Prompt.ask("[bold]Enter expected CAGR (%):[/bold] ", default="12.0"))
            break
        except ValueError:
            console.print("[red]Please enter a valid number.[/red]")

    console.print("\n[bold yellow]Calculating required investment...[/bold yellow]")
    console.print("\n[bold cyan]Select Investment Mode:[/bold cyan]")
    console.print("[bold yellow]1[/bold yellow]: SIP")
    console.print("[bold yellow]2[/bold yellow]: Lumpsum")
    console.print("[bold yellow]3[/bold yellow]: SIP + Lumpsum")

    while True:
        mode_choice = get_numeric_input("Choose an option (1-3):", default=1)
        if mode_choice in [1, 2, 3]:
            investment_modes = {1: "SIP", 2: "Lumpsum", 3: "SIP + Lumpsum"}
            investment_mode = investment_modes[mode_choice]
            break
        console.print("[red]Invalid choice. Please select 1, 2, or 3.[/red]")

    # Initialize variables
    initial_investment = 0
    sip_amount = 0

    if investment_mode == "Lumpsum":
        while True:
            try:
                initial_investment = int(Prompt.ask("[bold]Enter lumpsum amount (INR):[/bold] ", default="0"))
                if initial_investment < 0:
                    console.print("[red]Amount cannot be negative.[/red]")
                    continue
                break
            except ValueError:
                console.print("[red]Please enter a valid number.[/red]")
    
    elif investment_mode == "SIP":
        sip_amount = goals_calculator.calculate_sip(target_amount, time_horizon, cagr)
        console.print(f"\n[bold green]Required monthly SIP: ₹{sip_amount:,.2f}[/bold green]")
    
    elif investment_mode == "SIP + Lumpsum":
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
            initial_investment, sip_amount = goals_calculator.calculate_mixed(
                target_amount, time_horizon, cagr, lumpsum_percentage=lumpsum_percentage
            )
        else:
            lumpsum_amount = get_numeric_input("Enter the fixed Lumpsum amount (INR):", default=0, input_type=float)
            initial_investment, sip_amount = goals_calculator.calculate_mixed(
                target_amount, time_horizon, cagr, lumpsum_amount=lumpsum_amount
            )
        
        console.print(f"\n[bold green]Required investments:[/bold green]")
        console.print(f"[green]Lumpsum: ₹{initial_investment:,.2f}[/green]")
        console.print(f"[green]Monthly SIP: ₹{sip_amount:,.2f}[/green]")

    # Start Date Input
    start_date = Prompt.ask("[bold]Enter start date (YYYY-MM-DD, leave blank for today):[/bold] ").strip()
    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d")
    
    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        console.print("[red]Invalid date format. Using today's date instead.[/red]")
        start_date = datetime.now().strftime("%Y-%m-%d")

    notes = Prompt.ask("[bold]Enter notes (optional):[/bold] ", default="")

    return {
        "goal_name": goal_name,
        "target_amount": target_amount,
        "time_horizon": time_horizon,
        "cagr": cagr,
        "investment_mode": investment_mode,
        "initial_investment": initial_investment,
        "sip_amount": sip_amount,
        "start_date": start_date,
        "notes": notes
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

def log_contribution_menu():
    """Menu for logging a new contribution to a goal."""
    display_goals()  # Show available goals

    goal_id = Prompt.ask("[bold]Enter the ID of the goal to contribute to (or 0 to cancel):[/bold]").strip()
    if goal_id == "0":
        console.print("[yellow]Returning to main menu.[/yellow]")
        return

    if not goal_id.isdigit():
        console.print("[red]Invalid input. Please enter a valid goal ID.[/red]")
        return
    goal_id = int(goal_id)

    # Fetch goal details first
    goal = db.fetch_goal_by_id(goal_id)
    if not goal:
        console.print("[red]Goal not found.[/red]")
        return

    # Get basic contribution details
    while True:
        try:
            amount = float(Prompt.ask("[bold]Enter contribution amount (INR):[/bold]").strip())
            if amount <= 0:
                console.print("[red]Amount must be positive.[/red]")
                continue
            break
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid number.[/red]")

    date = Prompt.ask("[bold]Enter contribution date (YYYY-MM-DD, leave blank for today):[/bold]").strip()
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        console.print("[red]Invalid date format. Using today's date instead.[/red]")
        date = datetime.now().strftime("%Y-%m-%d")

    # Log the contribution
    try:
        db.log_contribution(goal_id, amount, date)
        console.print("[green]Contribution logged successfully![/green]")
    except Exception as e:
        console.print(f"[red]Error logging contribution: {str(e)}[/red]")

def view_contributions_menu():
    """Allow users to view past contributions for a specific goal."""
    display_goals()  # Show available goals

    goal_id = Prompt.ask("[bold]Enter the ID of the goal to view contributions (or 0 to cancel):[/bold]").strip()
    if goal_id == "0":
        console.print("[yellow]Returning to main menu.[/yellow]")
        return

    # Ensure goal_id is valid
    if not goal_id.isdigit():
        console.print("[red]Invalid input. Please enter a valid goal ID.[/red]")
        return
    goal_id = int(goal_id)

    contributions = db.fetch_contributions(goal_id)

    if not contributions:
        console.print("[yellow]No contributions found for this goal.[/yellow]")
        return

    table = Table(title=f"Contribution History for Goal ID {goal_id}")
    table.add_column("ID", style="bold yellow")
    table.add_column("Amount (INR)", justify="right", style="green")
    table.add_column("Date", justify="center", style="bold cyan")

    for entry in contributions:
        table.add_row(str(entry[0]), f"{entry[1]:,.2f}", entry[2])

    console.print(table)

def export_to_csv():
    """Export financial goals and contributions to CSV files."""
    goals = db.fetch_all_goals()
    contributions = db.fetch_all_contributions()

    goals_filename = "goals_export.csv"
    contributions_filename = "contributions_export.csv"
    
    # Check if files already exist
    files_exist = []
    if os.path.exists(goals_filename):
        files_exist.append(goals_filename)
    if os.path.exists(contributions_filename):
        files_exist.append(contributions_filename)
        
    if files_exist:
        file_list = ", ".join(files_exist)
        confirm = Prompt.ask(
            f"[bold yellow]Warning: {file_list} already exist. Overwrite? (y/n)[/bold yellow]",
            choices=["y", "n"], default="n"
        )
        if confirm.lower() != "y":
            console.print("[yellow]Export cancelled.[/yellow]")
            return

    # Export goals to CSV
    with open(goals_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Goal Name", "Target Amount", "Time Horizon", "CAGR (%)",
                         "Investment Mode", "Lumpsum (INR)", "SIP (INR)", "Start Date",
                         "Created At", "Notes", "Total Contributions"])
        writer.writerows(goals)

    console.print(f"[green]Goals exported successfully to {goals_filename}[/green]")

    # Export contributions to CSV
    with open(contributions_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Goal ID", "Goal Name", "Amount (INR)", "Date"])
        writer.writerows(contributions)

    console.print(f"[green]Contributions exported successfully to {contributions_filename}[/green]")

def plot_goal_progress(goal_id, goal_name, target_amount):
    """Generate a progress graph for a financial goal."""
    contributions = db.fetch_contributions_for_graph(goal_id)

    if not contributions:
        console.print("[yellow]No contributions recorded for this goal.[/yellow]")
        return

    try:
        # Convert data into lists for plotting
        dates = [datetime.strptime(entry[0], "%Y-%m-%d") for entry in contributions]
        amounts = [entry[1] for entry in contributions]

        # Generate cumulative sum for progress tracking
        cumulative_contributions = [sum(amounts[:i+1]) for i in range(len(amounts))]

        # Expected progress line (assuming uniform contributions)
        expected_dates = [dates[0], dates[-1]]
        expected_amounts = [0, target_amount]

        # Plot the graph
        plt.figure(figsize=(8, 5))
        plt.plot(dates, cumulative_contributions, marker='o', linestyle='-', color='blue', label="Actual Contributions")
        plt.plot(expected_dates, expected_amounts, linestyle="dashed", color="red", label="Expected Progress")
        
        plt.xlabel("Date")
        plt.ylabel("Amount (INR)")
        plt.title(f"Progress for {goal_name}")
        plt.legend()
        plt.grid(True)

        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show(block=False)
    except Exception as e:
        console.print(f"[red]Error generating graph: {str(e)}[/red]")
        console.print("[yellow]Continuing with text-based progress report...[/yellow]")

def view_progress_graph_menu():
    """Allow users to view a progress graph and milestone tracking."""
    display_goals()  # Show available goals

    goal_id = Prompt.ask("[bold]Enter the ID of the goal to view progress (or 0 to cancel):[/bold]").strip()
    if goal_id == "0":
        console.print("[yellow]Returning to main menu.[/yellow]")
        return

    if not goal_id.isdigit():
        console.print("[red]Invalid input. Please enter a valid goal ID.[/red]")
        return
    goal_id = int(goal_id)

    goal_data = db.fetch_goal_by_id(goal_id)
    if not goal_data:
        console.print("[red]Goal not found.[/red]")
        return

    goal_name, target_amount, time_horizon, cagr = goal_data[1], goal_data[2], goal_data[3], goal_data[4]

    # Show progress graph first
    plot_goal_progress(goal_id, goal_name, target_amount)

    # Then show milestone tracking
    console.print("\n[bold cyan]Milestone Progress:[/bold cyan]")
    calculate_milestones(goal_id, target_amount)

    # Show future value projection
    console.print("\n[bold cyan]Future Value Projection:[/bold cyan]")
    calculate_future_value(goal_id, target_amount, time_horizon, cagr)

    console.input("\nPress Enter to return to the main menu...")

def calculate_milestones(goal_id, target_amount):
    """Check milestone progress for a goal."""
    total_contributions = db.get_goal_total_contributions(goal_id)
    
    milestones = {
        "25%": target_amount * 0.25,
        "50%": target_amount * 0.50,
        "75%": target_amount * 0.75,
        "100% (Goal Achieved!)": target_amount
    }

    table = Table(title=f"Milestone Progress for Goal ID {goal_id}")
    table.add_column("Milestone", style="bold yellow")
    table.add_column("Target Amount (INR)", justify="right", style="cyan")
    table.add_column("Status", justify="center", style="bold green")

    for label, amount in milestones.items():
        status = "✔ Reached" if total_contributions >= amount else "❌ Pending"
        table.add_row(label, f"{amount:,.2f}", status)

    console.print(table)

def calculate_future_value(goal_id, target_amount, time_horizon, cagr):
    """Calculate future value of current contributions and determine shortfall/surplus."""
    total_contributions = db.get_goal_total_contributions(goal_id)
    goal_data = db.fetch_goal_by_id(goal_id)

    if not goal_data or len(goal_data) < 8:
        console.print("[red]Error: Goal data is incomplete or missing.[/red]")
        return

    sip_amount = goal_data[7]  # Monthly SIP amount
    cagr_decimal = cagr / 100
    n = 12  # Monthly compounding - moved outside the if block

    # Future Value of existing investments
    future_value_existing = total_contributions * ((1 + cagr_decimal) ** time_horizon)

    # Future Value of SIP contributions (corrected formula for monthly compounding)
    if cagr_decimal > 0:
        monthly_rate = cagr_decimal / n  # Convert annual CAGR to monthly
        months = time_horizon * n  # Total number of months
        fv_sip = sip_amount * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
    else:
        fv_sip = sip_amount * time_horizon * n  # If CAGR is 0, simple sum

    # Total Future Value
    total_future_value = future_value_existing + fv_sip
    shortfall = target_amount - total_future_value

    # Calculate required SIP increase if needed
    required_sip = 0
    if shortfall > 0:
        if cagr_decimal > 0:
            monthly_rate = cagr_decimal / n
            months = time_horizon * n
            required_sip = shortfall * monthly_rate / (((1 + monthly_rate) ** months - 1) * (1 + monthly_rate))
        else:
            # If CAGR is 0, simple division
            required_sip = shortfall / (time_horizon * n)

    # Display results
    table = Table(title=f"Future Value Projection for Goal ID {goal_id}")
    table.add_column("Metric", style="bold yellow")
    table.add_column("Value", justify="right", style="cyan")

    table.add_row("Current Contributions (INR)", f"{total_contributions:,.2f}")
    table.add_row("Ongoing SIP (INR)", f"{sip_amount:,.2f}")
    table.add_row("Expected Future Value (INR)", f"{total_future_value:,.2f}")
    table.add_row("Target Amount (INR)", f"{target_amount:,.2f}")
    table.add_row("Status", "[green]✔ On Track[/green]" if total_future_value >= target_amount else "[red]❌ Shortfall[/red]")

    if shortfall > 0:
        table.add_row("Shortfall Amount (INR)", f"{shortfall:,.2f}")
        table.add_row("Increase SIP to Stay on Track (INR)", f"{required_sip:,.2f}")

    console.print(table)

    # Guidance for the user
    console.print("\n[bold cyan]Based on expected returns:[/bold cyan]")
    if total_future_value >= target_amount:
        console.print("[green]✔ You are on track! Keep your current SIP to meet your goal.[/green]")
    else:
        console.print(f"[red]❌ Your current SIP of ₹{sip_amount:,.2f} is not enough.[/red]")
        console.print(f"[yellow]💡 Consider increasing it to ₹{required_sip:,.2f} to stay on track.[/yellow]")

def display_basics():
    """Display the status of financial basics in a table format."""
    basics = db.fetch_basics()
    
    if not basics:
        console.print("[yellow]No financial basics data found.[/yellow]")
        return

    table = Table(title="Financial Basics Status")
    table.add_column("Category", style="bold cyan")
    table.add_column("Target Amount", justify="right")
    table.add_column("Current Amount", justify="right")
    table.add_column("Progress", justify="left")
    table.add_column("Status", style="bold")
    table.add_column("Recommendation", style="italic")
    table.add_column("Last Updated", justify="right")

    for basic in basics:
        category, target, current, is_funded, recommendation, last_updated = basic
        
        # Calculate progress percentage
        progress_pct = (current / target * 100) if target > 0 else 0
        
        # Create progress bar
        progress_bar = create_progress_bar(progress_pct)
        
        # Format category name for display
        category_display = category.replace("_", " ").title()
        
        # Format amounts with commas and currency symbol
        target_display = f"₹{target:,.2f}"
        current_display = f"₹{current:,.2f}"
        
        # Determine status color and icon
        status = "[green]✓ Funded[/green]" if is_funded else f"[yellow]{progress_pct:.1f}% Complete[/yellow]"
        
        # Format date
        last_updated_display = datetime.fromisoformat(last_updated).strftime("%Y-%m-%d")

        table.add_row(
            category_display,
            target_display,
            current_display,
            progress_bar,
            status,
            recommendation,
            last_updated_display
        )

    console.print(table)

def create_progress_bar(percentage):
    """Create a visual progress bar."""
    width = 20
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    color = "green" if percentage >= 100 else "yellow" if percentage >= 50 else "red"
    return f"[{color}]{bar}[/{color}]"

def update_basic_menu(category):
    """Menu for updating a specific financial basic."""
    console.print(f"\n[bold cyan]Update {category}[/bold cyan]")
    
    # Convert category name to database format
    category_db = category.lower().replace(" ", "_")
    
    # Fetch current values
    conn = db.connect_db()  # Use db.connect_db() instead of connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT target_amount, current_amount 
        FROM financial_basics 
        WHERE category = ?
    """, (category_db,))
    result = cursor.fetchone()
    conn.close()
    
    current_target = result[0] if result else 0
    current_amount = result[1] if result else 0
    
    # Add input collection for recommendation calculation
    additional_info = {}
    if category == "Emergency Fund":
        monthly_expenses = get_numeric_input("Enter your monthly expenses (INR):")
        additional_info["monthly_expenses"] = monthly_expenses
        recommended = monthly_expenses * 6
    elif category == "Health Insurance":
        family_members = get_numeric_input("Enter number of family members:", input_type=int)
        additional_info["family_members"] = family_members
        recommended = max(500000, family_members * 200000)
    elif category == "Term Insurance":
        annual_income = get_numeric_input("Enter annual income (INR):")
        additional_info["annual_income"] = annual_income
        recommended = max(10000000, annual_income * 10)
    
    console.print(f"\n[bold green]Recommended amount: ₹{recommended:,.2f}[/bold green]")
    console.print(f"[bold yellow]Current target amount: ₹{current_target:,.2f}[/bold yellow]")
    
    # Ask if user wants to change target amount
    change_target = Prompt.ask(
        "[bold]Do you want to change the target amount?[/bold]",
        choices=["y", "n"],
        default="n"
    ).lower() == "y"
    
    if change_target:
        target_amount = get_numeric_input(f"Enter new target amount for {category} (INR):", default=recommended)
    else:
        target_amount = current_target
    
    console.print(f"[bold yellow]Current amount: ₹{current_amount:,.2f}[/bold yellow]")
    change_current = Prompt.ask(
        "[bold]Do you want to change the current amount?[/bold]",
        choices=["y", "n"],
        default="n"
    ).lower() == "y"
    
    if change_current:
        new_current_amount = get_numeric_input(f"Enter new current amount for {category} (INR):")
    else:
        new_current_amount = current_amount
    
    notes = Prompt.ask("[bold]Enter any notes (optional)[/bold]", default="")
    
    if db.update_basic(category, target_amount, new_current_amount, notes, additional_info):
        console.print(f"\n[green]Successfully updated {category}![/green]")
    else:
        console.print(f"\n[red]Failed to update {category}.[/red]")

def basics_menu():
    """Menu for managing financial basics."""
    while True:
        console.print("\n[bold cyan]=== Financial Basics ===[/bold cyan]\n")
        
        table = Table(show_header=False)
        table.add_column("Option", justify="center", style="bold yellow")
        table.add_column("Description", style="bold")
        
        table.add_row("1", "Update Emergency Fund")
        table.add_row("2", "Update Health Insurance")
        table.add_row("3", "Update Term Insurance")
        table.add_row("4", "View Basics Status")
        table.add_row("5", "Back to Main Menu")
        
        console.print(table)
        
        choice = Prompt.ask("[bold]Choose an option (1-5)[/bold]", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1":
            update_basic_menu("Emergency Fund")
        elif choice == "2":
            update_basic_menu("Health Insurance")
        elif choice == "3":
            update_basic_menu("Term Insurance")
        elif choice == "4":
            display_basics()
        elif choice == "5":
            break

def backup_menu():
    """Handle database backup and restore operations."""
    while True:
        console.print("\n[bold cyan]=== Backup & Restore ===[/bold cyan]\n")
        
        table = Table(show_header=False)
        table.add_column("Option", justify="center", style="bold yellow")
        table.add_column("Description", style="bold")
        
        table.add_row("1", "Create Backup")
        table.add_row("2", "Restore from Backup")
        table.add_row("3", "List Backups")
        table.add_row("4", "Back to Main Menu")
        
        console.print(table)
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"])
        
        if choice == "1":
            try:
                backup_dir = db.export_all_data()
                console.print(f"[green]Backup created successfully in: {backup_dir}[/green]")
            except Exception as e:
                console.print(f"[red]Error creating backup: {str(e)}[/red]")
        
        elif choice == "2":
            backups = db.list_backups()
            if not backups:
                console.print("[yellow]No backups found![/yellow]")
                continue
                
            table = Table(title="Available Backups")
            table.add_column("Index", style="cyan")
            table.add_column("Backup Date", style="green")
            
            for i, backup in enumerate(backups, 1):
                table.add_row(str(i), backup)
            
            console.print(table)
            
            backup_index = Prompt.ask(
                "Enter backup number to restore (0 to cancel)",
                choices=[str(i) for i in range(len(backups) + 1)]
            )
            
            if backup_index == "0":
                continue
                
            selected_backup = os.path.join("backups", backups[int(backup_index) - 1])
            
            if Prompt.ask(
                "[bold red]Warning: This will overwrite all current data. Continue?[/bold red]",
                choices=["y", "n"]
            ) == "y":
                try:
                    db.import_all_data(selected_backup)
                    console.print("[green]Data restored successfully![/green]")
                except Exception as e:
                    console.print(f"[red]Error restoring backup: {str(e)}[/red]")
        
        elif choice == "3":
            backups = db.list_backups()
            if not backups:
                console.print("[yellow]No backups found![/yellow]")
                continue
                
            table = Table(title="Available Backups")
            table.add_column("Backup Date", style="green")
            
            for backup in backups:
                table.add_row(backup)
            
            console.print(table)
        
        elif choice == "4":
            break

def main_menu():
    """Display CLI menu with Rich UI."""
    while True:
        console.print("\n[bold cyan]=== Financial Goals Tracker ===[/bold cyan]\n")

        table = Table(show_header=False)
        table.add_column("Option", justify="center", style="bold yellow", no_wrap=True)
        table.add_column("Description", style="bold")

        table.add_row("1", "The Basics")
        table.add_row("2", "Add Goal")
        table.add_row("3", "View Goals")
        table.add_row("4", "Goal Calculator")
        table.add_row("5", "Edit Goal")
        table.add_row("6", "Delete Goal")
        table.add_row("7", "Log Contribution")
        table.add_row("8", "View Contributions")
        table.add_row("9", "Export to CSV")
        table.add_row("10", "View Progress Graph")
        table.add_row("11", "Backup & Restore")
        table.add_row("12", "Exit")

        console.print(table)

        while True:
            choice = Prompt.ask("[bold]Choose an option (1-12)[/bold]")
            try:
                choice = int(choice)
                if choice in range(1, 13):
                    break
                console.print("[red]Invalid choice. Please select a valid option (1-12).[/red]")
            except ValueError:
                console.print("[red]Invalid input. Please enter a number (1-12).[/red]")

        if choice == 1:
            basics_menu()
        elif choice == 2:
            goal_data = get_user_input()
            db.insert_goal(goal_data)
            console.print("\n[green]Goal added successfully![/green]\n")
        elif choice == 3:
            display_goals()
        elif choice == 4:
            goal_calculator_menu()
        elif choice == 5:
            edit_goal_menu()
        elif choice == 6:
            delete_goal_menu()
        elif choice == 7:
            log_contribution_menu()
        elif choice == 8:
            view_contributions_menu()
        elif choice == 9:
            export_menu()
        elif choice == 10:
            view_progress_graph_menu()
        elif choice == 11:
            backup_menu()
        elif choice == 12:
            console.print("[bold red]Exiting program.[/bold red]")
            break

if __name__ == "__main__":
    db.initialize_db()  # Ensure DB is set up
    main_menu()

