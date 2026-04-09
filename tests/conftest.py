"""Pytest configuration for Plane MCP Server tests."""

import os

import pytest

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def anyio_backend():
    """Set default async backend for pytest-asyncio."""
    return "asyncio"


def pytest_configure(config):
    """Register custom markers and configure skip logic."""
    config.addinivalue_line("markers", "oauth: mark test as requiring OAuth credentials")
    config.addinivalue_line("markers", "integration: full integration test against Plane API")
    config.addinivalue_line("markers", "http: HTTP transport mode test")


def pytest_collection_modifyitems(config, items):
    """Skip OAuth tests if credentials are not configured."""
    oauth_client_id = os.getenv("PLANE_OAUTH_PROVIDER_CLIENT_ID", "").strip()
    oauth_client_secret = os.getenv("PLANE_OAUTH_PROVIDER_CLIENT_SECRET", "").strip()

    has_oauth = bool(oauth_client_id and oauth_client_secret)

    if not has_oauth:
        # Skip OAuth-marked tests
        skip_oauth = pytest.mark.skip(reason="OAuth credentials not configured")
        for item in items:
            if "oauth" in item.keywords:
                item.add_marker(skip_oauth)

        # Also skip stateless HTTP OAuth tests (by class name)
        skip_oauth_http = pytest.mark.skip(reason="OAuth credentials not configured for HTTP tests")
        for item in items:
            if "TestStatelessHttpOAuth" in str(item):
                item.add_marker(skip_oauth_http)
