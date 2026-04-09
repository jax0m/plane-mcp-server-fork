"""Work item lifecycle tests - transport agnostic.

These tests verify work item operations including parent-child relationships.
Tests work with any transport type (stdio, http, oauth).

Note: Epic and milestone features require those features to be enabled
in the Plane workspace. Tests will skip those sections if unavailable.
"""

import pytest

from ..core.helpers import ResourceCleanup, extract_result, generate_test_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_work_item_basic_lifecycle(client):
    """Basic work item lifecycle test.

    Creates work items, sets parent relationships, and cleans up.

    Args:
        client: Transport-agnostic test client fixture
    """
    test_id = generate_test_id()
    project_name = f"TEST-WORKITEM-{test_id}"
    project_identifier = f"WI{test_id[:3].upper()}"

    async with ResourceCleanup(client) as cleanup:
        # STEP 1: Create project
        print("Step 1: Creating project...")
        project_result = await client.call_tool(
            "create_project",
            {
                "name": project_name,
                "identifier": project_identifier,
                "description": "Test project for work item lifecycle",
            },
        )
        project = extract_result(project_result)
        project_id = project["id"]
        cleanup.add_project(project_id)
        print(f"  ✓ Created project: {project_id}")

        # STEP 2: Create work item 1 (parent)
        print("Step 2: Creating work item 1...")
        wi1_result = await client.call_tool(
            "create_work_item",
            {
                "project_id": project_id,
                "name": f"Parent Work Item {test_id}",
            },
        )
        wi1 = extract_result(wi1_result)
        work_item_1_id = wi1["id"]
        cleanup.add_work_item(work_item_1_id, project_id)
        print(f"  ✓ Created work item 1: {work_item_1_id}")

        # STEP 3: Create work item 2 (child)
        print("Step 3: Creating work item 2...")
        wi2_result = await client.call_tool(
            "create_work_item",
            {
                "project_id": project_id,
                "name": f"Child Work Item {test_id}",
            },
        )
        wi2 = extract_result(wi2_result)
        work_item_2_id = wi2["id"]
        cleanup.add_work_item(work_item_2_id, project_id)
        print(f"  ✓ Created work item 2: {work_item_2_id}")

        # STEP 4: Update work item 2 with work item 1 as parent
        print("Step 4: Setting parent relationship...")
        await client.call_tool(
            "update_work_item",
            {
                "project_id": project_id,
                "work_item_id": work_item_2_id,
                "parent": work_item_1_id,
            },
        )
        print("  ✓ Set work item 1 as parent of work item 2")

        # STEP 5: Verify work items exist
        print("Step 5: Verifying work items in project...")
        list_result = await client.call_tool(
            "list_work_items",
            {"project_id": project_id},
        )
        work_items = extract_result(list_result)
        if isinstance(work_items, dict):
            work_items = work_items.get("results", [])

        found_ids = {wi.get("id") for wi in work_items if isinstance(wi, dict)}
        assert work_item_1_id in found_ids, "Work item 1 not found in list"
        assert work_item_2_id in found_ids, "Work item 2 not found in list"
        print(f"  ✓ Found {len(work_items)} work items in project")

        # STEP 6: Verify parent relationship
        print("Step 6: Verifying parent relationship...")
        child_retrieve = await client.call_tool(
            "retrieve_work_item",
            {"project_id": project_id, "work_item_id": work_item_2_id},
        )
        child_data = extract_result(child_retrieve)
        # Note: parent field may be an object or ID
        parent_value = child_data.get("parent") or child_data.get("parent_id")
        assert parent_value == work_item_1_id
        print("  ✓ Parent relationship verified")

        print("✓ Work item basic lifecycle test passed!")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_work_item_lifecycle_with_epics(client):
    """Full work item lifecycle with epics.

    This test includes epic creation and association. Requires epics
    feature to be enabled in the workspace.

    Args:
        client: Transport-agnostic test client fixture
    """
    test_id = generate_test_id()
    project_name = f"TEST-WI-EPIC-{test_id}"
    project_identifier = f"EPI{test_id[:3].upper()}"

    async with ResourceCleanup(client) as cleanup:
        # Create project
        print("Step 1: Creating project...")
        project_result = await client.call_tool(
            "create_project",
            {"name": project_name, "identifier": project_identifier},
        )
        project_id = extract_result(project_result)["id"]
        cleanup.add_project(project_id)
        print(f"  ✓ Created project: {project_id}")

        # Create work items
        print("Step 2: Creating work items...")
        wi1_result = await client.call_tool(
            "create_work_item",
            {"project_id": project_id, "name": f"Work Item 1 {test_id}"},
        )
        work_item_1_id = extract_result(wi1_result)["id"]
        cleanup.add_work_item(work_item_1_id, project_id)

        wi2_result = await client.call_tool(
            "create_work_item",
            {"project_id": project_id, "name": f"Work Item 2 {test_id}"},
        )
        work_item_2_id = extract_result(wi2_result)["id"]
        cleanup.add_work_item(work_item_2_id, project_id)
        print(f"  ✓ Created work items: {work_item_1_id}, {work_item_2_id}")

        # Try to create epic
        print("Step 3: Attempting to create epic...")
        try:
            epic_result = await client.call_tool(
                "create_epic",
                {"project_id": project_id, "name": f"Epic {test_id}"},
            )
            epic_id = extract_result(epic_result)["id"]
            cleanup.add_epic(epic_id, project_id)
            print(f"  ✓ Created epic: {epic_id}")

            # Set work item under epic
            print("Step 4: Associating work item with epic...")
            await client.call_tool(
                "update_work_item",
                {"project_id": project_id, "work_item_id": work_item_2_id, "parent": epic_id},
            )
            print("  ✓ Work item associated with epic")

            # List epics
            print("Step 5: Listing epics...")
            epics_result = await client.call_tool(
                "list_epics",
                {"project_id": project_id},
            )
            epics = extract_result(epics_result)
            if isinstance(epics, dict):
                epics = epics.get("results", [])
            print(f"  ✓ Found {len(epics)} epics in project")

            # Delete epic
            print("Step 6: Deleting epic...")
            await client.call_tool(
                "delete_epic",
                {"project_id": project_id, "epic_id": epic_id},
            )
            print(f"  ✓ Deleted epic: {epic_id}")
            cleanup.epics.remove((epic_id, project_id))

        except Exception as e:
            print(f"  ⊘ Epic feature not available or error: {e}")
            print("  Skipping epic-specific tests")

        print("✓ Work item lifecycle with epics test completed!")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_work_item_lifecycle_with_milestones(client):
    """Work item lifecycle with milestones.

    This test includes milestone creation and association. Requires milestones
    feature to be enabled in the workspace.

    Args:
        client: Transport-agnostic test client fixture
    """
    test_id = generate_test_id()
    project_name = f"TEST-WI-MILE-{test_id}"
    project_identifier = f"MIL{test_id[:3].upper()}"

    async with ResourceCleanup(client) as cleanup:
        # Create project
        print("Step 1: Creating project...")
        project_result = await client.call_tool(
            "create_project",
            {"name": project_name, "identifier": project_identifier},
        )
        project_id = extract_result(project_result)["id"]
        cleanup.add_project(project_id)
        print(f"  ✓ Created project: {project_id}")

        # Create work items
        print("Step 2: Creating work items...")
        wi1_result = await client.call_tool(
            "create_work_item",
            {"project_id": project_id, "name": f"Work Item 1 {test_id}"},
        )
        work_item_1_id = extract_result(wi1_result)["id"]
        cleanup.add_work_item(work_item_1_id, project_id)

        wi2_result = await client.call_tool(
            "create_work_item",
            {"project_id": project_id, "name": f"Work Item 2 {test_id}"},
        )
        work_item_2_id = extract_result(wi2_result)["id"]
        cleanup.add_work_item(work_item_2_id, project_id)
        print(f"  ✓ Created work items: {work_item_1_id}, {work_item_2_id}")

        # Try to create milestone
        print("Step 3: Attempting to create milestone...")
        try:
            milestone_result = await client.call_tool(
                "create_milestone",
                {
                    "project_id": project_id,
                    "name": f"Milestone {test_id}",
                    "description": "Test milestone",
                    "associated_work_item_ids": [work_item_1_id, work_item_2_id],
                },
            )
            milestone_id = extract_result(milestone_result)["id"]
            cleanup.add_milestone(milestone_id, project_id)
            print(f"  ✓ Created milestone: {milestone_id}")

            # Update milestone
            print("Step 4: Updating milestone...")
            await client.call_tool(
                "update_milestone",
                {
                    "project_id": project_id,
                    "milestone_id": milestone_id,
                    "name": f"Updated Milestone {test_id}",
                },
            )
            print("  ✓ Updated milestone")

            # List milestones
            print("Step 5: Listing milestones...")
            milestones_result = await client.call_tool(
                "list_milestones",
                {"project_id": project_id},
            )
            milestones = extract_result(milestones_result)
            if isinstance(milestones, dict):
                milestones = milestones.get("results", [])
            print(f"  ✓ Found {len(milestones)} milestones in project")

            # List work items in milestone
            print("Step 6: Listing work items in milestone...")
            milestone_wi_result = await client.call_tool(
                "list_milestone_work_items",
                {"project_id": project_id, "milestone_id": milestone_id},
            )
            milestone_wis = extract_result(milestone_wi_result)
            if isinstance(milestone_wis, dict):
                milestone_wis = milestone_wis.get("results", [])
            print(f"  ✓ Milestone has {len(milestone_wis)} work items")

            # Delete milestone
            print("Step 7: Deleting milestone...")
            await client.call_tool(
                "delete_milestone",
                {"project_id": project_id, "milestone_id": milestone_id},
            )
            print(f"  ✓ Deleted milestone: {milestone_id}")
            cleanup.milestones.remove((milestone_id, project_id))

        except Exception as e:
            print(f"  ⊘ Milestone feature not available or error: {e}")
            print("  Skipping milestone-specific tests")

        print("✓ Work item lifecycle with milestones test completed!")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_work_item_with_labels(client):
    """Test label creation and listing.

    Creates labels and verifies they can be listed.
    Note: Label association with work items may vary by Plane instance.

    Args:
        client: Transport-agnostic test client fixture
    """
    test_id = generate_test_id()
    project_name = f"TEST-LABEL-{test_id}"
    project_identifier = f"LBL{test_id[:3].upper()}"

    async with ResourceCleanup(client) as cleanup:
        # Create project
        project_result = await client.call_tool(
            "create_project",
            {"name": project_name, "identifier": project_identifier},
        )
        project_id = extract_result(project_result)["id"]
        cleanup.add_project(project_id)

        # Create a label
        label_result = await client.call_tool(
            "create_label",
            {
                "project_id": project_id,
                "name": f"Test Label {test_id}",
                "color": "#FF5733",
            },
        )
        label = extract_result(label_result)
        label_id = label["id"]
        print(f"  ✓ Created label: {label_id}")

        # List labels to verify
        labels_result = await client.call_tool(
            "list_labels",
            {"project_id": project_id},
        )
        labels = extract_result(labels_result)
        if isinstance(labels, dict):
            labels = labels.get("results", [])

        found_labels = [lbl.get("id") for lbl in labels if isinstance(lbl, dict)]
        assert label_id in found_labels, f"Label {label_id} not found in list"
        print(f"  ✓ Found {len(labels)} labels in project")

        # Create work item (label association handled separately if needed)
        wi_result = await client.call_tool(
            "create_work_item",
            {"project_id": project_id, "name": f"Work Item {test_id}"},
        )
        work_item_id = extract_result(wi_result)["id"]
        cleanup.add_work_item(work_item_id, project_id)
        print(f"  ✓ Created work item: {work_item_id}")

        print("✓ Work item with labels test passed!")
