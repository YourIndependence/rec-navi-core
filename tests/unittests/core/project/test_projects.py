# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for projects core logic."""

import pytest

from recnavi.core.project.projects import get_group_projects
from recnavi.core.project.projects import get_my_projects
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from tests.mockups.mock_database import MockDatabase


def _item(
    project_id: str,
    *,
    group_id: str = "group-123",
    owner: str = "owner-1",
    assigned: list[str] | None = None,
    day: int = 1,
) -> dict[str, object]:
    """Build a raw project item."""
    return {
        "projectId": project_id,
        "groupId": group_id,
        "projectName": f"Name {project_id}",
        "ownerUserId": owner,
        "createdAt": f"2026-09-{day:02d}T00:00:00Z",
        "updatedAt": f"2026-09-{day:02d}T00:00:00Z",
        "description": "",
        "status": "in_progress",
        "assignedUserIds": assigned or [],
        "scenes": [],
    }


def _user(role: UserRole, *, user_id: str = "owner-1") -> User:
    """Build a caller in group-123."""
    return User(
        user_id=user_id,
        user_name="name",
        role=role,
        group_id="group-123",
    )


@pytest.mark.asyncio
async def test_get_group_projects_returns_all_projects_of_group():
    """Owner sees every project of the group regardless of assignment."""
    mock_db = MockDatabase(
        initial_items=[
            _item("proj-1", assigned=["staff-1"], day=1),
            _item("proj-2", owner="owner-2", day=2),
            _item("proj-other", group_id="group-456", day=3),
        ],
    )

    projects, next_cursor = await get_group_projects(
        projects_db=mock_db,
        user=_user(UserRole.OWNER),
    )

    assert {p.project_id for p in projects} == {"proj-1", "proj-2"}
    assert next_cursor is None


@pytest.mark.asyncio
async def test_get_group_projects_returns_summaries_without_scenes():
    """Items are ProjectSummary and carry status but no scenes."""
    mock_db = MockDatabase(initial_items=[_item("proj-1")])

    projects, _ = await get_group_projects(
        projects_db=mock_db,
        user=_user(UserRole.OWNER),
    )

    dumped = projects[0].model_dump(by_alias=True)
    assert set(dumped) == {
        "projectId",
        "projectName",
        "description",
        "ownerUserId",
        "createdAt",
        "status",
    }


@pytest.mark.asyncio
async def test_get_group_projects_allows_admin():
    """Admin may list the group projects."""
    mock_db = MockDatabase(initial_items=[_item("proj-1")])

    projects, _ = await get_group_projects(
        projects_db=mock_db,
        user=_user(UserRole.ADMIN),
    )

    assert len(projects) == 1


@pytest.mark.asyncio
async def test_get_group_projects_rejects_staff():
    """Staff gets an authorization error."""
    mock_db = MockDatabase(initial_items=[_item("proj-1")])

    with pytest.raises(ClientAuthorizationError):
        await get_group_projects(
            projects_db=mock_db,
            user=_user(UserRole.STAFF, user_id="staff-1"),
        )


@pytest.mark.asyncio
async def test_get_group_projects_returns_empty_for_empty_group():
    """No projects gives an empty list and no cursor."""
    projects, next_cursor = await get_group_projects(
        projects_db=MockDatabase(),
        user=_user(UserRole.OWNER),
    )

    assert projects == []
    assert next_cursor is None


@pytest.mark.asyncio
async def test_get_group_projects_paginates_across_pages():
    """Following next_cursor visits every project exactly once."""
    mock_db = MockDatabase(
        initial_items=[_item(f"proj-{i}", day=i) for i in range(1, 6)],
    )
    owner = _user(UserRole.OWNER)

    seen: list[str] = []
    cursor = None
    for _ in range(5):
        projects, cursor = await get_group_projects(
            projects_db=mock_db,
            user=owner,
            limit=2,
            cursor=cursor,
        )
        seen.extend(p.project_id for p in projects)
        if cursor is None:
            break

    assert sorted(seen) == [f"proj-{i}" for i in range(1, 6)]
    assert cursor is None


@pytest.mark.asyncio
async def test_get_my_projects_returns_only_assigned_projects():
    """Only projects assigned to the user come back."""
    mock_db = MockDatabase(
        initial_items=[
            _item("proj-a", assigned=["staff-1", "staff-2"], day=1),
            _item("proj-b", assigned=["staff-2"], day=2),
            _item("proj-c", assigned=["staff-1"], day=3),
        ],
    )

    projects, next_cursor = await get_my_projects(
        projects_db=mock_db,
        user_id="staff-1",
        group_id="group-123",
    )

    assert {p.project_id for p in projects} == {"proj-a", "proj-c"}
    assert next_cursor is None


@pytest.mark.asyncio
async def test_get_my_projects_excludes_owned_but_unassigned():
    """Being the owner alone does not make a project show up."""
    mock_db = MockDatabase(
        initial_items=[_item("proj-1", owner="user_1", assigned=[])],
    )

    projects, _ = await get_my_projects(
        projects_db=mock_db,
        user_id="user_1",
        group_id="group-123",
    )

    assert projects == []


@pytest.mark.asyncio
async def test_get_my_projects_does_not_match_id_substrings():
    """user_1 must not match user_10 as owner or as assignee."""
    mock_db = MockDatabase(
        initial_items=[
            _item("proj-1", owner="user_10", assigned=["user_10"]),
        ],
    )

    projects, _ = await get_my_projects(
        projects_db=mock_db,
        user_id="user_1",
        group_id="group-123",
    )

    assert projects == []


@pytest.mark.asyncio
async def test_get_my_projects_does_not_return_other_group():
    """Assigned projects of another group are excluded."""
    mock_db = MockDatabase(
        initial_items=[
            _item("proj-mine", assigned=["staff-1"], day=1),
            _item(
                "proj-other",
                group_id="group-456",
                assigned=["staff-1"],
                day=2,
            ),
        ],
    )

    projects, _ = await get_my_projects(
        projects_db=mock_db,
        user_id="staff-1",
        group_id="group-123",
    )

    assert [p.project_id for p in projects] == ["proj-mine"]


@pytest.mark.asyncio
async def test_get_my_projects_limit_counts_examined_items():
    """limit is the number examined, so fewer may be returned with a cursor."""
    mock_db = MockDatabase(
        initial_items=[
            _item("proj-1", assigned=["staff-1"], day=1),
            _item("proj-2", assigned=["staff-2"], day=2),
            _item("proj-3", assigned=["staff-1"], day=3),
        ],
    )

    projects, next_cursor = await get_my_projects(
        projects_db=mock_db,
        user_id="staff-1",
        group_id="group-123",
        limit=2,
    )

    assert [p.project_id for p in projects] == ["proj-1"]
    assert next_cursor is not None


@pytest.mark.asyncio
async def test_get_my_projects_returns_cursor_on_empty_page():
    """An all-filtered page is empty but still carries a cursor."""
    mock_db = MockDatabase(
        initial_items=[
            _item("proj-1", assigned=["staff-2"], day=1),
            _item("proj-2", assigned=["staff-2"], day=2),
            _item("proj-3", assigned=["staff-1"], day=3),
        ],
    )

    projects, next_cursor = await get_my_projects(
        projects_db=mock_db,
        user_id="staff-1",
        group_id="group-123",
        limit=2,
    )

    assert projects == []
    assert next_cursor is not None

    next_projects, last_cursor = await get_my_projects(
        projects_db=mock_db,
        user_id="staff-1",
        group_id="group-123",
        limit=2,
        cursor=next_cursor,
    )

    assert [p.project_id for p in next_projects] == ["proj-3"]
    assert last_cursor is None
