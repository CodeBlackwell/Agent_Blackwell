#!/usr/bin/env python3
"""
Migration Script: Enable MCP File System Integration

This script demonstrates how to migrate existing workflows to use the MCP
filesystem server for secure and auditable file operations.
"""

import sys
import os
from pathlib import Path
import argparse
import asyncio

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from workflows.tdd.file_manager import TDDFileManager
from workflows.tdd.file_manager_mcp import TDDFileManagerMCP, create_tdd_file_manager
from workflows.mvp_incremental.code_saver import CodeSaver
from workflows.mvp_incremental.code_saver_mcp import CodeSaverMCP, create_code_saver
from config.mcp_config import MCP_FILESYSTEM_CONFIG


def print_banner():
    """Print migration script banner."""
    print("=" * 60)
    print("MCP File System Migration Script")
    print("=" * 60)
    print()


def check_environment():
    """Check current environment configuration."""
    print("🔍 Checking environment configuration...")
    print()
    
    # Check if MCP is enabled via environment
    mcp_enabled = os.getenv("USE_MCP_FILESYSTEM", "false").lower() == "true"
    print(f"USE_MCP_FILESYSTEM: {'✅ Enabled' if mcp_enabled else '❌ Disabled'}")
    
    # Check sandbox configuration
    sandbox_root = MCP_FILESYSTEM_CONFIG.get("sandbox_root", "./generated")
    print(f"Sandbox Root: {sandbox_root}")
    
    # Check if sandbox exists
    sandbox_path = Path(sandbox_root)
    if sandbox_path.exists():
        print(f"Sandbox Status: ✅ Exists")
    else:
        print(f"Sandbox Status: ⚠️  Does not exist (will be created)")
    
    print()
    return mcp_enabled


async def test_file_operations():
    """Test basic file operations with both implementations."""
    print("🧪 Testing file operations...")
    print()
    
    # Test content
    test_code = """
def hello_world():
    return "Hello from MCP!"

if __name__ == "__main__":
    print(hello_world())
"""
    
    # Test with legacy implementation
    print("📁 Testing Legacy File Manager (Direct I/O)...")
    legacy_fm = TDDFileManager()
    
    # Simulate coder output
    coder_output = f"""
PROJECT CREATED: test_legacy_20240101_120000

FILENAME: main.py
```python
{test_code}
```

Location: ./generated/test_legacy_20240101_120000
"""
    
    files = legacy_fm.parse_files(coder_output)
    print(f"  - Parsed {len(files)} files")
    
    # Test with MCP implementation
    print("\n📁 Testing MCP File Manager...")
    
    # Use async context manager
    async with TDDFileManagerMCP(use_mcp=True, agent_name="migration_test") as mcp_fm:
        # Simulate coder output
        coder_output_mcp = coder_output.replace("test_legacy", "test_mcp")
        
        files_mcp = mcp_fm.parse_files(coder_output_mcp)
        print(f"  - Parsed {len(files_mcp)} files")
        
        # Update files
        success = mcp_fm.update_files_in_project(files_mcp)
        print(f"  - File update: {'✅ Success' if success else '❌ Failed'}")
        
        # List files
        file_list = mcp_fm.list_project_files()
        print(f"  - Files in project: {file_list}")
    
    print()


async def test_code_saver():
    """Test code saving with both implementations."""
    print("💾 Testing Code Saver...")
    print()
    
    # Test with legacy implementation
    print("📁 Testing Legacy Code Saver (Direct I/O)...")
    legacy_cs = CodeSaver()
    session_path = legacy_cs.create_session_directory("migration_test_legacy")
    print(f"  - Created session: {session_path}")
    
    # Save some files
    code_dict = {
        "app.py": "print('Legacy implementation')",
        "config.py": "DEBUG = True"
    }
    
    saved_paths = legacy_cs.save_code_files(code_dict)
    print(f"  - Saved {len(saved_paths)} files")
    
    # Test with MCP implementation
    print("\n📁 Testing MCP Code Saver...")
    
    async with CodeSaverMCP(use_mcp=True, agent_name="migration_test") as mcp_cs:
        session_path_mcp = mcp_cs.create_session_directory("migration_test_mcp")
        print(f"  - Created session: {session_path_mcp}")
        
        # Save files via MCP
        code_dict_mcp = {
            "app.py": "print('MCP implementation')",
            "config.py": "DEBUG = False",
            "README.md": "# MCP Test Project"
        }
        
        saved_paths_mcp = mcp_cs.save_code_files(code_dict_mcp)
        print(f"  - Saved {len(saved_paths_mcp)} files via MCP")
        
        # Get summary
        summary = mcp_cs.get_summary()
        print(f"  - Total size: {summary['total_size_kb']} KB")
        
        # Get metrics
        metrics = await mcp_cs.get_metrics()
        if metrics:
            print(f"  - MCP Metrics: {list(metrics.keys())}")
    
    print()


def show_migration_steps():
    """Show step-by-step migration guide."""
    print("📋 Migration Steps:")
    print()
    print("1. Update environment variables:")
    print("   export USE_MCP_FILESYSTEM=true")
    print()
    print("2. Update your workflow code:")
    print("   # Replace direct instantiation")
    print("   # Before: file_manager = TDDFileManager()")
    print("   # After:  file_manager = create_tdd_file_manager(use_mcp=True)")
    print()
    print("3. Handle async operations if needed:")
    print("   # For async workflows, use context manager")
    print("   async with TDDFileManagerMCP(use_mcp=True) as fm:")
    print("       # Your file operations here")
    print()
    print("4. Update agent configurations in config/mcp_config.py")
    print("   - Set appropriate permissions for each agent")
    print("   - Configure sandbox paths")
    print()
    print("5. Monitor audit logs:")
    print("   tail -f logs/mcp_filesystem_audit.log")
    print()


def enable_mcp_globally():
    """Enable MCP filesystem globally."""
    print("🔧 Enabling MCP File System...")
    print()
    
    # Create .env.mcp file with MCP enabled
    env_content = """# MCP File System Configuration
USE_MCP_FILESYSTEM=true

# Optional: Custom sandbox location
# MCP_FILESYSTEM_SANDBOX=/path/to/custom/sandbox

# Optional: Custom audit log location  
# MCP_FILESYSTEM_AUDIT_LOG=/path/to/audit.log
"""
    
    env_file = project_root / ".env.mcp"
    env_file.write_text(env_content)
    print(f"✅ Created {env_file}")
    print()
    print("To activate:")
    print("  cp .env.mcp .env  # Or merge with existing .env")
    print()


async def main():
    """Main migration script."""
    parser = argparse.ArgumentParser(description="Migrate to MCP File System")
    parser.add_argument("--test", action="store_true", help="Run tests")
    parser.add_argument("--enable", action="store_true", help="Enable MCP globally")
    parser.add_argument("--check", action="store_true", help="Check current configuration")
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.check or not any([args.test, args.enable]):
        # Default action: check configuration
        mcp_enabled = check_environment()
        if not mcp_enabled:
            print("💡 Tip: Use --enable to enable MCP filesystem")
            print()
        show_migration_steps()
    
    if args.test:
        await test_file_operations()
        await test_code_saver()
        print("✅ All tests completed!")
        print()
    
    if args.enable:
        enable_mcp_globally()
        print("✅ MCP File System enabled!")
        print("   Don't forget to update your .env file")
        print()
    
    print("🎉 Migration script completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())