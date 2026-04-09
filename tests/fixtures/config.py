"""Configuration loading for test fixtures.

Provides a unified configuration object that works across all transport types.
"""

import os
from dataclasses import dataclass


@dataclass
class TransportConfig:
    """Configuration for a specific transport type.

    Attributes:
        transport_type: The transport to use (stdio, http, oauth)
        api_key: Plane API key for authentication
        workspace_slug: Workspace slug for the API
        base_url: Plane API base URL
        mcp_url: MCP server URL (for HTTP transport)
        oauth_client_id: OAuth client ID (for OAuth transport)
        oauth_client_secret: OAuth client secret (for OAuth transport)
    """

    transport_type: str = "stdio"
    api_key: str = ""
    workspace_slug: str = ""
    base_url: str = "https://api.plane.so"
    mcp_url: str = "http://localhost:8211"
    oauth_client_id: str | None = None
    oauth_client_secret: str | None = None

    def has_plane_credentials(self) -> bool:
        """Check if Plane API credentials are configured."""
        return bool(self.api_key and self.workspace_slug)

    def has_oauth_credentials(self) -> bool:
        """Check if OAuth credentials are configured."""
        return bool(self.oauth_client_id and self.oauth_client_secret)

    def is_valid_for_transport(self) -> bool:
        """Check if configuration is valid for the selected transport."""
        if self.transport_type == "stdio":
            return self.has_plane_credentials()
        elif self.transport_type == "http":
            return self.has_plane_credentials()
        elif self.transport_type == "oauth":
            return self.has_oauth_credentials()
        return False


def load_config(override_transport: str | None = None) -> TransportConfig:
    """Load configuration from environment variables.

    Args:
        override_transport: Optional transport type override (for testing)

    Returns:
        TransportConfig populated from environment variables

    Raises:
        RuntimeError: If required credentials are missing for the transport
    """
    # Get transport type from environment or override
    transport_type = override_transport or os.getenv("TEST_TRANSPORT", "stdio").lower()

    # Load Plane API credentials
    # Support both PLANE_* and PLANE_TEST_* prefixes
    api_key = os.getenv("PLANE_API_KEY") or os.getenv("PLANE_TEST_API_KEY") or ""

    workspace_slug = os.getenv("PLANE_WORKSPACE_SLUG") or os.getenv("PLANE_TEST_WORKSPACE_SLUG") or ""

    base_url = os.getenv("PLANE_BASE_URL") or os.getenv("PLANE_TEST_BASE_URL") or "https://api.plane.so"

    mcp_url = os.getenv("PLANE_TEST_MCP_URL", "http://localhost:8211")

    # Load OAuth credentials
    oauth_client_id = os.getenv("PLANE_OAUTH_PROVIDER_CLIENT_ID")
    oauth_client_secret = os.getenv("PLANE_OAUTH_PROVIDER_CLIENT_SECRET")

    config = TransportConfig(
        transport_type=transport_type,
        api_key=api_key,
        workspace_slug=workspace_slug,
        base_url=base_url,
        mcp_url=mcp_url,
        oauth_client_id=oauth_client_id,
        oauth_client_secret=oauth_client_secret,
    )

    return config
