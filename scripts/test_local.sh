#!/bin/bash
# Local test runner for Plane MCP Server
# Environment variable priority: OS env vars > .env > .env.test

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

echo "=========================================="
echo "Plane MCP Server - Local Test Runner"
echo "=========================================="

# Track server PID for cleanup
SERVER_PID=""
cleanup() {
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        echo ""
        echo "Stopping MCP Server (PID: $SERVER_PID)..."
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
        echo "Server stopped."
    fi
}
trap cleanup EXIT INT TERM

# Load environment variables in priority order
# OS environment variables take precedence
load_env_file() {
    local file=$1
    if [ -f "$file" ]; then
        echo "Found $file, loading environment variables..."
        # Filter out comments and empty lines, only export if not already set
        while IFS='=' read -r key value; do
            # Skip comments and empty lines
            [[ "$key" =~ ^[[:space:]]*# ]] && continue
            [[ -z "$key" ]] && continue
            # Remove leading/trailing whitespace
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs)
            # Only set if not already in environment
            if [ -z "${!key+x}" ]; then
                export "$key=$value"
                echo "  Loaded: $key"
            else
                echo "  Skipped (already set): $key"
            fi
        done < "$file"
        return 0
    fi
    return 1
}

# Try to load environment files in order
if ! load_env_file ".env"; then
    if ! load_env_file ".env.test"; then
        echo "Warning: No .env or .env.test file found. Using current environment variables."
    fi
fi

# Validate required variables for integration tests
if [ -z "$PLANE_TEST_API_KEY" ]; then
    echo "Warning: PLANE_TEST_API_KEY not set. Integration tests will fail."
fi

if [ -z "$PLANE_TEST_WORKSPACE_SLUG" ]; then
    echo "Warning: PLANE_TEST_WORKSPACE_SLUG not set. Integration tests will fail."
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

# Check if port is already in use
if lsof -ti:8211 > /dev/null 2>&1; then
    echo "Port 8211 is already in use. Killing existing process..."
    kill $(lsof -ti:8211) 2>/dev/null || true
    sleep 1
fi

# Start MCP server in background
echo "Starting HTTP server..."
uv run python -m plane_mcp http > /tmp/plane_mcp_server.log 2>&1 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for server to be ready (up to 30 seconds)
echo "Waiting for server to start..."
for i in {1..30}; do
    if curl -s http://localhost:8211/mcp > /dev/null 2>&1; then
        echo "✓ MCP Server is ready"
        break
    fi
    # Check if server process is still running
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "✗ Server process died unexpectedly"
        echo "=== Server log output ==="
        cat /tmp/plane_mcp_server.log 2>/dev/null || echo "(log file not found)"
        echo "==========================="
        exit 1
    fi
    sleep 1
done

# Verify server is running
if ! curl -s http://localhost:8211/mcp > /dev/null 2>&1; then
    echo "⚠ Warning: MCP Server may not be fully ready. Integration tests may fail."
    echo "=== Server log output ==="
    cat /tmp/plane_mcp_server.log 2>/dev/null || echo "(log file not found)"
    echo "==========================="
fi

echo ""
echo "Running tests..."
echo ""

# Run pytest with appropriate options
TEST_RESULT=0
uv run pytest \
    tests/ \
    -v \
    --tb=short \
    --strict-markers \
    -m "oauth or integration or http" \
    "$@" || TEST_RESULT=$?

echo ""
echo "=========================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo "Test run complete - ALL TESTS PASSED!"
else
    echo "Test run complete - SOME TESTS FAILED"
    echo "Exit code: $TEST_RESULT"
fi
echo "=========================================="

# Cleanup will happen via trap
exit $TEST_RESULT
