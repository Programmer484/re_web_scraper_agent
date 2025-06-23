#!/usr/bin/env python3
"""
Simple test script to verify the property search microservice setup
Run this before deploying to ensure everything works correctly
"""

import sys
import os
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    print(f"✅ Python version {sys.version.split()[0]} is compatible")
    return True

def check_dependencies():
    """Check if required packages can be imported"""
    required_packages = [
        'fastapi',
        'uvicorn', 
        'pydantic',
        'python-dotenv',
        'apify_client',
        'grafi'
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == 'python-dotenv':
                import dotenv
            elif package == 'apify_client':
                import apify_client
            elif package == 'grafi':
                import grafi
            else:
                __import__(package)
            print(f"✅ {package} - installed")
        except ImportError:
            print(f"❌ {package} - missing")
            missing.append(package)
    
    if missing:
        print(f"\n🔧 Install missing packages: pip install {' '.join(missing)}")
        return False
    return True

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env file not found")
        print("📝 Create .env file with: APIFY_TOKEN=your_token_here")
        return False
    
    print("✅ .env file found")
    
    # Check for required variables
    with open(env_path) as f:
        content = f.read()
        if 'APIFY_TOKEN' in content:
            print("✅ APIFY_TOKEN found in .env")
        else:
            print("⚠️  APIFY_TOKEN not found in .env (may cause API errors)")
    
    return True

def test_api_import():
    """Test if the API server can be imported"""
    try:
        sys.path.insert(0, os.getcwd())
        import api_server
        print("✅ API server imports successfully")
        return True
    except Exception as e:
        print(f"❌ API server import failed: {e}")
        return False

def test_agent_import():
    """Test if the agent modules can be imported"""
    try:
        from src import models
        from src.nodes import profile_builder, zillow_node, normalizer
        print("✅ Agent modules import successfully")
        return True
    except Exception as e:
        print(f"❌ Agent modules import failed: {e}")
        return False

def run_quick_test():
    """Run a quick API test"""
    try:
        import requests
        print("\n🧪 Running quick API test...")
        
        # Start server in background (this is just a test)
        import threading
        import time
        from api_server import app
        import uvicorn
        
        def run_server():
            uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(3)  # Give server time to start
        
        # Test health endpoint
        response = requests.get("http://127.0.0.1:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ API health check passed")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
            
    except ImportError:
        print("⚠️  Requests not installed, skipping API test")
        print("   Install with: pip install requests")
        return True
    except Exception as e:
        print(f"⚠️  API test failed: {e}")
        return True  # Non-critical for setup

def main():
    """Run all setup checks"""
    print("🔍 Property Search Microservice Setup Check")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("API Server Import", test_api_import),
        ("Agent Modules Import", test_agent_import),
    ]
    
    results = {}
    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        results[name] = check_func()
    
    # Optional API test
    run_quick_test()
    
    print("\n" + "=" * 50)
    print("📊 SETUP SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All checks passed! Your microservice is ready to deploy.")
        print("\n🚀 Next steps:")
        print("1. Run: python api_server.py")
        print("2. Test: curl http://localhost:8000/health")
        print("3. View docs: http://localhost:8000/docs")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above before deploying.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 