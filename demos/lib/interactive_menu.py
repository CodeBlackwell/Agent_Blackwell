"""
Interactive menu system for the unified runner.
"""
import sys
from typing import List, Tuple, Optional


class InteractiveMenu:
    """Provides interactive menu functionality."""
    
    def __init__(self):
        self.width = 80
        
    def print_banner(self, title: str, subtitle: str = ""):
        """Print a formatted banner."""
        print("=" * self.width)
        print(title.center(self.width))
        if subtitle:
            print(subtitle.center(self.width))
        print("=" * self.width)
        print()
        
    def print_section(self, title: str):
        """Print a section header."""
        print(f"\n{title}")
        print("-" * len(title))
        
    def show_menu(self, title: str, options: List[Tuple[str, str]]) -> str:
        """Show a menu and get user choice."""
        self.print_section(title)
        
        for key, description in options:
            print(f"  {key}. {description}")
            
        print("\n  0. Exit")
        
        while True:
            choice = input("\nEnter your choice: ").strip()
            if choice in [opt[0] for opt in options] + ["0"]:
                return choice
            print("Invalid choice. Please try again.")
            
    def get_text_input(self, prompt: str, required: bool = True) -> Optional[str]:
        """Get text input from user."""
        while True:
            value = input(f"\n{prompt}: ").strip()
            if value or not required:
                return value
            print("This field is required. Please enter a value.")
            
    def get_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Get yes/no input from user."""
        default_str = "Y/n" if default else "y/N"
        while True:
            value = input(f"\n{prompt} [{default_str}]: ").strip().lower()
            if not value:
                return default
            if value in ['y', 'yes']:
                return True
            if value in ['n', 'no']:
                return False
            print("Please enter 'y' or 'n'.")
            
    def show_error(self, message: str, suggestions: List[str] = None):
        """Show an error message."""
        print(f"\n❌ ERROR: {message}")
        if suggestions:
            print("\n💡 Suggestions:")
            for suggestion in suggestions:
                print(f"   - {suggestion}")
                
    def show_success(self, message: str):
        """Show a success message."""
        print(f"\n✅ SUCCESS: {message}")
        
    def wait_for_enter(self):
        """Wait for user to press Enter."""
        input("\nPress Enter to continue...")
        
    def clear_screen(self):
        """Clear the terminal screen."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')