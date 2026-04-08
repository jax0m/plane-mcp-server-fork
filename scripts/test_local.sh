#!/bin/bash
# Local test runner for Plane MCP Server
# Uses .env file if present, or environment variables

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

echo "=========================================="
echo "Plane MCP Server - Local Test Runner"
echo "=========================================="

# Check for .env file
if [ -f ".env" ]; then
    echo "Found .env file, loading environment variables..."
    # Filter out comments and empty lines
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
elif [ -f ".env.test.local" ]; then
    echo "Found .env.test.local, loading environment variables..."
    export $(grep -v '^#' .env.test.local | grep -v '^$' | xargs)
else
    echo "Warning: No .env file found. Using current environment variables."
fi

# Validate required variables for integration tests
if [ -z "$PLANE_TEST_API_KEY" ]; then
    echo "Warning: PLANE_TEST_API_KEY not set. Integration tests will be skipped."
fi

if [ -z "$PLANE_TEST_WORKSPACE_SLUG" ]; then
    echo "Warning: PLANE_TEST_WORKSPACE_SLUG not set. Integration tests will be skipped."
fi

# Display OAuth status
if [ -n "$PLANE_OAUTH_PROVIDER_CLIENT_ID" ] && [ -n "$PLANE_OAUTH_PROVIDER_CLIENT_SECRET" ]; then
    echo "✓ OAuth credentials configured - OAuth tests will run"
else
    echo "⊘ OAuth credentials not configured - OAuth tests will be skipped"
fi

echo ""
echo "Starting MCP Server for integration tests..."
echo ""

# Start MCP server in background if integration tests will run
if uv run pytest --collect-only tests/test_integration.py 2>/dev/null | grep -q "test session"; then
    echo "Starting HTTP server..."
    uv run python -m plane_mcp http &
    SERVER_PID=$!
    echo "Server PID: $SERVER_PID"

    # Wait for server to be ready (up to 30 seconds)
    echo "Waiting for server to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8211/mcp > /dev/null 2>&1; then
            echo "✓ MCP Server is ready"
            break
        fi
        sleep 1
    done

    # Verify server is running
    if ! curl -s http://localhost:8211/mcp > /dev/null 2>&1; then
        echo "⚠ Warning: MCP Server failed to start. Integration tests may fail."
    fi
fi

echo ""
echo "Running tests..."
echo ""

# Run pytest with appropriate options
# -v for verbose output
# --tb=short for shorter tracebacks
# --strict-markers to catch undefined markers
# -m to run all tests (oauth, integration, http)
uv run pytest \
    tests/ \
    -v \
    --tb=short \
    --strict-markers \
    -m "oauth or integration or http" \
    "$@"

# Cleanup server if we started it
if [ -n "${SERVER_PID}" ]; then
    echo ""
    echo "Stopping MCP Server..."
    kill $SERVER_PID 2>/dev/null || true
fi

echo ""
echo "========================================="
echo "To push changes to remote, run:"
echo "  git add -A && git commit -m 'your message'"
echo "  git push origin test-improvements"
echo ""
echo "========================================="

echo ""
echo "=========================================="
echo "Test run complete!"
echo "=========================================="
