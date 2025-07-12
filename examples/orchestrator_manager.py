#!/usr/bin/env python3
"""
Orchestrator management utilities for demo scripts.
Handles starting, stopping, and health checks for the orchestrator.
"""

import subprocess
import time
import psutil
import requests
import os
import sys
import signal
from typing import Optional, Tuple

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def find_process_on_port(port: int) -> Optional[int]:
    """Find process ID using a specific port."""
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port and conn.status == 'LISTEN':
                return conn.pid
    except (psutil.AccessDenied, PermissionError):
        # On macOS, we might not have permission to see all connections
        # Try using lsof instead
        return find_process_on_port_lsof(port)
    return None


def find_process_on_port_lsof(port: int) -> Optional[int]:
    """Find process ID using lsof command (fallback for macOS)."""
    try:
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            # lsof might return multiple PIDs, get the first one
            pids = result.stdout.strip().split('\n')
            return int(pids[0])
    except (subprocess.SubprocessError, ValueError):
        pass
    return None


def kill_process_on_port(port: int) -> bool:
    """Kill any process using the specified port."""
    pid = find_process_on_port(port)
    if pid:
        try:
            process = psutil.Process(pid)
            print(f"🔪 Killing existing process (PID: {pid}) on port {port}")
            process.terminate()
            
            # Wait for graceful termination
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                # Force kill if needed
                print(f"⚠️  Process didn't terminate gracefully, forcing kill...")
                process.kill()
                process.wait(timeout=5)
            
            print(f"✅ Successfully killed process on port {port}")
            return True
        except psutil.NoSuchProcess:
            # Process already gone
            return True
        except (psutil.AccessDenied, PermissionError) as e:
            # Try using kill command directly
            print(f"🔄 Using system kill command due to permission error...")
            try:
                subprocess.run(['kill', '-TERM', str(pid)], check=True)
                time.sleep(2)
                # Check if still running
                if subprocess.run(['kill', '-0', str(pid)], capture_output=True).returncode == 0:
                    subprocess.run(['kill', '-KILL', str(pid)], check=True)
                print(f"✅ Successfully killed process on port {port}")
                return True
            except subprocess.CalledProcessError:
                print(f"⚠️  Could not kill process: {e}")
                return False
    return True  # No process to kill


def is_orchestrator_healthy(url: str = "http://localhost:8000/health", timeout: int = 2) -> bool:
    """Check if the orchestrator is running and healthy."""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except:
        return False


def start_orchestrator() -> Optional[subprocess.Popen]:
    """Start the orchestrator in a subprocess."""
    orchestrator_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "orchestrator",
        "orchestrator_agent.py"
    )
    
    if not os.path.exists(orchestrator_path):
        print(f"❌ Orchestrator not found at: {orchestrator_path}")
        return None
    
    try:
        print(f"🚀 Starting orchestrator from: {orchestrator_path}")
        
        # Start orchestrator with proper Python path
        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        process = subprocess.Popen(
            [sys.executable, orchestrator_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            preexec_fn=os.setsid if sys.platform != 'win32' else None
        )
        
        # Wait a bit for startup
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"❌ Orchestrator failed to start!")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return None
        
        print(f"✅ Orchestrator started (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ Error starting orchestrator: {e}")
        return None


def ensure_orchestrator_running(port: int = 8000, max_attempts: int = 3) -> Tuple[bool, Optional[subprocess.Popen]]:
    """
    Ensure the orchestrator is running, starting it if necessary.
    
    Returns:
        Tuple of (success, process) where process is the subprocess if we started it
    """
    orchestrator_url = f"http://localhost:{port}/health"
    
    # Check if already running and healthy
    if is_orchestrator_healthy(orchestrator_url):
        print("✅ Orchestrator is already running and healthy")
        return True, None
    
    # Only try to kill if we're sure something is on the port
    print(f"🔍 Checking for processes on port {port}...")
    try:
        # Quick check if port is in use
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:  # Port is in use
            print(f"📍 Port {port} is in use, attempting to free it...")
            kill_process_on_port(port)
    except Exception as e:
        print(f"⚠️  Could not check port status: {e}")
    
    # Give system time to release the port
    time.sleep(2)
    
    # Try to start orchestrator
    for attempt in range(max_attempts):
        print(f"\n📡 Starting orchestrator (attempt {attempt + 1}/{max_attempts})...")
        
        process = start_orchestrator()
        if not process:
            continue
        
        # Wait for orchestrator to be ready
        print("⏳ Waiting for orchestrator to be ready...")
        for i in range(30):  # Wait up to 30 seconds
            if is_orchestrator_healthy(orchestrator_url):
                print("✅ Orchestrator is ready!")
                return True, process
            
            # Check if process crashed
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print(f"❌ Orchestrator process crashed!")
                print(f"Exit code: {process.returncode}")
                if stdout:
                    print(f"STDOUT: {stdout.decode()}")
                if stderr:
                    print(f"STDERR: {stderr.decode()}")
                break
            
            time.sleep(1)
            if i % 5 == 4:  # Print progress every 5 seconds
                print(f"   Still waiting... ({i+1}/30)")
        
        # If we get here, orchestrator didn't start properly
        if process.poll() is None:
            print("⚠️  Orchestrator didn't respond in time, terminating...")
            try:
                if sys.platform != 'win32':
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
    
    print("❌ Failed to start orchestrator after all attempts")
    return False, None


def cleanup_orchestrator(process: Optional[subprocess.Popen]):
    """Clean up the orchestrator process if we started it."""
    if process and process.poll() is None:
        print("\n🧹 Cleaning up orchestrator...")
        try:
            if sys.platform != 'win32':
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            else:
                process.terminate()
            process.wait(timeout=5)
            print("✅ Orchestrator stopped")
        except Exception as e:
            print(f"⚠️  Error stopping orchestrator: {e}")
            try:
                process.kill()
            except:
                pass


class OrchestratorManager:
    """Context manager for orchestrator lifecycle."""
    
    def __init__(self, port: int = 8000):
        self.port = port
        self.process = None
        self.started_by_us = False
    
    def __enter__(self):
        """Start orchestrator if needed."""
        success, self.process = ensure_orchestrator_running(self.port)
        self.started_by_us = self.process is not None
        
        if not success:
            raise RuntimeError("Failed to ensure orchestrator is running")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up orchestrator if we started it."""
        if self.started_by_us and self.process:
            cleanup_orchestrator(self.process)


# Simple test
if __name__ == "__main__":
    print("🧪 Testing orchestrator manager...")
    
    with OrchestratorManager() as manager:
        print("\n📍 Inside context manager - orchestrator should be running")
        print(f"   Health check: {is_orchestrator_healthy()}")
        
        # Simulate some work
        time.sleep(2)
    
    print("\n📍 Outside context manager")
    print("   If we started it, orchestrator should be stopped now")