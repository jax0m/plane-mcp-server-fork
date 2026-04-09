"""Core utilities for transport-agnostic testing.

This module provides shared utilities used across all test modules,
independent of the transport type being tested.
"""

from .helpers import extract_result, generate_test_id
from .test_client import AbstractTestClient, HttpTestClient, StdioTestClient

__all__ = [
    "extract_result",
    "generate_test_id",
    "AbstractTestClient",
    "StdioTestClient",
    "HttpTestClient",
]
