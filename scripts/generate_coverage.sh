#!/bin/bash
set -x

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Use the venv's Python
PYTHON_BIN="$PROJECT_ROOT/venv/bin/python"

# Check if venv Python exists
if [ ! -f "$PYTHON_BIN" ]; then
    echo "Error: Virtual environment Python not found at $PYTHON_BIN"
    echo "Please ensure your virtual environment is set up correctly."
    exit 1
fi

echo "Do you want to use the --keepdb flag? (yes/no)"
read use_keepdb

if [ "$use_keepdb" == "yes" ]; then
    keep_db_flag="--keepdb"
else
    keep_db_flag=""
fi

echo "Running tests and generating coverage report (excluding migrations)..."

# Run tests with venv's Python
"$PYTHON_BIN" -m coverage run --rcfile=.coveragerc --source=. manage.py test $keep_db_flag

# Generate the HTML coverage report
"$PYTHON_BIN" -m coverage html

# Show the coverage summary with missing lines
"$PYTHON_BIN" -m coverage report -m

echo "Coverage report generated. Open 'htmlcov/index.html' to view the detailed report."