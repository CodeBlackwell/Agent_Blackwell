"""
Interactive menu components for the demo system.
Provides user-friendly menus and prompts for interactive mode.
"""

import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class InteractiveMenu:
    """Provides interactive menu functionality."""
    
    def __init__(self, enable_colors: bool = True):
        """Initialize the interactive menu.
        
        Args:
            enable_colors: Whether to use ANSI colors in output
        """
        self.enable_colors = enable_colors
        
    def _color(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if self.enable_colors:
            return f"{color}{text}{Colors.END}"
        return text
        
    def print_banner(self, title: str, subtitle: Optional[str] = None):
        """Print a banner with title and optional subtitle."""
        width = 70
        print("\n" + "=" * width)
        print(self._color(title.center(width), Colors.BOLD + Colors.CYAN))
        if subtitle:
            print(subtitle.center(width))
        print("=" * width + "\n")
        
    def print_section(self, title: str):
        """Print a section header."""
        print(f"\n{self._color(title, Colors.BOLD + Colors.BLUE)}")
        print("-" * len(title))
        
    def show_menu(self, title: str, options: List[Tuple[str, str]], 
                  allow_back: bool = True) -> str:
        """Show a menu and get user choice.
        
        Args:
            title: Menu title
            options: List of (key, description) tuples
            allow_back: Whether to show a back option
            
        Returns:
            Selected option key
        """
        self.print_section(title)
        
        # Display options
        for key, desc in options:
            print(f"  {self._color(key, Colors.YELLOW)}. {desc}")
            
        if allow_back:
            print(f"  {self._color('0', Colors.YELLOW)}. Back/Exit")
            
        # Get user choice
        while True:
            choice = input(f"\n{self._color('Enter your choice:', Colors.GREEN)} ").strip()
            
            # Check if valid
            valid_keys = [opt[0] for opt in options]
            if allow_back:
                valid_keys.append('0')
                
            if choice in valid_keys:
                return choice
            else:
                print(self._color("Invalid choice. Please try again.", Colors.RED))
                
    def get_text_input(self, prompt: str, default: Optional[str] = None,
                      required: bool = True) -> str:
        """Get text input from user.
        
        Args:
            prompt: Input prompt
            default: Default value if user presses Enter
            required: Whether input is required
            
        Returns:
            User input string
        """
        if default:
            prompt_text = f"{prompt} [{default}]: "
        else:
            prompt_text = f"{prompt}: "
            
        while True:
            value = input(self._color(prompt_text, Colors.GREEN)).strip()
            
            if not value and default:
                return default
                
            if not value and required:
                print(self._color("This field is required.", Colors.RED))
                continue
                
            return value
            
    def get_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Get yes/no input from user.
        
        Args:
            prompt: Question to ask
            default: Default value if user presses Enter
            
        Returns:
            True for yes, False for no
        """
        default_str = "Y/n" if default else "y/N"
        
        while True:
            value = input(f"{self._color(prompt, Colors.GREEN)} ({default_str}): ").strip().lower()
            
            if not value:
                return default
                
            if value in ['y', 'yes']:
                return True
            elif value in ['n', 'no']:
                return False
            else:
                print(self._color("Please enter 'y' or 'n'.", Colors.RED))
                
    def get_multiline_input(self, prompt: str, end_marker: str = "END") -> str:
        """Get multiline input from user.
        
        Args:
            prompt: Initial prompt
            end_marker: String that marks end of input
            
        Returns:
            Multiline string
        """
        print(self._color(prompt, Colors.GREEN))
        print(f"(Type '{end_marker}' on a new line when finished)")
        print("-" * 40)
        
        lines = []
        while True:
            line = input()
            if line.strip().upper() == end_marker:
                break
            lines.append(line)
            
        return '\n'.join(lines)
        
    def show_options_list(self, title: str, options: List[Dict[str, str]],
                         fields: List[str] = ['name', 'description']):
        """Show a formatted list of options.
        
        Args:
            title: List title
            options: List of option dictionaries
            fields: Fields to display from each option
        """
        self.print_section(title)
        
        if not options:
            print("  (No options available)")
            return
            
        for i, option in enumerate(options, 1):
            print(f"\n  {self._color(str(i), Colors.YELLOW)}. ", end='')
            
            for j, field in enumerate(fields):
                value = option.get(field, '')
                if j == 0:  # First field in bold
                    print(self._color(value, Colors.BOLD), end='')
                else:
                    print(f" - {value}", end='')
            print()
            
    def show_progress(self, message: str, current: int, total: int):
        """Show a progress indicator.
        
        Args:
            message: Progress message
            current: Current item number
            total: Total number of items
        """
        percentage = (current / total) * 100 if total > 0 else 0
        bar_length = 30
        filled = int(bar_length * current / total) if total > 0 else 0
        
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\r{message}: [{bar}] {percentage:.1f}% ({current}/{total})", end='', flush=True)
        
        if current >= total:
            print()  # New line when complete
            
    def show_status(self, message: str, status: str = "info"):
        """Show a status message with appropriate styling.
        
        Args:
            message: Status message
            status: One of 'info', 'success', 'warning', 'error'
        """
        icons = {
            'info': ('ℹ️ ', Colors.BLUE),
            'success': ('✅', Colors.GREEN),
            'warning': ('⚠️ ', Colors.YELLOW),
            'error': ('❌', Colors.RED)
        }
        
        icon, color = icons.get(status, ('  ', Colors.END))
        print(f"{icon} {self._color(message, color)}")
        
    def confirm_action(self, action: str, details: Optional[List[str]] = None) -> bool:
        """Confirm an action with the user.
        
        Args:
            action: Description of the action
            details: Optional list of details to show
            
        Returns:
            True if confirmed, False otherwise
        """
        print(f"\n{self._color('Confirm Action', Colors.BOLD + Colors.YELLOW)}")
        print(f"Action: {action}")
        
        if details:
            print("\nDetails:")
            for detail in details:
                print(f"  • {detail}")
                
        return self.get_yes_no("\nProceed with this action?", default=True)
        
    def show_error(self, error: str, suggestions: Optional[List[str]] = None):
        """Show an error message with optional suggestions.
        
        Args:
            error: Error message
            suggestions: Optional list of suggestions
        """
        print(f"\n{self._color('ERROR', Colors.BOLD + Colors.RED)}: {error}")
        
        if suggestions:
            print("\nSuggestions:")
            for suggestion in suggestions:
                print(f"  • {suggestion}")
                
    def wait_for_enter(self, message: str = "Press Enter to continue..."):
        """Wait for user to press Enter."""
        input(f"\n{self._color(message, Colors.CYAN)}")


# Convenience instance for quick use
menu = InteractiveMenu()