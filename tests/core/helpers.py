"""Shared helper utilities for tests.

These utilities are transport-agnostic and work with any MCP client.
"""

import json
import uuid
from typing import Any


def extract_result(result: Any) -> dict | list:
    """Extract data from an MCP tool result.

    Handles different result formats:
    - Pydantic models with structured_content
    - Content with text that may be JSON
    - Raw dict/list responses

    Args:
        result: The raw result from an MCP tool call

    Returns:
        The extracted data as a dict or list
    """
    # Handle Pydantic models with structured_content
    if hasattr(result, "structured_content") and result.structured_content is not None:
        return result.structured_content

    # Handle content with text
    if hasattr(result, "content") and result.content:
        content = result.content[0]
        if hasattr(content, "text"):
            try:
                return json.loads(content.text)
            except json.JSONDecodeError:
                return {"raw": content.text}

    # Return as-is if it's already a dict or list
    if isinstance(result, dict):
        return result
    if isinstance(result, list):
        return result

    return {}


def generate_test_id() -> str:
    """Generate a unique test identifier.

    Returns:
        A short hex string suitable for test resource naming
    """
    return uuid.uuid4().hex[:8]


def format_resource_name(prefix: str, test_id: str) -> str:
    """Format a test resource name with prefix and test ID.

    Args:
        prefix: Resource type prefix (e.g., "TEST", "PROJECT")
        test_id: Unique test identifier from generate_test_id()

    Returns:
        Formatted resource name
    """
    return f"{prefix}-{test_id}"
