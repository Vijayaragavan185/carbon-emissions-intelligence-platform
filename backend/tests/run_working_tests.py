#!/usr/bin/env python3
"""Simple working test runner"""

import sys
import os
import subprocess

def main():
    # Get backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("🧪 Running Working Carbon Emissions Tests")
    print(f"📁 Backend directory: {backend_dir}")
    
    # Set environment
    env = os.environ.copy()
    env['PYTHONPATH'] = backend_dir
    
    # Test command
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_working_compliance.py", 
        "-v", "-s", "--tb=short"
    ]
    
    print(f"🚀 Running: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            cmd, 
            cwd=backend_dir, 
            env=env,
            text=True
        )
        
        if result.returncode == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️ Tests completed with return code: {result.returncode}")
            
    except Exception as e:
        print(f"💥 Error running tests: {e}")

if __name__ == "__main__":
    main()
