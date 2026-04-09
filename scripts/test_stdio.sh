#!/bin/bash
# Stdio-based test runner for Plane MCP Server
# This runs the MCP server in stdio mode and tests communicate via stdin/stdout

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

echo "=========================================="
echo "Plane MCP Server - Stdio Test Runner"
echo "=========================================="

# Load environment variables in priority order
load_env_file() {
    local file=$1
    if [ -f "$file" ]; then
        echo "Found $file, loading environment variables..."
        while IFS='=' read -r key value; do
            [[ "$key" =~ ^[[:space:]]*# ]] && continue
            [[ -z "$key" ]] && continue
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs)
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

if ! load_env_file ".env"; then
    if ! load_env_file ".env.test"; then
        echo "Warning: No .env or .env.test file found."
    fi
fi

# Map test environment variables to stdio mode variables
# PLANE_TEST_* -> PLANE_*
if [ -z "$PLANE_API_KEY" ] && [ -n "$PLANE_TEST_API_KEY" ]; then
    export PLANE_API_KEY="$PLANE_TEST_API_KEY"
fi

if [ -z "$PLANE_WORKSPACE_SLUG" ] && [ -n "$PLANE_TEST_WORKSPACE_SLUG" ]; then
    export PLANE_WORKSPACE_SLUG="$PLANE_TEST_WORKSPACE_SLUG"
fi

if [ -z "$PLANE_BASE_URL" ] && [ -n "$PLANE_TEST_BASE_URL" ]; then
    export PLANE_BASE_URL="$PLANE_TEST_BASE_URL"
fi

# Validate required variables
if [ -z "$PLANE_API_KEY" ]; then
    echo "Error: PLANE_API_KEY is required for stdio mode"
    exit 1
fi

if [ -z "$PLANE_WORKSPACE_SLUG" ]; then
    echo "Error: PLANE_WORKSPACE_SLUG is required for stdio mode"
    exit 1
fi

echo ""
echo "Environment Validation:"

# Check if running in GitHub Actions
if [ -n "$GITHUB_ACTIONS" ]; then
    echo "  ✓ Running in GitHub Actions environment"
    echo "  ✓ Environment variables loaded from GitHub Secrets"
else
    echo "  PLANE_BASE_URL: ${PLANE_BASE_URL:-https://api.plane.so}"
    echo "  PLANE_WORKSPACE_SLUG: $PLANE_WORKSPACE_SLUG"
    echo "  PLANE_API_KEY: ${PLANE_API_KEY:0:10}..."
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
echo "Running stdio-based integration tests..."
echo ""

# Run modular transport-agnostic tests
echo "=========================================="
echo "Running modular transport-agnostic tests"
echo "=========================================="
uv run pytest tests/test_modules/ -v --tb=short "$@"
TEST_RESULT=$?

if [ $TEST_RESULT -ne 0 ]; then
    echo ""
    echo "=========================================="
    echo "Tests failed!"
    echo "=========================================="
    exit 1
fi

echo ""
echo "=========================================="
echo "All tests passed!"
echo "=========================================="
