#!/usr/bin/env python3
"""
Pre-Deployment Validation Script for AURION Backend
Run this before deploying to catch common issues
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a critical file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ MISSING {description}: {filepath}")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path(__file__).parent / ".env"
    
    if not env_path.exists():
        print("❌ CRITICAL: .env file not found!")
        print("   Create .env from .env.example and fill in your values")
        return False
    
    print("✅ .env file exists")
    
    # Check for critical variables
    required_vars = [
        "MONGODB_URL",
        "REDIS_URL",
        "PINECONE_API_KEY",
        "JWT_SECRET_KEY",
        "MAIL_USERNAME",
        "MAIL_PASSWORD"
    ]
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    missing = []
    for var in required_vars:
        if f"{var}=" not in content or f"{var}=your" in content or f"{var}=..." in content:
            missing.append(var)
    
    if missing:
        print(f"⚠️  WARNING: These variables might not be set: {', '.join(missing)}")
        return False
    
    print("✅ All critical environment variables appear to be set")
    return True

def check_localhost_references():
    """Check for hardcoded localhost references"""
    print("\n🔍 Checking for hardcoded localhost/127.0.0.1 references...")
    
    files_to_check = [
        "app/main.py",
        "app/core/config.py",
        "app/email_service.py",
        "app/auth_flow.py"
    ]
    
    issues = []
    for file in files_to_check:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'localhost' in content.lower() or '127.0.0.1' in content:
                    # Check if it's in a comment or default value
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if ('localhost' in line.lower() or '127.0.0.1' in line) and \
                           not line.strip().startswith('#') and \
                           'default' not in line.lower() and \
                           'fallback' not in line.lower():
                            issues.append(f"{file}:{i}")
    
    if issues:
        print(f"⚠️  Found potential hardcoded URLs in:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ No hardcoded localhost references found")
        return True

def main():
    print("=" * 60)
    print("AURION Backend - Pre-Deployment Validation")
    print("=" * 60)
    print()
    
    all_good = True
    
    # Check critical files
    print("📋 Checking Critical Files...")
    all_good &= check_file_exists("requirements.txt", "Dependencies file")
    all_good &= check_file_exists("runtime.txt", "Python runtime specification")
    all_good &= check_file_exists("render.yaml", "Render configuration")
    all_good &= check_file_exists(".env.example", "Environment template")
    all_good &= check_file_exists("app/main.py", "Main application file")
    all_good &= check_file_exists("app/core/config.py", "Configuration file")
    print()
    
    # Check .env
    print("🔑 Checking Environment Configuration...")
    all_good &= check_env_file()
    print()
    
    # Check for localhost references
    all_good &= check_localhost_references()
    print()
    
    # Check Python version
    print("🐍 Python Version Check...")
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor >= 11:
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"⚠️  Python {python_version.major}.{python_version.minor}.{python_version.micro} (Recommended: 3.11+)")
    print()
    
    # Final verdict
    print("=" * 60)
    if all_good:
        print("✅ All checks passed! Ready for deployment")
        print()
        print("Next steps:")
        print("1. Push code to GitHub")
        print("2. Deploy on Render")
        print("3. Add environment variables in Render dashboard")
        return 0
    else:
        print("❌ Some issues found. Please fix them before deploying.")
        print()
        print("See documentation:")
        print("- ENV_SETUP_GUIDE.md for environment setup")
        print("- DEPLOYMENT_GUIDE.md for deployment steps")
        return 1

if __name__ == "__main__":
    sys.exit(main())
