#!/usr/bin/env python3
"""
Script to update API keys in the .env file with the new values provided by the user.
"""

import os
from pathlib import Path

def update_env_file():
    """Update the .env file with new API keys."""
    env_file = Path(".env")
    
    # New API keys provided by user
    new_keys = {
        "NLP_CLOUD_API_KEY": "0613cee2b450d26427a99605203450c4983ffa6f",
        "GEMINI_API_KEY": "AIzaSyCOfh49maEBTDLLjh7HNJpfC2jDVYFBOSc"
    }
    
    # Read existing .env file
    env_content = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_content[key] = value
    
    # Update with new keys
    env_content.update(new_keys)
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.write("# AURION Backend Environment Variables\n")
        f.write("# Updated with new API keys\n\n")
        
        # Write all keys
        for key, value in env_content.items():
            f.write(f"{key}={value}\n")
    
    print("✅ Updated .env file with new API keys:")
    for key, value in new_keys.items():
        print(f"  {key}: {value[:10]}...")

if __name__ == "__main__":
    update_env_file()
