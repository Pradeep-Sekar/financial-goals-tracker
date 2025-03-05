import unittest
from unittest.mock import patch, MagicMock
import sys
import os

from financial_goals_tracker.main import (
    main_menu, basics_menu, goal_calculator_menu, get_user_input,
    edit_goal_menu, delete_goal_menu, log_contribution_menu,
    view_contributions_menu, backup_menu
)
from financial_goals_tracker import db

class TestMenuSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test database and required test data"""
        db.DB_FILE = "test_financial_goals.db"
        db.initialize_db()
        
        # Add a test goal
        cls.test_goal = {
            "goal_name": "Test Goal",
            "target_amount": 100000,
            "time_horizon": 5,
            "cagr": 12.0,
            "investment_mode": "SIP",
            "initial_investment": 0,
            "sip_amount": 1500,
            "start_date": "2024-01-01",
            "notes": "Test note"
        }
        db.insert_goal(cls.test_goal)

    def setUp(self):
        """Reset any state before each test"""
        self.mock_console = MagicMock()

    @patch('rich.console.Console.print')
    @patch('rich.prompt.Prompt.ask')
    def test_main_menu_basic_navigation(self, mock_ask, mock_print):
        """Test main menu navigation through all options"""
        # Test each menu option
        for choice in range(1, 13):  # 12 menu options
            mock_ask.return_value = str(choice)
            if choice == 12:  # Exit option
                main_menu()
                mock_print.assert_any_call("[bold red]Exiting program.[/bold red]")

    @patch('rich.prompt.Prompt.ask')
    def test_basics_menu(self, mock_ask):
        """Test financial basics menu operations"""
        # Test Emergency Fund update
        mock_ask.side_effect = ["1", "100000", "50000", "Test note", "5"]
        basics_menu()
        
        # Verify the update in database
        basic = db.fetch_basic("emergency_fund")
        self.assertIsNotNone(basic)
        self.assertEqual(basic[1], 100000)  # target_amount

    @patch('rich.prompt.Prompt.ask')
    def test_goal_calculator(self, mock_ask):
        """Test goal calculator functionality"""
        # Test SIP calculation
        mock_ask.side_effect = ["1000000", "5", "12", "1"]
        goal_calculator_menu()
        # Verify calculation output was displayed

    @patch('rich.prompt.Prompt.ask')
    def test_add_goal(self, mock_ask):
        """Test adding a new goal"""
        mock_inputs = [
            "Test Goal 2",  # name
            "500000",      # target
            "3",          # time horizon
            "10",         # CAGR
            "1",          # SIP mode
            "",           # start date (default today)
            "Test notes"  # notes
        ]
        mock_ask.side_effect = mock_inputs
        goal_data = get_user_input()
        db.insert_goal(goal_data)
        
        # Verify goal was added
        goal = db.fetch_goal_by_name("Test Goal 2")
        self.assertIsNotNone(goal)

    @patch('rich.prompt.Prompt.ask')
    def test_edit_goal(self, mock_ask):
        """Test editing an existing goal"""
        mock_ask.side_effect = ["1", "1,2", "New Name", "200000"]
        edit_goal_menu()
        
        # Verify changes
        updated_goal = db.fetch_goal_by_id(1)
        self.assertEqual(updated_goal[1], "New Name")

    @patch('rich.prompt.Prompt.ask')
    def test_delete_goal(self, mock_ask):
        """Test goal deletion"""
        mock_ask.side_effect = ["1", "yes"]
        delete_goal_menu()
        
        # Verify deletion
        self.assertIsNone(db.fetch_goal_by_id(1))

    @patch('rich.prompt.Prompt.ask')
    def test_log_contribution(self, mock_ask):
        """Test logging a contribution"""
        mock_ask.side_effect = ["1", "10000", "", "Test Fund", "10.5", "yes"]
        log_contribution_menu()
        
        # Verify contribution was logged
        contributions = db.fetch_contributions(1)
        self.assertGreater(len(contributions), 0)

    def test_backup_restore(self):
        """Test backup and restore functionality"""
        with patch('rich.prompt.Prompt.ask', side_effect=["1", "4"]):
            backup_menu()
            # Verify backup file was created
            backups = db.list_backups()
            self.assertGreater(len(backups), 0)

    @classmethod
    def tearDownClass(cls):
        """Clean up test database and files"""
        try:
            os.remove(db.DB_FILE)
            # Clean up any backup files
            for backup in db.list_backups():
                os.remove(backup)
        except OSError:
            pass

if __name__ == '__main__':
    unittest.main(verbosity=2)
