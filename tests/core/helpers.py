"""Shared helper utilities for tests.

These utilities are transport-agnostic and work with any MCP client.
"""

import json
import uuid
from typing import Any

from .test_client import AbstractTestClient


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


def get_cleanup_prefix() -> str:
    """Get the prefix used for test resources.

    Returns:
        Prefix string used to identify test resources
    """
    return "TEST"


class ResourceCleanup:
    """Context manager for automatic test resource cleanup.

    Tracks created resources and ensures they are cleaned up even if tests fail.

    Usage:
        async with ResourceCleanup(client) as cleanup:
            project_id = await client.call_tool("create_project", {...})
            cleanup.add_project(project_id)

            work_item_id = await client.call_tool("create_work_item", {...})
            cleanup.add_work_item(work_item_id, project_id)
    """

    def __init__(self, client: AbstractTestClient):
        self.client = client
        self.projects: list[str] = []
        self.work_items: list[tuple[str, str]] = []  # (work_item_id, project_id)
        self.epics: list[tuple[str, str]] = []  # (epic_id, project_id)
        self.milestones: list[tuple[str, str]] = []  # (milestone_id, project_id)
        self._cleanup_order_reversed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up all tracked resources in reverse order of creation."""
        # Clean up in reverse order: milestones -> epics -> work_items -> projects
        try:
            # Clean up milestones first (they reference work items)
            for milestone_id, project_id in reversed(self.milestones):
                try:
                    await self.client.call_tool(
                        "delete_milestone", {"project_id": project_id, "milestone_id": milestone_id}
                    )
                    print(f"  ✓ Cleaned up milestone: {milestone_id}")
                except Exception as e:
                    print(f"  ⚠ Could not delete milestone {milestone_id}: {e}")

            # Clean up epics (they may have child work items)
            for epic_id, project_id in reversed(self.epics):
                try:
                    await self.client.call_tool("delete_epic", {"project_id": project_id, "epic_id": epic_id})
                    print(f"  ✓ Cleaned up epic: {epic_id}")
                except Exception as e:
                    print(f"  ⚠ Could not delete epic {epic_id}: {e}")

            # Clean up work items
            for work_item_id, project_id in reversed(self.work_items):
                try:
                    await self.client.call_tool(
                        "delete_work_item", {"project_id": project_id, "work_item_id": work_item_id}
                    )
                    print(f"  ✓ Cleaned up work item: {work_item_id}")
                except Exception as e:
                    print(f"  ⚠ Could not delete work item {work_item_id}: {e}")

            # Clean up projects last (they contain everything else)
            for project_id in reversed(self.projects):
                try:
                    await self.client.call_tool("delete_project", {"project_id": project_id})
                    print(f"  ✓ Cleaned up project: {project_id}")
                except Exception as e:
                    print(f"  ⚠ Could not delete project {project_id}: {e}")
        except Exception as e:
            print(f"  ⚠ Error during cleanup: {e}")

    def add_project(self, project_id: str) -> None:
        """Track a project for cleanup."""
        self.projects.append(project_id)

    def add_work_item(self, work_item_id: str, project_id: str) -> None:
        """Track a work item for cleanup."""
        self.work_items.append((work_item_id, project_id))

    def add_epic(self, epic_id: str, project_id: str) -> None:
        """Track an epic for cleanup."""
        self.epics.append((epic_id, project_id))

    def add_milestone(self, milestone_id: str, project_id: str) -> None:
        """Track a milestone for cleanup."""
        self.milestones.append((milestone_id, project_id))


async def cleanup_leftover_projects(client: AbstractTestClient, prefix: str = "TEST") -> int:
    """Clean up leftover test projects from previous failed runs.

    Args:
        client: Transport-agnostic test client
        prefix: Prefix to identify test projects (default: "TEST")

    Returns:
        Number of projects cleaned up
    """
    cleaned_count = 0

    try:
        list_result = await client.call_tool("list_projects", {})
        projects = extract_result(list_result)

        if isinstance(projects, dict):
            projects = projects.get("results", [])

        for project in projects:
            if isinstance(project, dict):
                name = project.get("name", "")
                if name.startswith(f"{prefix}-"):
                    project_id = project.get("id")
                    if project_id:
                        try:
                            await client.call_tool("delete_project", {"project_id": project_id})
                            print(f"  ✓ Cleaned up leftover project: {name}")
                            cleaned_count += 1
                        except Exception as e:
                            print(f"  ⊘ Could not delete project {name}: {e}")
    except Exception as e:
        print(f"  ⊘ Error during leftover cleanup: {e}")

    return cleaned_count
