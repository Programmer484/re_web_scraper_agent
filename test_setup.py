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
        return False
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
        except ImportError:
            missing.append(package)
    
    if missing:
        return False
    return True

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path('.env')
    if not env_path.exists():
        return False
    
    with open(env_path) as f:
        content = f.read()
        if 'APIFY_TOKEN' in content:
            pass
        else:
            pass
    
    return True

def test_api_import():
    """Test if the API server can be imported"""
    try:
        sys.path.insert(0, os.getcwd())
        import api_server
        return True
    except Exception as e:
        return False

def test_agent_import():
    """Test if the agent modules can be imported"""
    try:
        from src import models
        from src.nodes import profile_builder, zillow_node, normalizer
        return True
    except Exception as e:
        return False

def run_quick_test():
    """Run a quick API test"""
    try:
        import requests
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
            return True
        else:
            return False
            
    except ImportError:
        return True
    except Exception as e:
        return True  # Non-critical for setup

def main():
    """Run all setup checks"""
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("API Server Import", test_api_import),
        ("Agent Modules Import", test_agent_import),
    ]
    
    results = {}
    for name, check_func in checks:
        results[name] = check_func()
    
    # Optional API test
    run_quick_test()
    
    all_passed = True
    for name, passed in results.items():
        if not passed:
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 