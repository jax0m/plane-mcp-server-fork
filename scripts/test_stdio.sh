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
echo "Running stdio-based integration tests..."
echo ""

# Run the stdio tests
uv run pytest tests/test_stdio_integration.py -v --tb=short "$@"

echo ""
echo "=========================================="
echo "Stdio test run complete!"
echo "=========================================="
