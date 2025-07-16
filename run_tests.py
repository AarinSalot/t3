#!/usr/bin/env python3
"""
Test runner script for the Flask Employee API.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py -v           # Run with verbose output
    python run_tests.py --cov        # Run with coverage report
    python run_tests.py --help       # Show help
"""

import sys
import subprocess
import os

def run_tests():
    """Run the test suite with pytest."""
    
    # Ensure we're in the project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Base pytest command
    cmd = ['python3', '-m', 'pytest']
    
    # Add arguments from command line
    if len(sys.argv) > 1:
        if '--help' in sys.argv or '-h' in sys.argv:
            print(__doc__)
            return
        
        # Add custom arguments
        for arg in sys.argv[1:]:
            if arg == '--cov':
                # Full coverage report
                cmd.extend(['--cov=app', '--cov-report=term-missing', '--cov-report=html'])
            elif arg == '-v' or arg == '--verbose':
                cmd.append('-v')
            elif arg == '--fast':
                # Skip slow tests
                cmd.extend(['-m', 'not slow'])
            else:
                cmd.append(arg)
    else:
        # Default: run all tests with basic coverage
        cmd.extend(['--cov=app', '--cov-report=term-missing'])
    
    print(f"Running: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        # Run the tests
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code) 