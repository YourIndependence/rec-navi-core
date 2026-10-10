# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for the shared MockDatabase."""

import pytest

from recnavi.exceptions.exceptions import ClientConflictError
from recnavi.exceptions.exceptions import ClientNotFoundError
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_put_item_replaces_by_key_names():
    """Test put_item replaces the item with the same configured key."""
    database = MockDatabase(key_names=("groupId", "sceneId"))

    await database.put_item({"groupId": "g", "sceneId": "a", "v": 1})
    await database.put_item({"groupId": "g", "sceneId": "b", "v": 1})
    await database.put_item({"groupId": "g", "sceneId": "a", "v": 2})

    assert sorted((i["sceneId"], i["v"]) for i in database.items) == [
        ("a", 2),
        ("b", 1),
    ]


@pytest.mark.asyncio
async def test_put_item_replaces_by_default_key_fields():
    """Test put_item replaces by well-known key fields without key_names."""
    database = MockDatabase([{"projectId": "p1", "version": 1}])

    await database.put_item({"projectId": "p1", "version": 2})

    assert database.items == [{"projectId": "p1", "version": 2}]


@pytest.mark.asyncio
async def test_put_item_appends_when_no_key_matches():
    """Test put_item appends items without a matching key."""
    database = MockDatabase()

    await database.put_item({"projectId": "p1"})
    await database.put_item({"projectId": "p2"})

    assert len(database.items) == 2


@pytest.mark.asyncio
async def test_conditional_put_succeeds_when_version_matches():
    """Test a conditional put with the expected version replaces the item."""
    database = MockDatabase([{"projectId": "p1", "version": 1}])

    await database.put_item(
        {"projectId": "p1", "version": 2},
        condition_expression="version = :expected_version",
        expression_attribute_values={":expected_version": 1},
    )

    assert database.items == [{"projectId": "p1", "version": 2}]


@pytest.mark.asyncio
async def test_conditional_put_conflicts_when_version_differs():
    """Test a conditional put with a stale version raises a conflict."""
    database = MockDatabase([{"projectId": "p1", "version": 3}])

    with pytest.raises(ClientConflictError):
        await database.put_item(
            {"projectId": "p1", "version": 2},
            condition_expression="version = :expected_version",
            expression_attribute_values={":expected_version": 1},
        )

    assert database.items == [{"projectId": "p1", "version": 3}]


@pytest.mark.asyncio
async def test_conditional_put_conflicts_when_item_missing():
    """Test a conditional put on a missing item raises a conflict."""
    database = MockDatabase()

    with pytest.raises(ClientConflictError):
        await database.put_item(
            {"projectId": "p1", "version": 2},
            condition_expression="version = :expected_version",
            expression_attribute_values={":expected_version": 1},
        )


@pytest.mark.asyncio
async def test_update_item_sets_scene_fields_with_name_placeholders():
    """Test update_item applies scenes[i].field assignments."""
    database = MockDatabase(
        [
            {
                "projectId": "p1",
                "scenes": [{"sceneId": "s1"}, {"sceneId": "s2"}],
            },
        ],
    )

    result = await database.update_item(
        key={"projectId": "p1"},
        update_expression=(
            "SET scenes[1].#status = :status, scenes[1].video_key = :key, "
            "updatedAt = :now"
        ),
        condition_expression="scenes[1].sceneId = :sceneId",
        expression_attribute_names={"#status": "status"},
        expression_attribute_values={
            ":status": "REVIEWED",
            ":key": "k",
            ":now": "t",
            ":sceneId": "s2",
        },
    )

    assert result["scenes"][0] == {"sceneId": "s1"}
    assert result["scenes"][1] == {
        "sceneId": "s2",
        "status": "REVIEWED",
        "videoKey": "k",
    }
    assert result["updatedAt"] == "t"
    assert database.items == [result]


@pytest.mark.asyncio
async def test_update_item_conflicts_when_scene_id_differs():
    """Test update_item raises a conflict on a scene id mismatch."""
    database = MockDatabase(
        [{"projectId": "p1", "scenes": [{"sceneId": "s1"}]}],
    )

    with pytest.raises(ClientConflictError):
        await database.update_item(
            key={"projectId": "p1"},
            update_expression="SET scenes[0].#n = :n",
            condition_expression="scenes[0].sceneId = :sceneId",
            expression_attribute_names={"#n": "note"},
            expression_attribute_values={":n": "x", ":sceneId": "other"},
        )

    assert database.items[0]["scenes"] == [{"sceneId": "s1"}]


@pytest.mark.asyncio
async def test_update_item_conflicts_when_scene_index_out_of_range():
    """Test update_item raises a conflict when the scene index is absent."""
    database = MockDatabase([{"projectId": "p1", "scenes": []}])

    with pytest.raises(ClientConflictError):
        await database.update_item(
            key={"projectId": "p1"},
            update_expression="SET scenes[0].#n = :n",
            condition_expression="scenes[0].sceneId = :sceneId",
            expression_attribute_names={"#n": "note"},
            expression_attribute_values={":n": "x", ":sceneId": "s1"},
        )


@pytest.mark.asyncio
async def test_update_item_raises_not_found_for_unknown_key():
    """Test update_item raises ClientNotFoundError for a missing item."""
    database = MockDatabase()

    with pytest.raises(ClientNotFoundError):
        await database.update_item(
            key={"projectId": "missing"},
            update_expression="SET #n = :n",
            expression_attribute_names={"#n": "note"},
            expression_attribute_values={":n": "x"},
        )


@pytest.mark.asyncio
async def test_scan_paginates_and_delete_item_removes():
    """Test scan pagination and delete_item behave like a table."""
    database = MockDatabase([{"projectId": f"p{i}"} for i in range(3)])

    first = await database.scan(limit=2)
    second = await database.scan(
        limit=2,
        exclusive_start_key=first.last_evaluated_key,
    )
    await database.delete_item({"projectId": "p0"})

    assert [i["projectId"] for i in first.items] == ["p0", "p1"]
    assert [i["projectId"] for i in second.items] == ["p2"]
    assert second.last_evaluated_key is None
    assert [i["projectId"] for i in database.items] == ["p1", "p2"]
