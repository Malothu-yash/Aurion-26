"""
Startup script for AURION backend server.
Ensures proper working directory and environment loading.
"""
import os
import sys
import subprocess

# Change to the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Add to Python path
sys.path.insert(0, script_dir)

print(f"Working directory: {os.getcwd()}")
print(f"Python path includes: {script_dir}")
print(f".env file exists: {os.path.exists('.env')}")
print("\nStarting AURION server...\n")

# Start uvicorn
subprocess.run([
    sys.executable, "-m", "uvicorn",
    "app.main:app",
    "--reload",
    "--host", "0.0.0.0",
    "--port", "8000"
])
