"""Transport-agnostic test modules.

This package contains test suites that can run against any transport type
(stdio, http, oauth) without modification.

Test modules are organized by Plane domain:
- test_projects: Project CRUD operations
- test_work_items: Work item lifecycle
- test_epics: Epic management
- test_milestones: Milestone operations
- test_tool_registry: Tool availability verification

Each test uses the `client` fixture which automatically routes to the
configured transport type.
"""

__all__ = []
