# run_tests.py
import pytest
import sys

if __name__ == "__main__":
    # Run tests with verbose output and coverage
    result = pytest.main([
        "-v",           # verbose output
        "--tb=short",   # shorter tracebacks
        "--cov=src",    # measure coverage of src/
        "--cov-report=term-missing",  # show missing lines
        "tests/"
    ])
    sys.exit(result)