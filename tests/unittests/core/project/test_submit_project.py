# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for submit_project core logic."""

import pytest

from recnavi.core.project.submit_project import build_review_url
from recnavi.core.project.submit_project import submit_project
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientNotFoundError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from recnavi.exceptions.exceptions import NotificationSendError
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_notifier import MockNotifier


BASE_URL = "https://example.com/"


def _project_db() -> MockDatabase:
    return MockDatabase(
        initial_items=[
            {
                "projectId": "proj-1",
                "groupId": "group-1",
                "projectName": "Spring Menu",
                "ownerUserId": "owner-1",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "assignedUserIds": ["staff-1"],
                "status": "in_progress",
                "version": 1,
                "scenes": [],
            },
        ],
    )


def _users_db(*, email: str | None = "owner@example.com") -> MockDatabase:
    owner = {"userId": "owner-1", "userName": "Owner", "groupId": "group-1"}
    if email is not None:
        owner["email"] = email
    return MockDatabase(initial_items=[owner], key_names=("userId",))


def _user(user_id: str, role: UserRole) -> User:
    return User(
        user_id=user_id,
        user_name=f"Name {user_id}",
        group_id="group-1",
        role=role,
    )


async def _submit(
    *,
    user: User,
    notifier: MockNotifier,
    projects_db: MockDatabase | None = None,
    users_db: MockDatabase | None = None,
    project_id: str = "proj-1",
) -> None:
    await submit_project(
        projects_db=projects_db or _project_db(),
        users_db=users_db or _users_db(),
        notifier=notifier,
        base_url=BASE_URL,
        project_id=project_id,
        user=user,
    )


def test_build_review_url_joins_base_url_and_project_id():
    """Test trailing slashes on the base URL are normalized."""
    assert (
        build_review_url(base_url="https://example.com/", project_id="p1")
        == "https://example.com/project/p1"
    )


@pytest.mark.asyncio
async def test_submit_project_assigned_staff_notifies_owner():
    """Test assigned staff triggers exactly one email to the owner."""
    notifier = MockNotifier()

    result = await submit_project(
        projects_db=_project_db(),
        users_db=_users_db(),
        notifier=notifier,
        base_url=BASE_URL,
        project_id="proj-1",
        user=_user("staff-1", UserRole.STAFF),
    )

    assert result is None
    assert notifier.sent == [
        {
            "to_email": "owner@example.com",
            "project_name": "Spring Menu",
            "staff_name": "Name staff-1",
            "review_url": "https://example.com/project/proj-1",
        },
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user",
    [
        _user("staff-2", UserRole.STAFF),
        _user("owner-9", UserRole.OWNER),
    ],
)
async def test_submit_project_without_permission_sends_nothing(user):
    """Test users who fail validate_permission are rejected before any email."""
    notifier = MockNotifier()

    with pytest.raises(ClientAuthorizationError):
        await _submit(user=user, notifier=notifier)

    assert notifier.sent == []


@pytest.mark.asyncio
async def test_submit_project_owner_without_email_raises_unprocessable():
    """Test an owner without an email address cannot be notified."""
    notifier = MockNotifier()

    with pytest.raises(ClientUnprocessableEntityError):
        await _submit(
            user=_user("staff-1", UserRole.STAFF),
            notifier=notifier,
            users_db=_users_db(email=None),
        )

    assert notifier.sent == []


@pytest.mark.asyncio
async def test_submit_project_missing_owner_record_raises_unprocessable():
    """Test a missing owner user record is treated as having no email."""
    with pytest.raises(ClientUnprocessableEntityError):
        await _submit(
            user=_user("staff-1", UserRole.STAFF),
            notifier=MockNotifier(),
            users_db=MockDatabase(key_names=("userId",)),
        )


@pytest.mark.asyncio
async def test_submit_project_not_found_raises():
    """Test a missing project raises not found."""
    notifier = MockNotifier()

    with pytest.raises(ClientNotFoundError):
        await _submit(
            user=_user("staff-1", UserRole.STAFF),
            notifier=notifier,
            project_id="missing",
        )

    assert notifier.sent == []


@pytest.mark.asyncio
async def test_submit_project_propagates_notification_failure():
    """Test a delivery failure is not swallowed."""
    with pytest.raises(NotificationSendError):
        await _submit(
            user=_user("staff-1", UserRole.STAFF),
            notifier=MockNotifier(fail=True),
        )
