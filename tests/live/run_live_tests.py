#!/usr/bin/env python3
"""
Main entry point for running live tests
Provides a simple interface to execute tests at different complexity levels
"""

import asyncio
import sys
import argparse
from pathlib import Path
from typing import List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.live.test_runner import LiveTestRunner, TestLevel
from tests.live.test_categories import get_test_count, estimate_total_runtime


def print_banner():
    """Print welcome banner"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║          🚀 MVP Incremental TDD - Live Test Suite 🚀          ║
║                                                               ║
║  Testing real workflow execution without mocks                ║
║  Progressive complexity: Simple → Complex → Edge Cases        ║
╚═══════════════════════════════════════════════════════════════╝
""")


def print_test_summary():
    """Print summary of available tests"""
    counts = get_test_count()
    runtime = estimate_total_runtime()
    
    print("📊 Available Tests by Level:")
    print("─" * 50)
    
    total = 0
    for level in TestLevel:
        count = counts.get(level, 0)
        total += count
        level_time = runtime["by_level"].get(level.value, 0)
        print(f"  {level.value.upper():<15} {count:>3} tests  (~{level_time/60:.1f} min)")
    
    print("─" * 50)
    print(f"  {'TOTAL':<15} {total:>3} tests  (~{runtime['total_minutes']:.1f} min)")
    print()


async def run_quick_test():
    """Run a single quick test to verify setup"""
    print("🧪 Running quick verification test...")
    
    runner = LiveTestRunner(verbose=True)
    
    # Run just the calculator test
    results = await runner.run_all_tests(levels=[TestLevel.SIMPLE])
    
    if results.summary["passed"] > 0:
        print("\n✅ Quick test passed! System is ready for live testing.")
    else:
        print("\n❌ Quick test failed. Please check your setup.")
        
    return results.summary["failed"] == 0


async def run_interactive_mode():
    """Interactive mode for selecting tests"""
    print_test_summary()
    
    print("Select test levels to run:")
    print("1. Simple tests only")
    print("2. Simple + Moderate tests")
    print("3. All main tests (Simple + Moderate + Complex)")
    print("4. Advanced tests only")
    print("5. Edge case tests only")
    print("6. All tests (Warning: This will take a while!)")
    print("7. Custom selection")
    print("Q. Quit")
    
    choice = input("\nEnter your choice (1-7 or Q): ").strip().lower()
    
    if choice == 'q':
        return None
        
    level_map = {
        '1': [TestLevel.SIMPLE],
        '2': [TestLevel.SIMPLE, TestLevel.MODERATE],
        '3': [TestLevel.SIMPLE, TestLevel.MODERATE, TestLevel.COMPLEX],
        '4': [TestLevel.ADVANCED],
        '5': [TestLevel.EDGE_CASES],
        '6': list(TestLevel),
    }
    
    if choice in level_map:
        return level_map[choice]
    elif choice == '7':
        # Custom selection
        print("\nAvailable levels:")
        for i, level in enumerate(TestLevel, 1):
            print(f"{i}. {level.value}")
            
        selections = input("\nEnter level numbers separated by spaces: ").strip().split()
        
        levels = []
        for sel in selections:
            try:
                idx = int(sel) - 1
                if 0 <= idx < len(TestLevel):
                    levels.append(list(TestLevel)[idx])
            except ValueError:
                pass
                
        return levels if levels else None
    else:
        print("Invalid choice.")
        return None


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run live tests for MVP Incremental TDD Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python run_live_tests.py --all
  
  # Run specific levels
  python run_live_tests.py --levels simple moderate
  
  # Run in parallel with custom output
  python run_live_tests.py --all --parallel --output-dir ./my_results
  
  # Interactive mode
  python run_live_tests.py
  
  # Quick verification
  python run_live_tests.py --quick
"""
    )
    
    parser.add_argument("--all", action="store_true", 
                       help="Run all tests")
    parser.add_argument("--levels", nargs="+", choices=[l.value for l in TestLevel],
                       help="Specific test levels to run")
    parser.add_argument("--parallel", action="store_true",
                       help="Run tests in parallel")
    parser.add_argument("--quiet", action="store_true",
                       help="Reduce output verbosity")
    parser.add_argument("--output-dir", type=str,
                       help="Custom output directory for results")
    parser.add_argument("--quick", action="store_true",
                       help="Run a quick verification test")
    parser.add_argument("--list", action="store_true",
                       help="List all available tests")
    
    args = parser.parse_args()
    
    print_banner()
    
    # Handle list option
    if args.list:
        print_test_summary()
        return 0
    
    # Handle quick test
    if args.quick:
        success = await run_quick_test()
        return 0 if success else 1
    
    # Determine which tests to run
    levels = None
    
    if args.all:
        levels = list(TestLevel)
        print("🎯 Running ALL tests...")
    elif args.levels:
        levels = [TestLevel(l) for l in args.levels]
        print(f"🎯 Running {len(levels)} test level(s): {', '.join(l.value for l in levels)}")
    else:
        # Interactive mode
        levels = await run_interactive_mode()
        if levels is None:
            print("👋 Goodbye!")
            return 0
            
    # Create runner
    output_dir = Path(args.output_dir) if args.output_dir else None
    runner = LiveTestRunner(
        output_dir=output_dir,
        parallel=args.parallel,
        verbose=not args.quiet
    )
    
    # Confirm before running many tests
    if len(levels) > 2:
        runtime = estimate_total_runtime()
        total_time = sum(runtime["by_level"].get(l.value, 0) for l in levels) / 60
        
        print(f"\n⚠️  This will run approximately {total_time:.1f} minutes of tests.")
        confirm = input("Continue? (y/N): ").strip().lower()
        
        if confirm != 'y':
            print("👋 Test run cancelled.")
            return 0
    
    # Run tests
    print("\n" + "="*60)
    results = await runner.run_all_tests(levels=levels)
    
    # Print final summary
    if results.summary["failed"] == 0:
        print("\n🎉 All tests passed successfully!")
        return 0
    else:
        print(f"\n⚠️  {results.summary['failed']} test(s) failed.")
        return 1


if __name__ == "__main__":
    try:
        # Check for required dependencies
        try:
            import docker
            docker.from_env().ping()
        except Exception as e:
            print("❌ Docker is not available. Please ensure Docker is installed and running.")
            print(f"   Error: {e}")
            sys.exit(1)
            
        # Run main
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\n👋 Test run interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)