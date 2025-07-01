import asyncio
import os
from datetime import datetime
from acp_sdk.client import Client
from acp_sdk import Message
from acp_sdk.models import MessagePart

def ensure_logs_dir():
    """Create logs directory if it doesn't exist"""
    if not os.path.exists("./logs"):
        os.makedirs("./logs")
        print("📁 Created ./logs directory")

def write_log(filename: str, content: str):
    """Write content to a log file"""
    ensure_logs_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"./logs/{timestamp}_{filename}"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        f.write(content)
    
    print(f"📝 Logged to: {log_file}")

async def test_coding_team():
    """Test the coding team system with different workflow specifications"""
    
    async with Client(base_url="http://localhost:8080") as client:
        
        # Test 1: Explicit TDD workflow
        print("🧪 Test 1: Explicit TDD Workflow")
        print("-" * 50)
        
        try:
            run = await client.run_sync(
                agent="orchestrator",
                input=[Message(parts=[MessagePart(
                    content="Use TDD workflow to build a simple todo list API with add, delete, and mark complete functionality",
                    content_type="text/plain"
                )])]
            )
            
            # Write full output to log file
            full_output = ""
            for message in run.output:
                for part in message.parts:
                    full_output += part.content + "\n\n"
            
            write_log("tdd_workflow_todo_api.log", full_output)
            print("✅ TDD Workflow completed - full output logged")
                    
        except Exception as e:
            print(f"❌ Error in TDD workflow: {e}")
            write_log("tdd_workflow_error.log", str(e))
        
        # Test 2: Explicit full workflow
        print("\n🔄 Test 2: Explicit Full Workflow")
        print("-" * 50)
        
        try:
            run = await client.run_sync(
                agent="orchestrator",
                input=[Message(parts=[MessagePart(
                    content="Use full workflow to create a user registration system",
                    content_type="text/plain"
                )])]
            )
            
            # Write full output to log file
            full_output = ""
            for message in run.output:
                for part in message.parts:
                    full_output += part.content + "\n\n"
            
            write_log("full_workflow_user_registration.log", full_output)
            print("✅ Full Workflow completed - full output logged")
                    
        except Exception as e:
            print(f"❌ Error in full workflow: {e}")
            write_log("full_workflow_error.log", str(e))
            
        # Test 3: Individual step - just planning
        print("\n📋 Test 3: Just Planning")
        print("-" * 50)
        
        try:
            run = await client.run_sync(
                agent="orchestrator",
                input=[Message(parts=[MessagePart(
                    content="Just do planning for a real-time chat application",
                    content_type="text/plain"
                )])]
            )
            
            # Write full output to log file
            full_output = ""
            for message in run.output:
                for part in message.parts:
                    full_output += part.content + "\n\n"
            
            write_log("planning_only_chat_app.log", full_output)
            print("✅ Planning completed - full output logged")
                    
        except Exception as e:
            print(f"❌ Error in planning: {e}")
            write_log("planning_error.log", str(e))
            
        # Test 4: Just test writing
        print("\n🧪 Test 4: Just Test Writing")
        print("-" * 50)
        
        try:
            run = await client.run_sync(
                agent="orchestrator",
                input=[Message(parts=[MessagePart(
                    content="Write tests for a user authentication system with login, logout, and password reset",
                    content_type="text/plain"
                )])]
            )
            
            # Write full output to log file
            full_output = ""
            for message in run.output:
                for part in message.parts:
                    full_output += part.content + "\n\n"
            
            write_log("test_writing_auth_system.log", full_output)
            print("✅ Test Writing completed - full output logged")
                    
        except Exception as e:
            print(f"❌ Error in test writing: {e}")
            write_log("test_writing_error.log", str(e))

        # Test 5: Default behavior (should default to TDD for new project)
        print("\n🎯 Test 5: Default Behavior")
        print("-" * 50)
        
        try:
            run = await client.run_sync(
                agent="orchestrator",
                input=[Message(parts=[MessagePart(
                    content="Build a simple blog API with posts and comments",
                    content_type="text/plain"
                )])]
            )
            
            # Write full output to log file
            full_output = ""
            for message in run.output:
                for part in message.parts:
                    full_output += part.content + "\n\n"
            
            write_log("default_behavior_blog_api.log", full_output)
            print("✅ Default Behavior completed - full output logged")
                    
        except Exception as e:
            print(f"❌ Error in default behavior: {e}")
            write_log("default_behavior_error.log", str(e))

        print(f"\n📁 All test outputs have been saved to ./logs/ directory")
        print(f"📊 Check the log files for complete agent responses")


def show_usage_examples():
    """Show examples of how to specify workflows"""
    print("🎯 WORKFLOW SPECIFICATION EXAMPLES")
    print("="*60)
    print()
    
    examples = [
        ("TDD Workflow", [
            "Use TDD workflow to build a REST API",
            "Apply test-driven development to create a login system",
            "TDD workflow for a shopping cart feature"
        ]),
        ("Full Workflow", [
            "Use full workflow to develop a web scraper",
            "Complete cycle for building a file upload system",
            "Full workflow but skip the review phase"
        ]),
        ("Individual Steps", [
            "Just do planning for a mobile app",
            "Only design the architecture for a microservice",
            "Write tests for the payment processing module",
            "Just implement the user profile feature",
            "Only review this existing code"
        ]),
        ("Default Behavior", [
            "Build a task management system",  # → TDD workflow
            "Review my authentication code",   # → review only
            "Design a database schema",        # → design only
            "Plan a social media platform"    # → planning only
        ])
    ]
    
    for category, example_list in examples:
        print(f"📌 {category}:")
        for example in example_list:
            print(f"   • \"{example}\"")
        print()
    
    print("💡 TIPS:")
    print("   • Be explicit about workflow choice for predictable results")
    print("   • Use 'skip X' or 'without X' to exclude team members")
    print("   • Default behavior tries to be smart about what you need")
    print("   • TDD workflow is recommended for new features")
    print("   • All full outputs are logged to ./logs/ directory")
    print()

def list_recent_logs():
    """List recent log files"""
    ensure_logs_dir()
    
    try:
        log_files = [f for f in os.listdir("./logs") if f.endswith('.log')]
        if not log_files:
            print("📁 No log files found in ./logs directory")
            return
        
        # Sort by modification time (newest first)
        log_files.sort(key=lambda x: os.path.getmtime(f"./logs/{x}"), reverse=True)
        
        print(f"📊 Recent log files in ./logs/:")
        print("-" * 40)
        for i, log_file in enumerate(log_files[:10]):  # Show last 10
            file_path = f"./logs/{log_file}"
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            file_size = os.path.getsize(file_path)
            print(f"{i+1:2d}. {log_file}")
            print(f"    📅 {mod_time.strftime('%Y-%m-%d %H:%M:%S')} | 📏 {file_size:,} bytes")
        
        if len(log_files) > 10:
            print(f"    ... and {len(log_files) - 10} more files")
            
    except Exception as e:
        print(f"❌ Error reading logs directory: {e}")

# Simple synchronous test function
def simple_test():
    """Simple test that you can run easily"""
    print("🚀 Starting Coding Team Tests...")
    print("Make sure the server is running on port 8080 first!")
    print()
    
    # Show usage examples first
    show_usage_examples()
    
    # Ask user what they want to test
    print("Choose an option:")
    print("1. Run all test scenarios (outputs logged to ./logs/)")
    print("2. Show workflow examples only")
    print("3. List recent log files")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        ensure_logs_dir()
        print(f"📁 All test outputs will be saved to ./logs/ directory")
        print("🔄 Starting tests...")
        try:
            asyncio.run(test_coding_team())
        except KeyboardInterrupt:
            print("\n👋 Tests interrupted by user")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            write_log("test_runner_error.log", str(e))
            print("Make sure:")
            print("1. The server is running (python coding_team.py)")
            print("2. Your .env file has OPENAI_API_KEY set")
            print("3. All dependencies are installed")
    elif choice == "2":
        print("✅ Examples shown above!")
    elif choice == "3":
        list_recent_logs()
    elif choice == "4":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    simple_test()