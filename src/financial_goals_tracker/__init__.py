"""Financial Goals Tracker package."""

# Import all submodules
from . import db
from . import goals_calculator
from . import investment_recommendation

# Import main last to avoid circular imports
from . import main

__version__ = "0.1.0"
__all__ = ['db', 'goals_calculator', 'investment_recommendation', 'main']
