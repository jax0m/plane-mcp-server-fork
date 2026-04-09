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

# Load a single variable from a file if not already set
# Args: $1=var_name, $2=file_path
load_var_from_file() {
    local var_name="$1"
    local file="$2"
    
    # Only try to load if variable is not already set
    if [ -n "${!var_name+x}" ]; then
        return 0  # Already set, skip
    fi
    
    if [ -f "$file" ]; then
        # Extract the value for this specific variable
        local value=$(grep -E "^${var_name}=" "$file" 2>/dev/null | head -1 | cut -d'=' -f2- | xargs)
        if [ -n "$value" ]; then
            export "$var_name=$value"
            return 0
        fi
    fi
    return 1
}

# Load each required variable individually with proper precedence
# Priority: OS env vars > .env > .env.test

# PLANE_API_KEY / PLANE_TEST_API_KEY
if [ -z "$PLANE_API_KEY" ]; then
    if ! load_var_from_file "PLANE_API_KEY" ".env"; then
        if ! load_var_from_file "PLANE_API_KEY" ".env.test"; then
            if ! load_var_from_file "PLANE_TEST_API_KEY" ".env"; then
                load_var_from_file "PLANE_TEST_API_KEY" ".env.test"
            fi
        fi
    fi
    # Map PLANE_TEST_API_KEY to PLANE_API_KEY if needed
    if [ -n "$PLANE_TEST_API_KEY" ] && [ -z "$PLANE_API_KEY" ]; then
        export PLANE_API_KEY="$PLANE_TEST_API_KEY"
    fi
fi

# PLANE_WORKSPACE_SLUG / PLANE_TEST_WORKSPACE_SLUG
if [ -z "$PLANE_WORKSPACE_SLUG" ]; then
    if ! load_var_from_file "PLANE_WORKSPACE_SLUG" ".env"; then
        if ! load_var_from_file "PLANE_WORKSPACE_SLUG" ".env.test"; then
            if ! load_var_from_file "PLANE_TEST_WORKSPACE_SLUG" ".env"; then
                load_var_from_file "PLANE_TEST_WORKSPACE_SLUG" ".env.test"
            fi
        fi
    fi
    # Map PLANE_TEST_WORKSPACE_SLUG to PLANE_WORKSPACE_SLUG if needed
    if [ -n "$PLANE_TEST_WORKSPACE_SLUG" ] && [ -z "$PLANE_WORKSPACE_SLUG" ]; then
        export PLANE_WORKSPACE_SLUG="$PLANE_TEST_WORKSPACE_SLUG"
    fi
fi

# PLANE_BASE_URL / PLANE_TEST_BASE_URL
if [ -z "$PLANE_BASE_URL" ]; then
    if ! load_var_from_file "PLANE_BASE_URL" ".env"; then
        if ! load_var_from_file "PLANE_BASE_URL" ".env.test"; then
            if ! load_var_from_file "PLANE_TEST_BASE_URL" ".env"; then
                load_var_from_file "PLANE_TEST_BASE_URL" ".env.test"
            fi
        fi
    fi
    # Map PLANE_TEST_BASE_URL to PLANE_BASE_URL if needed
    if [ -n "$PLANE_TEST_BASE_URL" ] && [ -z "$PLANE_BASE_URL" ]; then
        export PLANE_BASE_URL="$PLANE_TEST_BASE_URL"
    fi
fi

# PLANE_OAUTH_PROVIDER_CLIENT_ID
if [ -z "$PLANE_OAUTH_PROVIDER_CLIENT_ID" ]; then
    load_var_from_file "PLANE_OAUTH_PROVIDER_CLIENT_ID" ".env"
    load_var_from_file "PLANE_OAUTH_PROVIDER_CLIENT_ID" ".env.test"
fi

# PLANE_OAUTH_PROVIDER_CLIENT_SECRET
if [ -z "$PLANE_OAUTH_PROVIDER_CLIENT_SECRET" ]; then
    load_var_from_file "PLANE_OAUTH_PROVIDER_CLIENT_SECRET" ".env"
    load_var_from_file "PLANE_OAUTH_PROVIDER_CLIENT_SECRET" ".env.test"
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
    echo "  ✓ OAuth credentials configured - OAuth tests will run"
else
    echo "  ⊘ OAuth credentials not configured - OAuth tests will be skipped"
fi

echo ""
echo "Environment Validation:"

# Check if running in GitHub Actions
if [ -n "$GITHUB_ACTIONS" ]; then
    echo "  ✓ Running in GitHub Actions environment"
    echo "  ✓ Environment variables loaded from GitHub Secrets"
else
    echo "  Variable Sources:"
    echo "    PLANE_BASE_URL: ${PLANE_BASE_URL:-https://api.plane.so}"
    echo "    PLANE_WORKSPACE_SLUG: $PLANE_WORKSPACE_SLUG"
    echo "    PLANE_API_KEY: ${PLANE_API_KEY:0:10}..."
fi

# Validate environment variables are not defaults/placeholders
if [ "$PLANE_API_KEY" = "your_api_key_here" ] || [ -z "$PLANE_API_KEY" ]; then
    echo ""
    echo "❌ ERROR: PLANE_API_KEY is not configured or is using default value"
    echo "   Please set PLANE_API_KEY to your actual API key"
    exit 1
fi

if [ "$PLANE_WORKSPACE_SLUG" = "your_workspace_slug_here" ] || [ -z "$PLANE_WORKSPACE_SLUG" ]; then
    echo ""
    echo "❌ ERROR: PLANE_WORKSPACE_SLUG is not configured or is using default value"
    echo "   Please set PLANE_WORKSPACE_SLUG to your actual workspace slug"
    exit 1
fi

if [ "$PLANE_BASE_URL" = "https://api.plane.so" ]; then
    echo "  ⚠ Note: Using default PLANE_BASE_URL (https://api.plane.so)"
fi

echo "  ✓ All required environment variables validated"

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
