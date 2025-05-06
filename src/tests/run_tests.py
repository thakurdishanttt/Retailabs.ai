import subprocess
import sys
import time
import os
import signal
import logging
from pathlib import Path

# Add the parent directory to sys.path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_runner")

def start_api_server():
    """Start the API server as a subprocess"""
    logger.info("Starting API server...")
    
    # Use Python executable to run the main.py file
    server_process = subprocess.Popen(
        [sys.executable, "-m", "src.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    logger.info("Waiting for server to start...")
    time.sleep(3)  # Give the server some time to start
    
    return server_process

def run_tests():
    """Run the API tests"""
    logger.info("Running API tests...")
    
    # Run the test script
    test_process = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "test_api.py")],
        capture_output=True,
        text=True
    )
    
    # Print test output
    if test_process.stdout:
        print(test_process.stdout)
    
    if test_process.stderr:
        print(test_process.stderr)
    
    return test_process.returncode == 0

def main():
    """Main function to run tests with API server"""
    server_process = None
    
    try:
        # Start API server
        server_process = start_api_server()
        
        # Run tests
        success = run_tests()
        
        # Return appropriate exit code
        return 0 if success else 1
    
    finally:
        # Always stop the server
        if server_process:
            logger.info("Stopping API server...")
            
            # Try to terminate gracefully first
            server_process.terminate()
            
            try:
                # Wait for process to terminate
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # If it doesn't terminate, kill it
                logger.warning("Server didn't terminate gracefully, killing it...")
                server_process.kill()

if __name__ == "__main__":
    sys.exit(main())
