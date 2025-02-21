import math

def calculate_lumpsum(target_amount, time_horizon, cagr):
    """Calculate the required lumpsum investment today to reach the target amount."""
    rate = cagr / 100  # Convert CAGR to decimal
    lumpsum = target_amount / ((1 + rate) ** time_horizon)
    return round(lumpsum, 2)

def calculate_sip(target_amount, time_horizon, cagr):
    """Calculate the required monthly SIP to reach the target amount."""
    rate = cagr / 100  # Convert CAGR to decimal
    n = 12  # Monthly SIPs
    months = time_horizon * 12
    monthly_rate = rate / n

    if monthly_rate == 0:
        return round(target_amount / months, 2)  # Avoid division by zero

    sip = target_amount * (monthly_rate / ((1 + monthly_rate) ** months - 1))
    return round(sip, 2)

def calculate_mixed(target_amount, time_horizon, cagr, lumpsum_percentage=None, lumpsum_amount=None):
    """Calculate a mix of Lumpsum + SIP based on either a percentage or fixed amount."""
    
    print(f"\nDEBUG: target_amount={target_amount}, time_horizon={time_horizon}, cagr={cagr}, "
          f"lumpsum_percentage={lumpsum_percentage}, lumpsum_amount={lumpsum_amount}\n")  # Debug print
    
    if lumpsum_amount is not None:  # User entered a fixed lumpsum
        initial_lumpsum = lumpsum_amount
    elif lumpsum_percentage is not None:  # User entered a percentage
        initial_lumpsum = target_amount * (lumpsum_percentage / 100)
    else:
        raise ValueError("Either lumpsum_percentage or lumpsum_amount must be provided.")

    # Ensure the lumpsum does not exceed the target
    initial_lumpsum = min(initial_lumpsum, target_amount)
    remaining_target = target_amount - initial_lumpsum

    print(f"\nDEBUG: initial_lumpsum={initial_lumpsum}, remaining_target={remaining_target}\n")  # Debug print

    # Calculate investments
    lumpsum_investment = calculate_lumpsum(initial_lumpsum, time_horizon, cagr)
    sip_investment = calculate_sip(remaining_target, time_horizon, cagr)

    print(f"\nDEBUG: lumpsum_investment={lumpsum_investment}, sip_investment={sip_investment}\n")  # Debug print

    return round(lumpsum_investment, 2), round(sip_investment, 2)