#!/bin/bash

echo "=== FMC Scraper Test Setup ==="
echo "This script installs test dependencies and runs pytest."
echo ""

# Check if system-wide Python packages are available
if command -v python3 &> /dev/null; then
    PYTHON3=$(command -v python3)
    echo "[OK] Found Python3: $PYTHON3"
else
    echo "[ERROR] Python3 not found"
    exit 1
fi

# Try to install with --break-system-packages (for system Python)
echo "[INFO] Attempting to install dependencies (may require --break-system-packages)"
echo ""

# Install core dependencies
echo "Installing: pytest, pytest-asyncio, responses, httpx, lbc, fastapi, uvicorn..."
$PYTHON3 -m pip install \
    pytest \
    pytest-asyncio \
    responses \
    httpx \
    lbc \
    fastapi \
    uvicorn \
    beautifulsoup4 \
    requests \
    python-dotenv \
    --break-system-packages \
    2>&1 | grep -E "(Successfully|already satisfied|ERROR|error)" || echo "[OK] Packages processed"

echo ""
echo "=== Running pytest ==="
cd "$(dirname "$0")"

# Run all tests
echo "Running: pytest tests/ -v --tb=short"
$PYTHON3 -m pytest tests/ -v --tb=short

# Capture exit code
EXIT_CODE=$?
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "[OK] All tests passed"
else
    echo "[WARN] Some tests failed or encountered errors (exit code: $EXIT_CODE)"
fi

exit $EXIT_CODE
