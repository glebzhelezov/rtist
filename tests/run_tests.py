#!/usr/bin/env python
"""Test runner for mtrip."""

import sys
import unittest
import os

if __name__ == "__main__":
    # Add parent directory to path so we can import tests
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Discover and run all tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(os.path.dirname(os.path.abspath(__file__)), pattern="test_*.py")
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return appropriate exit code
    sys.exit(not result.wasSuccessful())