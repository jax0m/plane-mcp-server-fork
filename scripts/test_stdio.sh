#!/bin/bash
# Stdio-based test runner for Plane MCP Server
# Environment variable priority: OS env vars > .env > .env.test

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

echo "=========================================="
echo "Plane MCP Server - Stdio Test Runner"
echo "=========================================="

# Load a single variable from a file if not already set
# Args: $1=var_name, $2=file_path
load_var_from_file() {
    local var_name="$1"
    local file="$2"

    # Only try to load if variable is not already set
    if [ -n "${!var_name+x}" ]; then
        return 0
    fi

    if [ -f "$file" ]; then
        local value
        value=$(grep -E "^${var_name}=" "$file" 2>/dev/null | head -1 | cut -d'=' -f2- | xargs 2>/dev/null || true)
        if [ -n "$value" ]; then
            export "$var_name=$value"
            return 0
        fi
    fi
    return 1
}

# Load variables from .env files with fallback
# Priority: OS env vars > .env > .env.test
load_env_vars() {
    # PLANE_API_KEY
    load_var_from_file "PLANE_API_KEY" ".env" || load_var_from_file "PLANE_API_KEY" ".env.test" || true
    load_var_from_file "PLANE_TEST_API_KEY" ".env" || load_var_from_file "PLANE_TEST_API_KEY" ".env.test" || true

    # PLANE_WORKSPACE_SLUG
    load_var_from_file "PLANE_WORKSPACE_SLUG" ".env" || load_var_from_file "PLANE_WORKSPACE_SLUG" ".env.test" || true
    load_var_from_file "PLANE_TEST_WORKSPACE_SLUG" ".env" || load_var_from_file "PLANE_TEST_WORKSPACE_SLUG" ".env.test" || true

    # PLANE_BASE_URL
    load_var_from_file "PLANE_BASE_URL" ".env" || load_var_from_file "PLANE_BASE_URL" ".env.test" || true
    load_var_from_file "PLANE_TEST_BASE_URL" ".env" || load_var_from_file "PLANE_TEST_BASE_URL" ".env.test" || true

    # PLANE_OAUTH_PROVIDER_CLIENT_ID
    load_var_from_file "PLANE_OAUTH_PROVIDER_CLIENT_ID" ".env" || load_var_from_file "PLANE_OAUTH_PROVIDER_CLIENT_ID" ".env.test" || true

    # PLANE_OAUTH_PROVIDER_CLIENT_SECRET
    load_var_from_file "PLANE_OAUTH_PROVIDER_CLIENT_SECRET" ".env" || load_var_from_file "PLANE_OAUTH_PROVIDER_CLIENT_SECRET" ".env.test" || true
}

load_env_vars

# Map PLANE_TEST_* to PLANE_* if needed (only if PLANE_* not set)
[ -n "$PLANE_TEST_API_KEY" ] && [ -z "$PLANE_API_KEY" ] && export PLANE_API_KEY="$PLANE_TEST_API_KEY"
[ -n "$PLANE_TEST_WORKSPACE_SLUG" ] && [ -z "$PLANE_WORKSPACE_SLUG" ] && export PLANE_WORKSPACE_SLUG="$PLANE_TEST_WORKSPACE_SLUG"
[ -n "$PLANE_TEST_BASE_URL" ] && [ -z "$PLANE_BASE_URL" ] && export PLANE_BASE_URL="$PLANE_TEST_BASE_URL"

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

# Display OAuth status
if [ -n "$PLANE_OAUTH_PROVIDER_CLIENT_ID" ] && [ -n "$PLANE_OAUTH_PROVIDER_CLIENT_SECRET" ]; then
    echo "  ✓ OAuth credentials configured - OAuth tests will run"
else
    echo "  ⊘ OAuth credentials not configured - OAuth tests will be skipped"
fi

echo ""
echo "Running stdio-based integration tests..."
echo ""

# Run the stdio tests
uv run pytest tests/test_stdio_integration.py -v --tb=short "$@"

echo ""
echo "=========================================="
echo "Stdio test run complete!"
echo "=========================================="
