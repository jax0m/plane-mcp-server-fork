"""Test fixtures for Plane MCP Server.

This module provides transport-agnostic test fixtures that enable
the same test logic to run against different transport types:
- stdio: Direct process communication (recommended for CI/CD)
- http: HTTP transport with API key authentication
- oauth: OAuth transport (requires OAuth credentials)
"""

from .config import TransportConfig, load_config
from .transports import get_transport_fixture

__all__ = ["TransportConfig", "load_config", "get_transport_fixture"]
